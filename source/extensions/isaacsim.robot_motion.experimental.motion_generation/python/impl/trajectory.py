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

from abc import ABC, abstractmethod

from .types import Action


class Trajectory(ABC):
    """Interface class for defining a continuous-time trajectory for a robot in Isaac Sim.

    All trajectories start at time input == 0.0, and end after their duration.
    """

    @property
    @abstractmethod
    def duration(self) -> float:
        """Return the duration of the trajectory.

        Returns:
            Duration of the trajectory in seconds.
        """
        pass

    @abstractmethod
    def get_active_joints(self) -> list[str]:
        """Get the active joints directly controlled by this Trajectory.

        A Trajectory may be specified for only a subset of the joints in a robot Articulation.
        For example, it may include the DOFs in a robot arm, but not in the gripper.

        Returns:
            Names of active joints. The order of joints in this list determines the order
            in which a Trajectory will return joint targets for the robot.
        """
        pass

    @abstractmethod
    def get_joint_targets(self, time: float) -> Action:
        """Return joint targets for the robot at the given time.

        The Trajectory interface assumes trajectories to be represented continuously between
        a start time and end time. An instance of this class that internally generates
        discrete time trajectories will need to implement some form of interpolation for
        times that have not been computed.

        Args:
            time: Time in trajectory at which to return joint targets.

        Returns:
            Action object containing the joint targets for the robot at the given time.
        """
        pass
