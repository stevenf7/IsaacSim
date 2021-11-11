# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
from omni.isaac.core.controllers import BaseController
from omni.isaac.core.utils.types import ArticulationAction
from omni.isaac.core.utils.rotations import quat_to_euler_angles
import numpy as np
import math


class WheelBasePoseController(BaseController):
    def __init__(self, name: str, open_loop_wheel_controller: BaseController) -> None:
        """[summary]

        Args:
            name (str): [description]
            open_loop_wheel_controller (BaseController): A controller that takes in a command of
                                                        [longitudinal velocity, steering angle] and returns the
                                                        ArticulationAction to be applied to the wheels.
        """
        super().__init__(name)
        self._open_loop_wheel_controller = open_loop_wheel_controller
        return

    def forward(
        self,
        start_position: np.ndarray,
        start_orientation: np.ndarray,
        goal_position: np.ndarray,
        lateral_velocity: float = 20.0,
        kp: float = 10.0,
    ) -> ArticulationAction:
        """[summary]

        Args:
            start_position (np.ndarray): [description]
            start_orientation (np.ndarray): [description]
            goal_position (np.ndarray): [description]
            lateral_velocity (float, optional): [description]. Defaults to 20.0.
            kp (float, optional): [description]. Defaults to 10.0.

        Returns:
            ArticulationAction: [description]
        """
        if np.mean(np.abs(start_position[:2] - goal_position[:2])) < 0.5:
            return ArticulationAction(joint_velocities=[0.0, 0.0])

        steering_yaw = math.atan2(
            goal_position[1] - start_position[1], float(goal_position[0] - start_position[0] + 1e-5)
        )
        current_yaw_heading = quat_to_euler_angles(start_orientation)[-1]
        yaw_error = steering_yaw - current_yaw_heading
        rotational_velocity_yaw = kp * yaw_error
        if abs(yaw_error) > 0.002:
            command = [0.0, rotational_velocity_yaw]
        elif np.mean(np.abs(start_position[:2] - goal_position[:2])) > 0.5:
            command = [lateral_velocity, 0]
        else:
            command = [0.0, 0.0]
        return self._open_loop_wheel_controller.forward(command)

    def reset(self) -> None:
        """[summary]
        """
        return
