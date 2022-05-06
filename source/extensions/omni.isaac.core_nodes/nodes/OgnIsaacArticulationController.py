# Copyright (c) 2022, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.


from omni.isaac.core.articulations.articulation import Articulation
from omni.isaac.core.utils.types import ArticulationAction
import numpy as np


class InternalState:
    def __init__(self):
        self.robot_prim = None
        self.controller_handle = None
        self.joint_names = []
        self.joint_indices = []
        self.joint_picked = False

    def initialize_controller(self, prim_path):
        self.controller_handle = Articulation(prim_path)
        self.controller_handle.initialize()
        self.num_dof = self.controller_handle.num_dof

    def joint_indicator(self):
        if self.joint_names:
            self.joint_indices = []
            for name in self.joint_names:
                self.joint_indices.append(self.controller_handle.get_dof_index(name))
        elif self.joint_indices:
            self.joint_indices = self.joint_indices
        else:
            # when indices is none (not []), it defaults too all DOFs
            self.joint_indices = None
        self.joint_picked = True

    def apply_action(self, joint_positions=None, joint_velocities=None, joint_efforts=None):
        joint_actions = ArticulationAction()
        if joint_positions is not None:
            joint_actions.joint_positions = joint_positions
        elif joint_velocities is not None:
            joint_actions.joint_velocities = joint_velocities
        elif joint_efforts is not None:
            joint_actions.joint_efforts = joint_efforts
        self.controller_handle.apply_action(control_actions=joint_actions, indices=self.joint_indices)


class OgnIsaacArticulationController:
    """
        nodes for moving an articulated robot with joint commands
    """

    @staticmethod
    def internal_state():
        return InternalState()

    @staticmethod
    def compute(db) -> bool:
        try:
            state = db.internal_state
            robot_prim = db.inputs.targetPrim.path

            # initialize the controller handle for the robot
            if robot_prim != state.robot_prim:
                state.initialize_controller(robot_prim)
            # pick the joints that are being commanded, this can be different at every step
            robot_param_bundle = db.inputs.robotParams
            for attr in robot_param_bundle.attributes:
                if attr.name == "joint_names":
                    joint_names = attr.value
                    if joint_names != state.joint_names:
                        state.joint_names = joint_names
                        state.joint_picked = False
                elif attr.name == "joint_indicies":
                    joint_indices = attr.value
                    if np.array(joint_indices != state.joint_indices).all():
                        state.joint_indices = np.array(joint_indices)
                        state.joint_picked = False
            if not state.joint_picked:
                state.joint_indicator()

            joint_positions = None
            joint_velocities = None
            joint_efforts = None

            command_bundle = db.inputs.jointCommands
            for attr in command_bundle.attributes:
                if attr.name == "joint_positions":
                    joint_positions = attr.value
                elif attr.name == "joint_velocities":
                    joint_velocities = attr.value
                elif attr.name == "joint_efforts":
                    joint_efforts = attr.value

            state.apply_action(joint_positions, joint_velocities, joint_efforts)

        except Exception as error:
            db.log_warn(str(error))
            return False

        return True
