# Copyright (c) 2022, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.


from omni.isaac.core.utils.types import ArticulationAction
from omni.isaac.wheeled_robots.controllers.differential_controller import DifferentialController
import numpy as np
import omni.graph.core as og


class InternalState:
    def __init__(self):
        self.wheel_radius = (float,)
        self.wheel_distance = (float,)
        self.controller_handle = None
        self.max_linear_speed = 1.0e20
        self.max_angular_speed = 1.0e20
        self.max_wheel_speed = 1.0e20
        self.intiailized = False

    def initialize(self) -> None:
        self.controller_handle = DifferentialController(
            "differential_controller",
            self.wheel_radius,
            self.wheel_distance,
            self.max_linear_speed,
            self.max_angular_speed,
            self.max_wheel_speed,
        )
        self.initialized = True

    def forward(self, command: np.ndarray) -> ArticulationAction:
        return self.controller_handle.forward(command)


class OgnDifferentialController:
    """
        nodes for moving an articulated robot with joint commands
    """

    @staticmethod
    def internal_state():
        return InternalState()

    @staticmethod
    def compute(db) -> bool:
        state = db.internal_state

        try:
            robot_param_bundle = db.inputs.robotParams
            wheel_radius_input = (
                -1
            )  ## needed this in case incoming bundle doesn't have any attributes and miss the next for loop
            wheel_distance_input = -1
            for attr in robot_param_bundle.attributes:
                if attr.name == "wheel_radius":
                    wheel_radius_input = attr.value[0]
                elif attr.name == "wheel_distance":
                    wheel_distance_input = attr.value[0]

            if wheel_radius_input <= 0 or wheel_distance_input <= 0:
                db.log_warning("invalid wheel radius and distance")
                return False

            if (wheel_radius_input != state.wheel_radius) or (wheel_distance_input != state.wheel_distance):
                state.wheel_radius = wheel_radius_input
                state.wheel_distance = wheel_distance_input
                state.initialized = False

            vehicle_limit_bundle = db.inputs.vehicleLimits
            for attr in vehicle_limit_bundle.attributes:
                if attr.name == "max_linear_speed":
                    max_linear_speed = attr.value[0]
                    if max_linear_speed != state.max_linear_speed:
                        state.max_linear_speed = max_linear_speed
                        state.initialized = False
                elif attr.name == "max_angular_speed":
                    max_angular_speed = attr.value[0]
                    if max_angular_speed != state.max_angular_speed:
                        state.max_angular_speed = max_linear_speed
                        state.initialized = False
                elif attr.name == "max_wheel_speed":
                    max_wheel_speed = attr.value[0]
                    if max_wheel_speed != state.max_wheel_speed:
                        state.max_wheel_speed = max_wheel_speed
                        state.initialized = False

            if not state.initialized:
                state.initialize()

            # send joint commands as a bundle out
            command_bundle = db.outputs.jointCommands
            command_bundle.clear()

            joint_actions = state.forward(np.array([db.inputs.linearVelocity, db.inputs.angularVelocity]))
            if joint_actions.joint_positions is not None:
                position_attr = command_bundle.insert(
                    (og.Type(og.BaseDataType.DOUBLE, array_depth=2), "joint_positions")
                )
                position_attr.value = joint_actions.joint_positions
            if joint_actions.joint_velocities is not None:
                velocity_attr = command_bundle.insert(
                    (og.Type(og.BaseDataType.DOUBLE, array_depth=2), "joint_velocities")
                )
                velocity_attr.value = joint_actions.joint_velocities
            if joint_actions.joint_efforts is not None:
                effort_attr = command_bundle.insert((og.Type(og.BaseDataType.DOUBLE, array_depth=2), "joint_efforts"))
                effort_attr.value = joint_actions.joint_efforts

        except Exception as error:
            db.log_warning(str(error))
            return False

        return True
