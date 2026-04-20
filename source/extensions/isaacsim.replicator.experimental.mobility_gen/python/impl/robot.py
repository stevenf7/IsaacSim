# SPDX-FileCopyrightText: Copyright (c) 2025-2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""MobilityGen robot base class, front-camera utilities, and robot registry."""

from __future__ import annotations

import math

import isaacsim.core.experimental.utils.transform as transform_utils

# Standard imports
import numpy as np

# Isaac Sim Imports
from isaacsim.core.experimental.objects import Camera
from isaacsim.core.experimental.prims import Articulation, XformPrim
from isaacsim.core.experimental.utils.stage import get_current_stage
from pxr import Sdf

# Extension imports
from .common import Buffer, Module
from .types import Pose2d
from .utils.registry import Registry


def _join_sdf_paths(*subpaths: str) -> str:
    p = Sdf.Path(subpaths[0])
    for subpath in subpaths[1:]:
        subpath = subpath.strip("/")
        if subpath:
            p = p.AppendPath(subpath)
    return str(p)


# =========================================================
#  BASE CLASSES
# =========================================================


class MobilityGenRobot(Module):
    """Abstract base class for robots.

    This class defines an abstract base class for robots.

    Robot implementations must subclass this class, define the
    required class parameters and abstract methods.

    The two main abstract methods subclasses must define are the build() and write_action()
    methods.
    """

    physics_dt: float
    """The physics timestep to use for simulating the robot."""

    z_offset: float
    """The Z-axis offset height to spawn the robot. """

    chase_camera_base_path: str
    """The relative USD path which will be used to spawn the third person view camera.  This is typically set
    to the robot base frame."""

    chase_camera_x_offset: float
    """The relative X-axis offset to spawn the third person view camera."""

    chase_camera_z_offset: float
    """The relative Z-axis offset to spawn the third person view camera."""

    chase_camera_tilt_angle: float
    """The tilt angle to apply to the third person view camera."""

    occupancy_map_radius: float
    """The robot footprint radius to use for spawning and path planning."""

    occupancy_map_collision_radius: float
    """The robot footprint radius to use for collision based episode termination."""

    front_camera_type: type[Module]
    """The static class representing the front camera.  It should define a build() and attach() method. """

    front_camera_base_path: str
    """The relative USD path to spawn the front camera."""

    front_camera_rotation: tuple[float, float, float]
    """The relative XYZ rotation used when spawning the front camera. """

    front_camera_translation: tuple[float, float, float]
    """The relative XYZ translation used when spawning the front camera. """

    keyboard_linear_velocity_gain: float
    """The gain used to map keyboard button presses to the robot's linear velocity.  A larger
    gain results in faster movement."""

    keyboard_angular_velocity_gain: float
    """The gain used to map keyboard button presses to the robot's angular velocity.  A larger
    gain results in faster movement."""

    gamepad_linear_velocity_gain: float
    """The gain used to map gamepad axis movement to the robot's linear velocity.  A larger
    gain results in faster movement."""

    gamepad_angular_velocity_gain: float
    """The gain used to map gamepad axis movement to the robot's angular velocity.  A larger
    gain results in faster movement."""

    random_action_linear_velocity_range: tuple[float, float]
    """The robot linear velocity limits for the random acceleration scenario."""

    random_action_angular_velocity_range: tuple[float, float]
    """The robot angular velocity limits for the random acceleration scenario."""

    random_action_linear_acceleration_std: float
    """The standard deviation used for sampling the robot linear acceleration each timestep during
    the random acceleration scenario."""

    random_action_angular_acceleration_std: float
    """The standard deviation used for sampling the robot angular acceleration each timestep during
    the random acceleration scenario."""

    random_action_grid_pose_sampler_grid_size: float
    """The grid size to use for spawning the robot during the random acceleration scenario."""

    path_following_speed: float
    """The constant linear speed to use for the path following scenario."""

    path_following_angular_gain: float
    """The gain used for the proportional steering control in the path following scenario.
    A larger gain results in quicker turning, but potential overshoot and wobbling."""

    path_following_stop_distance_threshold: float
    """The distance threshold at which point the robot will stop.  Applies to the path following scenario."""

    path_following_forward_angle_threshold = math.pi
    """The angle threshold at which point the robot will move forward.  Applies to the path following scenario."""

    path_following_target_point_offset_meters: float
    """The offset distance used to generate the 'target point' that the robot will follow in the path following scenario.
    A larger offset results in smoother motion, but too large may cause the robot to cut corners during turns."""

    def __init__(self, prim_path: str, articulation: Articulation, front_camera: Module) -> None:
        self.prim_path = prim_path
        self.articulation = articulation

        self.action = Buffer(np.zeros(2))
        self.position = Buffer()
        self.orientation = Buffer()
        self.joint_positions = Buffer()
        self.joint_velocities = Buffer()
        self.linear_velocity = Buffer()
        self.angular_velocity = Buffer()
        self.front_camera = front_camera

    @classmethod
    def build_front_camera(cls, prim_path: str) -> Module:
        """Build and attach the front camera at the given prim path.

        Args:
            prim_path: The USD prim path under which to spawn the camera.

        Returns:
            The built front camera module.
        """
        camera_path = _join_sdf_paths(prim_path, cls.front_camera_base_path)
        stage = get_current_stage(backend="usd")
        if not stage.GetPrimAtPath(camera_path).IsValid():
            stage.DefinePrim(camera_path, "Xform")

        orientation = transform_utils.euler_angles_to_quaternion(
            list(cls.front_camera_rotation), degrees=True, extrinsic=True
        ).numpy()
        translation = np.array(cls.front_camera_translation, dtype=np.float32)
        xform = XformPrim(camera_path)
        xform.reset_xform_op_properties()
        xform.set_local_poses(translation[np.newaxis], orientation[np.newaxis])

        return cls.front_camera_type.build(prim_path=camera_path)

    def build_chase_camera(self) -> str:
        """Build the chase (third-person) camera and return its USD path.

        Returns:
            The USD prim path of the created chase camera.
        """
        camera_path = _join_sdf_paths(self.prim_path, self.chase_camera_base_path, "chase_camera")

        camera = Camera(camera_path)
        camera.set_focal_lengths(10.0)
        camera.set_apertures(horizontal_apertures=30.0, vertical_apertures=30.0)
        camera.set_clipping_ranges(near_distances=0.1, far_distances=100000.0)

        orientation = transform_utils.euler_angles_to_quaternion(
            [self.chase_camera_tilt_angle, 0.0, -90.0], degrees=True, extrinsic=True
        ).numpy()
        translation = np.array([self.chase_camera_x_offset, 0.0, self.chase_camera_z_offset], dtype=np.float32)
        xform = XformPrim(camera_path)
        xform.reset_xform_op_properties()
        xform.set_local_poses(translation[np.newaxis], orientation[np.newaxis])

        return camera_path

    @classmethod
    def build(cls, prim_path: str) -> "MobilityGenRobot":
        """Build the robot at the given prim path.

        Args:
            prim_path: The USD prim path at which to spawn the robot.

        Returns:
            The constructed robot instance.
        """
        raise NotImplementedError

    def write_action(self, step_size: float) -> None:
        """Write the current action to the robot actuators.

        Args:
            step_size: The physics timestep size in seconds.
        """
        raise NotImplementedError

    def is_physics_ready(self) -> bool:
        """Return True if the physics tensor entity is valid and ready.

        Returns:
            True if the articulation physics tensor entity is valid.
        """
        return self.articulation.is_physics_tensor_entity_valid()

    def update_state(self) -> None:
        """Update all robot state buffers from the physics simulation."""
        if not self.articulation.is_physics_tensor_entity_valid():
            return
        positions, orientations = self.articulation.get_world_poses()
        self.position.set_value(positions.numpy()[0])
        self.orientation.set_value(orientations.numpy()[0])
        self.joint_positions.set_value(self.articulation.get_dof_positions().numpy()[0])
        self.joint_velocities.set_value(self.articulation.get_dof_velocities().numpy()[0])
        linear_vels, angular_vels = self.articulation.get_velocities()
        self.linear_velocity.set_value(linear_vels.numpy()[0])
        self.angular_velocity.set_value(angular_vels.numpy()[0])
        super().update_state()

    def write_replay_data(self) -> None:
        """Write pose and joint positions back to the simulation for replay."""
        position = self.position.get_value()
        orientation = self.orientation.get_value()
        self.articulation.set_world_poses(position[np.newaxis], orientation[np.newaxis])
        self.articulation.set_dof_positions(self.joint_positions.get_value()[np.newaxis])
        super().write_replay_data()

    def set_pose_2d(self, pose: Pose2d) -> None:
        """Set the robot's 2D pose in the world frame.

        Args:
            pose: The target 2D pose (x, y, theta).
        """
        if self.is_physics_ready():
            self.articulation.set_velocities(linear_velocities=np.zeros((1, 3)), angular_velocities=np.zeros((1, 3)))
        positions, orientations = self.articulation.get_world_poses()
        position = positions.numpy()[0]
        position[0] = pose.x
        position[1] = pose.y
        position[2] = self.z_offset
        orientation = transform_utils.euler_angles_to_quaternion([0.0, 0.0, pose.theta]).numpy()
        self.articulation.set_world_poses(position[np.newaxis], orientation[np.newaxis])

    def get_pose_2d(self) -> Pose2d:
        """Get the robot's current 2D pose from the physics simulation.

        Returns:
            The current 2D pose (x, y, theta) of the robot.
        """
        positions, orientations = self.articulation.get_world_poses()
        position = positions.numpy()[0]
        # extrinsic=True (default): output order [X,Y,Z] = [roll, pitch, yaw], so [2] is yaw
        theta = transform_utils.quaternion_to_euler_angles(orientations.numpy()[0]).numpy()[2]
        return Pose2d(x=position[0], y=position[1], theta=theta)


ROBOTS = Registry[MobilityGenRobot]()
