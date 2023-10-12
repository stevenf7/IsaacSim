# Copyright (c) 2022-2023, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#


import numpy as np
from omni.isaac.core.utils.types import ArticulationAction
from omni.isaac.core_nodes import BaseResetNode
from omni.isaac.wheeled_robots.controllers.differential_controller import DifferentialController
from omni.isaac.wheeled_robots.ogn.OgnDifferentialControllerDatabase import OgnDifferentialControllerDatabase


class OgnDifferentialControllerInternalState(BaseResetNode):
    def __init__(self):
        self.wheel_radius = (float,)
        self.wheel_distance = (float,)
        self.controller_handle = None
        self.max_linear_speed = 1.0e20
        self.max_angular_speed = 1.0e20
        self.max_wheel_speed = 1.0e20
        self.store_joint_actions = None
        self.outputs = None
        super().__init__(initialize=False)

    def initialize_controller(self) -> None:
        self.controller_handle = DifferentialController(
            name="differential_controller",
            wheel_radius=self.wheel_radius,
            wheel_base=self.wheel_distance,
            max_linear_speed=self.max_linear_speed,
            max_angular_speed=self.max_angular_speed,
            max_wheel_speed=self.max_wheel_speed,
        )
        self.initialized = True

    def forward(self, command: np.ndarray) -> ArticulationAction:
        return self.controller_handle.forward(command)

    def custom_reset(self):
        if self.initialized:
            if self.store_joint_actions.joint_positions is not None:
                self.outputs.positionCommand = [0.0, 0.0]
            if self.store_joint_actions.joint_velocities is not None:
                self.outputs.velocityCommand = [0.0, 0.0]
            if self.store_joint_actions.joint_efforts is not None:
                self.outputs.effortCommand = [0.0, 0.0]


class OgnDifferentialController:
    """
    nodes for moving an articulated robot with joint commands
    """

    @staticmethod
    def initialize(graph_context, node):
        # Store db.outputs in a private variable of State class so we can modify the output on simulation Stop
        db = OgnDifferentialControllerDatabase(node)
        state = OgnDifferentialControllerDatabase.per_node_internal_state(node)
        state.outputs = db.outputs

    @staticmethod
    def internal_state():
        return OgnDifferentialControllerInternalState()

    @staticmethod
    def compute(db) -> bool:
        state = db.internal_state

        try:
            if not state.initialized:

                if db.inputs.wheelRadius <= 0 or db.inputs.wheelDistance <= 0:
                    db.log_warning("invalid wheel radius and distance")
                    return False
                else:
                    state.wheel_radius = db.inputs.wheelRadius
                    state.wheel_distance = db.inputs.wheelDistance

                if db.inputs.maxLinearSpeed > 0:
                    state.max_linear_speed = db.inputs.maxLinearSpeed
                elif db.inputs.maxLinearSpeed == 0:
                    state.max_linear_speed = 1.0e20

                if db.inputs.maxAngularSpeed > 0:
                    state.max_angular_speed = db.inputs.maxAngularSpeed
                elif db.inputs.maxAngularSpeed == 0:
                    state.max_angular_speed = 1.0e20

                if db.inputs.maxWheelSpeed > 0:
                    state.max_wheel_speed = db.inputs.maxWheelSpeed
                elif db.inputs.maxWheelSpeed == 0:
                    state.max_wheel_speed = 1.0e20

                state.initialize_controller()

            joint_actions = state.forward(np.array([db.inputs.linearVelocity, db.inputs.angularVelocity]))
            if joint_actions.joint_positions is not None:
                db.outputs.positionCommand = joint_actions.joint_positions
            if joint_actions.joint_velocities is not None:
                db.outputs.velocityCommand = joint_actions.joint_velocities
            if joint_actions.joint_efforts is not None:
                db.outputs.effortCommand = joint_actions.joint_efforts

            state.store_joint_actions = joint_actions

        except Exception as error:
            db.log_error(str(error))
            return False

        return True

    @staticmethod
    def release(node):
        try:
            state = OgnDifferentialControllerDatabase.per_node_internal_state(node)
        except Exception:
            state = None
            pass

        if state is not None:
            state.reset()
