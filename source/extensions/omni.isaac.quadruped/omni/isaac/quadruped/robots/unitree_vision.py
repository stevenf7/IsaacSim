# Copyright (c) 2022, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#


# python
import os
import time
from typing import Optional
import numpy as np
import scipy.spatial.transform as tf
from typing import Optional
from dataclasses import dataclass, field
import asyncio

# omniverse
import carb
from pxr import Usd, UsdGeom, Sdf, Gf, UsdPhysics
import omni.kit.commands
import omni.kit.viewport_legacy
import omni.usd


from omni.isaac.quadruped.robots import Unitree


class UnitreeVision(Unitree):
    """[Summary]
    
    For unitree based quadrupeds (A1 or Go1) with camera
    """

    def __init__(
        self,
        prim_path: str,
        name: str = "unitree_quadruped",
        physics_dt: Optional[float] = 1 / 400.0,
        usd_path: Optional[str] = None,
        position: Optional[np.ndarray] = None,
        orientation: Optional[np.ndarray] = None,
        model: Optional[str] = "A1",
        is_ros2: Optional[bool] = False,
        way_points: Optional[np.ndarray] = None,
    ) -> None:
        """
        [Summary]
        
        initialize robot, set up sensors and controller
        
        Arguments:
            prim_path {str} -- prim path of the robot on the stage
            name {str} -- name of the quadruped
            physics_dt {float} -- physics downtime of the controller
            usd_path {str} -- robot usd filepath in the directory
            position {np.ndarray} -- position of the robot
            orientation {np.ndarray} -- orientation of the robot
            model {str} -- robot model (can be either A1 or Go1)
            way_points {np.ndarray} -- waypoints for the robot

        """
        super().__init__(prim_path, name, physics_dt, usd_path, position, orientation, model, way_points)

        self.image_width = 640
        self.image_height = 480

        self.cameras = [
            # 0name, 1offset, 2orientation, 3hori aperture, 4vert aperture, 5projection, 6focal length, 7focus distance
            ("/camera_left", Gf.Vec3d(0.2693, 0.025, 0.067), (90, 0, -90), 21, 16, "perspective", 24, 400),
            ("/camera_right", Gf.Vec3d(0.2693, -0.025, 0.067), (90, 0, -90), 21, 16, "perspective", 24, 400),
        ]
        self.ros_camera_prims = []
        self.camera_tick_counter = 0
        self.CAMERA_PERIOD = 1.0 / 15  # 30Hz

        # after stage is defined
        self._viewport_interface = omni.kit.viewport_legacy.get_viewport_interface()
        self._stage = omni.usd.get_context().get_stage()

        # add cameras on the imu link
        for i in range(len(self.cameras)):
            # add camera prim
            camera = self.cameras[i]
            camera_prim = UsdGeom.Camera(self._stage.DefinePrim(self._prim_path + "/imu_link" + camera[0], "Camera"))
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
            result, self.ros_camera_prim = omni.kit.commands.execute(
                "ROSBridgeCreateCamera",
                path=camera[0] + "ROS",
                parent=self._prim_path + "/imu_link",
                resolution=Gf.Vec2i(self.image_width, self.image_height),
                frame_id="/isaac_a1" + camera[0],
                camera_info_topic="/isaac_a1" + camera[0] + "/camera_info",
                rgb_topic="/isaac_a1/camera_forward" + camera[0] + "/rgb",
                rgb_enabled=True,
                point_cloud_topic="/isaac_a1/camera_forward" + camera[0] + "/pointcloud",
                point_cloud_enabled=False,
                enabled=False,
                camera_prim_rel=[camera_prim.GetPrim().GetPrimPath()],
            )
            self.ros_camera_prims.append(self.ros_camera_prim)

            # create viewports
            self.viewport_handle = self._viewport_interface.create_instance()
            self.viewport_window = self._viewport_interface.get_viewport_window(self.viewport_handle)
            # Get viewport name
            self.viewport_window_name = self._viewport_interface.get_viewport_window_name(self.viewport_handle)
            self.viewport_window.set_window_size(self.image_width + 8, self.image_height + 30)
            # Set window resolution
            self.viewport_window.set_texture_resolution(self.image_width, self.image_height)
            self.viewport_window.set_active_camera(self._prim_path + "/imu_link" + camera[0])

        self.main_viewport = omni.kit.viewport_legacy.get_default_viewport_window()
        # set viewpoint of the main camera
        self.main_viewport.set_camera_position("/OmniverseKit_Persp", 3, 3, 3, True)
        self.main_viewport.set_camera_target("/OmniverseKit_Persp", 0, 0, 0, True)
        self.main_viewport.set_camera_move_velocity(0)
        self.dockViewports()

        self.is_ros2 = is_ros2

    def dockViewports(self) -> None:
        """
        [Summary]
    
        For instantiating and docking view ports
        """
        # first, set main viewport
        self.main_viewport = omni.kit.viewport_legacy.get_default_viewport_window()
        # set viewpoint of the main camera
        self.main_viewport.set_camera_position("/OmniverseKit_Persp", 3, 3, 3, True)
        self.main_viewport.set_camera_target("/OmniverseKit_Persp", 0, 0, 0, True)
        self.main_viewport.set_camera_move_velocity(0)
        carter2_viewport = omni.ui.Workspace.get_window("Viewport 2")
        carter3_viewport = omni.ui.Workspace.get_window("Viewport 3")
        if self.main_viewport is not None and carter2_viewport is not None and carter3_viewport is not None:
            carter2_viewport.dock_in(self.main_viewport, omni.ui.DockPosition.RIGHT, 2 / 3.0)
            carter3_viewport.dock_in(carter2_viewport, omni.ui.DockPosition.RIGHT, 0.5)

    def update(self) -> None:
        """
        [Summary]
        
        Update robot variables from the environment

        """
        super().update()

    def advance(self, dt, goal, path_follow=False) -> np.ndarray:
        """[summary]
        
        calls the unitree advance to compute torque, and ticks the ros bridge cameras
        
        Argument:
        dt {float} -- Timestep update in the world.
        goal {List[int]} -- x velocity, y velocity, angular velocity, state switch
        path_follow {bool} -- True for following a set of coordinates, False for keyboard control

        Returns:
        np.ndarray -- The desired joint torques for the robot.
        """
        super().advance(dt, goal, path_follow)
        # tick ros camera
        self.camera_tick_counter += dt
        if self.camera_tick_counter >= self.CAMERA_PERIOD:
            self.camera_tick_counter = 0
            if self.is_ros2:
                omni.kit.commands.execute(
                    "Ros2BridgeTickComponent", path=self._prim_path + "/imu_link" + self.cameras[0][0] + "ROS"
                )
                omni.kit.commands.execute(
                    "Ros2BridgeTickComponent", path=self._prim_path + "/imu_link" + self.cameras[1][0] + "ROS"
                )
            else:
                omni.kit.commands.execute(
                    "RosBridgeTickComponent", path=self._prim_path + "/imu_link" + self.cameras[0][0] + "ROS"
                )
                omni.kit.commands.execute(
                    "RosBridgeTickComponent", path=self._prim_path + "/imu_link" + self.cameras[1][0] + "ROS"
                )
