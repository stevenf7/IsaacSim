# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
from typing import Optional, Tuple, Union, List, Sequence
import numpy as np
from collections import OrderedDict
from omni.isaac.dynamic_control import _dynamic_control
from omni.isaac.core.prims.xform_prim import XFormPrim
from omni.isaac.core.utils.types import DOFInfo
from omni.isaac.core.utils.types import JointsState, ArticulationAction
from omni.isaac.core.utils.transformations import tf_matrix_from_pose
from omni.isaac.core.utils.rotations import gf_quat_to_np_array
from pxr import Gf, Usd, UsdGeom, UsdPhysics, PhysxSchema
from omni.isaac.core.controllers.articulation_controller import ArticulationController
import carb
from omni.isaac.core.utils.prims import (
    is_prim_path_valid,
    get_prim_property,
    set_prim_property,
    get_prim_parent,
    get_prim_at_path,
)


class Articulation(XFormPrim):
    """     
            Provides high level functions to deal with an articulation prim and its attributes/ properties.

        Args:
            prim_path (str): [description]
            name (str, optional): [description]. Defaults to "articulation".
            position (Optional[Sequence[float]], optional): [description]. Defaults to None.
            translation (Optional[Sequence[float]], optional): [description]. Defaults to None.
            orientation (Optional[Sequence[float]], optional): [description]. Defaults to None.
            scale (Optional[Sequence[float]], optional): [description]. Defaults to None.
            visible (bool, optional): [description]. Defaults to True.
            articulation_controller (Optional[ArticulationController], optional): a custom ArticulationController which
                                                                                  inherits from it. Defaults to creating the
                                                                                  basic ArticulationController.

        Raises:
            Exception: [description]
        """

    def __init__(
        self,
        prim_path: str,
        name: str = "articulation",
        position: Optional[Sequence[float]] = None,
        translation: Optional[Sequence[float]] = None,
        orientation: Optional[Sequence[float]] = None,
        scale: Optional[Sequence[float]] = None,
        visible: bool = True,
        articulation_controller: Optional[ArticulationController] = None,
    ) -> None:
        if not is_prim_path_valid(prim_path):
            raise Exception("An articulation doesn't exist at path {}".format(prim_path))
        XFormPrim.__init__(
            self,
            prim_path=prim_path,
            name=name,
            position=position,
            translation=translation,
            orientation=orientation,
            scale=scale,
            visible=visible,
        )
        self._dc_interface = _dynamic_control.acquire_dynamic_control_interface()
        self._handle = None
        self._root_handle = None
        self._dofs_infos = OrderedDict()
        self._dof_names = []
        self._num_dof = None
        self._default_joints_state = None
        self._articulation_controller = articulation_controller
        if self._articulation_controller is None:
            self._articulation_controller = ArticulationController()
        self._handles_initialized = False
        return

    @property
    def articulation_handle(self) -> int:
        """[summary]

        Returns:
            int: [description]
        """
        return self._handle

    @property
    def handles_initialized(self) -> bool:
        """[summary]

        Returns:
            bool: [description]
        """
        return self._handles_initialized

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

    @property
    def dof_names(self) -> List[str]:
        """List of prim names for each DOF.

        Returns:
            list(string): prim names
        """
        return self._dof_names

    def initialize(self):
        """[summary]
        """
        if self._handles_initialized:
            return
        self._handles_initialized = True
        carb.log_info("initializing handles for {}".format(self.prim_path))
        self._handle = self._dc_interface.get_articulation(self.prim_path)
        self._root_handle = self._dc_interface.get_articulation_root_body(self._handle)
        self._num_dof = self._dc_interface.get_articulation_dof_count(self._handle)
        for index in range(self._num_dof):
            dof_handle = self._dc_interface.get_articulation_dof(self._handle, index)
            dof_name = self._dc_interface.get_dof_name(dof_handle)
            self._dof_names.append(self._dc_interface.get_dof_name(dof_handle))
            # add dof to list
            prim_path = self._dc_interface.get_dof_path(dof_handle)
            self._dofs_infos[dof_name] = DOFInfo(prim_path=prim_path, handle=dof_handle, prim=self.prim, index=index)
        self._articulation_controller.initialize(self._handle, self._dofs_infos)
        # get default targets set in usd
        default_actions = self._articulation_controller.get_applied_action()
        self._default_joints_state = JointsState(
            positions=np.array(default_actions.joint_positions),
            velocities=np.array(default_actions.joint_velocities),
            efforts=np.zeros_like(default_actions.joint_positions),
        )
        return

    def get_dof_index(self, dof_name: str) -> int:
        """[summary]

        Args:
            dof_name (str): [description]

        Returns:
            int: [description]
        """
        return self._dofs_infos[dof_name].index

    def read_kinematic_hierarchy(self) -> None:
        """[summary]
        """
        print("Articulation handle: {self._handle}")
        print("--- Hierarchy:\n", self._read_kinematic_hierarchy())
        return

    def _read_kinematic_hierarchy(self, body_index: Optional[int] = None, indent_level: int = 0) -> None:
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

    def get_articulation_body_count(self) -> int:
        """[summary]

        Returns:
            int: [description]
        """
        return self._dc_interface.get_articulation_body_count(self._handle)

    def disable_gravity(self) -> None:
        """Keep gravity from affecting the robot
        """
        for body_index in range(self._dc_interface.get_articulation_body_count(self._handle)):
            body = self._dc_interface.get_articulation_body(self._handle, body_index)
            self._dc_interface.set_rigid_body_disable_gravity(body, True)
        return

    def enable_gravity(self) -> None:
        """Gravity will affect the robot
        """
        for body_index in range(self._dc_interface.get_articulation_body_count(self._handle)):
            body = self._dc_interface.get_articulation_body(self._handle, body_index)
            self._dc_interface.set_rigid_body_disable_gravity(body, False)
        return

    def set_joint_positions(self, positions: np.ndarray, indices: Optional[Union[List, np.ndarray]] = None) -> None:
        """[summary]

        Args:
            positions (np.ndarray): [description]
            indices (Optional[Union[list, np.ndarray]], optional): [description]. Defaults to None.

        Raises:
            Exception: [description]
        """
        if isinstance(indices, np.ndarray):
            indices = indices.tolist()
        if self._handle is None:
            raise Exception("handles are not initialized yet")
        dof_states = self._dc_interface.get_articulation_dof_states(self._handle, _dynamic_control.STATE_POS)
        if indices is None:
            new_joint_positions = positions
        else:
            new_joint_positions = self.get_joint_positions()
            for i in range(len(indices)):
                new_joint_positions[indices[i]] = positions[i]
        dof_states["pos"] = new_joint_positions
        self._dc_interface.set_articulation_dof_states(self._handle, dof_states, _dynamic_control.STATE_POS)
        self._articulation_controller.apply_action(
            ArticulationAction(joint_positions=new_joint_positions, joint_velocities=None, joint_efforts=None)
        )
        return

    def set_joint_velocities(self, velocities: np.ndarray, indices: Optional[Union[List, np.ndarray]] = None) -> None:
        """[summary]

        Args:
            velocities (np.ndarray): [description]
            indices (Optional[Union[list, np.ndarray]], optional): [description]. Defaults to None.

        Raises:
            Exception: [description]
        """
        if isinstance(indices, np.ndarray):
            indices = indices.tolist()
        if self._handle is None:
            raise Exception("handles are not initialized yet")
        dof_states = self._dc_interface.get_articulation_dof_states(self._handle, _dynamic_control.STATE_VEL)
        if indices is None:
            new_joint_velocities = velocities
        else:
            new_joint_velocities = self.get_joint_velocities()
            for i in range(len(indices)):
                new_joint_velocities[indices[i]] = velocities[i]
        dof_states["vel"] = new_joint_velocities
        self._dc_interface.set_articulation_dof_states(self._handle, dof_states, _dynamic_control.STATE_VEL)
        self._articulation_controller.apply_action(
            ArticulationAction(joint_positions=None, joint_velocities=new_joint_velocities, joint_efforts=None)
        )
        return

    def set_joint_efforts(self, efforts: np.ndarray, indices: Optional[Union[List, np.ndarray]] = None) -> None:
        """[summary]

        Args:
            efforts (np.ndarray): [description]
            indices (Optional[Union[list, np.ndarray]], optional): [description]. Defaults to None.

        Raises:
            Exception: [description]
        """
        if isinstance(indices, np.ndarray):
            indices = indices.tolist()
        if self._handle is None:
            raise Exception("handles are not initialized yet")
        dof_states = self._dc_interface.get_articulation_dof_states(self._handle, _dynamic_control.STATE_EFFORT)
        if indices is None:
            new_joint_efforts = efforts
        else:
            new_joint_efforts = [0] * self.num_dof
            for i in range(len(indices)):
                new_joint_efforts[indices[i]] = efforts[i]
        dof_states["effort"] = new_joint_efforts
        self._dc_interface.set_articulation_dof_states(self._handle, dof_states, _dynamic_control.STATE_EFFORT)
        self._articulation_controller.apply_action(
            ArticulationAction(joint_positions=None, joint_velocities=None, joint_efforts=new_joint_efforts)
        )
        return

    def get_joint_positions(self) -> np.ndarray:
        """[summary]

        Raises:
            Exception: [description]

        Returns:
            np.ndarray: [description]
        """
        if self._handle is None:
            raise Exception("handles are not initialized yet")
        joint_positions = self._dc_interface.get_articulation_dof_states(self._handle, _dynamic_control.STATE_POS)
        joint_positions = [joint_positions[i][0] for i in range(len(joint_positions))]
        return np.array(joint_positions)

    def get_joint_velocities(self) -> np.ndarray:
        """[summary]

        Raises:
            Exception: [description]

        Returns:
            np.ndarray: [description]
        """
        if self._handle is None:
            raise Exception("handles are not initialized yet")
        joint_velocities = self._dc_interface.get_articulation_dof_states(self._handle, _dynamic_control.STATE_VEL)
        joint_velocities = [joint_velocities[i][1] for i in range(len(joint_velocities))]
        return np.array(joint_velocities)

    def get_joint_efforts(self) -> np.ndarray:
        """[summary]

        Raises:
            Exception: [description]

        Returns:
            np.ndarray: [description]
        """
        if self._handle is None:
            raise Exception("handles are not initialized yet")
        joint_efforts = self._dc_interface.get_articulation_dof_states(self._handle, _dynamic_control.STATE_EFFORT)
        joint_efforts = [joint_efforts[i][2] for i in range(len(joint_efforts))]
        return np.array(joint_efforts)

    def set_joints_default_state(
        self,
        positions: Optional[np.ndarray] = None,
        velocities: Optional[np.ndarray] = None,
        efforts: Optional[np.ndarray] = None,
    ) -> None:
        """[summary]

        Args:
            positions (Optional[np.ndarray], optional): [description]. Defaults to None.
            velocities (Optional[np.ndarray], optional): [description]. Defaults to None.
            efforts (Optional[np.ndarray], optional): [description]. Defaults to None.
        """
        if positions is not None:
            self._default_joints_state.positions = positions
        if velocities is not None:
            self._default_joints_state.velocities = velocities
        if efforts is not None:
            self._default_joints_state.efforts = efforts
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

    def post_reset(self) -> None:
        """[summary]
        """
        if self._handle is None:
            raise Exception("handles are not initialized yet")
        XFormPrim.post_reset(self)
        Articulation.set_joint_positions(self, self._default_joints_state.positions)
        Articulation.set_joint_velocities(self, self._default_joints_state.velocities)
        Articulation.set_joint_efforts(self, self._default_joints_state.efforts)
        return

    def get_articulation_controller(self) -> ArticulationController:
        """
        Returns:
            ArticulationController: PD Controller of all degrees of freedom of an articulation, can apply position targets, velocity targets and efforts.
        """
        return self._articulation_controller

    def set_linear_velocity(self, velocity: np.ndarray):
        """Sets the linear velocity of the prim in stage.

        Args:
            velocity (np.ndarray):linear velocity to set the rigid prim to. Shape (3,).
        """

        if self._root_handle is not None and self._dc_interface.is_simulating():
            self._dc_interface.set_rigid_body_linear_velocity(self._root_handle, velocity)
        else:
            self._rigid_api.GetVelocityAttr().Set(Gf.Vec3f(velocity.tolist()))
        return

    def get_linear_velocity(self) -> np.ndarray:
        """[summary]

        Returns:
            np.ndarray: [description]
        """
        if self._root_handle is not None and self._dc_interface.is_simulating():
            return self._dc_interface.get_rigid_body_linear_velocity(self._root_handle)
        else:
            return np.array(self._rigid_api.GetVelocityAttr().Get())

    def set_angular_velocity(self, velocity: np.ndarray) -> None:
        """[summary]

        Args:
            velocity (np.ndarray): [description]
        """
        if self._root_handle is not None and self._dc_interface.is_simulating():
            self._dc_interface.set_rigid_body_angular_velocity(self._root_handle, velocity)
        else:
            self._rigid_api.GetAngularVelocityAttr().Set(Gf.Vec3f(velocity.tolist()))
        return

    def get_angular_velocity(self) -> np.ndarray:
        """[summary]

        Returns:
            np.ndarray: [description]
        """
        if self._root_handle is not None and self._dc_interface.is_simulating():
            return self._dc_interface.get_rigid_body_angular_velocity(self._root_handle)
        else:
            return np.array(self._rigid_api.GetAngularVelocityAttr().Get())

    def set_world_pose(self, position: Optional[np.ndarray] = None, orientation: Optional[np.ndarray] = None) -> None:
        """Sets prim's pose with respect to the world's frame.

        Args:
            position (Optional[np.ndarray], optional): position in the world frame of the prim. shape is (3, ).
                                                       Defaults to None, which means left unchanged.
            orientation (Optional[np.ndarray], optional): quaternion orientation in the world frame of the prim. 
                                                          quaternion is scalar-first (w, x, y, z). shape is (4, ).
                                                          Defaults to None, which means left unchanged.
        """
        if self._root_handle is not None and self._dc_interface.is_simulating():
            current_position, current_orientation = self.get_world_pose()
            if position is None:
                position = current_position
            if orientation is None:
                orientation = current_orientation
            pose = _dynamic_control.Transform(
                position, [orientation[1], orientation[2], orientation[3], orientation[0]]
            )
            self._dc_interface.set_rigid_body_pose(self._root_handle, pose)
        else:
            XFormPrim.set_world_pose(self, position=position, orientation=orientation)
        return

    def get_world_pose(self) -> Tuple[np.ndarray, np.ndarray]:
        """Gets prim's pose with respect to the world's frame.

        Returns:
            Tuple[np.ndarray, np.ndarray]: first index is position in the world frame of the prim. shape is (3, ). 
                                           second index is quaternion orientation in the world frame of the prim.
                                           quaternion is scalar-first (w, x, y, z). shape is (4, ).
        """
        if self._root_handle is not None and self._dc_interface.is_simulating():
            pose = self._dc_interface.get_rigid_body_pose(self._root_handle)
            return np.asarray(pose.p), np.asarray([pose.r[3], pose.r[0], pose.r[1], pose.r[2]])
        else:
            return XFormPrim.get_world_pose(self)

    def set_local_pose(
        self, translation: Optional[np.ndarray] = None, orientation: Optional[np.ndarray] = None
    ) -> None:
        """Sets prim's pose with respect to the local frame (the prim's parent frame).

        Args:
            translation (Optional[np.ndarray], optional): translation in the local frame of the prim
                                                          (with respect to its parent prim). shape is (3, ).
                                                          Defaults to None, which means left unchanged.
            orientation (Optional[np.ndarray], optional): quaternion orientation in the world frame of the prim. 
                                                          quaternion is scalar-first (w, x, y, z). shape is (4, ).
                                                          Defaults to None, which means left unchanged.
        """
        if self._root_handle is not None and self._dc_interface.is_simulating():
            local_transform = tf_matrix_from_pose(translation=translation, orientation=orientation)
            parent_world_tf = UsdGeom.Xformable(get_prim_parent(self._prim)).ComputeLocalToWorldTransform(
                Usd.TimeCode.Default()
            )
            my_world_transform = np.matmul(parent_world_tf, local_transform)
            transform = Gf.Transform()
            transform.SetMatrix(Gf.Matrix4d(np.transpose(my_world_transform)))
            calculated_position = transform.GetTranslation()
            calculated_orientation = transform.GetRotation().GetQuat()
            Articulation.set_world_pose(
                self, position=np.array(calculated_position), orientation=gf_quat_to_np_array(calculated_orientation)
            )
            return
        else:
            XFormPrim.set_local_pose(self, translation=translation, orientation=orientation)
            return

    def get_local_pose(self) -> Tuple[np.ndarray, np.ndarray]:
        """Gets prim's pose with respect to the local frame (the prim's parent frame).

        Returns:
            Tuple[np.ndarray, np.ndarray]: first index is position in the local frame of the prim. shape is (3, ). 
                                           second index is quaternion orientation in the local frame of the prim.
                                           quaternion is scalar-first (w, x, y, z). shape is (4, ).
        """
        if self._root_handle is not None and self._dc_interface.is_simulating():
            parent_world_tf = UsdGeom.Xformable(get_prim_parent(self._prim)).ComputeLocalToWorldTransform(
                Usd.TimeCode.Default()
            )
            world_position, world_orientation = Articulation.get_world_pose(self)
            my_world_transform = tf_matrix_from_pose(translation=world_position, orientation=world_orientation)
            local_transform = np.matmul(np.linalg.inv(np.transpose(parent_world_tf)), my_world_transform)
            transform = Gf.Transform()
            transform.SetMatrix(Gf.Matrix4d(np.transpose(local_transform)))
            calculated_translation = transform.GetTranslation()
            calculated_orientation = transform.GetRotation().GetQuat()
            return np.array(calculated_translation), gf_quat_to_np_array(calculated_orientation)
        else:
            return XFormPrim.get_local_pose(self)

    def apply_action(
        self, control_actions: ArticulationAction, indices: Optional[Union[List, np.ndarray]] = None
    ) -> None:
        """[summary]

        Args:
            control_actions (ArticulationAction): actions to be applied for next physics step.
            indices (Optional[Union[list, np.ndarray]], optional): degree of freedom indices to apply actions to. 
                                                                   Defaults to all degrees of freedom.

        Raises:
            Exception: [description]
        """
        if isinstance(indices, np.ndarray):
            indices = indices.tolist()
        if self._handle is None:
            raise Exception("handles are not initialized yet")
        self._articulation_controller.apply_action(control_actions=control_actions, indices=indices)
        return

    def get_applied_action(self) -> ArticulationAction:
        """[summary]

        Raises:
            Exception: [description]

        Returns:
            ArticulationAction: [description]
        """
        if self._handle is None:
            raise Exception("handles are not initialized yet")
        return self._articulation_controller.get_applied_action()

    def set_solver_position_iteration_count(self, count: int) -> None:
        """[summary]

        Args:
            count (int): [description]
        """
        set_prim_property(self.prim_path, "physxArticulation:solverPositionIterationCount", count)
        return

    def get_solver_position_iteration_count(self) -> int:
        """[summary]

        Returns:
            int: [description]
        """
        return get_prim_property(self.prim_path, "physxArticulation:solverPositionIterationCount")

    def set_solver_velocity_iteration_count(self, count: int):
        """[summary]

        Args:
            count (int): [description]
        """
        set_prim_property(self.prim_path, "physxArticulation:solverVelocityIterationCount", count)
        return

    def get_solver_velocity_iteration_count(self) -> int:
        """[summary]

        Returns:
            int: [description]
        """
        return get_prim_property(self.prim_path, "physxArticulation:solverVelocityIterationCount")

    def set_stabilization_threshold(self, threshold: float) -> None:
        """[summary]

        Args:
            threshold (float): [description]
        """
        set_prim_property(self.prim_path, "physxArticulation:stabilizationThreshold", threshold)
        return

    def get_stabilization_threshold(self) -> float:
        """[summary]

        Returns:
            float: [description]
        """
        return get_prim_property(self.prim_path, "physxArticulation:stabilizationThreshold")

    def set_enabled_self_collisions(self, flag: bool) -> None:
        """[summary]

        Args:
            flag (bool): [description]
        """
        set_prim_property(self.prim_path, "physxArticulation:enabledSelfCollisions", flag)
        return

    def get_enabled_self_collisions(self) -> bool:
        """[summary]

        Returns:
            bool: [description]
        """
        return get_prim_property(self.prim_path, "physxArticulation:enabledSelfCollisions")

    def set_sleep_threshold(self, threshold: float) -> None:
        """[summary]

        Args:
            threshold (float): [description]
        """
        set_prim_property(self.prim_path, "physxArticulation:sleepThreshold", threshold)
        return

    def get_sleep_threshold(self) -> float:
        """[summary]

        Returns:
            float: [description]
        """
        return get_prim_property(self.prim_path, "physxArticulation:sleepThreshold")

    def set_drive_type(self, joint_path, drive_type):
        joint_prim = get_prim_at_path(f"{self.prim_path}/{joint_path}")

        # set drive type ("angular" or "linear")
        drive = UsdPhysics.DriveAPI.Apply(joint_prim, drive_type)
        return drive

    def set_drive_target_position(self, drive, target_value):
        if not drive.GetTargetPositionAttr():
            drive.CreateTargetPositionAttr(target_value)
        else:
            drive.GetTargetPositionAttr().Set(target_value)

    def set_drive_target_velocity(self, drive, target_value):
        if not drive.GetTargetVelocityAttr():
            drive.CreateTargetVelocityAttr(target_value)
        else:
            drive.GetTargetVelocityAttr().Set(target_value)

    def set_drive_stiffness(self, drive, stiffness):
        if not drive.GetStiffnessAttr():
            drive.CreateStiffnessAttr(stiffness)
        else:
            drive.GetStiffnessAttr().Set(stiffness)

    def set_drive_damping(self, drive, damping):
        if not drive.GetDampingAttr():
            drive.CreateDampingAttr(damping)
        else:
            drive.GetDampingAttr().Set(damping)

    def set_drive_max_force(self, drive, max_force):
        if not drive.GetMaxForceAttr():
            drive.CreateMaxForceAttr(max_force)
        else:
            drive.GetMaxForceAttr().Set(max_force)

    def set_drive(self, joint_path, drive_type, target_type, target_value, stiffness, damping, max_force) -> None:
        drive = self.set_drive_type(joint_path, drive_type)

        # set target type ("position" or "velocity")
        if target_type == "position":
            self.set_drive_target_position(drive, target_value)
        elif target_type == "velocity":
            self.set_drive_target_velocity(drive, target_value)

        self.set_drive_stiffness(drive, stiffness)
        self.set_drive_damping(drive, damping)
        self.set_drive_max_force(drive, max_force)
