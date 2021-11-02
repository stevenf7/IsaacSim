# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

import asyncio
import time

from output import Logger
from sampling import Sampler
from scene import Camera, Light, Object, Room


class SceneManager:
    """ For managing scene set-up and generation. """

    def __init__(self, sim_app, sim_context):
        """ Construct SceneManager. Set-up scenario in Isaac Sim. """

        import omni

        self.sim_app = sim_app
        self.sim_context = sim_context

        self.stage = omni.usd.get_context().get_stage()

        self.sample = Sampler().sample
        self.setup_scenario()

        self.play_frame = False
        self.objs = []
        self.lights = []

        self.camera = Camera(self.sim_app, self.sim_context, "/World/CameraRig", None, group=None)

    def setup_scenario(self):
        """ Load in base scenario(s) """

        import omni
        from omni.isaac.core.utils import stage

        # Load in a USD scenario, if needed
        self.load_scenario_model()

        # Generate a parameterizable room, if needed
        self.room = None
        if self.sample("scenario_room"):
            self.room = Room(self.sim_app, self.sim_context)

        self.stage = omni.usd.get_context().get_stage()

        # Set the up axis to the z axis
        stage.set_stage_up_axis("z")

    def load_scenario_model(self):
        """ Load in a USD scenario. """

        import omni

        # TODO: add multiples scenario support

        # Load in base scenario from Nucleus
        if self.sample("scenario_model"):

            async def load_stage(path):
                await omni.usd.get_context().open_stage_async(path)

            scenario_ref = self.sample("nucleus_server") + self.sample("scenario_model")
            setup_task = asyncio.ensure_future(load_stage(scenario_ref))
            while not setup_task.done():
                self.sim_context.render()

    def populate_scene(self, index):
        """ Populate a sample's scene a camera, objects, and lights. """

        # Update camera
        self.camera.place_in_scene()

        # Iterate through each group
        self.objs = []
        self.lights = []
        for group in self.sample("groups"):
            # Spawn objects
            num_objs = self.sample("obj_count", group=group)
            for i in range(num_objs):
                path = "/World/Sample/Objects/object_{}_{}".format(len(self.objs), index)
                ref = self.sample("nucleus_server") + self.sample("obj_model", group=group)
                obj = Object(self.sim_app, self.sim_context, ref, path, self.camera, group)
                obj.place_in_scene()
                obj.add_physics()
                self.objs.append(obj)

            # Spawn lights
            num_lights = self.sample("light_count", group=group)
            for i in range(num_lights):
                path = "/World/Sample/Lights/lights_{}".format(len(self.lights))
                light = Light(self.sim_app, self.sim_context, path, self.camera, group)
                light.place_in_scene()
                self.lights.append(light)

        # Update room
        if self.room:
            self.room.update()

        # Add skybox, if needed
        self.add_skybox()

    def update_scene(self, step_time=None, step_index=0):
        """ Update Omniverse after scene is generated. """

        from omni.isaac.core.utils.stage import is_stage_loading

        # Step positions of objs and lights
        if step_time:
            self.camera.step(step_time)

            for obj in self.objs:
                obj.step(step_time)

            for light in self.lights:
                light.step(step_time)

        # Wait for scene to finish loading
        while is_stage_loading():
            self.sim_context.render()

        # Determine if scene is played
        scene_assets = self.objs + self.lights
        self.play_frame = any([asset.physics for asset in scene_assets])

        # Play scene, if needed
        if self.play_frame:
            Logger.print("physically simulating...")
            self.sim_context.play()
            render = not self.sample("headless")

            sim_time = self.sample("physics_simulate_time")
            frames_to_simulate = int(sim_time * 60) + 1
            for i in range(frames_to_simulate):
                self.sim_context.step(render=render)
        else:
            self.sim_context.stop()

        # Napping
        if self.sample("nap"):
            print("napping")
            while True:
                self.sim_context.render()

        # Pausing
        start_time = time.time()
        pause_time = 0.05
        if step_index == 0:
            pause_time += self.sample("pause")
        while time.time() - start_time < pause_time:
            self.sim_context.render()

    def add_skybox(self):
        """ Add a DomeLight that creates a textured skybox, if needed. """

        import omni
        from pxr import UsdGeom, UsdLux

        sky_texture = self.sample("sky_texture")
        sky_light_intensity = self.sample("sky_light_intensity")

        if sky_texture:
            omni.kit.commands.execute(
                "CreatePrimCommand",
                prim_path="/World/Sample/Lights/skybox",
                prim_type="DomeLight",
                select_new_prim=False,
                attributes={
                    UsdLux.Tokens.intensity: sky_light_intensity,
                    UsdLux.Tokens.specular: 1,
                    UsdLux.Tokens.textureFile: self.sample("nucleus_server") + sky_texture,
                    UsdLux.Tokens.textureFormat: UsdLux.Tokens.latlong,
                    UsdGeom.Tokens.visibility: "inherited",
                },
            )

    def prepare_scene(self, index):
        """ Scene preparation step. """

        self.valid_sample = True
        Logger.start_log_entry(index)
        Logger.print("Scene: " + str(index) + "\n")

    def finish_scene(self):
        """ Scene finish step. Clean-up variables, Isaac Sim stage. """

        from pxr import Sdf

        self.objs = []
        self.lights = []
        self.stage.RemovePrim(Sdf.Path("/World/Sample"))
        self.stage.RemovePrim(Sdf.Path("/Looks"))
        self.sim_context.stop()
        self.sim_context.render()
        self.play_frame = False
        Logger.finish_log_entry()
