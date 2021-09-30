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
from re import A, I
import omni.kit.test
import omni.kit.usd
import gc
import carb
import asyncio

# Import extension python module we are testing with absolute import path, as if we are external user (other extension)
import omni.kit.commands
from omni.isaac.dynamic_control import _dynamic_control

from .common import simulate, wait_for_rosmaster, add_carter_ros, add_carter
from omni.isaac.ros_bridge_ui.scripts.commands import get_path
from omni.isaac.utils.scripts.nucleus_utils import find_nucleus_server
from pxr import Sdf, Gf


# Having a test class dervived from omni.kit.test.AsyncTestCase declared on the root of module will make it auto-discoverable by omni.kit.test
class TestRosDifferentialBase(omni.kit.test.AsyncTestCase):
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

        result, nucleus_server = find_nucleus_server()
        if result is False:
            carb.log_error("Could not find nucleus server with /Isaac folder")
            return
        self._nucleus_path = nucleus_server + "/Isaac"
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

    async def test_differential_base(self):
        import rospy
        from copy import deepcopy

        from geometry_msgs.msg import Twist
        from nav_msgs.msg import Odometry

        await add_carter_ros()

        self._odom_data = None

        def odom_callback(data: Odometry):
            self._pose_data = data.pose.pose

        odom_sub = rospy.Subscriber("/odom", Odometry, odom_callback)
        cmd_vel_pub = rospy.Publisher("/cmd_vel", Twist, queue_size=1)

        def move_cmd_msg(x, y, z, ax, ay, az):
            msg = Twist()
            msg.linear.x = x
            msg.linear.y = y
            msg.linear.z = z
            msg.angular.x = ax
            msg.angular.y = ay
            msg.angular.z = az
            return msg

        self._timeline.play()
        await omni.kit.app.get_app().next_update_async()
        await simulate(1)

        # check 0: is carter initially stationary
        pose_data = deepcopy(self._pose_data)
        self.assertIsNotNone(self._pose_data)
        self.assertAlmostEqual(pose_data.position.x, 0, 1)
        self.assertAlmostEqual(pose_data.position.y, 0, 1)
        self.assertAlmostEqual(pose_data.position.z, 0, 1)
        self.assertAlmostEqual(pose_data.orientation.x, 0, 1)
        self.assertAlmostEqual(pose_data.orientation.y, 0, 1)
        self.assertAlmostEqual(pose_data.orientation.z, 0, 1)
        self.assertAlmostEqual(pose_data.orientation.w, 1, 1)

        # straight forward
        move_cmd = move_cmd_msg(0.2, 0.0, 0.0, 0.0, 0.0, 0.0)
        cmd_vel_pub.publish(move_cmd)
        self._timeline.play()
        await omni.kit.app.get_app().next_update_async()
        await simulate(2)

        # stop
        move_cmd = move_cmd_msg(0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
        cmd_vel_pub.publish(move_cmd)
        self._timeline.play()
        await omni.kit.app.get_app().next_update_async()
        await simulate(1)

        # check 1: location using default param
        pose_data = deepcopy(self._pose_data)
        self.assertAlmostEqual(pose_data.position.x, 0.39, 1)
        self.assertAlmostEqual(pose_data.orientation.w, 1, 1)

        ## change wheel rotation and wheel base
        omni.kit.commands.execute(
            "ChangeProperty", prop_path=Sdf.Path("/Carter/ROS_DifferentialBase.wheelRadius"), value=0.05, prev=None
        )

        self._timeline.play()
        await omni.kit.app.get_app().next_update_async()
        await simulate(1)

        # straight back
        move_cmd = move_cmd_msg(-0.2, 0.0, 0.0, 0.0, 0.0, 0.0)
        cmd_vel_pub.publish(move_cmd)
        self._timeline.play()
        await omni.kit.app.get_app().next_update_async()
        await simulate(2)

        # stop
        move_cmd = move_cmd_msg(0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
        cmd_vel_pub.publish(move_cmd)
        self._timeline.play()
        await omni.kit.app.get_app().next_update_async()
        await simulate(1)

        # check 3: location after change radius
        pose_data = deepcopy(self._pose_data)
        self.assertAlmostEqual(pose_data.position.x, -1.718, 1)
        self.assertAlmostEqual(pose_data.orientation.w, 1, 1)

        self._timeline.stop()

        odom_sub.unregister()
        cmd_vel_pub.unregister()
        pass

    # add carter and ROS topic from scratch
    async def test_differential_base_scratch(self):
        import rospy
        from copy import deepcopy

        from geometry_msgs.msg import Twist
        from nav_msgs.msg import Odometry

        await add_carter()

        self._odom_data = None

        def odom_callback(data: Odometry):
            self._pose_data = data.pose.pose

        odom_sub = rospy.Subscriber("/odom", Odometry, odom_callback)
        cmd_vel_pub = rospy.Publisher("/cmd_vel", Twist, queue_size=1)

        def move_cmd_msg(x, y, z, ax, ay, az):
            msg = Twist()
            msg.linear.x = x
            msg.linear.y = y
            msg.linear.z = z
            msg.angular.x = ax
            msg.angular.y = ay
            msg.angular.z = az
            return msg

        this_stage = omni.usd.get_context().get_stage()

        result, prim = omni.kit.commands.execute(
            "ROSBridgeCreateDifferentialBase",
            path="/ROS_DifferentialBase",
            parent="/",
            enabled=True,
            chassis_prim_rel=["/carter"],
            left_wheel_joint_name="left_wheel",
            right_wheel_joint_name="right_wheel",
            robot_front=Gf.Vec3f(1, 0, 0),
            wheel_radius=0.1,
            wheel_base=0.5,
            max_speed=Gf.Vec2f(1.5, 1.0),
            time_without_command=0.2,
            acceleration_smoothing=1.0,
        )

        self._timeline.play()
        await omni.kit.app.get_app().next_update_async()
        await simulate(1)

        # check 0: is carter initially stationary
        pose_data = deepcopy(self._pose_data)
        self.assertIsNotNone(self._pose_data)
        self.assertAlmostEqual(pose_data.position.x, 0, 1)
        self.assertAlmostEqual(pose_data.position.y, 0, 1)
        self.assertAlmostEqual(pose_data.position.z, 0, 1)
        self.assertAlmostEqual(pose_data.orientation.x, 0, 1)
        self.assertAlmostEqual(pose_data.orientation.y, 0, 1)
        self.assertAlmostEqual(pose_data.orientation.z, 0, 1)
        self.assertAlmostEqual(pose_data.orientation.w, 1, 1)

        # rotate
        move_cmd = move_cmd_msg(0.0, 0.0, 0.0, 0.0, 0.0, 0.2)
        cmd_vel_pub.publish(move_cmd)
        self._timeline.play()
        await omni.kit.app.get_app().next_update_async()
        await simulate(1)

        # stop
        move_cmd = move_cmd_msg(0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
        cmd_vel_pub.publish(move_cmd)
        self._timeline.play()
        await omni.kit.app.get_app().next_update_async()
        await simulate(1)

        # check 1: location using default param
        pose_data = deepcopy(self._pose_data)
        self.assertAlmostEqual(pose_data.orientation.z, 0.40, 1)
        self.assertAlmostEqual(pose_data.orientation.w, 0.916, 1)

        # change wheel rotation and wheel base
        omni.kit.commands.execute(
            "ChangeProperty", prop_path=Sdf.Path("/ROS_DifferentialBase.wheelBase"), value=0.8, prev=None
        )

        self._timeline.play()
        await omni.kit.app.get_app().next_update_async()
        await simulate(1)

        # rotate back
        move_cmd = move_cmd_msg(0.0, 0.0, 0.0, 0.0, 0.0, -0.2)
        cmd_vel_pub.publish(move_cmd)
        self._timeline.play()
        await omni.kit.app.get_app().next_update_async()
        await simulate(1)

        # stop
        move_cmd = move_cmd_msg(0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
        cmd_vel_pub.publish(move_cmd)
        self._timeline.play()
        await omni.kit.app.get_app().next_update_async()
        await simulate(1)

        # check 3: location after change radius
        pose_data = deepcopy(self._pose_data)
        self.assertAlmostEqual(pose_data.orientation.z, -0.234, 1)
        self.assertAlmostEqual(pose_data.orientation.w, 0.97, 1)

        self._timeline.stop()

        odom_sub.unregister()
        cmd_vel_pub.unregister()
        pass
