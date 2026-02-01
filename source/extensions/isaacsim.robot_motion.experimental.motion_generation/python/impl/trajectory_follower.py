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

from .base_controller import BaseController
from .trajectory import Trajectory
from .types import RobotState


class TrajectoryFollower(BaseController):
    """Controller implementation to follow a generic trajectory.

    If there is no trajectory set, the controller outputs a holding position for the
    robot, which is equal to the robot pose which was present when the reset function
    is run.
    """

    def __init__(self):
        """Initialize a TrajectoryFollower controller."""
        self._trajectory = None

        # time when the trajectory starts to run in the sim/real world.
        self._start_time = None

    def reset(self, estimated_state: RobotState, setpoint_state: Optional[RobotState], t: float, **kwargs) -> bool:
        """Reset state of the controller, deleting the internal trajectory object.

        Args:
            estimated_state: RobotState object to be reset.
            setpoint_state: Optional setpoint state of the robot.
            t: Current clock time (simulation or real).
            **kwargs: Custom arguments.

        Returns:
            True if there is an error, False otherwise.
        """

        # No trajectory, which is safest. Any trajectories we run
        # are set explicitly immediately before they run.
        self._trajectory = None
        self._start_time = None
        return False

    def forward(
        self, estimated_state: RobotState, setpoint_state: Optional[RobotState], t: float, **kwargs
    ) -> Optional[RobotState]:
        """Forward the trajectory follower.

        Args:
            estimated_state: The current estimated state of the robot.
            setpoint_state: Optional setpoint state of the robot.
            t: Current clock time (simulation or real).
            **kwargs: Additional keyword arguments.

        Returns:
            Desired robot state for the current time, or None if no trajectory is set
            or the trajectory has completed.

        Example:

        .. code-block:: python

            >>> target = follower.forward(estimated_state, setpoint_state, t)
            >>> if target is None:
            ...     print("Controller could not produce a valid result.")
        """
        if self._trajectory is None:
            # No issues, just don't do anything.
            return None

        # get the time since the trajectory started:
        trajectory_time = t - self._start_time

        if (trajectory_time < 0.0) or (trajectory_time > self._trajectory.duration):
            # Clear the trajectory.
            self.reset(estimated_state, setpoint_state, t)
            return None

        # read the trajectory, and return the desired joint states.
        return self._trajectory.get_target_state(trajectory_time)

    def set_trajectory(self, trajectory: Trajectory, start_time: float) -> None:
        """Set the trajectory to follow.

        Args:
            trajectory: The trajectory to follow.
            start_time: The time at which to start the trajectory.
        """
        self._trajectory = trajectory
        self._start_time = start_time

    def has_trajectory(self) -> bool:
        """Check if the trajectory follower has a trajectory set.

        Returns:
            True if a trajectory is set, False otherwise.
        """
        return self._trajectory is not None
