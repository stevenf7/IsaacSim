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
from typing import Optional

from .types import Action, RobotState


class BaseController(ABC):
    """Interface class for controllers."""

    @abstractmethod
    def forward(
        self, estimated_state: RobotState, setpoint_state: Optional[RobotState], t: float, **kwargs
    ) -> tuple[bool, Action]:
        """Define the desired joint action of the robot at the next time-step.

        This can be a desired joint position, velocity, or a feed-forward effort.

        Args:
            estimated_state: Current estimated state of the robot.
            setpoint_state: An optional setpoint of the robot.
            t: Current clock time (simulation or real).
            **kwargs: Custom arguments for the controller.

        Returns:
            A tuple containing a boolean indicating if there is an error (True if error),
            and an Action object to be forwarded to the robot.
        """
        pass

    @abstractmethod
    def reset(self, estimated_state: RobotState, setpoint_state: Optional[RobotState], t: float, **kwargs) -> bool:
        """Reset the internal state of the controller to safe values.

        This should be called immediately before running the controller for the first time.

        Args:
            estimated_state: Current estimated state of the robot.
            setpoint_state: An optional setpoint of the robot.
            t: Current clock time (simulation or real).
            **kwargs: Additional arguments for the controller.

        Returns:
            True if there is an error, False otherwise.
        """
        pass
