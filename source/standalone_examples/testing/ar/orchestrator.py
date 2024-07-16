# Copyright 2024 Amazon.com, Inc. or its affiliates. All Rights Reserved.

import logging
import os
import sys
from typing import List, Sequence

import carb
import omni
import omni.replicator.core as rep
from omni.isaac.core import SimulationContext
from omni.isaac.core.utils.carb import set_carb_setting
from omni.isaac.kit import SimulationApp
from pxr import PhysxSchema, Sdf, Usd
from renderer import Renderer
from SDG_CLI import logger
from usdrt import Usd as usdrt_Usd

RENDERFRAME_AT_0 = True


def create_renderers(output_path: str, num_subframes: int) -> List[Renderer]:
    renderers: List[Renderer] = []

    iseg_writer: rep.Writer = rep.WriterRegistry.get("BasicWriter")
    iseg_writer.initialize(output_dir=os.path.join(output_path, "00001", "1"), instance_segmentation=True)

    rgb_writer: rep.Writer = rep.WriterRegistry.get("BasicWriter")
    rgb_writer.initialize(output_dir=os.path.join(output_path, "00001", "1"), rgb=True)

    renderers.append(
        Renderer(
            camera_path="/World/Cameras/Front_Top_Cam",
            resolution=(512, 512),
            writers=[rgb_writer, iseg_writer],
            subframes=num_subframes,
            write_info_prim_path="/World/box",
        )
    )

    iseg_writer2: rep.Writer = rep.WriterRegistry.get("BasicWriter")
    iseg_writer2.initialize(output_dir=os.path.join(output_path, "00001", "2"), instance_segmentation=True)

    rgb_writer2: rep.Writer = rep.WriterRegistry.get("BasicWriter")
    rgb_writer2.initialize(output_dir=os.path.join(output_path, "00001", "2"), rgb=True)

    renderers.append(
        Renderer(
            camera_path="/World/Cameras/Front_Top_Cam",
            resolution=(1330, 758),
            writers=[rgb_writer2, iseg_writer2],
            subframes=num_subframes,
            write_info_prim_path="/World/item0",
        )
    )

    rgb_writer3: rep.Writer = rep.WriterRegistry.get("BasicWriter")
    rgb_writer3.initialize(output_dir=os.path.join(output_path, "00001", "3"), rgb=True)
    renderers.append(
        Renderer(
            camera_path="/World/Cameras/Front_Top_Cam",
            resolution=(1330, 758),
            writers=[rgb_writer3],
            subframes=num_subframes,
            write_info_prim_path="/World/Torus",
        )
    )

    return renderers


def create_simulation_context(physics_scene_prim) -> SimulationContext:
    if physics_scene_prim:
        physics_scene_api = PhysxSchema.PhysxSceneAPI(physics_scene_prim)
        enable_gpu_dynamics = physics_scene_api.GetEnableGPUDynamicsAttr().Get()

        if enable_gpu_dynamics:  # Ideally NVIDIA's code should handle this case
            logger.info("Use GPU")
            return SimulationContext(
                stage_units_in_meters=1.0,
                physics_prim_path=str(physics_scene_prim.GetPath()),
                set_defaults=False,
                device="cuda",
            )
        return SimulationContext(
            stage_units_in_meters=1.0,
            physics_prim_path=str(physics_scene_prim.GetPath()),
            set_defaults=False,
        )
    return SimulationContext(
        stage_units_in_meters=1.0,
        set_defaults=False,
    )


class Orchestrator:
    """Handles the loading, layering and creation of the components required for SDG as well as its general flow."""

    def __init__(
        self,
        scene: str,
        kit: SimulationApp,
        num_frames: int,
        num_subframes: int,
        num_steps: int,
        output_path: str,
        fabric: str,
        debug: bool,
    ) -> None:
        """Sets up the whole scene and renderers as well as omniverse required structures.

        This is done once per data generation.
        """
        # getting kit and carb settings
        self._kit = kit
        self._settings = carb.settings.get_settings()

        if debug:
            logger.setLevel(logging.DEBUG)
            self._settings.set_bool("/omni/replicator/debug", True)

        # setting context, layers, stage, event_bus
        self._context = omni.usd.get_context()
        self._context.new_stage()
        self._stage: Usd.Stage = self._context.get_stage()
        self._root_layer: Sdf.Layer = self._stage.GetRootLayer()
        self._bus = omni.kit.app.get_app().get_message_bus_event_stream()
        self._fabric = fabric
        self._num_frames = num_frames
        self._num_subframes = num_subframes
        self._num_steps = num_steps
        self._output_path = output_path

        # Step 1-1 load scene
        # load and append the scene layer
        base_layer: Sdf.Layer = Sdf.Layer.FindOrOpen(scene)
        if base_layer is None:
            logger.error(f"Could not load USD scene: {scene}")
            sys.exit(1)
        self._root_layer.subLayerPaths.append(base_layer.identifier)

        # Step 1-2
        # QUESTION: We had to create the simulationContext between creating the renderproduct and loading the scene or things broke
        #           However this was with an older version of Isaac Sim
        # create SimulationContext and hook in logging
        self._simulation_context: SimulationContext = create_simulation_context(
            self._stage.GetPrimAtPath("/World/physicsScene")
        )

        # If we add these lines, we can have GPU Enabled set to True so deformables work, and data is written back to USD stage
        if self._fabric == "NoFabric":
            logger.info("Turning Fabric off")
            manager = omni.kit.app.get_app().get_extension_manager()
            manager.set_extension_enabled_immediate("omni.physx.fabric", False)
            self._settings.set_bool("/physics/updateToUsd", True)
            self._settings.set_bool("/physics/updateParticlesToUsd", True)
            self._settings.set_bool("/physics/updateVelocitiesToUsd", True)
            self._settings.set_bool("/physics/updateForceSensorsToUsd", True)
            self._settings.set_bool("/physics/outputVelocitiesLocalSpace", True)

        def step_callback(step_size):
            logger.debug(
                f"Simulate with step: {step_size}, current time: {self._simulation_context.current_time}, step index: {self._simulation_context.current_time_step_index}"
            )

        def render_callback(event):
            logger.debug(
                f"Update app with step: {event.payload['dt']}, current time: {self._simulation_context.current_time}, step index: {self._simulation_context.current_time_step_index}"
            )

        self._simulation_context.add_physics_callback("physics_callback", step_callback)
        self._simulation_context.add_render_callback("render_callback", render_callback)

        # Step 1-3 setup rendertarget and writers
        # Define the renderers.
        self._renderers: Sequence[Renderer] = create_renderers(self._output_path, self._num_subframes)

        # We create the default renderproduct if needed
        self._renderproduct = rep.create.render_product("/OmniverseKit_Persp", (1920, 1080))

    def create_variation(self, output_path: str, seed: int = None) -> None:
        """Randomization the scene by triggering the omnigraph using an event. Randomization is saved into the variation
        Layer.

        This is done once per variation.
        """
        # make sure the output datafolder exists
        os.makedirs(output_path, exist_ok=True)

        # reset writer frame ID in between datasets
        for renderer in self._renderers:
            for writer in renderer._writers:
                writer._frame_id = 0

        # Step 2-1 prepare variationLayer
        # Add the variation layer which will store the randomized modification.
        variation_layer: Sdf.Layer = Sdf.Layer.CreateAnonymous("variation")
        self._root_layer.subLayerPaths.insert(0, variation_layer.identifier)
        self._stage.SetEditTarget(variation_layer)

        # Step 2-2 randomize scene
        set_carb_setting(self._settings, "/app/player/playSimulations", False)

        # QUESTION: How can we use here the controller to directly trigger the graphs without the need to run kit.update()
        # Randomize via the graph
        self._randomize()

        # We need to advance kit for the graph to process
        for _ in range(0, 10):
            self._kit.update()

        set_carb_setting(self._settings, "/app/player/playSimulations", True)

        # Step 2-3 save and remove variationlayer
        # write variation layer to output folder and remove it so that we are back to the base scene structure
        variation_layer.Export(os.path.join(output_path, "variation.usda"), "seed = " + str(seed))

        # set the root layer as edit and remove the variation layer
        self._stage.SetEditTarget(self._root_layer)
        self._root_layer.subLayerPaths.remove(variation_layer.identifier)

    def run(self, output_path: str) -> None:
        """Plays the world with the variation layer.

        This is done once per variation.
        """

        # Step 4-1 prepare layers
        # load and add the variation layer
        variation_layer: Sdf.Layer = Sdf.Layer.FindOrOpen(os.path.join(output_path, "variation.usda"))
        self._root_layer.subLayerPaths.insert(0, variation_layer.identifier)

        # add the simulation layer
        simulation_layer: Sdf.Layer = Sdf.Layer.CreateAnonymous("simulation")
        self._root_layer.subLayerPaths.insert(0, simulation_layer.identifier)
        self._stage.SetEditTarget(simulation_layer)

        # Step 4-2 Setup the SimulationContext
        # NOTE:  not sure if we need the reset
        logger.debug(f"Simulation Context time before reset: {self._simulation_context.current_time}")
        self._simulation_context.reset()
        logger.debug(f"Simulation Context time before stop: {self._simulation_context.current_time}")
        self._simulation_context.stop()
        logger.debug(f"Simulation Context time before first render: {self._simulation_context.current_time}")

        set_carb_setting(self._settings, "/app/player/playSimulations", False)

        # Render frame at 0
        if RENDERFRAME_AT_0:
            # QUESTION: When we don't have this timeline play and commit silently,
            # the dataset after the first take an extra step. Why is this the case?
            # See reproduction_outputs/logger_debug_extra_step.txt for more info
            omni.timeline.get_timeline_interface().play()
            # We need this to update the timeline interface state or else it does not play and physics does not step properly
            omni.timeline.get_timeline_interface().commit_silently()
            for renderer in self._renderers:
                renderer.render_frame(self._renderproduct, output_path)

        # loop until all cameras are done
        for i in range(self._num_frames):
            # QUESTION: Why do we always have to restart? Is there a way to have replicator not pause the timeline
            if not omni.timeline.get_timeline_interface().is_playing():
                # QUESTION: Why is the timeline current time so different from the SimulationContext current time?
                # Does this lead to any unexpected physics issues?
                logger.debug(f"Timeline time before play: {omni.timeline.get_timeline_interface().get_current_time()}")
                omni.timeline.get_timeline_interface().play()
                # We need this to update the timeline interface state or else it does not play and physics does not step properly
                omni.timeline.get_timeline_interface().commit_silently()
                logger.debug(f"Timeline time after play: {omni.timeline.get_timeline_interface().get_current_time()}")
                # or update
                # omni.kit.app.get_app().update()

            # Step 4-3 advance physics
            logger.debug(f"Simulation Context time before advance simulation: {self._simulation_context.current_time}")
            self.advance_simulation()

            # USDRT experiments
            fabric_layer_identifier: str = ""

            # Plan 1: Work only in USD and save Fabric changes back to USD stage -- leads to weird results
            if self._fabric == "WriteToStage":
                logger.info("Writing Fabric changes to stage")
                usdrt_stage: usdrt_Usd.Stage = usdrt_Usd.Stage.Attach(omni.usd.get_context().get_stage_id())
                usdrt_stage.WriteToStage()
            # Plan 2: Export Fabric data as a layer for reproduction purposes -- works, but Fabric attribute names incompatible with USD stage
            elif self._fabric == "WriteToLayer":
                logger.info("Writing Fabric changes to layer")
                usdrt_stage: usdrt_Usd.Stage = usdrt_Usd.Stage.Attach(omni.usd.get_context().get_stage_id())
                fabric_layer_dir = os.path.join(output_path, "fabric_layer")
                os.makedirs(fabric_layer_dir, exist_ok=True)
                fabric_layer_path: str = os.path.join(fabric_layer_dir, f"fabric_{i}.usda")
                usdrt_stage.WriteToLayer(fabric_layer_path)

                # Test to reinsert fabric layer after WriteToLayer() -- leads to weird results
                # fabric_layer: Sdf.Layer = Sdf.Layer.FindOrOpen(fabric_layer_path)
                # fabric_layer_identifier: str = fabric_layer.identifier
                # self._root_layer.subLayerPaths.insert(0, fabric_layer_identifier)
                # self._stage.SetEditTarget(fabric_layer)

            # Step 4-4 loop over the cameras
            for renderer in self._renderers:
                # Step 4-5 render the cameras
                logger.debug(f"Simulation Context time before rendering: {self._simulation_context.current_time}")
                renderer.render_frame(self._renderproduct, output_path)

            # Remove fabric layer after rendering
            # if self._fabric == "WriteToLayer":
            #     self._root_layer.subLayerPaths.remove(fabric_layer_identifier)

        # Step 4-6 Stop the SimulationContext
        # NOTE: not sure if we need the reset
        self._simulation_context.reset()
        self._simulation_context.stop()

        # Step 4-7 remove layers
        self._stage.SetEditTarget(self._root_layer)
        self._root_layer.subLayerPaths.remove(simulation_layer.identifier)

        # remove variation layer
        self._root_layer.subLayerPaths.remove(variation_layer.identifier)

    def _randomize(self) -> None:
        """Triggers randomization."""
        self._bus.push(carb.events.type_from_string("omni.graph.action.Randomize"), payload={})

    def advance_simulation(self):
        """Advances the simulation based on the current behavior."""
        set_carb_setting(self._settings, "/app/player/playSimulations", True)

        for _ in range(0, self._num_steps):
            # QUESTION: How can we make sure that our Graphs for simulation are executed when the simulation steps
            self._simulation_context.step(render=False)

        # NOTE: if we add this kit update, physics settles with Enable GPU dynamics set to True
        # QUESTION: why is this required for rigid bodies when GPU dynamics and fabric is enabled (even if we don't have deformables in the scene?)
        omni.kit.app.get_app().update()

        set_carb_setting(self._settings, "/app/player/playSimulations", False)
