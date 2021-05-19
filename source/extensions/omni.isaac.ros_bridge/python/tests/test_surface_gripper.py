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

from omni.isaac.ros_ui.scripts.roscore import Roscore
from .common import create_joint_state, set_rotate, set_translate, simulate, wait_for_rosmaster
from omni.isaac.utils.scripts.nucleus_utils import find_nucleus_server
from omni.isaac.utils.scripts.test_utils import load_test_file
import rospy
from pxr import Gf, PhysicsSchemaTools

# Having a test class dervived from omni.kit.test.AsyncTestCase declared on the root of module will make it auto-discoverable by omni.kit.test
class TestSurfaceGripper(omni.kit.test.AsyncTestCase):
    # Before running each test
    async def setUp(self):
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
        self._roscore.startup(kit_folder + "/python/bin", self._ros_extension_path + "/noetic", "_CATKIN_SETUP_DIR")
        await wait_for_rosmaster()
        await omni.kit.app.get_app().next_update_async()

        try:
            rospy.init_node("isaac_sim_test_rospy", anonymous=True, disable_signals=True, log_level=rospy.ERROR)
        except rospy.exceptions.ROSException as e:
            print("Node has already been initialized, do nothing")

        print("STARTUP")
        pass

    # After running each test
    async def tearDown(self):
        print("TEARDOWN")
        while omni.usd.get_context().get_stage_loading_status()[2] > 0:
            print("tearDown, assets still loading, waiting to finish...")
            await asyncio.sleep(1.0)
        # rospy.signal_shutdown("test_complete")
        self._roscore.shutdown()
        self._roscore = None
        self._timeline = None
        # await omni.usd.get_context().new_stage_async()
        gc.collect()
        pass

    async def test_gripper(self):
        from sensor_msgs.msg import JointState

        (result, error) = await load_test_file(self._nucleus_path + "/Samples/ROS/Robots/UR10_Long_Suction_ROS.usd")
        self.assertTrue(result)

        stage = omni.usd.get_context().get_stage()

        PhysicsSchemaTools.addGroundPlane(stage, "/World/groundPlane", "Z", 1500, Gf.Vec3f(0, 0, 0), Gf.Vec3f(0.5))

        self.assertTrue(result)

        binPrim = stage.DefinePrim("/World/bin_1", "Xform")
        binPrim.GetReferences().AddReference(self._nucleus_path + "/Props/KLT_Bin/small_KLT.usd")
        set_translate(binPrim, (60, -50, 20))
        set_rotate(binPrim, Gf.Matrix3d(Gf.Rotation((1, 0, 0), 0)))

        binPrim = stage.DefinePrim("/World/bin_2", "Xform")
        binPrim.GetReferences().AddReference(self._nucleus_path + "/Props/KLT_Bin/small_KLT.usd")
        set_translate(binPrim, (60, 50, 20))
        set_rotate(binPrim, Gf.Matrix3d(Gf.Rotation((0, 1, 0), -90)))

        binPrim = stage.DefinePrim("/World/bin_3", "Xform")
        binPrim.GetReferences().AddReference(self._nucleus_path + "/Props/KLT_Bin/small_KLT.usd")
        set_translate(binPrim, (100, -50, 20))
        set_rotate(binPrim, Gf.Matrix3d(Gf.Rotation((0, 1, 0), 180)))

        pub = rospy.Publisher("joint_command", JointState, queue_size=10)
        suction_pub = rospy.Publisher("gripper_command", JointState, queue_size=10)
        self._gripper_state = -1.0

        def suction_callback(data):
            self._gripper_state = data.position[0]

        suction_sub = rospy.Subscriber("gripper_state", JointState, suction_callback)
        joints = [
            "shoulder_pan_joint",
            "shoulder_lift_joint",
            "elbow_joint",
            "wrist_1_joint",
            "wrist_2_joint",
            "wrist_3_joint",
        ]
        states = {}
        states["bin_1"] = {
            "grab": [-3.6246972, -1.9399462, -1.9311233, -0.8515033, 1.5707023, -0.48315188],
            "lift": [-3.624738, -1.7179015, -1.6415617, -1.364, 1.570694, -0.48314723],
        }
        states["bin_2"] = {
            "grab": [-2.2353225, -1.7653593, -1.7642521, -1.1936475, 1.5708172, 0.9060481],
            "lift": [-2.2353387, -1.717932, -1.6415195, -1.3640339, 1.5708125, 0.9060407],
        }
        states["bin_3"] = {
            "grab": [-3.4586642, -2.3406546, -0.99169415, -1.3797174, 1.5731614, -0.31733325],
            "lift": [-3.4579735, -2.3299344, -0.75304776, -1.6444204, 1.5707126, -0.3164174],
        }

        self._timeline.play()
        await omni.kit.app.get_app().next_update_async()
        await simulate(1)

        handle_1 = self._dc.get_rigid_body("/World/bin_1")
        handle_2 = self._dc.get_rigid_body("/World/bin_2")
        handle_3 = self._dc.get_rigid_body("/World/bin_3")
        self.assertLess(self._dc.get_rigid_body_pose(handle_1).p.z, 10)
        self.assertLess(self._dc.get_rigid_body_pose(handle_2).p.z, 10)
        self.assertLess(self._dc.get_rigid_body_pose(handle_3).p.z, 10)

        def send_close_message():
            suction_pub.publish(create_joint_state(["gripper"], [1.0]))
            pass

        def send_open_message():
            suction_pub.publish(create_joint_state(["gripper"], [0.0]))
            pass

        def send_joint_message(angles):
            pub.publish(create_joint_state(joints, angles))

        send_joint_message(states["bin_1"]["lift"])
        send_open_message()
        await simulate(4)
        send_joint_message(states["bin_1"]["grab"])
        await simulate(2)
        send_close_message()
        await simulate(2)
        send_joint_message(states["bin_1"]["lift"])
        await simulate(2)
        self.assertGreater(self._dc.get_rigid_body_pose(handle_1).p.z, 10)

        send_open_message()
        await simulate(2)
        send_joint_message(states["bin_2"]["lift"])
        await simulate(2)
        send_joint_message(states["bin_2"]["grab"])
        await simulate(2)
        send_close_message()
        await simulate(2)
        send_joint_message(states["bin_2"]["lift"])
        await simulate(2)
        self.assertGreater(self._dc.get_rigid_body_pose(handle_2).p.z, 10)

        send_open_message()
        await simulate(2)
        send_joint_message(states["bin_3"]["lift"])
        await simulate(2)
        send_joint_message(states["bin_3"]["grab"])
        await simulate(2)
        send_close_message()
        await simulate(2)
        send_joint_message(states["bin_3"]["lift"])
        await simulate(2)
        self.assertGreater(self._dc.get_rigid_body_pose(handle_3).p.z, 10)

        # Check to make sure that stopping simulation clears gripper state
        send_open_message()
        await simulate(2)
        send_joint_message(states["bin_3"]["lift"])
        await simulate(2)
        send_joint_message(states["bin_3"]["grab"])
        await simulate(2)
        send_close_message()
        await simulate(2)
        self.assertEqual(self._gripper_state, 1.0)
        self._timeline.stop()
        await omni.kit.app.get_app().next_update_async()
        self._timeline.play()
        await simulate(2)
        self.assertEqual(self._gripper_state, 0.0)
        self._timeline.stop()
        pass
