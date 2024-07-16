# Copyright 2024 Amazon.com, Inc. or its affiliates. All Rights Reserved.

import csv
import os
from typing import List, Optional, Tuple

import omni.kit.app
import omni.replicator.core as rep
import omni.usd
from omni.isaac.core import SimulationContext
from omni.isaac.core.utils.render_product import set_camera_prim_path, set_resolution
from omni.replicator.core import Writer
from pxr import Gf, Sdf, Usd
from SDG_CLI import logger
from usdrt import Gf as usdrt_Gf
from usdrt import Rt as usdrt_Rt
from usdrt import Usd as usdrt_Usd


class Renderer:
    """Runs the simulation one time. When it renders output is dependent on the orchestrator. Camerapath can bind the
    the renderer to a specific camera and resolution determines the output resolution of the writers. Negative resolution
    skips rendering of images for better performance. Writers defined what is written and modifiers can be used to
    modify the scene, e.g. hide some assets or change annotations.
    """

    def __init__(
        self,
        camera_path: str = "",
        resolution: Tuple[int, int] = (-1, -1),
        writers: List[Writer] = None,
        subframes: int = -1,
        write_info_prim_path: Optional[str] = None,
    ) -> None:
        self._camera_path = camera_path
        self._resolution = resolution
        self._writers = writers
        self._subframes = subframes
        self._write_info_prim_path = write_info_prim_path

    # Helper functions to get position from USD stage and USDRT stage
    def get_position_from_prim(self, prim: Usd.Prim) -> Gf.Vec3d:
        return omni.usd.get_world_transform_matrix(prim).ExtractTranslation()

    def get_position_from_xformable(self, xformable: Optional[usdrt_Rt.Xformable]) -> Optional[usdrt_Gf.Vec3d]:
        if xformable is not None:
            if xformable.GetWorldPositionAttr().HasValue():
                return xformable.GetWorldPositionAttr().Get()
        return None

    # Usually we would have our custom writer to extract prim data from the stage, this is a simplified version
    def write_prim_info(self, stage: Usd.Stage, frame_id: int, output_dir: str) -> None:
        # Get USDRT stage
        usdrt_stage: usdrt_Usd.Stage = usdrt_Usd.Stage.Attach(omni.usd.get_context().get_stage_id())

        usdrt_prim: Optional[usdrt_Rt.Prim] = None
        xformable: Optional[usdrt_Rt.Xformable] = None

        prim: Usd.Prim = stage.GetPrimAtPath(self._write_info_prim_path)
        usdrt_prim: usdrt_Usd.Prim = usdrt_stage.GetPrimAtPath(self._write_info_prim_path)

        # We can get Fabric attributes with the USDRT API here
        # points = usdrt_prim.GetAttribute("points").Get()

        # We can get transforms using Rt.Xformable
        xformable: usdrt_Rt.Xformable = usdrt_Rt.Xformable(usdrt_prim)

        value: Gf.Vec3d = self.get_position_from_prim(prim)
        usdrt_value: Optional[usdrt_Gf.Vec3d] = self.get_position_from_xformable(xformable)

        # Write out position data to csv file
        prim_info_dir = os.path.join(output_dir, "prim_info")
        os.makedirs(prim_info_dir, exist_ok=True)
        file_path: str = os.path.join(prim_info_dir, prim.GetName() + ".csv")
        with open(file_path, "a") as csv_file:
            csv_writer: csv.writer = csv.writer(csv_file, lineterminator="\n")

            # Write headers if first row
            if os.stat(file_path).st_size == 0:
                csv_writer.writerow(["Frame", "USD Position", "Fabric Position"])

            csv_writer.writerow([frame_id, value, usdrt_value])

    def render_frame(self, render_product, output_path) -> None:
        """Renders the current frame of all the writers."""
        # Step 4-5-1 bind camera with the rendertarget and setup writers
        # setup renderproduct
        set_camera_prim_path(render_product.path, self._camera_path)
        set_resolution(render_product.path, self._resolution)
        stage: Usd.Stage = omni.usd.get_context().get_stage()

        # QUESTION: How can we set a new outputpath here? This feels hacky
        output_dir = ""
        frame_id = 0
        for writer in self._writers:
            output_dir = os.path.join(output_path, os.path.basename(writer._backend.output_dir))
            frame_id: int = writer._frame_id
            writer._backend = rep.BackendDispatch(output_dir=output_dir)
            writer.backend = writer._backend
            os.makedirs(writer._backend.output_dir, exist_ok=True)

        # attach all writers
        for writer in self._writers:
            writer.attach(render_product, trigger=None)
            writer.schedule_write()

        # QUESTION: Do we need to set the externalFrameCounter?
        # carb.settings.get_settings().set_int("/rtx/externalFrameCounter", frame)
        # QUESTION: Why do we need a kit update after writer.schedule_write() for PathTracing but not for RayTracedLighting?
        # Is there any way we could bypass this kit update for PathTracing?
        omni.kit.app.get_app().update()

        # Step 4-5-2 render
        rep.orchestrator.step(rt_subframes=self._subframes)

        # Write prim info
        if self._write_info_prim_path is not None:
            logger.debug(f"Writing prim info for {self._write_info_prim_path}")
            self.write_prim_info(stage, frame_id, output_dir)

        # Write Simulation Layer
        simulation_layer_dir = os.path.join(output_dir, "simulation_layer")
        os.makedirs(simulation_layer_dir, exist_ok=True)
        file_path: str = os.path.join(simulation_layer_dir, f"simulationLayer_{frame_id:04}.usda")
        root_layer: Sdf.Layer = stage.GetRootLayer()
        simulation_layer_identifier: str = next(
            (layer for layer in root_layer.subLayerPaths if layer.endswith("simulation")), None
        )
        simulation_layer: Sdf.Layer = Sdf.Layer.Find(simulation_layer_identifier)
        simulation_layer.Export(file_path, "simulationtime = " + str(SimulationContext.instance().current_time))

        # Step 4-5-3 remove camera from rendertarget
        for writer in self._writers:
            writer.detach()
