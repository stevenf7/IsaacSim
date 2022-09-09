# Copyright (c) 2018-2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

# NOTE:
#   omni.kit.test - std python's unittest module with additional wrapping to add suport for async/await tests
#   For most things refer to unittest docs: https://docs.python.org/3/library/unittest.html
import omni.kit.test
import omni.kit.usd
import gc
import carb
import asyncio

# Import extension python module we are testing with absolute import path, as if we are external user (other extension)
import omni.kit.commands
from omni.isaac.dynamic_control import _dynamic_control

from .common import add_cube, add_carter_ros
from omni.isaac.core.utils.nucleus import get_assets_root_path
from pxr import Sdf, Gf
from omni.isaac.core.utils.physics import simulate_async
import omni.graph.core as og
import omni.kit.viewport.utility

# Having a test class dervived from omni.kit.test.AsyncTestCase declared on the root of module will make it auto-discoverable by omni.kit.test
class TestRos2Camera(omni.kit.test.AsyncTestCase):
    # Before running each test
    async def setUp(self):
        import rclpy

        await omni.usd.get_context().new_stage_async()
        self._timeline = omni.timeline.get_timeline_interface()
        self._dc = _dynamic_control.acquire_dynamic_control_interface()

        ext_manager = omni.kit.app.get_app().get_extension_manager()
        ext_id = ext_manager.get_enabled_extension_id("omni.isaac.ros2_bridge-humble")
        self._ros_extension_path = ext_manager.get_extension_path(ext_id)

        self._assets_root_path = get_assets_root_path()
        if self._assets_root_path is None:
            carb.log_error("Could not find Isaac Sim assets folder")
            return
        kit_folder = carb.tokens.get_tokens_interface().resolve("${kit}")

        self._physics_rate = 60
        carb.settings.get_settings().set_bool("/app/runLoops/main/rateLimitEnabled", True)
        carb.settings.get_settings().set_int("/app/runLoops/main/rateLimitFrequency", int(self._physics_rate))
        carb.settings.get_settings().set_int("/persistent/simulation/minFrameRate", int(self._physics_rate))
        await omni.kit.app.get_app().next_update_async()
        rclpy.init()

        pass

    # After running each test
    async def tearDown(self):
        import rclpy

        while omni.usd.get_context().get_stage_loading_status()[2] > 0:
            print("tearDown, assets still loading, waiting to finish...")
            await asyncio.sleep(1.0)

        self._timeline = None
        rclpy.shutdown()
        gc.collect()
        pass

    async def test_camera(self):
        import rclpy

        viewport_window = omni.kit.viewport.utility.get_active_viewport_window()
        try:
            og.Controller.edit(
                {"graph_path": "/ActionGraph", "evaluator_name": "execution"},
                {
                    og.Controller.Keys.CREATE_NODES: [
                        ("OnPlaybackTick", "omni.graph.action.OnPlaybackTick"),
                        ("RGBPublish", "omni.isaac.ros2_bridge.ROS2CameraHelper"),
                        ("CameraInfoPublish", "omni.isaac.ros2_bridge.ROS2CameraHelper"),
                    ],
                    og.Controller.Keys.SET_VALUES: [
                        ("RGBPublish.inputs:viewport", viewport_window.title),
                        ("RGBPublish.inputs:topicName", "rgb"),
                        ("RGBPublish.inputs:type", "rgb"),
                        ("CameraInfoPublish.inputs:viewport", viewport_window.title),
                        ("CameraInfoPublish.inputs:topicName", "camera_info"),
                        ("CameraInfoPublish.inputs:type", "camera_info"),
                    ],
                    og.Controller.Keys.CONNECT: [
                        ("OnPlaybackTick.outputs:tick", "RGBPublish.inputs:execIn"),
                        ("OnPlaybackTick.outputs:tick", "CameraInfoPublish.inputs:execIn"),
                    ],
                },
            )
        except Exception as e:
            print(e)
        await omni.kit.app.get_app().next_update_async()

        # acquire the viewport window
        viewport_api = omni.kit.viewport.utility.get_active_viewport()
        # Set viewport resolution, changes will occur on next frame
        viewport_api.set_texture_resolution((800, 600))

        await omni.kit.app.get_app().next_update_async()

        from sensor_msgs.msg import CameraInfo, Image

        self._camera_info = None
        self._camera_rgb = None

        def camera_info_callback(data: CameraInfo):
            self._camera_info = data

        def rgb_callback(data: Image):
            self._camera_rgb = data

        node = rclpy.create_node("camera_tester")
        camera_info_sub = node.create_subscription(CameraInfo, "camera_info", camera_info_callback, 1)
        rgb_sub = node.create_subscription(Image, "rgb", rgb_callback, 1)

        await asyncio.sleep(2.0)

        omni.kit.commands.execute(
            "ChangeProperty", prop_path=Sdf.Path("/OmniverseKit_Persp.horizontalAperture"), value=6.0, prev=0
        )

        omni.kit.commands.execute(
            "ChangeProperty", prop_path=Sdf.Path("/OmniverseKit_Persp.verticalAperture"), value=4.5, prev=0
        )

        def spin():
            rclpy.spin_once(node, timeout_sec=0.1)

        self._timeline.play()
        await omni.kit.app.get_app().next_update_async()
        await simulate_async(1, 60, spin)
        while self._camera_info is None:
            await simulate_async(1, 60, spin)

        self.assertEqual(self._camera_info.width, 800)
        self.assertEqual(self._camera_info.height, 600)
        self.assertAlmostEqual(self._camera_info.p[0], self._camera_info.p[5], delta=1.5)
        self.assertAlmostEqual(self._camera_info.k[0], self._camera_info.k[4], delta=1.5)

        self._timeline.stop()
        await omni.kit.app.get_app().next_update_async()
        spin()
        # make sure all previous messages are cleared
        await asyncio.sleep(2.0)
        self._camera_info = None

        omni.kit.commands.execute(
            "ChangeProperty", prop_path=Sdf.Path("/OmniverseKit_Persp.horizontalAperture"), value=6, prev=0
        )

        omni.kit.commands.execute(
            "ChangeProperty", prop_path=Sdf.Path("/OmniverseKit_Persp.verticalAperture"), value=6, prev=0
        )

        await omni.kit.app.get_app().next_update_async()
        self._timeline.play()
        await omni.kit.app.get_app().next_update_async()
        await omni.kit.app.get_app().next_update_async()
        await simulate_async(1, 60, spin)
        while self._camera_info is None:
            await simulate_async(1, 60, spin)

        self.assertAlmostEqual(self._camera_info.p[0], 2419, delta=1)
        self.assertAlmostEqual(self._camera_info.p[5], 1814, delta=1)
