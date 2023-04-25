# Copyright (c) 2018-2022, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#


import numpy as np
import omni.kit.test
from omni.isaac.core.prims.xform_prim import XFormPrim
from omni.isaac.core.utils.rotations import euler_angles_to_quat
from omni.isaac.core.utils.stage import is_stage_loading
from omni.isaac.core.utils.viewports import destroy_all_viewports, get_viewport_names
from omni.kit.viewport.utility import create_viewport_window, get_viewport_from_window_name
from omni.isaac.core.utils.render_product import create_hydra_texture, set_camera_prim_path, set_resolution
from pxr import Gf

from ..utils.base_isaac_benchmark import BaseIsaacBenchmark


class TestBenchmarkCamera(BaseIsaacBenchmark):
    async def setUp(self):
        await super().setUp()
        pass

    async def tearDown(self):
        await super().tearDown()
        pass

    async def benchmark_camera(self, n_camera, resolution):
        self.test_run.test_name = f"{n_camera}_cameras_{resolution[0]}_{resolution[1]}_resolution"
        self.set_phase("loading")
        self.start_collecting_frametime()

        scene_path = "/Isaac/Environments/Simple_Warehouse/full_warehouse.usd"
        await self.fully_load_stage(self.assets_root_path + scene_path)
        stage = omni.usd.get_context().get_stage()

        timeline = omni.timeline.get_timeline_interface()
        timeline.play()

        for i in range(n_camera):
            camera_path = "/Cameras/Camera_" + str(i)
            # add the cameras on stage if not already exist
            camera_prim = stage.GetPrimAtPath(camera_path)
            if not camera_prim.IsValid():
                stage.DefinePrim(camera_path, "Camera")
                camera_prim = XFormPrim(camera_path)
                q = euler_angles_to_quat([90, 0, 90 + i * 360 / n_camera], degrees=True)
                camera_prim.set_world_pose(np.array([-8, 13, 2.0]), q)
                camera_translation = Gf.Vec3f()  # these positions are used for full_warehouse.usd

            texture, texture_path = create_hydra_texture(resolution, camera_path)
            await omni.kit.app.get_app().next_update_async()

        # make sure scene is loaded in all viewports
        while is_stage_loading():
            print("asset still loading, waiting to finish")
            await omni.kit.app.get_app().next_update_async()
        await omni.kit.app.get_app().next_update_async()

        self.stop_collecting_frametime()
        await self.store_measurements()

        # perform benchmark
        self.set_phase("benchmark")
        self.start_collecting_frametime()

        while self.get_num_frames() < 120:
            await omni.kit.app.get_app().next_update_async()

        self.stop_collecting_frametime()
        await self.store_measurements()

        timeline.stop()

    # ----------------------------------------------------------------------
    async def test_benchmark_1_camera_720p(self):
        await self.benchmark_camera(1, [1280, 720])

    async def test_benchmark_2_camera_720p(self):
        await self.benchmark_camera(2, [1280, 720])

    async def test_benchmark_4_camera_720p(self):
        await self.benchmark_camera(4, [1280, 720])

    async def test_benchmark_8_camera_720p(self):
        await self.benchmark_camera(8, [1280, 720])

    async def test_benchmark_1_camera_1080(self):
        await self.benchmark_camera(1, [1920, 1080])

    async def test_benchmark_2_camera_1080(self):
        await self.benchmark_camera(2, [1920, 1080])

    async def test_benchmark_4_camera_1080(self):
        await self.benchmark_camera(4, [1920, 1080])

    async def test_benchmark_8_camera_1080(self):
        await self.benchmark_camera(8, [1920, 1080])
