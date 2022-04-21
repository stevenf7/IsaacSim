# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

"""
Introduction:

In this standalone, the jetbot will move in a pre-determined pattern (time based), while publishing stereo camera rgb images
and imu sensor data for VINS fusion demonstration.
"""


from omni.isaac.kit import SimulationApp

simulation_app = SimulationApp({"headless": False})

from omni.isaac.core import World
from omni.isaac.core.utils.extensions import enable_extension
from omni.isaac.jetbot import Jetbot
from omni.isaac.core.utils.stage import get_current_stage
from omni.isaac.core.utils.prims import define_prim, get_prim_at_path
from omni.isaac.core.utils.nucleus import get_assets_root_path, get_assets_server

from omni.isaac.jetbot.controllers import DifferentialController
import numpy as np
from typing import Optional, Tuple
from pxr import Usd, UsdGeom, Sdf, Gf, UsdPhysics

# omniverse
import carb
import omni.kit.commands
import omni.kit.viewport_legacy
import omni.usd
from omni.isaac.core.utils.types import ArticulationAction
from omni.isaac.imu_sensor import _imu_sensor


# enable ROS bridge extension
enable_extension("omni.isaac.ros_bridge")
# check if rosmaster node is running
# this is to prevent this sample from waiting indefinetly if roscore is not running
# can be removed in regular usage
simulation_app.update()
result, check = omni.kit.commands.execute("RosBridgeRosMasterCheck")
if not check:
    carb.log_error("Please run roscore before executing this script")
    simulation_app.close()
    exit()

from std_msgs.msg import Float32MultiArray
import sensor_msgs.msg as sensor_msgs
import rospy


class JetbotVision(Jetbot):
    def __init__(
        self,
        prim_path: str,
        name: str = "jetbot",
        usd_path: Optional[str] = None,
        position: Optional[np.ndarray] = None,
        orientation: Optional[np.ndarray] = None,
    ) -> None:
        """
        [Summary]
        
        create a jetbot with a stereo camera set up located on the camera rack spaced out at 10 cm
        
        """
        super().__init__(prim_path=prim_path, name=name, usd_path=usd_path, position=position, orientation=orientation)
        self._meters_per_unit = UsdGeom.GetStageMetersPerUnit(omni.usd.get_context().get_stage())
        self._stage = get_current_stage()
        self._viewport_interface = omni.kit.viewport_legacy.get_viewport_interface()

        self._image_width = 640
        self._image_height = 480

        self.cameras = [
            # 0name, 1offset, 2orientation, 3hori aperture, 4vert aperture, 5projection, 6focal length, 7focus distance
            ("/camera_left", Gf.Vec3d(2.43254, 5, 0.0), (110, 0, -90), 21, 16, "perspective", 24, 400),
            ("/camera_right", Gf.Vec3d(2.43254, -5, 0.0), (110, 0, -90), 21, 16, "perspective", 24, 400),
        ]
        self._ros_camera_prims = []
        self._camera_tick_counter = 0
        self._CAMERA_PERIOD = 1.0 / 15  # 30Hz

        # add cameras on the imu link
        for i in range(len(self.cameras)):
            # add camera prim
            camera = self.cameras[i]
            camera_prim = UsdGeom.Camera(
                self._stage.DefinePrim(self._prim_path + "/chassis/rgb_camera" + camera[0], "Camera")
            )
            xform_api = UsdGeom.XformCommonAPI(camera_prim)
            xform_api.SetRotate(camera[2], UsdGeom.XformCommonAPI.RotationOrderXYZ)
            xform_api.SetTranslate(camera[1])
            camera_prim.GetHorizontalApertureAttr().Set(camera[3])
            camera_prim.GetVerticalApertureAttr().Set(camera[4])
            camera_prim.GetProjectionAttr().Set(camera[5])
            camera_prim.GetFocalLengthAttr().Set(camera[6])
            camera_prim.GetFocusDistanceAttr().Set(camera[7])

            # add ROS cameras to prims
            # only enable one point cloud
            result, self._ros_camera_prim = omni.kit.commands.execute(
                "ROSBridgeCreateCamera",
                path=camera[0] + "ROS",
                parent=self._prim_path + "/chassis/rgb_camera",
                resolution=Gf.Vec2i(self._image_width, self._image_height),
                frame_id="/jetbot" + camera[0],
                camera_info_topic="/jetbot" + camera[0] + "/camera_info",
                rgb_topic="/jetbot/camera_forward" + camera[0] + "/rgb",
                rgb_enabled=True,
                point_cloud_topic="/jetbot/camera_forward" + camera[0] + "/pointcloud",
                point_cloud_enabled=False,
                enabled=True,
                camera_prim_rel=[camera_prim.GetPrim().GetPrimPath()],
            )
            if not result:
                carb.log_error("failed to add ros camera: " + str(camera[0]))

            self._ros_camera_prims.append(self._ros_camera_prim)

            # create viewports
            self._viewport_handle = self._viewport_interface.create_instance()
            self._viewport_window = self._viewport_interface.get_viewport_window(self._viewport_handle)
            # Get viewport name
            self._viewport_window_name = self._viewport_interface.get_viewport_window_name(self._viewport_handle)
            self._viewport_window.set_window_size(self._image_width + 8, self._image_height + 30)
            # Set window resolution
            self._viewport_window.set_texture_resolution(self._image_width, self._image_height)
            self._viewport_window.set_active_camera(self._prim_path + "/chassis/rgb_camera" + camera[0])

        self._main_viewport = omni.kit.viewport_legacy.get_default_viewport_window()
        # set viewpoint of the main camera
        self._main_viewport.set_camera_position("/OmniverseKit_Persp", 3, 3, 3, True)
        self._main_viewport.set_camera_target("/OmniverseKit_Persp", 0, 0, 0, True)
        self._main_viewport.set_camera_move_velocity(0)
        self.dockViewports()

        # imu sensor setup
        self._is = _imu_sensor.acquire_imu_sensor_interface()
        self._imu_path = self._prim_path + "/chassis"

        _is_props = _imu_sensor.SensorProperties()
        _is_props.position = carb.Float3(0, 0, 0)
        _is_props.orientation = carb.Float4(0, 0, 0, 1)
        _is_props.sensorPeriod = -1  # 2ms
        self._imu_sensor_handle = self._is.add_sensor_on_body(self._imu_path, _is_props)
        self._base_lin = np.zeros(3)
        self._ang_vel = np.zeros(3)

        self._imu_msg = sensor_msgs.Imu()
        self._imu_msg.header.frame_id = "base_link"
        # set up ros publisher and clock
        _, _ = omni.kit.commands.execute("ROSBridgeCreateClock", path="/ROS_Clock", sim_time=True, enabled=False)
        self._imu_pub = rospy.Publisher("jetbot/imu_data", sensor_msgs.Imu, queue_size=21)

    def update_imu_sensor_data(self) -> None:
        """
        [summary]
        
        Updates processed imu sensor data from the robot body, store them in member variable _base_lin and _ang_vel
        """
        reading = self._is.get_sensor_readings(self._imu_sensor_handle)
        if reading.shape[0]:
            # linear acceleration
            self._imu_msg.linear_acceleration.x = float(reading[-1]["lin_acc_x"]) * self._meters_per_unit
            self._imu_msg.linear_acceleration.y = float(reading[-1]["lin_acc_y"]) * self._meters_per_unit
            self._imu_msg.linear_acceleration.z = float(reading[-1]["lin_acc_z"]) * self._meters_per_unit

            # angular velocity
            self._imu_msg.angular_velocity.x = float(reading[-1]["ang_vel_x"])
            self._imu_msg.angular_velocity.y = float(reading[-1]["ang_vel_y"])
            self._imu_msg.angular_velocity.z = float(reading[-1]["ang_vel_z"])
        else:
            self._imu_msg.linear_acceleration.x = 0
            self._imu_msg.linear_acceleration.y = 0
            self._imu_msg.linear_acceleration.z = 0

            # angular velocity
            self._imu_msg.angular_velocity.x = 0
            self._imu_msg.angular_velocity.y = 0
            self._imu_msg.angular_velocity.z = 0

        return

    def dockViewports(self) -> None:
        """
        [Summary]
    
        For instantiating and docking view ports
        """
        # first, set main viewport
        self._main_viewport = omni.kit.viewport_legacy.get_default_viewport_window()
        # set viewpoint of the main camera
        self._main_viewport.set_camera_position("/OmniverseKit_Persp", 3, 3, 3, True)
        self._main_viewport.set_camera_target("/OmniverseKit_Persp", 0, 0, 0, True)
        self._main_viewport.set_camera_move_velocity(0)
        carter2_viewport = omni.ui.Workspace.get_window("Viewport 2")
        carter3_viewport = omni.ui.Workspace.get_window("Viewport 3")
        if self._main_viewport is not None and carter2_viewport is not None and carter3_viewport is not None:
            carter2_viewport.dock_in(self._main_viewport, omni.ui.DockPosition.RIGHT, 2 / 3.0)
            carter3_viewport.dock_in(carter2_viewport, omni.ui.DockPosition.RIGHT, 0.5)

    def apply_wheel_actions(self, actions: ArticulationAction, current_time: float) -> None:
        """
        [Summary]

        Apply wheel articulation actions, update imu data, and tick ros bridge compnent
        """
        super().apply_wheel_actions(actions)

        # update imu data
        self.update_imu_sensor_data()
        # tick ros camera
        self._camera_tick_counter = current_time
        if self._camera_tick_counter >= self._CAMERA_PERIOD:
            self._camera_tick_counter = 0
            omni.kit.commands.execute(
                "RosBridgeTickComponent", path=self._prim_path + "/chassis" + self.cameras[0][0] + "ROS"
            )
            omni.kit.commands.execute(
                "RosBridgeTickComponent", path=self._prim_path + "/chassis" + self.cameras[1][0] + "ROS"
            )


if __name__ == "__main__":
    my_world = World(stage_units_in_meters=0.01)
    my_jetbot = my_world.scene.add(
        JetbotVision(prim_path="/World/Jetbot", name="my_jetbot", position=np.array([0, 0.0, 2.0]))
    )

    assets_root_path = get_assets_root_path()
    if assets_root_path is None:
        carb.log_error("Could not find Isaac Sim assets folder")

    prim = get_prim_at_path("/World/Warehouse")
    if not prim.IsValid():
        prim = define_prim("/World/Warehouse", "Xform")
        # asset_path = assets_root_path + "/Environments/Simple_Warehouse/warehouse.usd"
        assets_server_path = get_assets_server()
        if assets_server_path is None:
            carb.log_error("Could not find Isaac Sim assets server")
        asset_path = assets_server_path + "/Users/stevfeng/random_basic.usd"
        prim.GetReferences().AddReference(asset_path)

    my_controller = DifferentialController(name="simple_control")
    my_world.reset()

    rospy.init_node("jetbot", anonymous=False)
    rospy.set_param("use_sim_time", True)

    i = 0
    while simulation_app.is_running():
        my_world.step(render=True)
        omni.kit.commands.execute("RosBridgeTickComponent", path="/ROS_Clock")
        ros_time = rospy.get_rostime()

        current_time = ros_time.to_sec()
        if my_world.is_playing():
            print("index" + str(i))
            if my_world.current_time_step_index == 0:
                my_world.reset()
                my_controller.reset()
            if i >= 0 and i < 1000:
                # forward
                my_jetbot.apply_wheel_actions(my_controller.forward(command=[5, 0]), current_time)
                print("linear velocity" + str(my_jetbot.get_linear_velocity()))
            elif i >= 1000 and i < 1300:
                # rotate
                my_jetbot.apply_wheel_actions(my_controller.forward(command=[0.0, np.pi / 12]), current_time)
                print("angular velocity" + str(my_jetbot.get_angular_velocity()))
            elif i >= 1300 and i < 2000:
                # forward
                my_jetbot.apply_wheel_actions(my_controller.forward(command=[5, 0]), current_time)
                print("linear velocity" + str(my_jetbot.get_linear_velocity()))
            elif i >= 2000:
                i = 1
            i += 1

        my_jetbot.imu_msg.header.stamp = ros_time
        my_jetbot.imu_pub.publish(my_jetbot.imu_msg)

    simulation_app.close()
