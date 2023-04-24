# Copyright (c) 2018-2022, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#


import omni.kit.test
from omni.isaac.core.utils.rotations import euler_angles_to_quat

# from omni.isaac.core.prims._impl.single_prim_wrapper import set_default_state
from omni.isaac.core.utils.viewports import destroy_all_viewports, get_viewport_names
from pxr import Gf, UsdGeom

from ..utils.base_isaac_benchmark import BaseIsaacBenchmark
from ..utils.helper import add_ros_camera


class TestBenchmarkRos1Camera(BaseIsaacBenchmark):
    async def setUp(self):
        await super().setUp()
        destroy_all_viewports(destroy_main_viewport=False)
        pass

    async def tearDown(self):
        await super().tearDown()
        destroy_all_viewports(destroy_main_viewport=False)
        pass

    # ----------------------------------------------------------------------
    async def benchmark_ros1_camera(self, n_camera, resolution):
        self.test_run.test_name = f"{n_camera}_cameras_{resolution[0]}_{resolution[1]}_resolution_ros_1"
        self.set_phase("loading")
        self.start_collecting_frametime()
        scene_path = "/Isaac/Environments/Simple_Warehouse/full_warehouse.usd"
        await self.fully_load_stage(self.assets_root_path + scene_path)
        stage = omni.usd.get_context().get_stage()

        timeline = omni.timeline.get_timeline_interface()
        timeline.play()

        for i in range(n_camera):

            # add a camera on stage
            camera_path = "/Cameras/Camera_" + str(i)
            if i == 0:
                viewport_name = "Viewport"
            else:
                viewport_name = "Viewport " + str(i)
            stage = omni.usd.get_context().get_stage()
            camera_prim = stage.DefinePrim(camera_path, "Camera")
            camera_translation = Gf.Vec3f([-8, 13, 2.0])  # these positions are used for full_warehouse.usd
            if "xformOp:translate" not in camera_prim.GetPropertyNames():
                UsdGeom.Xformable(camera_prim).AddTranslateOp()
            camera_prim.GetAttribute("xformOp:translate").Set(camera_translation)
            q = euler_angles_to_quat([90, 0, 90 + i * 360 / n_camera], degrees=True)
            camera_orientation = Gf.Quatf(q[0], q[1], q[2], q[3])
            if "xformOp:orient" not in camera_prim.GetPropertyNames():
                UsdGeom.Xformable(camera_prim).AddOrientOp()
            camera_prim.GetAttribute("xformOp:orient").Set(
                camera_orientation
            )  # rotate cameras to look at slightly different view, repeated views affect fps

            # add corresponding ROS camera publisher (that also creates viewports)
            graph_path = "/ROS/ROS_camera_" + str(i)
            ros_topic = "/rgb_" + str(i)
            add_ros_camera(
                camera_prim_path=camera_path,
                graph_path=graph_path,
                camera_topic=ros_topic,
                viewport_name=viewport_name,
                viewport_resolution=resolution,
            )
            await omni.kit.app.get_app().next_update_async()

            while viewport_name not in get_viewport_names():
                await omni.kit.app.get_app().next_update_async()
            if i > 0:
                main_viewport = omni.ui.Workspace.get_window("Viewport")
                new_viewport = omni.ui.Workspace.get_window(viewport_name)
                new_viewport.dock_in(main_viewport, omni.ui.DockPosition.RIGHT, 1.0 / n_camera)
            await omni.kit.app.get_app().next_update_async()

            self.stop_collecting_frametime()
            await self.store_measurements()

            self.set_phase("benchmark")
            self.start_collecting_frametime()

            while self.get_num_frames() < 120:
                await omni.kit.app.get_app().next_update_async()

            self.stop_collecting_frametime()
            await self.store_measurements()

            timeline.stop()

    async def test_benchmark_ros1_1_camera_720p(self):
        await self.benchmark_ros1_camera(1, [1280, 720])

    async def test_benchmark_ros1_2_camera_720p(self):
        await self.benchmark_ros1_camera(2, [1280, 720])

    async def test_benchmark_ros1_4_camera_720p(self):
        await self.benchmark_ros1_camera(4, [1280, 720])

    async def test_benchmark_ros1_8_camera_720p(self):
        await self.benchmark_ros1_camera(8, [1280, 720])

    async def test_benchmark_ros1_1_camera_1080(self):
        await self.benchmark_ros1_camera(1, [1920, 1080])

    async def test_benchmark_ros1_2_camera_1080(self):
        await self.benchmark_ros1_camera(2, [1920, 1080])

    async def test_benchmark_ros1_4_camera_1080(self):
        await self.benchmark_ros1_camera(4, [1920, 1080])

    async def test_benchmark_ros1_8_camera_1080(self):
        await self.benchmark_ros1_camera(8, [1920, 1080])
