# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
from typing import Optional, Tuple
import numpy as np
import carb
from omni.isaac.core.robots.robot import Robot
from omni.isaac.core.prims.rigid_prim import RigidPrim
from omni.isaac.core.utils.nucleus_utils import find_nucleus_server
from omni.isaac.core.utils.types import ArticulationAction
from pxr import Usd


class DofBot(Robot):
    def __init__(
        self,
        stage: Usd.Stage,
        prim_path: str,
        name: str,
        usd_path: Optional[str] = None,
        position: Optional[np.ndarray] = None,
        orientation: Optional[np.ndarray] = None,
    ) -> None:
        """[summary]

        Args:
            stage (Usd.Stage): [description]
            prim_path (str): [description]
            name (str): [description]
            usd_path (str, optional): [description]
            position (Optional[np.ndarray], optional): [description]. Defaults to None.
            orientation (Optional[np.ndarray], optional): [description]. Defaults to None.
        """
        self._stage = stage
        prim = stage.GetPrimAtPath(prim_path)
        if not prim.IsValid():
            prim = stage.DefinePrim(prim_path, "Xform")
            if usd_path:
                prim.GetReferences().AddReference(usd_path)
            else:
                result, nucleus_server = find_nucleus_server()
                if result is False:
                    carb.log_error("Could not find nucleus server with /Isaac folder")
                    return
                asset_path = nucleus_server + "/Isaac/Robots/Dofbot/dofbot.usd"
                prim.GetReferences().AddReference(asset_path)
        super().__init__(prim=prim, name=name, position=position, orientation=orientation, articulation_controller=None)
        self._gripper_dof_names = ["Finger_Left_01_RevoluteJoint", "Finger_Right_01_RevoluteJoint"]
        self._end_effector = None
        self._end_effector_prim_name = "Finger_Right_01"
        self._grippers_dof_indices = None
        self._gripper_open_position = (-0.8739178, 0.67192185)
        self._gripper_closed_position = (0.523599, -0.523599)
        # TODO: check the default state and how to reset
        # TODO: account for gripper length, (difference between end effector tracking and actual gripper?)
        return

    @property
    def end_effector(self) -> RigidPrim:
        """[summary]

        Returns:
            RigidPrim: [description]
        """
        return self._end_effector

    @property
    def grippers_dof_indices(self) -> Tuple[int, int]:
        """[summary]

        Returns:
            int: [description]
        """
        return self._grippers_dof_indices

    @property
    def gripper_open_position(self):
        """[summary]

        Returns:
            [type]: [description]
        """
        return self._gripper_open_position

    @property
    def gripper_closed_position(self):
        """[summary]

        Returns:
            [type]: [description]
        """
        return self._gripper_closed_position

    # TODO: units in dc are different than the ones in USD for some reason?
    def get_end_effector_pose(self) -> Tuple[np.ndarray, np.ndarray]:
        """[summary]

        Returns:
            Tuple[np.ndarray, np.ndarray]: [description]
        """
        return self._end_effector.get_pose()

    def get_end_effector_linear_velocity(self) -> np.ndarray:
        """[summary]

        Returns:
            np.ndarray: [description]
        """
        return self._end_effector.get_linear_velocity()

    def get_end_effector_angular_velocity(self) -> np.ndarray:
        """[summary]

        Returns:
            np.ndarray: [description]
        """
        return self._end_effector.get_angular_velocity()

    def apply_gripper_actions(self, gripper_actions: ArticulationAction):
        joint_actions = ArticulationAction()
        if gripper_actions.joint_positions is not None:
            joint_actions.joint_positions = np.zeros(2)
            joint_actions.joint_positions[self._grippers_dof_indices[0]] = gripper_actions.joint_positions[0]
            joint_actions.joint_positions[self._grippers_dof_indices[1]] = gripper_actions.joint_positions[1]
        if gripper_actions.joint_velocities is not None:
            joint_actions.joint_velocities = np.zeros(2)
            joint_actions.joint_velocities[self._grippers_dof_indices[0]] = gripper_actions.joint_velocities[0]
            joint_actions.joint_velocities[self._grippers_dof_indices[1]] = gripper_actions.joint_velocities[1]
        if gripper_actions.joint_efforts is not None:
            joint_actions.joint_efforts = np.zeros(2)
            joint_actions.joint_efforts[self._grippers_dof_indices[0]] = gripper_actions.joint_efforts[0]
            joint_actions.joint_efforts[self._grippers_dof_indices[1]] = gripper_actions.joint_efforts[1]
        self.apply_action(control_actions=joint_actions)
        return

    def get_gripper_position(self) -> Tuple[float, float]:
        """[summary]

        Returns:
            Tuple[float, float]: [description]
        """
        joint_positions = self.get_joint_positions()
        return joint_positions[self._grippers_dof_indices[0]], joint_positions[self._grippers_dof_indices[1]]

    def set_gripper_position(self, gripper_positions: Tuple[float, float]) -> None:
        """[summary]

        Args:
            gripper_positions (Tuple[float, float]): [description]
        """
        joint_positions = self.get_joint_positions()
        joint_positions[self._grippers_dof_indices[0]] = gripper_positions[0]
        joint_positions[self._grippers_dof_indices[1]] = gripper_positions[1]
        self.set_joint_positions(joint_positions=joint_positions)
        return

    def get_gripper_velocity(self) -> Tuple[float, float]:
        """[summary]

        Returns:
            Tuple[np.ndarray, np.ndarray]: [description]
        """
        joint_velocities = self.get_joint_velocities()
        return joint_velocities[self._grippers_dof_indices[0]], joint_velocities[self._grippers_dof_indices[1]]

    def set_grippper_velocity(self, gripper_velocities: Tuple[float, float]) -> None:
        """[summary]

        Args:
            gripper_velocities (Tuple[float, float]): [description]
        """
        joint_velocities = self.get_joint_velocities()
        joint_velocities[self._grippers_dof_indices[0]] = gripper_velocities[0]
        joint_velocities[self._grippers_dof_indices[1]] = gripper_velocities[1]
        self.set_joint_velocities(joint_velocities=joint_velocities)
        return

    def initialize_handles(self) -> None:
        """[summary]
        """
        super().initialize_handles()
        self._end_effector_handle = self._dc_interface.find_articulation_body(
            self._handle, self._end_effector_prim_name
        )
        end_effector_prim_path = self._dc_interface.get_rigid_body_path(self._end_effector_handle)
        end_effector_prim = self._stage.GetPrimAtPath(end_effector_prim_path)
        self._end_effector = RigidPrim(prim=end_effector_prim, name=self._name + "_end_effector")
        self._end_effector.initialize_handles()
        self._grippers_dof_indices = (
            self.get_dof_index(self._gripper_dof_names[0]),
            self.get_dof_index(self._gripper_dof_names[1]),
        )
        return

    def reset(self) -> None:
        """[summary]
        """
        super().reset()
        self._articulation_controller.switch_dof_control_mode(dof_index=self._grippers_dof_indices[0], mode="position")
        self._articulation_controller.switch_dof_control_mode(dof_index=self._grippers_dof_indices[1], mode="position")
        return
