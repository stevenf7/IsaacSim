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

from enum import Enum
from typing import Optional

from .base_controller import BaseController
from .types import Action, RobotState


# Class to contain any number of controllers. Because they all have the same API,
# we can swap any two controllers at run-time.
class ControllerContainer(BaseController):
    """Controller class which contains any number of controllers.

    Can switch between controllers at run-time using an enum.
    """

    def __init__(self, controller_options: dict[Enum, BaseController], initial_controller_selection: Enum):
        """Initialize a ControllerContainer.

        Args:
            controller_options: Dictionary of controllers to choose from, keyed by enum.
            initial_controller_selection: Initial controller, selected by enum.
        """
        self._controller_options = controller_options
        self._active_controller = controller_options[initial_controller_selection]

        # storing the initial, active, and next controller:
        self._initial_controller_selection = initial_controller_selection
        self._active_controller_selection = initial_controller_selection
        self._next_controller_selection = initial_controller_selection

    def reset(self, estimated_state: RobotState, setpoint_state: Optional[RobotState], t: float, **kwargs) -> bool:
        """Set the initial controller to be active again and call reset on it.

        Args:
            estimated_state: RobotState object to be used for the controller.
            setpoint_state: An optional desired state of the robot.
            t: Current clock time (simulation or real).
            **kwargs: Custom arguments.

        Returns:
            True if there is an error, False otherwise.
        """
        self._active_controller_selection = self._initial_controller_selection
        self._next_controller_selection = self._initial_controller_selection
        self._active_controller = self._controller_options[self._initial_controller_selection]
        return self._active_controller.reset(estimated_state, setpoint_state, t, **kwargs)

    def forward(
        self, estimated_state: RobotState, setpoint_state: Optional[RobotState], t: float, **kwargs
    ) -> tuple[bool, Action]:
        """Run the active controller.

        If the active controller has changed since the last forward call, the controller is
        switched to the next controller, and then the reset function is called on the new
        controller.

        Args:
            estimated_state: RobotState object to be used for the controller.
            t: Current clock time (simulation or real).
            setpoint_state: An optional desired state of the robot.
            **kwargs: Custom arguments.

        Returns:
            A tuple containing a boolean indicating if there is an error (True if error),
            and an Action object to be forwarded to the robot.

        Raises:
            RuntimeError: If resetting the new controller fails during the switch.
        """
        if self._next_controller_selection != self._active_controller_selection:
            self._active_controller = self._controller_options[self._next_controller_selection]

            # save which controller is active.
            self._active_controller_selection = self._next_controller_selection

            error = self._active_controller.reset(estimated_state, setpoint_state, t, **kwargs)

            if error:
                raise RuntimeError(
                    f"Error resetting controller {self._next_controller_selection} during call to forward."
                )

        # run the controller and return its result.
        return self._active_controller.forward(estimated_state, setpoint_state, t, **kwargs)

    def set_next_controller(self, next_controller_selection: Enum) -> None:
        """Set the controller which will be running starting at the next time-step.

        This function is typically called by a higher-level behavior control scheme,
        such as a state-machine or a behavior tree.

        Args:
            next_controller_selection: Enum of the controller to switch to.

        Raises:
            RuntimeError: If the requested enum does not correspond to any controller.
        """
        if next_controller_selection not in self._controller_options.keys():
            raise RuntimeError("There is no controller which corresponds to the requested enum.")
        self._next_controller_selection = next_controller_selection

    def get_active_controller_enum(self) -> Enum:
        """Get the enum of the currently active controller.

        This function is typically called by a higher-level behavior control scheme,
        such as a state-machine or a behavior tree.

        Returns:
            The enum of the currently active controller.
        """
        return self._active_controller_selection

    def get_controller(self, controller_selection: Enum) -> BaseController:
        """Get a controller object.

        This is useful to call custom methods on a controller which are not part of the BaseController interface.
        For example, many controllers may require long-term goals (setpoints). These types
        of functions are not part of the BaseController interface, and must be called on
        the controller object directly.

        Args:
            controller_selection: Enum of the controller to get.

        Returns:
            The controller object.

        Raises:
            LookupError: If the selected controller is not part of the available options.
        """
        if controller_selection not in self._controller_options.keys():
            raise LookupError("The selected controller is not a part of the available options.")
        return self._controller_options[controller_selection]
