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
from omni.isaac.core.utils.physics import simulate_async
from omni.isaac.core.utils.stage import open_stage_async
from omni.isaac.nucleus import get_assets_root_path_async

from .common import wait_for_rosmaster_async


# Having a test class dervived from omni.kit.test.AsyncTestCase declared on the root of module will make it auto-discoverable by omni.kit.test
class TestRosJointState(omni.kit.test.AsyncTestCase):
    # Before running each test
    async def setUp(self):
        import rospy
        from omni.isaac.ros_bridge.scripts.roscore import Roscore

        await omni.usd.get_context().new_stage_async()
        self._timeline = omni.timeline.get_timeline_interface()
        self._stage = omni.usd.get_context().get_stage()
        ext_manager = omni.kit.app.get_app().get_extension_manager()
        ext_id = ext_manager.get_enabled_extension_id("omni.isaac.ros_bridge")
        self._ros_extension_path = ext_manager.get_extension_path(ext_id)
        kit_folder = carb.tokens.get_tokens_interface().resolve("${kit}")
        self._physics_rate = 60
        carb.settings.get_settings().set_bool("/app/runLoops/main/rateLimitEnabled", True)
        carb.settings.get_settings().set_int("/app/runLoops/main/rateLimitFrequency", int(self._physics_rate))
        carb.settings.get_settings().set_int("/persistent/simulation/minFrameRate", int(self._physics_rate))
        await omni.kit.app.get_app().next_update_async()

        # # start ROS
        self._roscore = Roscore()
        await wait_for_rosmaster_async()
        # You must disable signals so that the init node call does not take over the ctrl-c callback for kit
        try:
            rospy.init_node("isaac_sim_test_joint_drive", anonymous=True, disable_signals=True, log_level=rospy.ERROR)
        except rospy.exceptions.ROSException as e:
            print("Node has already been initialized, do nothing")
        pass

    # After running each test
    async def tearDown(self):
        self._stage = None
        self._timeline = None
        # rospy.signal_shutdown("test_complete")
        self._roscore.shutdown()
        self._roscore = None

        gc.collect()
        pass

    async def test_joint_state_publisher(self):
        # open simple_articulation asset (with one drivable revolute and one drivable prismatic joint)
        self._assets_root_path = await get_assets_root_path_async()
        await omni.kit.app.get_app().next_update_async()
        self.usd_path = self._assets_root_path + "/Isaac/Robots/Simple/articulation_3_joints.usd"
        (result, error) = await open_stage_async(self.usd_path)
        await omni.kit.app.get_app().next_update_async()
        self.assertTrue(result)  # Make sure the stage loaded
        self._stage = omni.usd.get_context().get_stage()
        PI = 3.1415925359

        import rospy
        from sensor_msgs.msg import JointState

        # setup ROS listener of the joint_state topic
        self.js_ros = JointState()

        def js_callback(data: JointState):
            self.js_ros.position = data.position
            self.js_ros.velocity = data.velocity
            self.js_ros.effort = data.effort

        js_sub = rospy.Subscriber("/joint_states", JointState, js_callback)

        # ROS-ify asset by adding a joint state publisher
        try:
            og.Controller.edit(
                {"graph_path": "/ActionGraph", "evaluator_name": "execution"},
                {
                    og.Controller.Keys.CREATE_NODES: [
                        ("OnPlaybackTick", "omni.graph.action.OnPlaybackTick"),
                        ("PublishJointState", "omni.isaac.ros_bridge.ROS1PublishJointState"),
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

        # # start the robot joint at 0,
        # def reset_robot():
        #     self.art.set_joint_positions([0,0,0])
        #     self.art.set_joint_velocities([0,0,0])
        #     self.art.set_joint_efforts([0,0,0])

        # # need to set the stiffness and damping parameters accordingly for position control

        # joint_names = ["CenterRevoluteJoint","PrismaticJoint","DistalRevoluteJoint"]
        # test_positions = [1.4,0.5,-0.4]
        # test_velocities = [2,-0.01,-2.5]
        # test_efforts = [-0.2,0.02,0.2]

        # # tick and stop
        # self._timeline.play()
        # await simulate_async(0.2)

        # # get the robot handle
        # self.art = Articulation("/Articulation")
        # self.art.initialize()
        # await simulate_async(0.2)

        # # reset_robot()
        # await simulate_async(0.5)
        # self.art.set_joint_positions(test_positions)
        # await simulate_async(1.0)
        # received_positions = self.js_ros.position
        # self._timeline.stop()

        # #check the message on ROS side is the same as the state on Isaac side
        # self.assertEqual(received_positions, test_positions)

        default_position = [-80 * PI / 180.0, 0.4, 30 * PI / 180.0]
        self._timeline.play()
        await simulate_async(1.0)
        # received_position = self.js_ros.position
        # print("\nreceived_positions", received_position)
        self._timeline.stop()
        received_position = self.js_ros.position
        # print("\nLAST received_positions", received_position)
        # print("\ndefault_positions", default_position)

        self.assertAlmostEqual(received_position[0], default_position[0], delta=1e-3)
        self.assertAlmostEqual(received_position[1], default_position[1], delta=1e-3)
        self.assertAlmostEqual(received_position[2], default_position[2], delta=1e-3)

        #     # reset robot
        #     # repeat for velocity drive
        #     # need to set the stiffness and damping parameters for velocity control

        #     # repeat for effort drive
        #     # need to set the stiffness and damping parameters for effort control

        #     # repeat for mixed messages
        #     # need to set the stiffness and damping parameters

        self._timeline.stop()
        js_sub.unregister()
        pass

    # async def test_joint_state_subscriber(self):
    # #     # test if sent stuff from the ROS side, do you get the right output from the joint state subscriber node (not necessarily how it applies onto the robot, just the node's output)
    # #     # test for prismatic joints,

    #     import rospy
    #     from sensor_msgs.msg import JointState

    #     PI = 3.1415925359
    #     js_pub = rospy.Publisher('joint_command', JointState, queue_size=10)

    #     # ROS-ify asset by adding a joint state publisher
    #     try:
    #         (test_graph, (tick_node,sub_node), _, _) = og.Controller.edit(
    #             {"graph_path": "/ActionGraph", "evaluator_name": "execution"},
    #             {
    #                 og.Controller.Keys.CREATE_NODES: [
    #                     ("OnPlaybackTick", "omni.graph.action.OnPlaybackTick"),
    #                     ("SubscribeJointState", "omni.isaac.ros_bridge.ROS1SubscribeJointState"),
    #                 ],
    #                 og.Controller.Keys.CONNECT: [
    #                     ("OnPlaybackTick.outputs:tick", "SubscribeJointState.inputs:execIn"),
    #                 ],
    #             },
    #         )
    #     except Exception as e:
    #         print(e)

    #     # test position drive
    #     js_position = JointState()
    #     js_position.name = ["CenterRevoluteJoint","PrismaticJoint","DistalRevoluteJoint"]
    #     js_position.position = [45*PI/180.0, 0.2, -120*PI/180.0]

    #     # tick and stop
    #     self._timeline.play()
    #     js_pub.publish(js_position)
    #     og.Controller.evaluate_sync(test_graph)
    #     attr = og.Controller.attribute(("outputs:jointNames", sub_node))
    #     print("\nbefore attr", og.Controller.get(attr))
    #     # # attr = og.Controller.attribute(("outputs:positionCommand", sub_node))
    #     # attr = og.Controller.attribute(("outputs:jointNames", sub_node))
    #     # print("\nattr", attr)
    #     # print("\nattr", og.Controller.get(attr))

    #     # the OG graph with the JS publisher should be ticking
    #     await simulate_async(10.0)
    #     # joint_position_received = og.
    #     # attr = og.Controller.attribute(("outputs:positionCommand", sub_node))
    #     attr = og.Controller.attribute(("outputs:jointNames", sub_node))
    #     print("\nattr", attr)
    #     print("\nattr", og.Controller.get(attr))
    #     # Tick the ROS Clock
    #     og.Controller.evaluate_sync(test_graph)
    #     attr = og.Controller.attribute(("outputs:jointNames", sub_node))
    #     print("\nafter attr", og.Controller.get(attr))

    #     self._timeline.stop()
    #     js_pub.unregister()

    #     pass
