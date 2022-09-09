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

from .common import add_cube, wait_for_rosmaster, add_carter_ros
from omni.isaac.core.utils.nucleus import get_assets_root_path
from pxr import Sdf, Gf
from omni.isaac.core.utils.physics import simulate_async
import omni.graph.core as og
import omni.kit.viewport.utility

# Having a test class dervived from omni.kit.test.AsyncTestCase declared on the root of module will make it auto-discoverable by omni.kit.test
class TestRosCamera(omni.kit.test.AsyncTestCase):
    # Before running each test
    async def setUp(self):
        from omni.isaac.ros_bridge.scripts.roscore import Roscore
        import rospy

        await omni.usd.get_context().new_stage_async()
        self._timeline = omni.timeline.get_timeline_interface()
        self._dc = _dynamic_control.acquire_dynamic_control_interface()

        ext_manager = omni.kit.app.get_app().get_extension_manager()
        ext_id = ext_manager.get_enabled_extension_id("omni.isaac.ros_bridge")
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

        self._roscore = Roscore()
        await wait_for_rosmaster()
        await omni.kit.app.get_app().next_update_async()

        try:
            rospy.init_node("isaac_sim_test_rospy", anonymous=True, disable_signals=True, log_level=rospy.ERROR)
        except rospy.exceptions.ROSException as e:
            print("Node has already been initialized, do nothing")

        pass

    # After running each test
    async def tearDown(self):
        while omni.usd.get_context().get_stage_loading_status()[2] > 0:
            print("tearDown, assets still loading, waiting to finish...")
            await asyncio.sleep(1.0)
        # rospy.signal_shutdown("test_complete")
        self._roscore = None
        self._timeline = None
        gc.collect()
        pass

    async def test_camera(self):
        import rospy

        viewport_window = omni.kit.viewport.utility.get_active_viewport_window()

        try:
            og.Controller.edit(
                {"graph_path": "/ActionGraph", "evaluator_name": "execution"},
                {
                    og.Controller.Keys.CREATE_NODES: [
                        ("OnPlaybackTick", "omni.graph.action.OnPlaybackTick"),
                        ("RGBPublish", "omni.isaac.ros_bridge.ROS1CameraHelper"),
                        ("CameraInfoPublish", "omni.isaac.ros_bridge.ROS1CameraHelper"),
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

        camera_info_sub = rospy.Subscriber("camera_info", CameraInfo, camera_info_callback)

        rgb_sub = rospy.Subscriber("rgb", Image, rgb_callback)
        await asyncio.sleep(2.0)

        omni.kit.commands.execute(
            "ChangeProperty", prop_path=Sdf.Path("/OmniverseKit_Persp.horizontalAperture"), value=6.0, prev=0
        )

        omni.kit.commands.execute(
            "ChangeProperty", prop_path=Sdf.Path("/OmniverseKit_Persp.verticalAperture"), value=4.5, prev=0
        )

        self._timeline.play()
        await omni.kit.app.get_app().next_update_async()
        await simulate_async(1)
        while self._camera_info is None:
            await simulate_async(1)

        self.assertEqual(self._camera_info.width, 800)
        self.assertEqual(self._camera_info.height, 600)
        self.assertAlmostEqual(self._camera_info.P[0], self._camera_info.P[5], delta=1.5)
        self.assertAlmostEqual(self._camera_info.K[0], self._camera_info.K[4], delta=1.5)

        self._timeline.stop()
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
        await simulate_async(1)
        while self._camera_info is None:
            await simulate_async(1)

        self.assertAlmostEqual(self._camera_info.P[0], 2419, delta=1)
        self.assertAlmostEqual(self._camera_info.P[5], 1814, delta=1)

        camera_info_sub.unregister()
        rgb_sub.unregister()
