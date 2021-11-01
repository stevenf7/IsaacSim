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
from omni.isaac.core.utils.transformations import tf_matrix_from_pose
from omni.isaac.core.utils.rotations import gf_quatd_to_np_array
from pxr import Gf, Usd, UsdGeom
from omni.isaac.core.controllers.articulation_controller import ArticulationController
import carb
from omni.isaac.core.utils.prims import is_prim_path_valid, get_prim_property, set_prim_property, get_prim_parent


class Articulation(XFormPrim):
    def __init__(
        self,
        prim_path: str,
        name: Optional[str] = "articulation",
        position: Optional[np.ndarray] = None,
        translation: Optional[np.ndarray] = None,
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
        XFormPrim.__init__(
            self, prim_path=prim_path, name=name, position=position, translation=translation, orientation=orientation
        )
        self._dc_interface = _dynamic_control.acquire_dynamic_control_interface()
        self._handle = None
        self._root_handle = None
        # Handles related to robot
        self._dofs_infos = OrderedDict()
        self._num_dof = None
        self._default_joints_state = None
        self._articulation_controller = articulation_controller
        if self._articulation_controller is None:
            self._articulation_controller = ArticulationController()
        # TODO: add exceptions if user missed calling initialize handles
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
    def handles_initialized(self) -> int:
        """[summary]

        Returns:
            int: [description]
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

    def initialize_handles(self):
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
            # add dof to list
            prim_path = self._dc_interface.get_dof_path(dof_handle)
            self._dofs_infos[dof_name] = DOFInfo(prim_path=prim_path, handle=dof_handle, prim=self.prim, index=index)
        self._articulation_controller.initialize_handles(self._handle, self._dofs_infos)
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

    def set_joint_positions(self, joint_positions: np.ndarray, indices=None) -> None:
        """[summary]

        Args:
            joint_positions (np.ndarray): [description]
        """
        if self._handle is None:
            raise Exception("handles are not initialized yet")
        dof_states = self._dc_interface.get_articulation_dof_states(self._handle, _dynamic_control.STATE_POS)
        if indices is None:
            new_joint_positions = joint_positions
        else:
            new_joint_positions = self.get_joint_positions()
            for i in range(len(indices)):
                new_joint_positions[indices[i]] = joint_positions[i]
        dof_states["pos"] = new_joint_positions
        self._dc_interface.set_articulation_dof_states(self._handle, dof_states, _dynamic_control.STATE_POS)
        self._articulation_controller.apply_action(
            ArticulationAction(joint_positions=new_joint_positions, joint_velocities=None, joint_efforts=None)
        )
        return

    def set_joint_velocities(self, joint_velocities: np.ndarray, indices=None) -> None:
        """[summary]

        Args:
            joint_velocities (np.ndarray): [description]
        """
        if self._handle is None:
            raise Exception("handles are not initialized yet")
        dof_states = self._dc_interface.get_articulation_dof_states(self._handle, _dynamic_control.STATE_VEL)
        if indices is None:
            new_joint_velocities = joint_velocities
        else:
            new_joint_velocities = self.get_joint_velocities()
            for i in range(len(indices)):
                new_joint_velocities[indices[i]] = joint_velocities[i]
        dof_states["vel"] = new_joint_velocities
        self._dc_interface.set_articulation_dof_states(self._handle, dof_states, _dynamic_control.STATE_VEL)
        self._articulation_controller.apply_action(
            ArticulationAction(joint_positions=None, joint_velocities=new_joint_velocities, joint_efforts=None)
        )
        return

    def set_joint_efforts(self, joint_efforts: np.ndarray, indices=None) -> None:
        """[summary]

        Args:
            joint_efforts (np.ndarray): [description]
        """
        if self._handle is None:
            raise Exception("handles are not initialized yet")
        dof_states = self._dc_interface.get_articulation_dof_states(self._handle, _dynamic_control.STATE_EFFORT)
        if indices is None:
            new_joint_efforts = joint_efforts
        else:
            new_joint_efforts = [0] * self.num_dof
            for i in range(len(indices)):
                new_joint_efforts[indices[i]] = joint_efforts[i]
        dof_states["effort"] = new_joint_efforts
        self._dc_interface.set_articulation_dof_states(self._handle, dof_states, _dynamic_control.STATE_EFFORT)
        self._articulation_controller.apply_action(
            ArticulationAction(joint_positions=None, joint_velocities=None, joint_efforts=new_joint_efforts)
        )
        return

    def get_joint_positions(self) -> np.ndarray:
        """[summary]

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

        Returns:
            np.ndarray: [description]
        """
        if self._handle is None:
            raise Exception("handles are not initialized yet")
        joint_efforts = self._dc_interface.get_articulation_dof_states(self._handle, _dynamic_control.STATE_EFFORT)
        joint_efforts = [joint_efforts[i][2] for i in range(len(joint_efforts))]
        return joint_efforts

    def set_joints_default_state(
        self,
        positions: Optional[np.ndarray] = None,
        velocities: Optional[np.ndarray] = None,
        efforts: Optional[np.ndarray] = None,
    ) -> None:
        """[summary]

        Args:
            positions (np.ndarray): [description]
            velocities (np.ndarray): [description]
            efforts (np.ndarray): [description]
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
        """[summary]

        Returns:
            ArticulationController: [description]
        """
        return self._articulation_controller

    def set_linear_velocity(self, linear_velocity: np.ndarray):
        """Sets the linear velocity of the prim in stage. The method does this through the physx API.
            Note: It has to be called while simulating i.e after .play() or .reset() is called

        Args:
            linear_velocity (np.ndarray): linear velocity to set the rigid prim to. Shape (3,).
        """
        if self._root_handle is not None and self._dc_interface.is_simulating():
            self._dc_interface.set_rigid_body_linear_velocity(self._root_handle, linear_velocity)
        else:
            self._rigid_api.GetVelocityAttr().Set(Gf.Vec3f(linear_velocity.tolist()))
        return

    def get_linear_velocity(self) -> np.ndarray:
        if self._root_handle is not None and self._dc_interface.is_simulating():
            return self._dc_interface.get_rigid_body_linear_velocity(self._root_handle)
        else:
            return np.array(self._rigid_api.GetVelocityAttr().Get())

    def set_angular_velocity(self, angular_velocity: np.ndarray) -> None:
        if self._root_handle is not None and self._dc_interface.is_simulating():
            self._dc_interface.set_rigid_body_angular_velocity(self._root_handle, angular_velocity)
        else:
            self._rigid_api.GetAngularVelocityAttr().Set(Gf.Vec3f(angular_velocity.tolist()))
        return

    def get_angular_velocity(self):
        if self._root_handle is not None and self._dc_interface.is_simulating():
            return self._dc_interface.get_rigid_body_angular_velocity(self._root_handle)
        else:
            return np.array(self._rigid_api.GetAngularVelocityAttr().Get())

    def set_world_pose(self, position: Optional[np.ndarray] = None, orientation: Optional[np.ndarray] = None) -> None:
        """Sets the pose of the prim in stage. The method does this through the physx API.
            Note: It has to be called while simulating i.e after .play() or .reset() is called

        Args:
             position (np.ndarray, optional): position in the world frame to set the prim. shape is (3, ) Defaults to None.
             orientation (np.ndarray, optional): quaternion orientation in the world frame to set the prim. 
                                              quaternion is scalar-first (w, x, y, z). shape is (4, ). Defaults to None.
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
        """
        Gets the current pose of the prim. Note: It has to be called while simulating i.e after .play() or .reset() is called
        
        Returns:
            Tuple(np.ndarray, np.ndarray): the first position (3,) is the usd position and the second is the orientation 
                                            as a quaternion. quaternion is scalar-first (w, x, y, z). shape (4,).
        """
        if self._root_handle is not None and self._dc_interface.is_simulating():
            pose = self._dc_interface.get_rigid_body_pose(self._root_handle)
            return np.asarray(pose.p), np.asarray([pose.r[3], pose.r[0], pose.r[1], pose.r[2]])
        else:
            return XFormPrim.get_world_pose(self)

    def set_local_pose(self, translation=None, orientation=None):
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
                self, position=np.array(calculated_position), orientation=gf_quatd_to_np_array(calculated_orientation)
            )
            return
        else:
            XFormPrim.set_local_pose(translation=translation, orientation=orientation)
            return

    def get_local_pose(self):
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
            return np.array(calculated_translation), gf_quatd_to_np_array(calculated_orientation)
        else:
            return XFormPrim.get_local_pose()

    def apply_action(self, control_actions: ArticulationAction, indices=None) -> None:
        """[summary]

        Args:
            control_actions (ArticulationAction): [description]
        """
        if self._handle is None:
            raise Exception("handles are not initialized yet")
        self._articulation_controller.apply_action(control_actions=control_actions, indices=indices)
        return

    def get_applied_action(self):
        if self._handle is None:
            raise Exception("handles are not initialized yet")
        return self._articulation_controller.get_applied_action()

    def set_solver_position_iteration_count(self, count):
        set_prim_property(self.prim_path, "physxArticulation:solverPositionIterationCount", count)
        return

    def get_solver_position_iteration_count(self):
        return get_prim_property(self.prim_path, "physxArticulation:solverPositionIterationCount")

    def set_solver_velocity_iteration_count(self, count):
        set_prim_property(self.prim_path, "physxArticulation:solverVelocityIterationCount", count)
        return

    def get_solver_velocity_iteration_count(self):
        return get_prim_property(self.prim_path, "physxArticulation:solverVelocityIterationCount")

    def set_stabilization_threshold(self, threshold):
        set_prim_property(self.prim_path, "physxArticulation:stabilizationThreshold", threshold)
        return

    def get_stabilization_threshold(self):
        return get_prim_property(self.prim_path, "physxArticulation:stabilizationThreshold")

    def set_enabled_self_collisions(self, flag):
        set_prim_property(self.prim_path, "physxArticulation:enabledSelfCollisions", flag)
        return

    def get_enabled_self_collisions(self):
        return get_prim_property(self.prim_path, "physxArticulation:enabledSelfCollisions")

    def set_sleep_threshold(self, threshold):
        set_prim_property(self.prim_path, "physxArticulation:sleepThreshold", threshold)
        return

    def get_sleep_threshold(self):
        return get_prim_property(self.prim_path, "physxArticulation:sleepThreshold")
