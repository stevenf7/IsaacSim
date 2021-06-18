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

from .common import add_cube, simulate, wait_for_rosmaster
from omni.isaac.utils.scripts.nucleus_utils import find_nucleus_server
from omni.isaac.utils.scripts.test_utils import load_test_file
import rospy
from pxr import Gf, PhysicsSchemaTools, Sdf

# Having a test class dervived from omni.kit.test.AsyncTestCase declared on the root of module will make it auto-discoverable by omni.kit.test
class TestLidar(omni.kit.test.AsyncTestCase):
    # Before running each test
    async def setUp(self):
        from omni.isaac.ros_bridge_ui.scripts.roscore import Roscore

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
        while omni.usd.get_context().get_stage_loading_status()[2] > 0:
            print("tearDown, assets still loading, waiting to finish...")
            await asyncio.sleep(1.0)
        # rospy.signal_shutdown("test_complete")
        self._roscore.shutdown()
        self._roscore = None
        self._timeline = None
        gc.collect()
        pass

    async def test_lidar(self):
        from sensor_msgs.msg import LaserScan

        (result, error) = await load_test_file(self._nucleus_path + "/Samples/ROS/Robots/Carter_ROS.usd")
        self.assertTrue(result)

        stage = omni.usd.get_context().get_stage()

        PhysicsSchemaTools.addGroundPlane(stage, "/World/groundPlane", "Z", 1500, Gf.Vec3f(0, 0, -25), Gf.Vec3f(0.5))

        self.assertTrue(result)
        self._lidar_data = None

        def lida_callback(data: LaserScan):
            self._lidar_data = data

        lidar_sub = rospy.Subscriber("scan", LaserScan, lida_callback)

        await add_cube(stage, "/cube", 75, (200, 0, 75))

        self._timeline.play()
        await omni.kit.app.get_app().next_update_async()
        await simulate(1)
        self.assertIsNotNone(self._lidar_data)
        self.assertGreater(self._lidar_data.angle_max, self._lidar_data.angle_min)
        self.assertEqual(self._lidar_data.intensities[0], 0.0)
        self.assertEqual(len(self._lidar_data.intensities), 900)
        self.assertEqual(self._lidar_data.intensities[450], 255.0)
        self._timeline.stop()
        lidar_sub.unregister()
        pass

    async def test_lidar_manual(self):
        from sensor_msgs.msg import LaserScan

        (result, error) = await load_test_file(self._nucleus_path + "/Samples/ROS/Robots/Carter_ROS.usd")
        self.assertTrue(result)

        stage = omni.usd.get_context().get_stage()

        PhysicsSchemaTools.addGroundPlane(stage, "/World/groundPlane", "Z", 1500, Gf.Vec3f(0, 0, -25), Gf.Vec3f(0.5))

        self.assertTrue(result)
        self._lidar_data = None

        def lida_callback(data: LaserScan):
            self._lidar_data = data

        lidar_sub = rospy.Subscriber("scan", LaserScan, lida_callback)

        await add_cube(stage, "/cube", 75, (200, 0, 75))

        # disable the lidar so we can tick it manually
        omni.kit.commands.execute(
            "ChangeProperty", prop_path=Sdf.Path("/Carter/ROS_Lidar.enabled"), value=False, prev=None
        )
        await omni.kit.app.get_app().next_update_async()
        self._timeline.play()
        await omni.kit.app.get_app().next_update_async()
        await simulate(1)
        # Should be no data yet
        self.assertIsNone(self._lidar_data)
        # Enable lidar by ticking it once
        result, status = omni.kit.commands.execute("RosBridgeTickComponent", path="/Carter/ROS_Lidar")
        # Wait for ROS nodes to initialize
        await asyncio.sleep(1.0)
        # Publish a lidar message
        result, status = omni.kit.commands.execute("RosBridgeTickComponent", path="/Carter/ROS_Lidar")
        self.assertTrue(status)
        # wait for message
        await asyncio.sleep(1.0)
        # Check message
        self.assertIsNotNone(self._lidar_data)
        self.assertGreater(self._lidar_data.angle_max, self._lidar_data.angle_min)
        self.assertEqual(self._lidar_data.intensities[0], 0.0)
        self.assertEqual(len(self._lidar_data.intensities), 900)
        self.assertEqual(self._lidar_data.intensities[450], 255.0)
        self._timeline.stop()
        lidar_sub.unregister()
        pass
