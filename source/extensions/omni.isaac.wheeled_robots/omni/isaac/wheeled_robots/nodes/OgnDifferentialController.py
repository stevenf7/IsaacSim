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
        if db.inputs.wheelRadius <= 0 or db.inputs.wheelDistance <= 0:
            db.log_error("invalid wheel radius and distance")
            return False

        if (db.inputs.wheelRadius != state.wheel_radius) or (db.inputs.wheelDistance != state.wheel_distance):
            state.wheel_radius = db.inputs.wheelRadius
            state.wheel_distance = db.inputs.wheelDistance
            state.initialized = False

        if db.inputs.maxLinearSpeed:
            if db.inputs.max_linear_speed != state.maxLinearSpeed:
                state.max_linear_speed = db.inputs.maxLinearSpeed
                state.initialized = False

        if db.inputs.maxAngularSpeed:
            if db.inputs.max_angular_speed != state.maxAngularSpeed:
                state.max_angular_speed = db.inputs.maxAngularSpeed
                state.initialized = False

        if db.inputs.maxWheelSpeed:
            if db.inputs.max_wheel_speed != state.maxWheelSpeed:
                state.max_wheel_speed = db.inputs.maxWheelSpeed
                state.initialized = False

        if not state.initialized:
            state.initialize()

        # send joint commands as a bundle out
        command_bundle = db.outputs.jointCommands
        command_bundle.clear()

        joint_actions = state.forward(np.array([db.inputs.linearVelocity, db.inputs.angularVelocity]))
        if joint_actions.joint_positions is not None:
            position_attr = command_bundle.insert((og.Type(og.BaseDataType.DOUBLE, array_depth=2), "joint_positions"))
            position_attr.value = joint_actions.joint_positions
        if joint_actions.joint_velocities is not None:
            velocity_attr = command_bundle.insert((og.Type(og.BaseDataType.DOUBLE, array_depth=2), "joint_velocities"))
            velocity_attr.value = joint_actions.joint_velocities
        if joint_actions.joint_efforts is not None:
            effort_attr = command_bundle.insert((og.Type(og.BaseDataType.DOUBLE, array_depth=2), "joint_efforts"))
            effort_attr.value = joint_actions.joint_efforts

        return True
