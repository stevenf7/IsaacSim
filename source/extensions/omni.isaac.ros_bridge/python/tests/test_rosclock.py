# NOTE:
#   omni.kit.test - std python's unittest module with additional wrapping to add suport for async/await tests
#   For most things refer to unittest docs: https://docs.python.org/3/library/unittest.html
import omni.kit.test
import omni.kit.usd
import gc
import asyncio

# Import extension python module we are testing with absolute import path, as if we are external user (other extension)
import omni.kit.commands
from .common import wait_for_rosmaster, simulate
import rospy
import carb

# Having a test class dervived from omni.kit.test.AsyncTestCase declared on the root of module will make it auto-discoverable by omni.kit.test
class TestRosClock(omni.kit.test.AsyncTestCase):
    # Before running each test
    async def setUp(self):
        from omni.isaac.ros_bridge_ui.scripts.roscore import Roscore

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

        self._roscore = Roscore()
        self._roscore.startup(kit_folder + "/python/bin", self._ros_extension_path + "/noetic", "_CATKIN_SETUP_DIR")
        await wait_for_rosmaster()
        # You must disable signals so that the init node call does not take over the ctrl-c callback for kit
        try:
            rospy.init_node("isaac_sim_test_gripper", anonymous=True, disable_signals=True, log_level=rospy.ERROR)
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

    async def test_sim_clock(self):
        from rosgraph_msgs.msg import Clock

        result, prim = omni.kit.commands.execute("ROSBridgeCreateClock", path="/ROS_Clock", sim_time=True)
        self._time_sec = 0

        def clock_callback(data):
            self._time_sec = data.clock.to_sec()

        clock_sub = rospy.Subscriber("/clock", Clock, clock_callback)

        self._timeline.play()

        await simulate(2.1)
        self._timeline.stop()
        clock_sub.unregister()
        self.assertGreater(self._time_sec, 2.0)

        pass

    async def test_sim_clock_manual(self):
        from rosgraph_msgs.msg import Clock

        result, prim = omni.kit.commands.execute(
            "ROSBridgeCreateClock", path="/ROS_Clock", sim_time=True, queue_size=0, enabled=False
        )
        self._time_sec = 0

        def clock_callback(data):
            self._time_sec = data.clock.to_sec()

        clock_sub = rospy.Subscriber("/clock", Clock, clock_callback)
        await asyncio.sleep(1.0)
        self._timeline.play()

        await omni.kit.app.get_app().next_update_async()

        self.assertEqual(self._time_sec, 0.0)
        result, status = omni.kit.commands.execute("RosBridgeTickComponent", path="/ROS_Clock")
        # after first step we need to wait for ros node to initialize
        await asyncio.sleep(1.0)

        result, status = omni.kit.commands.execute("RosBridgeTickComponent", path="/ROS_Clock")
        # wait for message
        await asyncio.sleep(1.0)
        self.assertTrue(status)
        self.assertGreater(self._time_sec, 0.0)

        self._timeline.stop()
        clock_sub.unregister()

        pass

    async def test_system_clock(self):
        from rosgraph_msgs.msg import Clock
        import time

        result, prim = omni.kit.commands.execute("ROSBridgeCreateClock", path="/ROS_Clock", sim_time=False)
        self._time_sec = 0

        def clock_callback(data):
            self._time_sec = data.clock.to_sec()

        clock_sub = rospy.Subscriber("/clock", Clock, clock_callback)

        self._timeline.play()

        await simulate(1.0)
        self.assertAlmostEqual(self._time_sec, time.time(), delta=0.5)
        self._timeline.stop()
        clock_sub.unregister()
        pass
