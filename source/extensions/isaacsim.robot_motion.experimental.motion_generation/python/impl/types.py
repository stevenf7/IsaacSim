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

import numpy as np
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


def _combine_joint_states(
    joint_state_1: Optional[JointState], joint_state_2: Optional[JointState]
) -> tuple[bool, JointState]:
    if joint_state_1 is None:
        return True, joint_state_2

    if joint_state_2 is None:
        return True, joint_state_1

    common_names = set(joint_state_1.names) & set(joint_state_2.names)
    device = joint_state_1.positions.device

    # Here, there are names in common. These joint states are not parallel, so we cannot combine them.
    if not len(common_names) == 0:
        return False, JointState(
            names=[],
            positions=wp.array(),
            velocities=wp.array(),
            efforts=wp.array(),
        )

    # Combine the joint states:
    return True, JointState(
        names=[*joint_state_1.names, *joint_state_2.names],
        positions=wp.array(
            [*joint_state_1.positions.numpy().tolist(), *joint_state_2.positions.numpy().tolist()],
            dtype=joint_state_1.positions.dtype,
            device=device,
        ),
        velocities=wp.array(
            [*joint_state_1.velocities.numpy().tolist(), *joint_state_2.velocities.numpy().tolist()],
            dtype=joint_state_1.velocities.dtype,
            device=device,
        ),
        efforts=wp.array(
            [*joint_state_1.efforts.numpy().tolist(), *joint_state_2.efforts.numpy().tolist()],
            dtype=joint_state_1.efforts.dtype,
            device=device,
        ),
    )


def _combine_body_states(
    body_state_1: Optional[BodyState], body_state_2: Optional[BodyState]
) -> tuple[bool, BodyState]:
    if body_state_1 is None:
        return True, body_state_2

    if body_state_2 is None:
        return True, body_state_1

    common_names = set(body_state_1.names) & set(body_state_2.names)
    device = body_state_1.positions.device

    # Here, there are names in common. These joint states are not parallel, so we cannot combine them.
    if not len(common_names) == 0:
        return False, BodyState(
            names=[],
            positions=wp.array([], dtype=wp.vec3f),
            orientations=wp.array([], dtype=wp.quatf),
            linear_velocities=wp.array([], dtype=wp.vec3f),
            angular_velocities=wp.array([], dtype=wp.vec3f),
        )

    combined_positions = wp.from_numpy(
        np.concat([body_state_1.positions.numpy(), body_state_2.positions.numpy()], axis=0),
        dtype=wp.vec3f,
        device=device,
    )
    combined_linear_velocities = wp.from_numpy(
        np.concat([body_state_1.linear_velocities.numpy(), body_state_2.linear_velocities.numpy()], axis=0),
        dtype=wp.vec3f,
        device=device,
    )
    combined_orientations = wp.from_numpy(
        np.concat([body_state_1.orientations.numpy(), body_state_2.orientations.numpy()], axis=0),
        dtype=wp.quatf,
        device=device,
    )
    combined_angular_velocities = wp.from_numpy(
        np.concat([body_state_1.angular_velocities.numpy(), body_state_2.angular_velocities.numpy()], axis=0),
        dtype=wp.vec3f,
        device=device,
    )

    return True, BodyState(
        names=[*body_state_1.names, *body_state_2.names],
        positions=combined_positions,
        orientations=combined_orientations,
        linear_velocities=combined_linear_velocities,
        angular_velocities=combined_angular_velocities,
    )


def _combine_root_states(
    root_state_1: Optional[RootState], root_state_2: Optional[RootState]
) -> tuple[bool, RootState]:
    if root_state_1 is None:
        return True, root_state_2
    if root_state_2 is None:
        return True, root_state_1

    # They cannot both define a root state.
    return False, RootState(
        position=wp.vec3f(), orientation=wp.quatf(), linear_velocity=wp.vec3f(), angular_velocity=wp.vec3f()
    )


def combine_robot_states(
    robot_state_1: Optional[RobotState], robot_state_2: Optional[RobotState]
) -> Optional[RobotState]:

    # If either robot state is undefined, the entire robot state should be undefined.
    if (robot_state_1 is None) or (robot_state_2 is None):
        return None

    success, joints = _combine_joint_states(robot_state_1.joints, robot_state_2.joints)
    if not success:
        return None

    success, root = _combine_root_states(robot_state_1.root, robot_state_2.root)
    if not success:
        return None

    success, tool_frames = _combine_body_states(robot_state_1.tool_frames, robot_state_2.tool_frames)

    if not success:
        return None

    success, bodies = _combine_body_states(robot_state_1.bodies, robot_state_2.bodies)
    if not success:
        return None

    return RobotState(joints=joints, root=root, tool_frames=tool_frames, bodies=bodies)
