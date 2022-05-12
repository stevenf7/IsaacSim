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
import json


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

    def apply_action(self, joint_positions, joint_velocities, joint_efforts):
        joint_actions = ArticulationAction()
        joint_actions.joint_indices = self.joint_indices
        if joint_positions != []:
            joint_actions.joint_positions = joint_positions
        elif joint_velocities != []:
            joint_actions.joint_velocities = joint_velocities
        elif joint_efforts != []:
            joint_actions.joint_efforts = joint_efforts
        self.controller_handle.apply_action(control_actions=joint_actions)


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
            if db.inputs.usePath:
                robot_prim = db.inputs.robotPath
            else:
                if db.inputs.targetPrim.attributes == []:
                    return False
                else:
                    robot_prim = db.inputs.targetPrim.path

            # initialize the controller handle for the robot
            if robot_prim != state.robot_prim:
                state.initialize_controller(robot_prim)

            # pick the joints that are being commanded, this can be different at every step
            joint_names = db.inputs.jointNames
            if (joint_names != []) and (joint_names != state.joint_names):
                state.joint_names = joint_names
                state.joint_picked = False

            joint_indices = db.inputs.jointIndices
            if (joint_indices != []) and (np.array(joint_indices != state.joint_indices).all()):
                state.joint_indices = np.array(joint_indices)
                state.joint_picked = False

            if not state.joint_picked:
                state.joint_indicator()

            joint_positions = db.inputs.positionCommand
            joint_velocities = db.inputs.velocityCommand
            joint_efforts = db.inputs.effortCommand
            state.apply_action(joint_positions, joint_velocities, joint_efforts)

        except Exception as error:
            db.log_warn(str(error))
            return False

        return True
