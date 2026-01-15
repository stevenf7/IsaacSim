# SPDX-FileCopyrightText: Copyright (c) 2021-2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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

from typing import Optional

import warp as wp


class JointState:
    """JointState is a struct that contains the state of the joints of the robot."""

    def __init__(
        self,
        names: list[str],
        positions: wp.array(dtype=wp.Float),
        velocities: wp.array(dtype=wp.Float),
        efforts: wp.array(dtype=wp.Float),
    ):
        """Initialize a JointState.

        Args:
            names: The names of the joints.
            positions: The positions of the joints as a warp array.
            velocities: The velocities of the joints as a warp array.
            efforts: The efforts of the joints as a warp array.
        Raises:
            ValueError: If names, positions, velocities, and efforts are not of same length.
            ValueError: If positions is not a warp array.
            ValueError: If velocities is not a warp array.
            ValueError: If efforts is not a warp array.
        """

        # All inputs must be the same length:
        if not (len(names) == len(positions) == len(velocities) == len(efforts)):
            raise ValueError("names, positions, velocities and efforts must all have the same length")

        # Enforce that these are warp array inputs:
        if not isinstance(positions, wp.array):
            raise ValueError("Positions must be a warp array.")
        if not isinstance(velocities, wp.array):
            raise ValueError("Velocities must be a warp array.")
        if not isinstance(efforts, wp.array):
            raise ValueError("Efforts must be a warp array.")

        self.names = names
        self.positions = positions
        self.velocities = velocities
        self.efforts = efforts


class RootState:
    """RootState is a struct that contains the state of the root of the robot."""

    def __init__(
        self,
        position: wp.vec3,
        orientation: wp.quat,
        linear_velocity: wp.vec3,
        angular_velocity: wp.vec3,
    ):
        """Initialize a RootState object.

        Args:
            position: The position of the root as a warp vec3.
            orientation: The orientation of the root as a warp quaternion.
            linear_velocity: The linear velocity of the root as a warp vec3.
            angular_velocity: The angular velocity of the root as a warp vec3.

        Raises:
            ValueError: If position, orientation, linear_velocity, or angular_velocity are not
                the correct warp types (wp.vec3, wp.quat, wp.vec3, wp.vec3 respectively).
        """
        # Since it is rare that a user will be constructing RootState objects manually,
        # we will enforce stricter type checking here.
        if (
            not isinstance(position, wp.vec3)
            or not isinstance(orientation, wp.quat)
            or not isinstance(linear_velocity, wp.vec3)
            or not isinstance(angular_velocity, wp.vec3)
        ):
            raise ValueError("Position, orientation, linear velocity, and angular velocity must be warp types.")
        self.position = position
        self.orientation = orientation
        self.linear_velocity = linear_velocity
        self.angular_velocity = angular_velocity


class BodyState:
    """BodyState is a struct that contains the state of non-root rigid bodies of the robot."""

    def __init__(
        self,
        names: list[str],
        positions: wp.array(dtype=wp.vec3),
        orientations: wp.array(dtype=wp.quat),
        linear_velocities: wp.array(dtype=wp.vec3),
        angular_velocities: wp.array(dtype=wp.vec3),
    ):
        """Initialize a BodyState object.

        Args:
            names: The names of the non-root rigid bodies.
            positions: The positions of the non-root rigid bodies as a warp array of vec3.
            orientations: The orientations of the non-root rigid bodies as a warp array of quaternions.
            linear_velocities: The linear velocities of the non-root rigid bodies as a warp array of vec3.
            angular_velocities: The angular velocities of the non-root rigid bodies as a warp array of vec3.

        Raises:
            ValueError: If names, positions, orientations, linear_velocities, and angular_velocities
                do not all have the same length.
            ValueError: If positions, orientations, linear_velocities, or angular_velocities are not
                warp arrays.
        """
        if (
            len(names) != len(positions)
            or len(names) != len(orientations)
            or len(names) != len(linear_velocities)
            or len(names) != len(angular_velocities)
        ):
            raise ValueError(
                "All names, positions, orientations, linear velocities, and angular velocities must have the same length."
            )

        # Since it is rare that a user will be constructing BodyState objects manually,
        # we will enforce stricter type checking here.
        if (
            not isinstance(positions, wp.array)
            or not isinstance(orientations, wp.array)
            or not isinstance(linear_velocities, wp.array)
            or not isinstance(angular_velocities, wp.array)
        ):
            raise ValueError("Positions, orientations, linear velocities, and angular velocities must be warp types.")

        self.names = names
        self.positions = positions
        self.orientations = orientations
        self.linear_velocities = linear_velocities
        self.angular_velocities = angular_velocities


class RobotState:
    """RobotState is a composite struct that contains the state of the robot."""

    def __init__(
        self,
        joints: Optional[JointState] = None,
        root: Optional[RootState] = None,
        bodies: Optional[BodyState] = None,
        tool_frames: Optional[BodyState] = None,
    ):
        """Initialize a RobotState object.

        Args:
            joints: The state of the joints of the robot.
            root: The state of the root of the robot.
            bodies: The state of the non-root rigid bodies of the robot.
            tool_frames: The state of the tool frames (end-effectors) of the robot.
        """
        self.joints = joints
        self.root = root
        self.bodies = bodies
        self.tool_frames = tool_frames


class Action:
    """Action is a struct that contains the real-time joint-space action to be sent to a controlled robot."""

    def __init__(
        self,
        names: list[str],
        positions: Optional[wp.array(dtype=wp.Float)] = None,
        velocities: Optional[wp.array(dtype=wp.Float)] = None,
        efforts: Optional[wp.array(dtype=wp.Float)] = None,
    ):
        """Initialize an Action.

        Args:
            names: The names of the joints.
            positions: The desired positions of the joints as a warp array.
            velocities: The desired velocities of the joints as a warp array.
            efforts: The feed-forward efforts of the joints as a warp array.

        Raises:
            ValueError: If all of positions, velocities, and efforts are None.
            ValueError: If names and positions have different lengths when positions is provided.
            ValueError: If names and velocities have different lengths when velocities is provided.
            ValueError: If names and efforts have different lengths when efforts is provided.
            ValueError: If positions is provided but is not a warp array.
            ValueError: If velocities is provided but is not a warp array.
            ValueError: If efforts is provided but is not a warp array.
        """
        if (positions is None) and (velocities is None) and (efforts is None) and not (len(names) == 0):
            raise ValueError("If not position, velocity, or efforts are defined, then names cannot have any elements.")

        if (positions is not None) and (len(names) != len(positions)):
            raise ValueError("Names and positions must have the same length.")
        if (velocities is not None) and (len(names) != len(velocities)):
            raise ValueError("Names and velocities must have the same length.")
        if (efforts is not None) and (len(names) != len(efforts)):
            raise ValueError("Names and efforts must have the same length.")

        # Since it is rare that a user will be constructing Action objects manually,
        # we will enforce stricter type checking here.
        if (positions is not None) and (not isinstance(positions, wp.array)):
            raise ValueError("Positions must be a warp array.")
        if (velocities is not None) and (not isinstance(velocities, wp.array)):
            raise ValueError("Velocities must be a warp array.")
        if (efforts is not None) and (not isinstance(efforts, wp.array)):
            raise ValueError("Efforts must be a warp array.")

        self.names = names
        self.positions = positions
        self.velocities = velocities
        self.efforts = efforts
