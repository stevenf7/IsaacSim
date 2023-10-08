# Copyright (c) 2018-2023, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

import asyncio
import gc

import carb
import omni.graph.core as og

# Import extension python module we are testing with absolute import path, as if we are external user (other extension)
import omni.kit.commands

# NOTE:
#   omni.kit.test - std python's unittest module with additional wrapping to add suport for async/await tests
#   For most things refer to unittest docs: https://docs.python.org/3/library/unittest.html
import omni.kit.test
import omni.kit.usd
import usdrt.Sdf
from omni.isaac.core.articulations import Articulation
from omni.isaac.core.utils.nucleus import get_assets_root_path
from omni.isaac.core.utils.physics import simulate_async
from omni.isaac.core.utils.stage import open_stage_async

from .common import get_qos_profile


class TestRos2JointState(omni.kit.test.AsyncTestCase):
    # Before running each test
    async def setUp(self):
        import rclpy

        await omni.usd.get_context().new_stage_async()
        self._timeline = omni.timeline.get_timeline_interface()

        ext_manager = omni.kit.app.get_app().get_extension_manager()
        ext_id = ext_manager.get_enabled_extension_id("omni.isaac.ros2_bridge")
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

    async def test_joint_state_publisher(self):
        from copy import deepcopy

        import rclpy
        from sensor_msgs.msg import JointState

        # open simple_articulation asset (with one drivable revolute and one drivable prismatic joint)
        self._assets_root_path = get_assets_root_path()
        await omni.kit.app.get_app().next_update_async()
        self.usd_path = self._assets_root_path + "/Isaac/Robots/Simple/articulation_3_joints.usd"
        (result, error) = await open_stage_async(self.usd_path)
        await omni.kit.app.get_app().next_update_async()
        self.assertTrue(result)  # Make sure the stage loaded
        self._stage = omni.usd.get_context().get_stage()
        PI = 3.1415925359

        # setup ROS listener of the joint_state topic
        self.js_ros = JointState()

        def js_callback(data: JointState):
            self.js_ros.position = data.position
            self.js_ros.velocity = data.velocity
            self.js_ros.effort = data.effort

        node = rclpy.create_node("isaac_sim_test_joint_state_pub_sub")
        js_sub = node.create_subscription(JointState, "joint_states", js_callback, get_qos_profile())

        def spin():
            rclpy.spin_once(node, timeout_sec=0.1)

        # ROS-ify asset by adding a joint state publisher
        try:
            og.Controller.edit(
                {"graph_path": "/ActionGraph", "evaluator_name": "execution"},
                {
                    og.Controller.Keys.CREATE_NODES: [
                        ("OnPlaybackTick", "omni.graph.action.OnPlaybackTick"),
                        ("PublishJointState", "omni.isaac.ros2_bridge.ROS2PublishJointState"),
                    ],
                    og.Controller.Keys.SET_VALUES: [
                        (
                            "PublishJointState.inputs:targetPrim",
                            [usdrt.Sdf.Path("/Articulation")],
                        ),
                    ],
                    og.Controller.Keys.CONNECT: [
                        ("OnPlaybackTick.outputs:tick", "PublishJointState.inputs:execIn"),
                    ],
                },
            )
        except Exception as e:
            print(e)

        default_position = [-80 * PI / 180.0, 0.4, 30 * PI / 180.0]

        self._timeline.play()
        await omni.kit.app.get_app().next_update_async()
        await simulate_async(2, 60, spin)
        received_position = self.js_ros.position

        print("\n received_position", received_position)

        self.assertAlmostEqual(received_position[0], default_position[0], delta=1e-3)
        self.assertAlmostEqual(received_position[1], default_position[1], delta=1e-3)
        self.assertAlmostEqual(received_position[2], default_position[2], delta=1e-3)

        self._timeline.stop()
        spin()

        pass
