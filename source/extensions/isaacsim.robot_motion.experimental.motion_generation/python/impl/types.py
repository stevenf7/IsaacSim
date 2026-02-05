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

from typing import Literal

import numpy as np
import warp as wp


class JointState:
    """Container for the state of robot joints.

    At least one of positions, velocities, or efforts must be provided. All provided arrays
    must be 1D warp arrays with the same length as the names list.

    Args:
        names: The names of the joints.
        positions: The positions of the joints as a 1D warp array. Defaults to None.
        velocities: The velocities of the joints as a 1D warp array. Defaults to None.
        efforts: The efforts (torques) of the joints as a 1D warp array. Defaults to None.

    Raises:
        ValueError: If all of positions, velocities, and efforts are None.
        ValueError: If any provided array is not a warp array.
        ValueError: If any provided array is not 1D.
        ValueError: If any provided array length does not match the length of names.
    """

    def __init__(
        self,
        names: list[str],
        positions: wp.array | None = None,
        velocities: wp.array | None = None,
        efforts: wp.array | None = None,
    ):
        if (positions is None) and (velocities is None) and (efforts is None):
            raise ValueError("One of positions, velocities, or efforts must be defined.")

        for vector in [positions, velocities, efforts]:
            if vector is None:
                continue

            # Enforce that these are warp array inputs:
            if not isinstance(vector, wp.array) or (vector.ndim != 1):
                raise ValueError("All defined [positions, velocities, efforts] must be a warp array.")

            if len(vector) < 1:
                raise ValueError("Any defined [positions, velocities, efforts] must have at least len of 1.")

            if len(vector) != len(names):
                raise ValueError("Any defined [positions, velocities, efforts] must have the same length as 'names'")

        # all inputs are valid:
        self.names = names
        self.positions = positions
        self.velocities = velocities
        self.efforts = efforts


class RootState:
    """Container for the state of the robot's root link.

    At least one of position, orientation, linear_velocity, or angular_velocity must be provided.
    All provided arrays must be 1D warp arrays with the correct number of elements.

    Args:
        position: The position of the root as a 1D warp array with 3 elements (x, y, z).
            Defaults to None.
        orientation: The orientation of the root as a 1D warp array with 4 elements (w, x, y, z).
            Defaults to None.
        linear_velocity: The linear velocity of the root as a 1D warp array with 3 elements
            (x, y, z). Defaults to None.
        angular_velocity: The angular velocity of the root as a 1D warp array with 3 elements
            (x, y, z). Defaults to None.

    Raises:
        ValueError: If all of position, orientation, linear_velocity, and angular_velocity
            are None.
        ValueError: If any provided array is not a 1D warp array with the correct number
            of elements.
    """

    def __init__(
        self,
        position: wp.array | None = None,
        orientation: wp.array | None = None,
        linear_velocity: wp.array | None = None,
        angular_velocity: wp.array | None = None,
    ):
        if (position is None) and (orientation is None) and (linear_velocity is None) and (angular_velocity is None):
            raise ValueError("One of position, orientation, linear_velocity, or angular_velocity must be defined.")

        if position is not None:
            if not isinstance(position, wp.array) or (position.ndim != 1) or (len(position) != 3):
                raise ValueError("position must be a 1D warp array with 3 elements (x, y, z).")

        if orientation is not None:
            if not isinstance(orientation, wp.array) or (orientation.ndim != 1) or (len(orientation) != 4):
                raise ValueError("orientation must be a 1D warp array with 4 elements (w, x, y, z).")

        if linear_velocity is not None:
            if not isinstance(linear_velocity, wp.array) or (linear_velocity.ndim != 1) or (len(linear_velocity) != 3):
                raise ValueError("linear_velocity must be a 1D warp array with 3 elements (x, y, z).")

        if angular_velocity is not None:
            if (
                not isinstance(angular_velocity, wp.array)
                or (angular_velocity.ndim != 1)
                or (len(angular_velocity) != 3)
            ):
                raise ValueError("angular_velocity must be a 1D warp array with 3 elements (x, y, z).")

        self.position = position
        self.orientation = orientation
        self.linear_velocity = linear_velocity
        self.angular_velocity = angular_velocity


class BodyState:
    """Container for the state of non-root rigid bodies of the robot.

    At least one of positions, orientations, linear_velocities, or angular_velocities must be
    provided. All provided arrays must be 2D warp arrays with shape (N, K) where N equals the
    length of names and K is the appropriate dimension for the field.

    Args:
        names: The names of the rigid bodies.
        positions: The positions of the bodies as a 2D warp array with shape (N, 3).
            Defaults to None.
        orientations: The orientations of the bodies as a 2D warp array with shape (N, 4),
            where each row is a quaternion in (w, x, y, z) order. Defaults to None.
        linear_velocities: The linear velocities of the bodies as a 2D warp array with
            shape (N, 3). Defaults to None.
        angular_velocities: The angular velocities of the bodies as a 2D warp array with
            shape (N, 3). Defaults to None.

    Raises:
        ValueError: If all of positions, orientations, linear_velocities, and angular_velocities
            are None.
        ValueError: If any provided array is not a 2D warp array.
        ValueError: If any provided array has shape[0] not equal to the length of names.
        ValueError: If positions, linear_velocities, or angular_velocities has shape[1] != 3.
        ValueError: If orientations has shape[1] != 4.
    """

    def __init__(
        self,
        names: list[str],
        positions: wp.array | None = None,
        orientations: wp.array | None = None,
        linear_velocities: wp.array | None = None,
        angular_velocities: wp.array | None = None,
    ):
        if (
            (positions is None)
            and (orientations is None)
            and (linear_velocities is None)
            and (angular_velocities is None)
        ):
            raise ValueError(
                "One of positions, orientations, linear_velocities, or angular_velocities must be defined."
            )

        for vector in [positions, orientations, linear_velocities, angular_velocities]:
            if vector is None:
                continue

            # Enforce that these are warp array inputs:
            if not isinstance(vector, wp.array) or (vector.ndim != 2):
                raise ValueError(
                    "Any defined [positions, orientations, linear or angular velocity] must be a 2D warp array."
                )

            if vector.shape[0] < 1:
                raise ValueError(
                    "Any defined [positions, orientations, linear or angular velocity] must have shape[0] >= 1"
                )

            if vector.shape[0] != len(names):
                raise ValueError(
                    "Any defined [positions, orientations, linear or angular velocity] must have the same length as 'names'"
                )

        if (positions is not None) and (positions.shape[1] != 3):
            raise ValueError("positions.shape[1] must equal 3.")
        if (linear_velocities is not None) and (linear_velocities.shape[1] != 3):
            raise ValueError("linear_velocities.shape[1] must equal 3.")
        if (orientations is not None) and (orientations.shape[1] != 4):
            raise ValueError("orientations.shape[1] must equal 4.")
        if (angular_velocities is not None) and (angular_velocities.shape[1] != 3):
            raise ValueError("angular_velocities.shape[1] must equal 3.")

        self.names = names
        self.positions = positions
        self.orientations = orientations
        self.linear_velocities = linear_velocities
        self.angular_velocities = angular_velocities


class RobotState:
    """Composite container for the complete state of a robot.

    A RobotState aggregates the state of all robot components: joints, root link, rigid bodies,
    and tool frames. All components are optional, allowing partial state representations.

    Args:
        joints: The state of the robot's joints. Defaults to None.
        root: The state of the robot's root link. Defaults to None.
        bodies: The state of the robot's non-root rigid bodies. Defaults to None.
        tool_frames: The state of the robot's tool frames (end-effectors). Defaults to None.
    """

    def __init__(
        self,
        joints: JointState | None = None,
        root: RootState | None = None,
        bodies: BodyState | None = None,
        tool_frames: BodyState | None = None,
    ):
        self.joints = joints
        self.root = root
        self.bodies = bodies
        self.tool_frames = tool_frames


def _concatenate_warp_arrays(
    array_1: wp.array,
    array_2: wp.array,
) -> wp.array:
    """Concatenate two warp arrays along their first axis.

    Args:
        array_1: The first warp array.
        array_2: The second warp array.

    Returns:
        A new warp array containing the concatenated data with the same dtype and device
        as array_1.
    """
    return wp.array(np.concatenate([array_1.numpy(), array_2.numpy()]), dtype=array_1.dtype, device=array_1.device)


def _combine_joint_states(
    joint_state_1: JointState | None, joint_state_2: JointState | None
) -> JointState | Literal[False] | None:
    """Combine two joint states into one.

    Two joint states can be combined if they either:
    - Define the exact same joints with non-overlapping fields (e.g., one has positions, other
      has velocities).
    - Define completely different joints with the same fields defined.

    Args:
        joint_state_1: The first joint state, or None.
        joint_state_2: The second joint state, or None.

    Returns:
        The combined JointState if successful, None if both inputs are None, or False if the
        states cannot be combined due to conflicts.
    """
    if joint_state_1 is None:
        return joint_state_2

    if joint_state_2 is None:
        return joint_state_1

    common_names = set(joint_state_1.names) & set(joint_state_2.names)

    # CASE 1: We can combine two joint states on the exact same joints, as long as they define
    # non-overlapping fields.
    if common_names == set(joint_state_1.names) == set(joint_state_2.names):
        # If these two joint states define the same fields, they cannot be combined:
        if (joint_state_1.positions is not None) and (joint_state_2.positions is not None):
            return False
        if (joint_state_1.velocities is not None) and (joint_state_2.velocities is not None):
            return False
        if (joint_state_1.efforts is not None) and (joint_state_2.efforts is not None):
            return False

        # These can be combined:
        return JointState(
            names=joint_state_1.names,
            positions=joint_state_1.positions if joint_state_1.positions is not None else joint_state_2.positions,
            velocities=joint_state_1.velocities if joint_state_1.velocities is not None else joint_state_2.velocities,
            efforts=joint_state_1.efforts if joint_state_1.efforts is not None else joint_state_2.efforts,
        )

    # CASE 2: If we do not have _full_ overlap in joint names, then we cannot have any overlap.
    if not len(common_names) == 0:
        return False

    # With no overlap, both of the joint-states must define the same fields:
    if (joint_state_1.positions is None) != (joint_state_2.positions is None):
        return False

    if (joint_state_1.velocities is None) != (joint_state_2.velocities is None):
        return False

    if (joint_state_1.efforts is None) != (joint_state_2.efforts is None):
        return False

    # Combine the joint states:
    positions_out = None
    if joint_state_1.positions is not None:
        positions_out = _concatenate_warp_arrays(joint_state_1.positions, joint_state_2.positions)

    velocities_out = None
    if joint_state_1.velocities is not None:
        velocities_out = _concatenate_warp_arrays(joint_state_1.velocities, joint_state_2.velocities)

    efforts_out = None
    if joint_state_1.efforts is not None:
        efforts_out = _concatenate_warp_arrays(joint_state_1.efforts, joint_state_2.efforts)

    return JointState(
        names=[*joint_state_1.names, *joint_state_2.names],
        positions=positions_out,
        velocities=velocities_out,
        efforts=efforts_out,
    )


def _combine_body_states(
    body_state_1: BodyState | None, body_state_2: BodyState | None
) -> BodyState | Literal[False] | None:
    """Combine two body states into one.

    Two body states can be combined if they either:
    - Define the exact same bodies with non-overlapping fields (e.g., one has positions, other
      has orientations).
    - Define completely different bodies with the same fields defined.

    Args:
        body_state_1: The first body state, or None.
        body_state_2: The second body state, or None.

    Returns:
        The combined BodyState if successful, None if both inputs are None, or False if the
        states cannot be combined due to conflicts.
    """
    if body_state_1 is None:
        return body_state_2

    if body_state_2 is None:
        return body_state_1

    common_names = set(body_state_1.names) & set(body_state_2.names)

    # CASE 1: We can combine two body states on the exact same bodies, as long as they define
    # non-overlapping fields.
    if common_names == set(body_state_1.names) == set(body_state_2.names):
        # If these two body states define the same fields, they cannot be combined:
        if (body_state_1.positions is not None) and (body_state_2.positions is not None):
            return False
        if (body_state_1.orientations is not None) and (body_state_2.orientations is not None):
            return False
        if (body_state_1.linear_velocities is not None) and (body_state_2.linear_velocities is not None):
            return False
        if (body_state_1.angular_velocities is not None) and (body_state_2.angular_velocities is not None):
            return False

        # These can be combined:
        return BodyState(
            names=body_state_1.names,
            positions=body_state_1.positions if body_state_1.positions is not None else body_state_2.positions,
            orientations=(
                body_state_1.orientations if body_state_1.orientations is not None else body_state_2.orientations
            ),
            linear_velocities=(
                body_state_1.linear_velocities
                if body_state_1.linear_velocities is not None
                else body_state_2.linear_velocities
            ),
            angular_velocities=(
                body_state_1.angular_velocities
                if body_state_1.angular_velocities is not None
                else body_state_2.angular_velocities
            ),
        )

    # CASE 2: If we do not have _full_ overlap in body names, then we cannot have any overlap.
    if not len(common_names) == 0:
        return False

    # The two body states must define the same fields:
    if (body_state_1.positions is None) != (body_state_2.positions is None):
        return False

    if (body_state_1.orientations is None) != (body_state_2.orientations is None):
        return False

    if (body_state_1.linear_velocities is None) != (body_state_2.linear_velocities is None):
        return False

    if (body_state_1.angular_velocities is None) != (body_state_2.angular_velocities is None):
        return False

    # combine the states:
    combined_positions = None
    if body_state_1.positions is not None:
        combined_positions = _concatenate_warp_arrays(body_state_1.positions, body_state_2.positions)

    combined_linear_velocities = None
    if body_state_1.linear_velocities is not None:
        combined_linear_velocities = _concatenate_warp_arrays(
            body_state_1.linear_velocities, body_state_2.linear_velocities
        )

    combined_orientations = None
    if body_state_1.orientations is not None:
        combined_orientations = _concatenate_warp_arrays(body_state_1.orientations, body_state_2.orientations)

    combined_angular_velocities = None
    if body_state_1.angular_velocities is not None:
        combined_angular_velocities = _concatenate_warp_arrays(
            body_state_1.angular_velocities, body_state_2.angular_velocities
        )

    return BodyState(
        names=[*body_state_1.names, *body_state_2.names],
        positions=combined_positions,
        orientations=combined_orientations,
        linear_velocities=combined_linear_velocities,
        angular_velocities=combined_angular_velocities,
    )


def _combine_root_states(
    root_state_1: RootState | None, root_state_2: RootState | None
) -> RootState | Literal[False] | None:
    """Combine two root states into one.

    Two root states can be combined if they define non-overlapping fields. For example, one
    defines position and the other defines orientation.

    Args:
        root_state_1: The first root state, or None.
        root_state_2: The second root state, or None.

    Returns:
        The combined RootState if successful, None if both inputs are None, or False if the
        states cannot be combined due to field conflicts.
    """
    if root_state_1 is None:
        return root_state_2
    if root_state_2 is None:
        return root_state_1

    # If there is no overlap in the root_state fields, then they can be combined:
    if (root_state_1.position is not None) and (root_state_2.position is not None):
        return False
    if (root_state_1.orientation is not None) and (root_state_2.orientation is not None):
        return False
    if (root_state_1.linear_velocity is not None) and (root_state_2.linear_velocity is not None):
        return False
    if (root_state_1.angular_velocity is not None) and (root_state_2.angular_velocity is not None):
        return False

    # Combine the states:
    return RootState(
        position=root_state_1.position if root_state_1.position is not None else root_state_2.position,
        orientation=root_state_1.orientation if root_state_1.orientation is not None else root_state_2.orientation,
        linear_velocity=(
            root_state_1.linear_velocity if root_state_1.linear_velocity is not None else root_state_2.linear_velocity
        ),
        angular_velocity=(
            root_state_1.angular_velocity
            if root_state_1.angular_velocity is not None
            else root_state_2.angular_velocity
        ),
    )


def combine_robot_states(robot_state_1: RobotState | None, robot_state_2: RobotState | None) -> RobotState | None:
    """Combine two robot states into a single robot state.

    This function merges two RobotState objects by combining their respective joint states,
    root states, body states, and tool frame states. The combination succeeds only if the
    component states are compatible (i.e., they don't define conflicting values for the same
    joints, bodies, or root fields).

    Args:
        robot_state_1: The first robot state to combine, or None.
        robot_state_2: The second robot state to combine, or None.

    Returns:
        The combined RobotState if successful, or None if either input is None or if the
        states cannot be combined due to conflicts.

    Example:

        .. code-block:: python

            import warp as wp
            from isaacsim.robot_motion.experimental.motion_generation import (
                JointState, RobotState, combine_robot_states
            )

            # Create two robot states with different joints
            state_1 = RobotState(
                joints=JointState(names=["joint_0"], positions=wp.array([0.0]))
            )
            state_2 = RobotState(
                joints=JointState(names=["joint_1"], positions=wp.array([1.0]))
            )

            # Combine them into a single state
            combined = combine_robot_states(state_1, state_2)
            # combined.joints.names == ["joint_0", "joint_1"]
    """
    # If either robot state is undefined, the entire robot state should be undefined.
    if (robot_state_1 is None) or (robot_state_2 is None):
        return None

    joints = _combine_joint_states(robot_state_1.joints, robot_state_2.joints)
    if joints is False:
        return None

    root = _combine_root_states(robot_state_1.root, robot_state_2.root)
    if root is False:
        return None

    tool_frames = _combine_body_states(robot_state_1.tool_frames, robot_state_2.tool_frames)

    if tool_frames is False:
        return None

    bodies = _combine_body_states(robot_state_1.bodies, robot_state_2.bodies)
    if bodies is False:
        return None

    return RobotState(joints=joints, root=root, tool_frames=tool_frames, bodies=bodies)
