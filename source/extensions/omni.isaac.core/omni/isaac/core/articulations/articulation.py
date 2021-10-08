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
from collections import OrderedDict
from omni.isaac.dynamic_control import _dynamic_control
from omni.isaac.core.prims.xform_prim import XFormPrim
from omni.isaac.core.utils.types import DOFInfo
from omni.isaac.core.utils.types import JointsState, ArticulationAction
from omni.isaac.core.controllers.articulation_controllers import PDArticulationController, ArticulationController
from omni.isaac.core.utils.prims import is_prim_path_valid


class Articulation(XFormPrim):
    def __init__(
        self,
        prim_path: str,
        name: Optional[str] = "articulation",
        position: Optional[np.ndarray] = None,
        orientation: Optional[np.ndarray] = None,
        articulation_controller: Optional[ArticulationController] = None,
    ) -> None:
        """[summary]

        Args:
            prim_path (str): [description]
            name (Optional, optional): [description]. Defaults to None.
            position (Optional, optional): [description]. Defaults to None.
            orientation (Optional, optional): [description]. Defaults to None.
            articulation_controller (Optional, optional): [description]. Defaults to None.
        """
        if not is_prim_path_valid(prim_path):
            raise Exception("An articulation doesn't exist at path {}".format(prim_path))
        XFormPrim.__init__(self, prim_path=prim_path, name=name, position=position, orientation=orientation)
        self._dc_interface = _dynamic_control.acquire_dynamic_control_interface()
        self._handle = None
        self._root_handle = None
        # Handles related to robot
        self._dofs_infos = OrderedDict()
        self._num_dof = None
        self._default_joints_state = None
        self._articulation_controller = articulation_controller
        return

    @property
    def articulation_handle(self) -> int:
        """[summary]

        Returns:
            int: [description]
        """
        return self._handle

    @property
    def num_dof(self) -> int:
        """[summary]

        Returns:
            int: [description]
        """
        return self._num_dof

    @property
    def dof_properties(self) -> np.ndarray:
        """[summary]

        Returns:
            np.ndarray: [description]
        """
        return self._dc_interface.get_articulation_dof_properties(self._handle)

    def _initialize_handles(self):
        """[summary]
        """
        self._handle = self._dc_interface.get_articulation(self.prim_path)
        self._root_handle = self._dc_interface.get_articulation_root_body(self._handle)
        self._num_dof = self._dc_interface.get_articulation_dof_count(self._handle)
        for index in range(self._num_dof):
            dof_handle = self._dc_interface.get_articulation_dof(self._handle, index)
            dof_name = self._dc_interface.get_dof_name(dof_handle)
            # add dof to list
            prim_path = self._dc_interface.get_dof_path(dof_handle)
            self._dofs_infos[dof_name] = DOFInfo(prim_path=prim_path, handle=dof_handle, prim=self.prim, index=index)
        self._default_joints_state = JointsState(
            positions=self.get_joint_positions(),
            velocities=self.get_joint_velocities(),
            efforts=self.get_joint_efforts(),
        )
        if self._articulation_controller is None:
            self._articulation_controller = PDArticulationController(self._handle, self._dofs_infos)
        return

    def get_dof_index(self, dof_name: str) -> int:
        """[summary]

        Args:
            dof_name (str): [description]

        Returns:
            int: [description]
        """
        return self._dofs_infos[dof_name].index

    def summarize(self) -> None:
        """[summary]
        """
        # Print the articulation handle
        print("Articulation handle: {self._handle}")
        # Print information about kinematic chain
        print("--- Hierarchy:\n", self._read_kinematic_hierarchy())
        # # Information about the DOF states of the articulated object.
        # print("--- DOF states:\n", self._read_dof_state())
        # # Information about the DOF properties of the articulated object.
        # print("--- DOF properties:\n", self._read_dof_properties())

    def _read_kinematic_hierarchy(self, body_index: Optional[int] = None, indent_level: int = 0) -> None:
        """[summary]

        Args:
            body_index (Optional, optional): [description]. Defaults to None.
            indent_level (int, optional): [description]. Defaults to 0.

        Returns:
            [type]: [description]
        """
        if body_index is None:
            body_index = self._dc_interface.get_articulation_root_body(self._handle)
        indent = "|" + "-" * indent_level
        body_name = self._dc_interface.get_rigid_body_name(body_index)
        str_output = f"{indent}Body: {body_name}\n", "blue"
        for i in range(self._dc_interface.get_rigid_body_child_joint_count(body_index)):
            joint = self._dc_interface.get_rigid_body_child_joint(body_index, i)
            joint_name = self._dc_interface.get_joint_name(joint)
            child = self._dc_interface.get_joint_child_body(joint)
            child_name = self._dc_interface.get_rigid_body_name(child)
            str_output += f"{indent}>>Joint: {joint_name} -> {child_name}\n", "green"
            str_output += self._read_kinematic_hierarchy(child, indent_level + 4)
        return str_output

    def get_articulation_body_count(self):
        return self._dc_interface.get_articulation_body_count(self._handle)

    def disable_gravity(self) -> None:
        for body_index in range(self._dc_interface.get_articulation_body_count(self._handle)):
            body = self._dc_interface.get_articulation_body(self._handle, body_index)
            self._dc_interface.set_rigid_body_disable_gravity(body, False)
        return

    def _read_dof_state(self) -> None:
        """[summary]

        Raises:
            NotImplementedError: [description]
        """
        raise NotImplementedError

    def _read_dof_properties(self) -> None:
        """[summary]

        Raises:
            NotImplementedError: [description]
        """
        raise NotImplementedError

    def set_joint_positions(self, joint_positions: np.ndarray) -> None:
        """[summary]

        Args:
            joint_positions (np.ndarray): [description]
        """
        dof_states = self._dc_interface.get_articulation_dof_states(self._handle, _dynamic_control.STATE_POS)
        dof_states["pos"] = joint_positions
        self._dc_interface.set_articulation_dof_states(self._handle, dof_states, _dynamic_control.STATE_POS)
        self._articulation_controller.apply_action(
            ArticulationAction(joint_positions=joint_positions, joint_velocities=None, joint_efforts=None)
        )
        return

    def set_joint_velocities(self, joint_velocities: np.ndarray) -> None:
        """[summary]

        Args:
            joint_velocities (np.ndarray): [description]
        """
        dof_states = self._dc_interface.get_articulation_dof_states(self._handle, _dynamic_control.STATE_VEL)
        dof_states["vel"] = joint_velocities
        self._dc_interface.set_articulation_dof_states(self._handle, dof_states, _dynamic_control.STATE_VEL)
        self._articulation_controller.apply_action(
            ArticulationAction(joint_positions=None, joint_velocities=joint_velocities, joint_efforts=None)
        )
        return

    def set_joint_efforts(self, joint_efforts: np.ndarray) -> None:
        """[summary]

        Args:
            joint_efforts (np.ndarray): [description]
        """
        dof_states = self._dc_interface.get_articulation_dof_states(self._handle, _dynamic_control.STATE_EFFORT)
        dof_states["effort"] = joint_efforts
        self._dc_interface.set_articulation_dof_states(self._handle, dof_states, _dynamic_control.STATE_EFFORT)
        self._articulation_controller.apply_action(
            ArticulationAction(joint_positions=None, joint_velocities=None, joint_efforts=joint_efforts)
        )
        return

    def get_joint_positions(self) -> np.ndarray:
        """[summary]

        Returns:
            np.ndarray: [description]
        """
        joint_positions = self._dc_interface.get_articulation_dof_states(self._handle, _dynamic_control.STATE_POS)
        joint_positions = [joint_positions[i][0] for i in range(len(joint_positions))]
        return np.array(joint_positions)

    def get_joint_velocities(self) -> np.ndarray:
        """[summary]

        Returns:
            np.ndarray: [description]
        """
        joint_velocities = self._dc_interface.get_articulation_dof_states(self._handle, _dynamic_control.STATE_VEL)
        joint_velocities = [joint_velocities[i][1] for i in range(len(joint_velocities))]
        return np.array(joint_velocities)

    def get_joint_efforts(self) -> np.ndarray:
        """[summary]

        Returns:
            np.ndarray: [description]
        """
        joint_efforts = self._dc_interface.get_articulation_dof_states(self._handle, _dynamic_control.STATE_EFFORT)
        joint_efforts = [joint_efforts[i][2] for i in range(len(joint_efforts))]
        return joint_efforts

    def set_joints_default_state(self, positions: np.ndarray, velocities: np.ndarray, efforts: np.ndarray) -> None:
        """[summary]

        Args:
            positions (np.ndarray): [description]
            velocities (np.ndarray): [description]
            efforts (np.ndarray): [description]
        """
        self._default_joints_state = JointsState(positions, velocities, efforts)
        return

    def get_joints_state(self) -> JointsState:
        """[summary]

        Returns:
            JointsState: [description]
        """
        return JointsState(
            positions=self.get_joint_positions(),
            velocities=self.get_joint_velocities(),
            efforts=self.get_joint_efforts(),
        )

    def reset(self) -> None:
        """[summary]
        """
        XFormPrim.reset(self)
        # TODO: reset joints too
        return

    def get_articulation_controller(self) -> ArticulationController:
        """[summary]

        Returns:
            ArticulationController: [description]
        """
        return self._articulation_controller

    def set_angular_velocity(self, angular_velocity: np.ndarray) -> None:
        """[summary]

        Args:
            angular_velocity (np.ndarray): [description]
        """
        self._dc_interface.set_rigid_body_angular_velocity(self._root_handle, angular_velocity)
        return

    def get_linear_velocity(self) -> np.ndarray:
        """[summary]

        Returns:
            [type]: [description]
        """
        return self._dc_interface.get_rigid_body_linear_velocity(self._root_handle)

    def get_angular_velocity(self) -> np.ndarray:
        """[summary]

        Returns:
            np.ndarray: [description]
        """
        return self._dc_interface.get_rigid_body_angular_velocity(self._root_handle)

    def set_linear_velocity(self, linear_velocity: np.ndarray) -> None:
        """[summary]

        Args:
            linear_velocity (np.ndarray): [description]
        """
        self._dc_interface.set_rigid_body_linear_velocity(self._root_handle, linear_velocity)
        return

    def set_pose(self, position: Optional[np.ndarray] = None, orientation: Optional[np.ndarray] = None) -> None:
        """[summary]

        Args:
            position (Optional, optional): [description]. Defaults to None.
            orientation (Optional, optional): [description]. Defaults to None.
        """
        current_position, current_orientation = self.get_pose()
        if position is None:
            position = current_position
        if orientation is None:
            orientation = current_orientation
        pose = _dynamic_control.Transform(position, orientation)
        self._dc_interface.set_rigid_body_pose(self._root_handle, pose)
        return

    def get_pose(self) -> Tuple[np.ndarray, np.ndarray]:
        """[summary]

        Args:
            self ([type]): [description]
            np ([type]): [description]

        Returns:
            [type]: [description]
        """
        pose = self._dc_interface.get_rigid_body_pose(self._root_handle)
        return np.asarray(pose.p), np.asarray(pose.r)

    def apply_action(self, control_actions: ArticulationAction) -> None:
        """[summary]

        Args:
            control_actions (ArticulationAction): [description]
        """
        self._articulation_controller.apply_action(control_actions=control_actions)
        return
