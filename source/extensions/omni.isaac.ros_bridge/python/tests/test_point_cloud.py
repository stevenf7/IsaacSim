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

from .common import add_cube, simulate, wait_for_rosmaster, add_carter_ros
from omni.isaac.utils.scripts.nucleus_utils import find_nucleus_server
from pxr import Sdf

# Having a test class dervived from omni.kit.test.AsyncTestCase declared on the root of module will make it auto-discoverable by omni.kit.test
class TestRosPointCloud(omni.kit.test.AsyncTestCase):
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

    async def test_3D_point_cloud(self):
        import rospy

        from sensor_msgs.msg import PointCloud2

        await add_carter_ros()
        await add_cube("/cube", 80, (160, 10, 50))

        # Disable LaserScan for ROS Lidar (Required to enable highLod in Lidar sensor)
        omni.kit.commands.execute(
            "ChangeProperty", prop_path=Sdf.Path("/Carter/ROS_Lidar.laserScanEnabled"), value=False, prev=None
        )

        # Enable Point Cloud publisher for ROS Lidar
        omni.kit.commands.execute(
            "ChangeProperty", prop_path=Sdf.Path("/Carter/ROS_Lidar.pointCloudEnabled"), value=True, prev=None
        )

        # Enable highLod for Lidar
        omni.kit.commands.execute(
            "ChangeProperty", prop_path=Sdf.Path("/Carter/chassis_link/carter_lidar.highLod"), value=True, prev=None
        )

        self._point_cloud_data = None

        def point_cloud_callback(data: PointCloud2):
            self._point_cloud_data = data

        lidar_sub = rospy.Subscriber("/point_cloud", PointCloud2, point_cloud_callback)

        self._timeline.play()
        await omni.kit.app.get_app().next_update_async()
        await simulate(1)

        # If 3D point cloud (highLOD enabled)
        self.assertIsNotNone(self._point_cloud_data)
        self.assertGreater(self._point_cloud_data.height, 1)
        self.assertGreater(self._point_cloud_data.width, 1)
        self.assertEqual(
            self._point_cloud_data.row_step / self._point_cloud_data.point_step, self._point_cloud_data.width
        )
        self.assertEqual(
            len(self._point_cloud_data.data) / self._point_cloud_data.row_step, self._point_cloud_data.height
        )
        self.assertEqual(self._point_cloud_data.data[114210], 198)
        self.assertEqual(self._point_cloud_data.fields[0].datatype, 7)
        self.assertEqual(self._point_cloud_data.fields[1].datatype, 7)
        self.assertEqual(self._point_cloud_data.fields[2].datatype, 7)

        self._timeline.stop()
        lidar_sub.unregister()
        pass

    async def test_flat_point_cloud(self):
        import rospy

        from sensor_msgs.msg import PointCloud2

        await add_carter_ros()
        await add_cube("/cube", 80, (160, 10, 50))

        # Enable Point Cloud publisher for ROS Lidar
        omni.kit.commands.execute(
            "ChangeProperty", prop_path=Sdf.Path("/Carter/ROS_Lidar.pointCloudEnabled"), value=True, prev=None
        )

        self._point_cloud_data = None

        def point_cloud_callback(data: PointCloud2):
            self._point_cloud_data = data

        lidar_sub = rospy.Subscriber("/point_cloud", PointCloud2, point_cloud_callback)

        self._timeline.play()
        await omni.kit.app.get_app().next_update_async()
        await simulate(1)

        # If flat point cloud (highLOD disabled)
        self.assertEqual(self._point_cloud_data.height, 1)
        self.assertGreater(self._point_cloud_data.width, 1)
        self.assertEqual(len(self._point_cloud_data.data), self._point_cloud_data.row_step)
        self.assertEqual(
            self._point_cloud_data.row_step / self._point_cloud_data.point_step, self._point_cloud_data.width
        )
        self.assertEqual(self._point_cloud_data.data[11301], 29)
        self.assertEqual(self._point_cloud_data.fields[0].datatype, 7)
        self.assertEqual(self._point_cloud_data.fields[1].datatype, 7)
        self.assertEqual(self._point_cloud_data.fields[2].datatype, 7)

        self._timeline.stop()
        lidar_sub.unregister()
        pass

    async def test_depth_to_point_cloud(self):
        import rospy

        from sensor_msgs.msg import PointCloud2

        await add_carter_ros()
        await add_cube("/cube", 80, (160, 10, 50))

        # Setting the Point Cloud publisher topic in ROS Camera
        omni.kit.commands.execute(
            "ChangeProperty",
            prop_path=Sdf.Path("/Carter/ROS_Camera_Stereo_Left.pointCloudPubTopic"),
            value="/point_cloud_left",
            prev=None,
        )

        # Enable Point Cloud publisher in ROS Camera
        omni.kit.commands.execute(
            "ChangeProperty",
            prop_path=Sdf.Path("/Carter/ROS_Camera_Stereo_Left.pointCloudEnabled"),
            value=True,
            prev=None,
        )

        self._point_cloud_data = None

        def point_cloud_callback(data: PointCloud2):
            self._point_cloud_data = data

        camera_sub = rospy.Subscriber("/point_cloud_left", PointCloud2, point_cloud_callback)

        self._timeline.play()
        await omni.kit.app.get_app().next_update_async()
        await simulate(1)

        self.assertIsNotNone(self._point_cloud_data)
        self.assertGreater(self._point_cloud_data.height, 1)
        self.assertGreater(self._point_cloud_data.width, 1)
        self.assertEqual(
            self._point_cloud_data.row_step / self._point_cloud_data.point_step, self._point_cloud_data.width
        )
        self.assertEqual(
            len(self._point_cloud_data.data) / self._point_cloud_data.row_step, self._point_cloud_data.height
        )

        self.assertEqual(self._point_cloud_data.data[516327], 190)
        self.assertEqual(self._point_cloud_data.data[712187], 63)
        self.assertEqual(self._point_cloud_data.fields[0].datatype, 7)
        self.assertEqual(self._point_cloud_data.fields[1].datatype, 7)
        self.assertEqual(self._point_cloud_data.fields[2].datatype, 7)

        self._timeline.stop()
        camera_sub.unregister()
        pass

    async def test_3D_point_cloud_manual(self):
        import rospy

        from sensor_msgs.msg import PointCloud2

        await add_carter_ros()
        await add_cube("/cube", 80, (160, 10, 50))

        # Disable LaserScan for ROS Lidar (Required to enable highLod in Lidar sensor)
        omni.kit.commands.execute(
            "ChangeProperty", prop_path=Sdf.Path("/Carter/ROS_Lidar.laserScanEnabled"), value=False, prev=None
        )

        # Enable Point Cloud publisher for ROS Lidar
        omni.kit.commands.execute(
            "ChangeProperty", prop_path=Sdf.Path("/Carter/ROS_Lidar.pointCloudEnabled"), value=True, prev=None
        )

        # Enable highLod for Lidar
        omni.kit.commands.execute(
            "ChangeProperty", prop_path=Sdf.Path("/Carter/chassis_link/carter_lidar.highLod"), value=True, prev=None
        )

        self._point_cloud_data = None

        def point_cloud_callback(data: PointCloud2):
            self._point_cloud_data = data

        lidar_sub = rospy.Subscriber("point_cloud", PointCloud2, point_cloud_callback)

        # disable the lidar so we can tick it manually
        omni.kit.commands.execute(
            "ChangeProperty", prop_path=Sdf.Path("/Carter/ROS_Lidar.enabled"), value=False, prev=None
        )
        await omni.kit.app.get_app().next_update_async()
        self._timeline.play()
        await omni.kit.app.get_app().next_update_async()
        await simulate(1)
        # Should be no data yet
        self.assertIsNone(self._point_cloud_data)
        # Enable lidar by ticking it once
        result, status = omni.kit.commands.execute("RosBridgeTickComponent", path="/Carter/ROS_Lidar")
        # Wait for ROS nodes to initialize
        await asyncio.sleep(1.0)
        # Publish a point_cloud message
        result, status = omni.kit.commands.execute("RosBridgeTickComponent", path="/Carter/ROS_Lidar")
        self.assertTrue(status)
        # wait for message
        await asyncio.sleep(1.0)
        # Check message

        # If 3D point cloud (highLOD enabled)
        self.assertIsNotNone(self._point_cloud_data)
        self.assertGreater(self._point_cloud_data.height, 1)
        self.assertGreater(self._point_cloud_data.width, 1)
        self.assertEqual(
            self._point_cloud_data.row_step / self._point_cloud_data.point_step, self._point_cloud_data.width
        )
        self.assertEqual(
            len(self._point_cloud_data.data) / self._point_cloud_data.row_step, self._point_cloud_data.height
        )
        self.assertEqual(self._point_cloud_data.data[114210], 198)
        self.assertEqual(self._point_cloud_data.fields[0].datatype, 7)
        self.assertEqual(self._point_cloud_data.fields[1].datatype, 7)
        self.assertEqual(self._point_cloud_data.fields[2].datatype, 7)

        self._timeline.stop()
        lidar_sub.unregister()
        pass

    async def test_flat_point_cloud_manual(self):
        import rospy

        from sensor_msgs.msg import PointCloud2

        await add_carter_ros()
        await add_cube("/cube", 80, (160, 10, 50))

        # Enable Point Cloud publisher for ROS Lidar
        omni.kit.commands.execute(
            "ChangeProperty", prop_path=Sdf.Path("/Carter/ROS_Lidar.pointCloudEnabled"), value=True, prev=None
        )

        self._point_cloud_data = None

        def point_cloud_callback(data: PointCloud2):
            self._point_cloud_data = data

        lidar_sub = rospy.Subscriber("point_cloud", PointCloud2, point_cloud_callback)

        # disable the lidar so we can tick it manually
        omni.kit.commands.execute(
            "ChangeProperty", prop_path=Sdf.Path("/Carter/ROS_Lidar.enabled"), value=False, prev=None
        )
        await omni.kit.app.get_app().next_update_async()
        self._timeline.play()
        await omni.kit.app.get_app().next_update_async()
        await simulate(1)
        # Should be no data yet
        self.assertIsNone(self._point_cloud_data)
        # Enable lidar by ticking it once
        result, status = omni.kit.commands.execute("RosBridgeTickComponent", path="/Carter/ROS_Lidar")
        # Wait for ROS nodes to initialize
        await asyncio.sleep(1.0)
        # Publish a point_cloud message
        result, status = omni.kit.commands.execute("RosBridgeTickComponent", path="/Carter/ROS_Lidar")
        self.assertTrue(status)
        # wait for message
        await asyncio.sleep(1.0)
        # Check message

        # If flat point cloud (highLOD disabled)
        self.assertEqual(self._point_cloud_data.height, 1)
        self.assertGreater(self._point_cloud_data.width, 1)
        self.assertEqual(len(self._point_cloud_data.data), self._point_cloud_data.row_step)
        self.assertEqual(
            self._point_cloud_data.row_step / self._point_cloud_data.point_step, self._point_cloud_data.width
        )
        self.assertEqual(self._point_cloud_data.data[11301], 29)
        self.assertEqual(self._point_cloud_data.fields[0].datatype, 7)
        self.assertEqual(self._point_cloud_data.fields[1].datatype, 7)
        self.assertEqual(self._point_cloud_data.fields[2].datatype, 7)

        self._timeline.stop()
        lidar_sub.unregister()
        pass

    async def test_depth_to_point_cloud_manual(self):
        import rospy

        from sensor_msgs.msg import PointCloud2

        await add_carter_ros()
        await add_cube("/cube", 80, (160, 10, 50))

        # Setting the Point Cloud publisher topic in ROS Camera
        omni.kit.commands.execute(
            "ChangeProperty",
            prop_path=Sdf.Path("/Carter/ROS_Camera_Stereo_Left.pointCloudPubTopic"),
            value="/point_cloud_left",
            prev=None,
        )

        # Enable Point Cloud publisher in ROS Camera
        omni.kit.commands.execute(
            "ChangeProperty",
            prop_path=Sdf.Path("/Carter/ROS_Camera_Stereo_Left.pointCloudEnabled"),
            value=True,
            prev=None,
        )

        self._point_cloud_data = None

        def point_cloud_callback(data: PointCloud2):
            self._point_cloud_data = data

        camera_sub = rospy.Subscriber("point_cloud_left", PointCloud2, point_cloud_callback)

        # disable the ROS Camera so we can tick it manually
        omni.kit.commands.execute(
            "ChangeProperty", prop_path=Sdf.Path("/Carter/ROS_Camera_Stereo_Left.enabled"), value=False, prev=None
        )
        await omni.kit.app.get_app().next_update_async()
        self._timeline.play()
        await omni.kit.app.get_app().next_update_async()
        await simulate(1)
        # Should be no data yet
        self.assertIsNone(self._point_cloud_data)

        # Enable ROS Camera by ticking it once
        result, status = omni.kit.commands.execute("RosBridgeTickComponent", path="/Carter/ROS_Camera_Stereo_Left")

        # Wait for ROS nodes to initialize
        await asyncio.sleep(1.0)

        # Publish a point cloud message
        result, status = omni.kit.commands.execute("RosBridgeTickComponent", path="/Carter/ROS_Camera_Stereo_Left")
        self.assertTrue(status)

        # wait for message
        await asyncio.sleep(1.0)

        # Check message
        self.assertIsNotNone(self._point_cloud_data)
        self.assertGreater(self._point_cloud_data.height, 1)
        self.assertGreater(self._point_cloud_data.width, 1)
        self.assertEqual(
            self._point_cloud_data.row_step / self._point_cloud_data.point_step, self._point_cloud_data.width
        )
        self.assertEqual(
            len(self._point_cloud_data.data) / self._point_cloud_data.row_step, self._point_cloud_data.height
        )

        self.assertEqual(self._point_cloud_data.data[516327], 190)
        self.assertEqual(self._point_cloud_data.data[712187], 63)
        self.assertEqual(self._point_cloud_data.fields[0].datatype, 7)
        self.assertEqual(self._point_cloud_data.fields[1].datatype, 7)
        self.assertEqual(self._point_cloud_data.fields[2].datatype, 7)

        self._timeline.stop()
        camera_sub.unregister()
        pass
