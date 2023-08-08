# Copyright (c) 2021-2023, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
import gc
from collections import OrderedDict
from typing import List, Optional, Tuple, Union

import carb
import numpy as np
import omni.kit.app
import torch
import warp as wp
from omni.isaac.core.prims.xform_prim_view import XFormPrimView
from omni.isaac.core.utils.prims import get_prim_at_path, get_prim_parent, get_prim_property, set_prim_property
from omni.isaac.core.utils.types import ArticulationActions, JointsState
from pxr import PhysxSchema, Usd, UsdGeom, UsdPhysics


class ArticulationView(XFormPrimView):
    """
    Provides high level functions to deal with prims that has root articulation api applied to it (1 or more articulations)
    as well as its attributes/ properties.
    This object wraps all matching articulations found at the regex provided at the prim_paths_expr.

    Note: - each prim will have "xformOp:orient", "xformOp:translate" and "xformOp:scale" only post init,
            unless it is a non-root articulation link.

    Args:
        prim_paths_expr (str): prim paths regex to encapsulate all prims that match it.
                                example: "/World/Env[1-5]/Franka" will match /World/Env1/Franka,
                                /World/Env2/Franka..etc.
                                (a non regex prim path can also be used to encapsulate one rigid prim).
        name (str, optional): shortname to be used as a key by Scene class.
                                Note: needs to be unique if the object is added to the Scene.
                                Defaults to "articulation_prim_view".
        positions (Optional[Union[np.ndarray, torch.Tensor, wp.array]], optional): default positions in the world frame of the prims.
                                                                        shape is (N, 3). Defaults to None, which means left unchanged.
        translations (Optional[Union[np.ndarray, torch.Tensor, wp.array]], optional):
                                                        default translations in the local frame of the prims
                                                        (with respect to its parent prims). shape is (N, 3).
                                                        Defaults to None, which means left unchanged.
        orientations (Optional[Union[np.ndarray, torch.Tensor, wp.array]], optional):
                                                        default quaternion orientations in the world/ local frame of the prims
                                                        (depends if translation or position is specified).
                                                        quaternion is scalar-first (w, x, y, z). shape is (N, 4).
        scales (Optional[Union[np.ndarray, torch.Tensor, wp.array]], optional): local scales to be applied to
                                                        the prim's dimensions in the view. shape is (N, 3).
                                                        Defaults to None, which means left unchanged.
        visibilities (Optional[Union[np.ndarray, torch.Tensor, wp.array]], optional): set to false for an invisible prim in
                                                                            the stage while rendering. shape is (N,).
                                                                            Defaults to None.
        reset_xform_properties (bool, optional): True if the prims don't have the right set of xform properties
                                                (i.e: translate, orient and scale) ONLY and in that order.
                                                Set this parameter to False if the object were cloned using using
                                                the cloner api in omni.isaac.cloner. Defaults to True.
        enable_dof_force_sensors (bool, optional): enables the solver computed dof force sensors on articulation joints.
                                                    Defaults to False.
    """

    def __init__(
        self,
        prim_paths_expr: str,
        name: str = "articulation_prim_view",
        positions: Optional[Union[np.ndarray, torch.Tensor, wp.array]] = None,
        translations: Optional[Union[np.ndarray, torch.Tensor, wp.array]] = None,
        orientations: Optional[Union[np.ndarray, torch.Tensor, wp.array]] = None,
        scales: Optional[Union[np.ndarray, torch.Tensor, wp.array]] = None,
        visibilities: Optional[Union[np.ndarray, torch.Tensor, wp.array]] = None,
        reset_xform_properties: bool = True,
        enable_dof_force_sensors: bool = False,
    ) -> None:
        self._physics_view = None
        XFormPrimView.__init__(
            self,
            prim_paths_expr=prim_paths_expr,
            name=name,
            positions=positions,
            translations=translations,
            orientations=orientations,
            scales=scales,
            visibilities=visibilities,
            reset_xform_properties=reset_xform_properties,
        )
        self._is_initialized = False
        self._num_dof = None
        self._dof_paths = None
        self._default_joints_state = None
        self._dofs_infos = OrderedDict()
        self._dof_names = None
        self._body_names = None
        self._body_indices = None
        self._dof_indices = None
        self._dof_types = None
        self._metadata = None
        self._enable_dof_force_sensors = enable_dof_force_sensors
        return

    def __del__(self):
        del self._physics_view
        self._invalidate_physics_handle_event = None
        return

    @property
    def num_dof(self) -> int:
        """
        Returns:
            int: number of degrees of freedom for the articulations of prims in the view.
        """
        if not self._is_initialized:
            carb.log_warn("ArticulationView needs to be initialized.")
            return None
        return self._num_dof

    @property
    def num_bodies(self) -> int:
        """
        Returns:
            int: number of rigid bodies for the articulations of prims in the view.
        """
        if not self._is_initialized:
            carb.log_warn("ArticulationView needs to be initialized.")
            return None
        return self._num_bodies

    @property
    def num_shapes(self) -> int:
        """
        Returns:
            int: number of rigid shapes for the articulations of prims in the view.
        """
        if not self._is_initialized:
            carb.log_warn("ArticulationView needs to be initialized.")
            return None
        return self._num_shapes

    @property
    def num_fixed_tendons(self) -> int:
        """
        Returns:
            int: number of rigid shapes for the articulations of prims in the view.
        """
        if not self._is_initialized:
            carb.log_warn("ArticulationView needs to be initialized.")
            return None
        return self._num_fixed_tendons

    @property
    def body_names(self) -> List[str]:
        """
        Returns:
            List[str]: ordered names of bodies that corresponds to links for the articulations of prims in the view.
        """
        if not self._is_initialized:
            carb.log_warn("ArticulationView needs to be initialized.")
            return None
        return self._body_names

    @property
    def dof_names(self) -> List[str]:
        """
        Returns:
            List[str]: ordered names of joints that corresponds to degrees of freedom for the articulations of prims in the view.
        """
        if not self._is_initialized:
            carb.log_warn("ArticulationView needs to be initialized.")
            return None
        return self._dof_names

    @property
    def initialized(self) -> bool:
        """

        Returns:
            bool: True if the view object was initialized (after the first call of .initialize()). False otherwise.
        """
        return self._is_initialized

    def is_physics_handle_valid(self) -> bool:
        """
        Returns:
            bool: False if .initialize() needs to be called again for the physics handle to be valid. Otherwise True.
                Note: if physics handle is not valid many of the methods that requires physX will return None.
        """
        return self._physics_view is not None

    def initialize(self, physics_sim_view: omni.physics.tensors.SimulationView = None) -> None:
        """Create a physics simulation view if not passed and creates an articulation view using physX tensor api.

        Args:
            physics_sim_view (omni.physics.tensors.SimulationView, optional): current physics simulation view. Defaults to None.
        """
        if physics_sim_view is None:
            physics_sim_view = omni.physics.tensors.create_simulation_view(self._backend)
            physics_sim_view.set_subspace_roots("/")
        carb.log_info("initializing view for {}".format(self._name))
        self._physics_view = physics_sim_view.create_articulation_view(
            self._regex_prim_paths.replace(".*", "*"), self._enable_dof_force_sensors
        )
        assert self._physics_view.is_homogeneous
        self._physics_sim_view = physics_sim_view
        if not self._is_initialized:
            self._metadata = self._physics_view.shared_metatype
            self._num_dof = self._physics_view.max_dofs
            self._num_bodies = self._physics_view.max_links
            self._num_shapes = self._physics_view.max_shapes
            self._num_fixed_tendons = self._physics_view.max_fixed_tendons
            self._body_names = self._metadata.link_names
            self._body_indices = dict(zip(self._body_names, range(len(self._body_names))))
            self._dof_names = self._metadata.dof_names
            self._dof_indices = self._metadata.dof_indices
            self._dof_types = self._metadata.dof_types
            self._dof_paths = self._physics_view.dof_paths
            self._prim_paths = self._physics_view.prim_paths
            carb.log_info("Articulation Prim View Device: {}".format(self._device))
            self._is_initialized = True
            self._default_kps, self._default_kds = self.get_gains(clone=True)
            default_actions = self.get_applied_actions(clone=True)
            # TODO: implement effort part
            if self._default_joints_state is None:
                self._default_joints_state = JointsState(positions=None, velocities=None, efforts=None)
            if self._default_joints_state.positions is None:
                self._default_joints_state.positions = default_actions.joint_positions
            if self._default_joints_state.velocities is None:
                self._default_joints_state.velocities = default_actions.joint_velocities
            if self._default_joints_state.efforts is None:
                self._default_joints_state.efforts = self._backend_utils.create_zeros_tensor(
                    shape=[self.count, self.num_dof], dtype="float32", device=self._device
                )
        timeline = omni.timeline.get_timeline_interface()
        self._invalidate_physics_handle_event = timeline.get_timeline_event_stream().create_subscription_to_pop(
            self._invalidate_physics_handle_callback
        )
        return

    def _invalidate_physics_handle_callback(self, event):
        if event.type == int(omni.timeline.TimelineEventType.STOP):
            self._physics_view = None
            self._invalidate_physics_handle_event = None
        return

    def get_body_index(self, body_name: str) -> int:
        """Gets the body index in the articulation given its name.

        Args:
            body_name (str): name of the body/link to query.

        Returns:
            int: index of the body/link in the articulation buffers.
        """
        if not self._is_initialized:
            carb.log_warn("ArticulationView needs to be initialized.")
            return None
        return self._body_indices[body_name]

    def get_dof_index(self, dof_name: str) -> int:
        """Gets the dof index in the joint buffers given its name.

        Args:
            dof_name (str): name of the joint that corresponds to the degree of freedom to query.

        Returns:
            int: index of the degree of freedom in the joint buffers.
        """
        if not self._is_initialized:
            carb.log_warn("ArticulationView needs to be initialized.")
            return None
        return self._dof_indices[dof_name]

    def get_dof_types(self, dof_names: List[str] = None) -> List[str]:
        """Gets the dof types given the dof names.

        Args:
            dof_names (List[str], optional): names of the joints that corresponds to the degrees of freedom to query. Defaults to None.

        Returns:
            List[str]: types of the joints that corresponds to the degrees of freedom. Types can be invalid, translation or rotation.
        """
        if not self._is_initialized:
            carb.log_warn("ArticulationView needs to be initialized.")
            return None
        if dof_names is None:
            return self._dof_types
        else:
            return [self._physics_view.get_dof_type(self.get_dof_index(dof_name)) for dof_name in dof_names]

    def get_dof_limits(self) -> Union[np.ndarray, torch.Tensor]:
        """
        Returns:
            Union[np.ndarray, torch.Tensor, wp.array]: degrees of freedom position limits.
                                            shape is (N, num_dof, 2) where index 0 corresponds to the lower limit and index 1 corresponds to the upper limit.
        """
        if not self._is_initialized:
            carb.log_warn("ArticulationView needs to be initialized.")
            return None
        return self._physics_view.get_dof_limits()

    def set_friction_coefficients(
        self,
        values: Union[np.ndarray, torch.Tensor],
        indices: Optional[Union[np.ndarray, List, torch.Tensor, wp.array]] = None,
        joint_indices: Optional[Union[np.ndarray, List, torch.Tensor, wp.array]] = None,
    ) -> None:
        """Sets friction coefficients for articulation joints in the view.

        Args:
            values (Union[np.ndarray, torch.Tensor, wp.array]): friction coefficients for articulations in the view. shape (M, K).
            indices (Optional[Union[np.ndarray, List, torch.Tensor, wp.array]], optional): indicies to specify which prims
                                                                                 to manipulate. Shape (M,).
                                                                                 Where M <= size of the encapsulated prims in the view.
                                                                                 Defaults to None (i.e: all prims in the view).
            joint_indices (Optional[Union[np.ndarray, List, torch.Tensor, wp.array]], optional): joint indicies to specify which joints
                                                                                 to manipulate. Shape (K,).
                                                                                 Where K <= num of dofs.
                                                                                 Defaults to None (i.e: all dofs).
        """
        if not self._is_initialized:
            carb.log_warn("ArticulationView needs to be initialized.")
            return
        if not omni.timeline.get_timeline_interface().is_stopped() and self._physics_view is not None:
            indices = self._backend_utils.resolve_indices(indices, self.count, "cpu")
            joint_indices = self._backend_utils.resolve_indices(joint_indices, self.num_dof, "cpu")
            new_values = self._physics_view.get_dof_friction_coefficients()
            values = self._backend_utils.move_data(values, device="cpu")
            new_values = self._backend_utils.assign(
                values,
                new_values,
                [self._backend_utils.expand_dims(indices, 1) if self._backend != "warp" else indices, joint_indices],
            )
            self._physics_view.set_dof_friction_coefficients(new_values, indices)
        else:
            indices = self._backend_utils.to_list(
                self._backend_utils.resolve_indices(indices, self.count, self._device)
            )
            dof_types = self._backend_utils.to_list(self.get_dof_types())
            joint_indices = self._backend_utils.to_list(
                self._backend_utils.resolve_indices(joint_indices, self.num_dof, self._device)
            )
            values = self._backend_utils.to_list(values)
            articulation_read_idx = 0
            for i in indices:
                dof_read_idx = 0
                for dof_index in joint_indices:
                    drive_type = (
                        "angular" if dof_types[dof_index] == omni.physics.tensors.DofType.Rotation else "linear"
                    )
                    prim = PhysxSchema.PhysxJointAPI(get_prim_at_path(self._dof_paths[i][dof_index]))
                    if not prim.GetJointFrictionAttr():
                        prim.CreateJointFrictionAttr().Set(values[articulation_read_idx][dof_read_idx])
                    else:
                        prim.GetJointFrictionAttr().Set(values[articulation_read_idx][dof_read_idx])
                    dof_read_idx += 1
                articulation_read_idx += 1
        return

    def get_friction_coefficients(
        self,
        indices: Optional[Union[np.ndarray, List, torch.Tensor, wp.array]] = None,
        joint_indices: Optional[Union[np.ndarray, List, torch.Tensor, wp.array]] = None,
        clone: bool = True,
    ) -> Union[np.ndarray, torch.Tensor, wp.array]:
        """Gets friction coefficients for articulation in the view.

        Args:
            indices (Optional[Union[np.ndarray, List, torch.Tensor, wp.array]], optional): indicies to specify which prims
                                                                                 to query. Shape (M,).
                                                                                 Where M <= size of the encapsulated prims in the view.
                                                                                 Defaults to None (i.e: all prims in the view).
            joint_indices (Optional[Union[np.ndarray, List, torch.Tensor, wp.array]], optional): joint indicies to specify which joints
                                                                                 to query. Shape (K,).
                                                                                 Where K <= num of dofs.
                                                                                 Defaults to None (i.e: all dofs).
            clone (Optional[bool]): True to return a clone of the internal buffer. Otherwise False. Defaults to True.

        Returns:
            Union[np.ndarray, torch.Tensor, wp.indexedarray]: maximum efforts for articulations in the view. shape (M, K).
        """
        if not self._is_initialized:
            carb.log_warn("ArticulationView needs to be initialized.")
            return None
        if not omni.timeline.get_timeline_interface().is_stopped() and self._physics_view is not None:
            indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
            joint_indices = self._backend_utils.resolve_indices(joint_indices, self.num_dof, self._device)
            values = self._backend_utils.move_data(self._physics_view.get_dof_friction_coefficients(), self._device)
            if clone:
                values = self._backend_utils.clone_tensor(values, device=self._device)
            result = values[
                self._backend_utils.expand_dims(indices, 1) if self._backend != "warp" else indices, joint_indices
            ]
            return result
        else:
            indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
            joint_indices = self._backend_utils.resolve_indices(joint_indices, self.num_dof, self._device)
            values = np.zeros(shape=(indices.shape[0], joint_indices.shape[0]), dtype="float32")
            articulation_write_idx = 0
            indices = self._backend_utils.to_list(indices)
            joint_indices = self._backend_utils.to_list(joint_indices)
            for i in indices:
                dof_write_idx = 0
                for dof_index in joint_indices:
                    prim = PhysxSchema.PhysxJointAPI(get_prim_at_path(self._dof_paths[i][dof_index]))
                    if prim.GetJointFrictionAttr().Get():
                        values[articulation_write_idx][dof_write_idx] = prim.GetJointFrictionAttr().Get()
                    dof_write_idx += 1
                articulation_write_idx += 1
            values = self._backend_utils.convert(values, dtype="float32", device=self._device, indexed=True)
            return values

    def set_armatures(
        self,
        values: Union[np.ndarray, torch.Tensor, wp.array],
        indices: Optional[Union[np.ndarray, List, torch.Tensor, wp.array]] = None,
        joint_indices: Optional[Union[np.ndarray, List, torch.Tensor, wp.array]] = None,
    ) -> None:
        """Sets armatures for articulation joints in the view.

        Args:
            values (Union[np.ndarray, torch.Tensor, wp.array]): armatures for articulations in the view. shape (M, K).
            indices (Optional[Union[np.ndarray, List, torch.Tensor, wp.array]], optional): indicies to specify which prims
                                                                                 to manipulate. Shape (M,).
                                                                                 Where M <= size of the encapsulated prims in the view.
                                                                                 Defaults to None (i.e: all prims in the view).
            joint_indices (Optional[Union[np.ndarray, List, torch.Tensor, wp.array]], optional): joint indicies to specify which joints
                                                                                 to manipulate. Shape (K,).
                                                                                 Where K <= num of dofs.
                                                                                 Defaults to None (i.e: all dofs).
        """
        if not self._is_initialized:
            carb.log_warn("ArticulationView needs to be initialized.")
            return
        if not omni.timeline.get_timeline_interface().is_stopped() and self._physics_view is not None:
            indices = self._backend_utils.resolve_indices(indices, self.count, "cpu")
            joint_indices = self._backend_utils.resolve_indices(joint_indices, self.num_dof, "cpu")
            new_values = self._physics_view.get_dof_armatures()
            values = self._backend_utils.move_data(values, device="cpu")
            new_values = self._backend_utils.assign(
                values,
                new_values,
                [self._backend_utils.expand_dims(indices, 1) if self._backend != "warp" else indices, joint_indices],
            )
            self._physics_view.set_dof_armatures(new_values, indices)
        else:
            indices = self._backend_utils.to_list(
                self._backend_utils.resolve_indices(indices, self.count, self._device)
            )
            joint_indices = self._backend_utils.to_list(
                self._backend_utils.resolve_indices(joint_indices, self.num_dof, self._device)
            )
            values = self._backend_utils.to_list(values)
            articulation_read_idx = 0
            for i in indices:
                dof_read_idx = 0
                for dof_index in joint_indices:
                    prim = PhysxSchema.PhysxJointAPI(get_prim_at_path(self._dof_paths[i][dof_index]))
                    if not prim.GetArmatureAttr():
                        prim.CreateArmatureAttr().Set(values[articulation_read_idx][dof_read_idx])
                    else:
                        prim.GetArmatureAttr().Set(values[articulation_read_idx][dof_read_idx])
                    dof_read_idx += 1
                articulation_read_idx += 1
        return

    def get_armatures(
        self,
        indices: Optional[Union[np.ndarray, List, torch.Tensor, wp.array]] = None,
        joint_indices: Optional[Union[np.ndarray, List, torch.Tensor, wp.array]] = None,
        clone: bool = True,
    ) -> Union[np.ndarray, torch.Tensor, wp.indexedarray]:
        """Gets armatures for articulation in the view.

        Args:
            indices (Optional[Union[np.ndarray, List, torch.Tensor, wp.array]], optional): indicies to specify which prims
                                                                                 to query. Shape (M,).
                                                                                 Where M <= size of the encapsulated prims in the view.
                                                                                 Defaults to None (i.e: all prims in the view).
            joint_indices (Optional[Union[np.ndarray, List, torch.Tensor, wp.array]], optional): joint indicies to specify which joints
                                                                                 to query. Shape (K,).
                                                                                 Where K <= num of dofs.
                                                                                 Defaults to None (i.e: all dofs).
            clone (Optional[bool]): True to return a clone of the internal buffer. Otherwise False. Defaults to True.

        Returns:
            Union[np.ndarray, torch.Tensor, wp.indexedarray]: maximum efforts for articulations in the view. shape (M, K).
        """
        if not self._is_initialized:
            carb.log_warn("ArticulationView needs to be initialized.")
            return None
        if not omni.timeline.get_timeline_interface().is_stopped() and self._physics_view is not None:
            indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
            joint_indices = self._backend_utils.resolve_indices(joint_indices, self.num_dof, self._device)
            values = self._backend_utils.move_data(self._physics_view.get_dof_armatures(), device=self._device)
            if clone:
                values = self._backend_utils.clone_tensor(values, device=self._device)
            result = values[
                self._backend_utils.expand_dims(indices, 1) if self._backend != "warp" else indices, joint_indices
            ]
            return result
        else:
            indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
            joint_indices = self._backend_utils.resolve_indices(joint_indices, self.num_dof, self._device)
            values = np.zeros(shape=(indices.shape[0], joint_indices.shape[0]), dtype="float32")
            indices = self._backend_utils.to_list(indices)
            joint_indices = self._backend_utils.to_list(joint_indices)
            articulation_write_idx = 0
            for i in indices:
                dof_write_idx = 0
                for dof_index in joint_indices:
                    prim = PhysxSchema.PhysxJointAPI(get_prim_at_path(self._dof_paths[i][dof_index]))
                    if prim.GetArmatureAttr().Get():
                        values[articulation_write_idx, dof_write_idx] = prim.GetArmatureAttr().Get()
                    dof_write_idx += 1
                articulation_write_idx += 1
            values = self._backend_utils.convert(values, dtype="float32", device=self._device, indexed=True)
            return values

    def get_articulation_body_count(self) -> int:
        """
        Returns:
            int: number of links in the articulation.
        """
        if not self._is_initialized:
            carb.log_warn("ArticulationView needs to be initialized.")
            return None
        return self._metadata.link_count

    def set_joint_position_targets(
        self,
        positions: Optional[Union[np.ndarray, torch.Tensor, wp.array]],
        indices: Optional[Union[np.ndarray, List, torch.Tensor, wp.array]] = None,
        joint_indices: Optional[Union[np.ndarray, List, torch.Tensor, wp.array]] = None,
    ) -> None:
        """
        Sets the joint position targets for the implicit pd controllers.

        Args:
            positions (Optional[Union[np.ndarray, torch.Tensor, wp.array]]): joint position targets for the implicit pd controller.
                                                                    shape is (M, K).
            indices (Optional[Union[np.ndarray, List, torch.Tensor, wp.array]], optional): indicies to specify which prims
                                                                                 to manipulate. Shape (M,).
                                                                                 Where M <= size of the encapsulated prims in the view.
                                                                                 Defaults to None (i.e: all prims in the view).
            joint_indices (Optional[Union[np.ndarray, List, torch.Tensor, wp.array]], optional): joint indicies to specify which joints
                                                                                 to manipulate. Shape (K,).
                                                                                 Where K <= num of dofs.
                                                                                 Defaults to None (i.e: all dofs).
        """
        if not self._is_initialized:
            carb.log_warn("ArticulationView needs to be initialized.")
            return
        if not omni.timeline.get_timeline_interface().is_stopped() and self._physics_view is not None:
            indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
            joint_indices = self._backend_utils.resolve_indices(joint_indices, self.num_dof, self._device)
            action = self._physics_view.get_dof_position_targets()
            action = self._backend_utils.assign(
                self._backend_utils.move_data(positions, device=self._device),
                action,
                [self._backend_utils.expand_dims(indices, 1) if self._backend != "warp" else indices, joint_indices],
            )
            self._physics_view.set_dof_position_targets(action, indices)
        else:
            carb.log_warn("Physics Simulation View is not created yet in order to use set_joint_position_targets")

    def set_joint_positions(
        self,
        positions: Optional[Union[np.ndarray, torch.Tensor, wp.array]],
        indices: Optional[Union[np.ndarray, List, torch.Tensor, wp.array]] = None,
        joint_indices: Optional[Union[np.ndarray, List, torch.Tensor, wp.array]] = None,
    ) -> None:
        """Sets the joint positions of articulations in the view.

        Args:
            positions (Optional[Union[np.ndarray, torch.Tensor, wp.array]]): joint positions of articulations in the view to be set to in the next frame.
                                                                    shape is (M, K).
            indices (Optional[Union[np.ndarray, List, torch.Tensor, wp.array]], optional): indicies to specify which prims
                                                                                 to manipulate. Shape (M,).
                                                                                 Where M <= size of the encapsulated prims in the view.
                                                                                 Defaults to None (i.e: all prims in the view).
            joint_indices (Optional[Union[np.ndarray, List, torch.Tensor, wp.array]], optional): joint indicies to specify which joints
                                                                                 to manipulate. Shape (K,).
                                                                                 Where K <= num of dofs.
                                                                                 Defaults to None (i.e: all dofs).
        """
        if not self._is_initialized:
            carb.log_warn("ArticulationView needs to be initialized.")
            return
        if not omni.timeline.get_timeline_interface().is_stopped() and self._physics_view is not None:
            indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
            joint_indices = self._backend_utils.resolve_indices(joint_indices, self.num_dof, self._device)
            new_dof_pos = self._physics_view.get_dof_positions()
            new_dof_pos = self._backend_utils.assign(
                self._backend_utils.move_data(positions, device=self._device),
                new_dof_pos,
                [self._backend_utils.expand_dims(indices, 1) if self._backend != "warp" else indices, joint_indices],
            )
            self._physics_view.set_dof_positions(new_dof_pos, indices)
            self._physics_view.set_dof_position_targets(new_dof_pos, indices)
        else:
            carb.log_warn("Physics Simulation View is not created yet in order to use set_joint_positions")

    def set_joint_velocity_targets(
        self,
        velocities: Optional[Union[np.ndarray, torch.Tensor, wp.array]],
        indices: Optional[Union[np.ndarray, List, torch.Tensor, wp.array]] = None,
        joint_indices: Optional[Union[np.ndarray, List, torch.Tensor, wp.array]] = None,
    ) -> None:
        """
        Sets the joint velocity targets for the implicit pd controllers.

        Args:
            velocities (Optional[Union[np.ndarray, torch.Tensor, wp.array]]): joint velocity targets for the implicit pd controller.
                                                                    shape is (M, K).
            indices (Optional[Union[np.ndarray, List, torch.Tensor, wp.array]], optional): indicies to specify which prims
                                                                                 to manipulate. Shape (M,).
                                                                                 Where M <= size of the encapsulated prims in the view.
                                                                                 Defaults to None (i.e: all prims in the view).
            joint_indices (Optional[Union[np.ndarray, List, torch.Tensor, wp.array]], optional): joint indicies to specify which joints
                                                                                 to manipulate. Shape (K,).
                                                                                 Where K <= num of dofs.
                                                                                 Defaults to None (i.e: all dofs).
        """
        if not self._is_initialized:
            carb.log_warn("ArticulationView needs to be initialized.")
            return
        if not omni.timeline.get_timeline_interface().is_stopped() and self._physics_view is not None:
            indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
            joint_indices = self._backend_utils.resolve_indices(joint_indices, self.num_dof, self._device)
            action = self._physics_view.get_dof_velocity_targets()
            action = self._backend_utils.assign(
                self._backend_utils.move_data(velocities, device=self._device),
                action,
                [self._backend_utils.expand_dims(indices, 1) if self._backend != "warp" else indices, joint_indices],
            )
            self._physics_view.set_dof_velocity_targets(action, indices)
        else:
            carb.log_warn("Physics Simulation View is not created yet in order to use set_joint_velocity_targets")

    def set_joint_velocities(
        self,
        velocities: Optional[Union[np.ndarray, torch.Tensor, wp.array]],
        indices: Optional[Union[np.ndarray, List, torch.Tensor, wp.array]] = None,
        joint_indices: Optional[Union[np.ndarray, List, torch.Tensor, wp.array]] = None,
    ) -> None:
        """Sets the joint velocities of articulations in the view.

        Args:
            velocities (Optional[Union[np.ndarray, torch.Tensor, wp.array]]): joint velocities of articulations in the view to be set to in the next frame.
                                                                    shape is (M, K).
            indices (Optional[Union[np.ndarray, List, torch.Tensor, wp.array]], optional): indicies to specify which prims
                                                                                 to manipulate. Shape (M,).
                                                                                 Where M <= size of the encapsulated prims in the view.
                                                                                 Defaults to None (i.e: all prims in the view).
            joint_indices (Optional[Union[np.ndarray, List, torch.Tensor, wp.array]], optional): joint indicies to specify which joints
                                                                                 to manipulate. Shape (K,).
                                                                                 Where K <= num of dofs.
                                                                                 Defaults to None (i.e: all dofs).
        """
        if not self._is_initialized:
            carb.log_warn("ArticulationView needs to be initialized.")
            return
        if not omni.timeline.get_timeline_interface().is_stopped() and self._physics_view is not None:
            indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
            joint_indices = self._backend_utils.resolve_indices(joint_indices, self.num_dof, self._device)
            new_dof_vel = self._physics_view.get_dof_velocities()
            new_dof_vel = self._backend_utils.assign(
                self._backend_utils.move_data(velocities, device=self._device),
                new_dof_vel,
                [self._backend_utils.expand_dims(indices, 1) if self._backend != "warp" else indices, joint_indices],
            )
            self._physics_view.set_dof_velocities(new_dof_vel, indices)
            self._physics_view.set_dof_velocity_targets(new_dof_vel, indices)
        else:
            carb.log_warn("Physics Simulation View is not created yet in order to use set_joint_velocities")
        return

    def set_joint_efforts(
        self,
        efforts: Optional[Union[np.ndarray, torch.Tensor, wp.array]],
        indices: Optional[Union[np.ndarray, List, torch.Tensor, wp.array]] = None,
        joint_indices: Optional[Union[np.ndarray, List, torch.Tensor, wp.array]] = None,
    ) -> None:
        """Sets the joint efforts of articulations in the view.

        Args:
            efforts (Optional[Union[np.ndarray, torch.Tensor, wp.array]]): efforts of articulations in the view to be set to in the next frame.
                                                                    shape is (M, K).
            indices (Optional[Union[np.ndarray, List, torch.Tensor, wp.array]], optional): indicies to specify which prims
                                                                                 to manipulate. Shape (M,).
                                                                                 Where M <= size of the encapsulated prims in the view.
                                                                                 Defaults to None (i.e: all prims in the view).
            joint_indices (Optional[Union[np.ndarray, List, torch.Tensor, wp.array]], optional): joint indicies to specify which joints
                                                                                 to manipulate. Shape (K,).
                                                                                 Where K <= num of dofs.
                                                                                 Defaults to None (i.e: all dofs).
        """
        if not self._is_initialized:
            carb.log_warn("ArticulationView needs to be initialized.")
            return

        if not omni.timeline.get_timeline_interface().is_stopped() and self._physics_view is not None:
            indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
            joint_indices = self._backend_utils.resolve_indices(joint_indices, self.num_dof, self._device)
            # TODO: missing get_dof efforts/ forces?
            new_dof_efforts = self._backend_utils.create_zeros_tensor(
                shape=[self.count, self.num_dof], dtype="float32", device=self._device
            )
            new_dof_efforts = self._backend_utils.assign(
                self._backend_utils.move_data(efforts, device=self._device),
                new_dof_efforts,
                [self._backend_utils.expand_dims(indices, 1) if self._backend != "warp" else indices, joint_indices],
            )
            # TODO: double check this/ is this setting a force or applying a force?
            self._physics_view.set_dof_actuation_forces(new_dof_efforts, indices)
        else:
            carb.log_warn("Physics Simulation View is not created yet in order to use set_joint_efforts")
        return

    def get_applied_joint_efforts(
        self,
        indices: Optional[Union[np.ndarray, List, torch.Tensor, wp.array]] = None,
        joint_indices: Optional[Union[np.ndarray, List, torch.Tensor, wp.array]] = None,
        clone: bool = True,
    ) -> Union[np.ndarray, torch.Tensor, wp.indexedarray]:
        """Gets the joint efforts of articulations in the view. The method will return the efforts set by the set_joint_efforts.

        Args:
            indices (Optional[Union[np.ndarray, List, torch.Tensor, wp.array]], optional): indicies to specify which prims
                                                                                 to manipulate. Shape (M,).
                                                                                 Where M <= size of the encapsulated prims in the view.
                                                                                 Defaults to None (i.e: all prims in the view).
            joint_indices (Optional[Union[np.ndarray, List, torch.Tensor, wp.array]], optional): joint indicies to specify which joints
                                                                                 to manipulate. Shape (K,).
                                                                                 Where K <= num of dofs.
                                                                                 Defaults to None (i.e: all dofs).
            clone (bool, optional): True to return a clone of the internal buffer. Otherwise False. Defaults to True.

        Returns:
            Union[np.ndarray, torch.Tensor, wp.indexedarray]: joint efforts of articulations in the view assigned via set_joint_efforts. shape is (M, K).
        """
        if not self._is_initialized:
            carb.log_warn("ArticulationView needs to be initialized.")
            return None
        if not omni.timeline.get_timeline_interface().is_stopped() and self._physics_view is not None:
            indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
            joint_indices = self._backend_utils.resolve_indices(joint_indices, self.num_dof, self._device)
            current_joint_forces = self._physics_view.get_dof_actuation_forces()
            if clone:
                current_joint_forces = self._backend_utils.clone_tensor(current_joint_forces, device=self._device)
            result = current_joint_forces[
                self._backend_utils.expand_dims(indices, 1) if self._backend != "warp" else indices, joint_indices
            ]
            return result
        else:
            carb.log_warn("Physics Simulation View is not created yet in order to use get_applied_joint_efforts")
            return None

    def get_measured_joint_efforts(
        self,
        indices: Optional[Union[np.ndarray, List, torch.Tensor, wp.array]] = None,
        joint_indices: Optional[Union[np.ndarray, List, torch.Tensor, wp.array]] = None,
        clone: bool = True,
    ) -> Union[np.ndarray, torch.Tensor, wp.indexedarray]:
        """Gets the dof forces of articulations in the view. The method will return the solver computed projection of the joint forces in the dof motion direction.

        Args:
            indices (Optional[Union[np.ndarray, List, torch.Tensor]], optional): indicies to specify which prims
                                                                                 to manipulate. Shape (M,).
                                                                                 Where M <= size of the encapsulated prims in the view.
                                                                                 Defaults to None (i.e: all prims in the view).
            joint_indices (Optional[Union[np.ndarray, List, torch.Tensor]], optional): joint indicies to specify which joints
                                                                                 to manipulate. Shape (K,).
                                                                                 Where K <= num of dofs.
                                                                                 Defaults to None (i.e: all dofs).
            clone (bool, optional): True to return a clone of the internal buffer. Otherwise False. Defaults to True.

        Returns:
            Union[np.ndarray, torch.Tensor]: computed joint efforts of articulations in the view. shape is (M, K).
        """
        if not self._is_initialized:
            carb.log_warn("ArticulationView needs to be initialized.")
            return None
        if not omni.timeline.get_timeline_interface().is_stopped() and self._physics_view is not None:
            indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
            joint_indices = self._backend_utils.resolve_indices(joint_indices, self.num_dof, self._device)
            current_joint_forces = self._physics_view.get_dof_projected_joint_forces()
            if clone:
                result = self._backend_utils.clone_tensor(current_joint_forces, device=self._device)
            result = result[
                self._backend_utils.expand_dims(indices, 1) if self._backend != "warp" else indices, joint_indices
            ]
            return result
        else:
            carb.log_warn("Physics Simulation View is not created yet in order to use get_measured_joint_efforts")
            return None

    def get_measured_joint_forces(
        self,
        indices: Optional[Union[np.ndarray, List, torch.Tensor]] = None,
        joint_indices: Optional[Union[np.ndarray, List, torch.Tensor]] = None,
        clone: bool = True,
    ) -> Union[np.ndarray, torch.Tensor]:
        """Gets the joint forces of articulations in the view. The method will return the link incoming joint forces.

        Args:
            indices (Optional[Union[np.ndarray, List, torch.Tensor]], optional): indicies to specify which prims
                                                                                 to manipulate. Shape (M,).
                                                                                 Where M <= size of the encapsulated prims in the view.
                                                                                 Defaults to None (i.e: all prims in the view).
            joint_indices (Optional[Union[np.ndarray, List, torch.Tensor]], optional): link indicies to specify which link's incoming joints to get. Shape (K,).
                                                                                    Where K <= num of links/bodies.
                                                                                    Defaults to None (i.e: all dofs).
            clone (bool, optional): True to return a clone of the internal buffer. Otherwise False. Defaults to True.

        Returns:
            Union[np.ndarray, torch.Tensor]: joint forces of articulations in the view. shape is (M, K, 6).
        """
        if not self._is_initialized:
            carb.log_warn("ArticulationView needs to be initialized.")
            return None
        if not omni.timeline.get_timeline_interface().is_stopped() and self._physics_view is not None:
            indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
            joint_indices = self._backend_utils.resolve_indices(joint_indices, self.num_bodies, self._device)
            current_joint_forces = self._physics_view.get_link_incoming_joint_force()
            if clone:
                result = self._backend_utils.clone_tensor(current_joint_forces, device=self._device)
            result = result[
                self._backend_utils.expand_dims(indices, 1) if self._backend != "warp" else indices, joint_indices
            ]
            return result
        else:
            carb.log_warn("Physics Simulation View is not created yet in order to use get_measured_joint_forces")
            return None

    def get_joint_positions(
        self,
        indices: Optional[Union[np.ndarray, List, torch.Tensor, wp.array]] = None,
        joint_indices: Optional[Union[np.ndarray, List, torch.Tensor, wp.array]] = None,
        clone: bool = True,
    ) -> Union[np.ndarray, torch.Tensor, wp.indexedarray]:
        """Gets the joint positions of articulations in the view.

        Args:
            indices (Optional[Union[np.ndarray, List, torch.Tensor, wp.array]], optional): indicies to specify which prims
                                                                                 to query. Shape (M,).
                                                                                 Where M <= size of the encapsulated prims in the view.
                                                                                 Defaults to None (i.e: all prims in the view).
            joint_indices (Optional[Union[np.ndarray, List, torch.Tensor, wp.array]], optional): joint indicies to specify which joints
                                                                                 to query. Shape (K,).
                                                                                 Where K <= num of dofs.
                                                                                 Defaults to None (i.e: all dofs).
            clone (bool, optional): True to return a clone of the internal buffer. Otherwise False. Defaults to True.

        Returns:
            Union[np.ndarray, torch.Tensor, wp.indexedarray]: joint positions of articulations in the view.
                                                    shape is (M, K).
        """
        if not self._is_initialized:
            carb.log_warn("ArticulationView needs to be initialized.")
            return None
        if not omni.timeline.get_timeline_interface().is_stopped() and self._physics_view is not None:
            indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
            joint_indices = self._backend_utils.resolve_indices(joint_indices, self.num_dof, self._device)
            current_joint_positions = self._physics_view.get_dof_positions()
            if clone:
                current_joint_positions = self._backend_utils.clone_tensor(current_joint_positions, device=self._device)
            result = current_joint_positions[
                self._backend_utils.expand_dims(indices, 1) if self._backend != "warp" else indices, joint_indices
            ]
            return result
        else:
            carb.log_warn("Physics Simulation View is not created yet in order to use get_joint_positions")
            return None

    def get_joint_velocities(
        self,
        indices: Optional[Union[np.ndarray, List, torch.Tensor, wp.array]] = None,
        joint_indices: Optional[Union[np.ndarray, List, torch.Tensor, wp.array]] = None,
        clone: bool = True,
    ) -> Union[np.ndarray, torch.Tensor, wp.indexedarray]:
        """Gets the joint velocities of articulations in the view.

        Args:
            indices (Optional[Union[np.ndarray, List, torch.Tensor, wp.array]], optional): indicies to specify which prims
                                                                                 to query. Shape (M,).
                                                                                 Where M <= size of the encapsulated prims in the view.
                                                                                 Defaults to None (i.e: all prims in the view).
            joint_indices (Optional[Union[np.ndarray, List, torch.Tensor, wp.array]], optional): joint indicies to specify which joints
                                                                                 to query. Shape (K,).
                                                                                 Where K <= num of dofs.
                                                                                 Defaults to None (i.e: all dofs).
            clone (bool, optional): True to return a clone of the internal buffer. Otherwise False. Defaults to True.

        Returns:
            Union[np.ndarray, torch.Tensor, wp.indexedarray]: joint velocities of articulations in the view.
                                                    shape is (M, K).
        """
        if not self._is_initialized:
            carb.log_warn("ArticulationView needs to be initialized.")
            return None
        if not omni.timeline.get_timeline_interface().is_stopped() and self._physics_view is not None:
            indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
            joint_indices = self._backend_utils.resolve_indices(joint_indices, self.num_dof, self._device)
            current_joint_velocities = self._physics_view.get_dof_velocities()
            if clone:
                current_joint_velocities = self._backend_utils.clone_tensor(
                    current_joint_velocities, device=self._device
                )
            result = current_joint_velocities[
                self._backend_utils.expand_dims(indices, 1) if self._backend != "warp" else indices, joint_indices
            ]
            return result
        else:
            carb.log_warn("Physics Simulation View is not created yet in order to use get_joint_velocities")
            return None

    def apply_action(
        self,
        control_actions: ArticulationActions,
        indices: Optional[Union[np.ndarray, List, torch.Tensor, wp.array]] = None,
    ) -> None:
        """Applies ArticulationActions which encapsulates joint position targets, velocity targets, efforts and joint indices in one object.
            Can be used instead of the seperate set_joint_position_targets..etc.

        Args:
            control_actions (ArticulationActions): actions to be applied for next physics step.
            indices (Optional[Union[np.ndarray, List, torch.Tensor, wp.array]], optional): indicies to specify which prims
                                                                                 to manipulate. Shape (M,).
                                                                                 Where M <= size of the encapsulated prims in the view.
                                                                                 Defaults to None (i.e: all prims in the view).
        """
        if not self._is_initialized:
            carb.log_warn("ArticulationView needs to be initialized.")
            return
        if not omni.timeline.get_timeline_interface().is_stopped() and self._physics_view is not None:
            indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
            joint_indices = self._backend_utils.resolve_indices(
                control_actions.joint_indices, self.num_dof, self._device
            )

            if control_actions.joint_positions is not None:
                # TODO: optimize this operation
                action = self._physics_view.get_dof_position_targets()
                action = self._backend_utils.assign(
                    self._backend_utils.move_data(control_actions.joint_positions, device=self._device),
                    action,
                    [
                        self._backend_utils.expand_dims(indices, 1) if self._backend != "warp" else indices,
                        joint_indices,
                    ],
                )
                self._physics_view.set_dof_position_targets(action, indices)
            if control_actions.joint_velocities is not None:
                # TODO: optimize this operation
                action = self._physics_view.get_dof_velocity_targets()
                action = self._backend_utils.assign(
                    self._backend_utils.move_data(control_actions.joint_velocities, device=self._device),
                    action,
                    [
                        self._backend_utils.expand_dims(indices, 1) if self._backend != "warp" else indices,
                        joint_indices,
                    ],
                )
                self._physics_view.set_dof_velocity_targets(action, indices)
            if control_actions.joint_efforts is not None:
                # TODO: optimize this operation
                # action = self._backend_utils.clone_tensor(self._physics_view.get_dof_actuation_forces(), device=self._device)
                action = self._backend_utils.create_zeros_tensor(
                    (self.count, self.num_dof), dtype="float32", device=self._device
                )
                action = self._backend_utils.assign(
                    self._backend_utils.move_data(control_actions.joint_efforts, device=self._device),
                    action,
                    [
                        self._backend_utils.expand_dims(indices, 1) if self._backend != "warp" else indices,
                        joint_indices,
                    ],
                )
                self._physics_view.set_dof_actuation_forces(action, indices)
        else:
            carb.log_warn("Physics Simulation View is not created yet in order to use apply_action")
        return

    def get_applied_actions(self, clone: bool = True) -> ArticulationActions:
        """Gets current applied actions in an ArticulationActions object.

        Args:
            clone (bool, optional): True to return clones of the internal buffers. Otherwise False. Defaults to True.

        Returns:
            ArticulationActions: current applied actions (i.e: current position targets and velocity targets)
        """
        if not self._is_initialized:
            carb.log_warn("ArticulationView needs to be initialized.")
            return None
        if not omni.timeline.get_timeline_interface().is_stopped() and self._physics_view is not None:
            joint_positions = self._physics_view.get_dof_position_targets()
            if clone:
                joint_positions = self._backend_utils.clone_tensor(joint_positions, device=self._device)
            joint_velocities = self._physics_view.get_dof_velocity_targets()
            if clone:
                joint_velocities = self._backend_utils.clone_tensor(joint_velocities, device=self._device)
            joint_efforts = self._physics_view.get_dof_actuation_forces()
            if clone:
                joint_efforts = self._backend_utils.clone_tensor(joint_efforts, device=self._device)
            # TODO: implement the effort part
            return ArticulationActions(
                joint_positions=joint_positions,
                joint_velocities=joint_velocities,
                joint_efforts=joint_efforts,
                joint_indices=None,
            )
        else:
            carb.log_warn("Physics Simulation View is not created yet in order to use get_applied_actions")
            return None

    def set_world_poses(
        self,
        positions: Optional[Union[np.ndarray, torch.Tensor, wp.array]] = None,
        orientations: Optional[Union[np.ndarray, torch.Tensor, wp.array]] = None,
        indices: Optional[Union[np.ndarray, list, torch.Tensor, wp.array]] = None,
    ) -> None:
        """Sets poses of prims in the view with respect to the world's frame.

        Args:
            positions (Optional[Union[np.ndarray, torch.Tensor, wp.array]], optional): positions in the world frame of the prim. shape is (M, 3).
                                                                             Defaults to None, which means left unchanged.
            orientations (Optional[Union[np.ndarray, torch.Tensor, wp.array]], optional): quaternion orientations in the world frame of the prims.
                                                                                quaternion is scalar-first (w, x, y, z). shape is (M, 4).
                                                                                Defaults to None, which means left unchanged.
            indices (Optional[Union[np.ndarray, list, torch.Tensor, wp.array]], optional): indicies to specify which prims
                                                                                 to manipulate. Shape (M,).
                                                                                 Where M <= size of the encapsulated prims in the view.
                                                                                 Defaults to None (i.e: all prims in the view).
        """
        if not omni.timeline.get_timeline_interface().is_stopped() and self._physics_view is not None:
            indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
            current_positions, current_orientations = self.get_world_poses(clone=False)
            if not hasattr(self, "_pose_buf"):
                self._pose_buf = self._backend_utils.create_zeros_tensor(
                    shape=[self.count, 7], dtype="float32", device=self._device
                )
            if positions is not None:
                positions = self._backend_utils.move_data(positions, self._device)
            if orientations is not None:
                orientations = self._backend_utils.move_data(orientations, self._device)
            pose = self._backend_utils.assign_pose(
                current_positions, current_orientations, positions, orientations, indices, self._device, self._pose_buf
            )
            self._physics_view.set_root_transforms(pose, indices)
            return
        else:
            XFormPrimView.set_world_poses(self, positions=positions, orientations=orientations, indices=indices)
        return

    def get_world_poses(
        self, indices: Optional[Union[np.ndarray, list, torch.Tensor, wp.array]] = None, clone: bool = True
    ) -> Union[
        Tuple[np.ndarray, np.ndarray], Tuple[torch.Tensor, torch.Tensor], Tuple[wp.indexedarray, wp.indexedarray]
    ]:
        """Gets the poses of the prims in the view with respect to the world's frame.

        Args:
            indices (Optional[Union[np.ndarray, list, torch.Tensor, wp.array]], optional): indicies to specify which prims
                                                                                 to query. Shape (M,).
                                                                                 Where M <= size of the encapsulated prims in the view.
                                                                                 Defaults to None (i.e: all prims in the view).
            clone (bool, optional): True to return a clone of the internal buffer. Otherwise False. Defaults to True.

        Returns:
            Union[Tuple[np.ndarray, np.ndarray], Tuple[torch.Tensor, torch.Tensor], Tuple[wp.indexedarray, wp.indexedarray]]:
                                        first index is positions in the world frame of the prims. shape is (M, 3).
                                           second index is quaternion orientations in the world frame of the prims.
                                           quaternion is scalar-first (w, x, y, z). shape is (M, 4).
        """
        if not omni.timeline.get_timeline_interface().is_stopped() and self._physics_view is not None:
            indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
            pose = self._physics_view.get_root_transforms()
            if clone:
                pose = self._backend_utils.clone_tensor(pose, device=self._device)
            pos = pose[indices, 0:3]
            rot = self._backend_utils.xyzw2wxyz(pose[indices, 3:7])
            return pos, rot
        else:
            pos, rot = XFormPrimView.get_world_poses(self, indices=indices)
            ret_pos = self._backend_utils.convert(pos, dtype="float32", device=self._device, indexed=True)
            ret_rot = self._backend_utils.convert(rot, dtype="float32", device=self._device, indexed=True)
            return ret_pos, ret_rot

    def get_local_poses(
        self, indices: Optional[Union[np.ndarray, list, torch.Tensor, wp.array]] = None
    ) -> Union[
        Tuple[np.ndarray, np.ndarray], Tuple[torch.Tensor, torch.Tensor], Tuple[wp.indexedarray, wp.indexedarray]
    ]:
        """Gets prim poses in the view with respect to the local frame (the prim's parent frame).

        Args:
            indices (Optional[Union[np.ndarray, list, torch.Tensor, wp.array]], optional): indicies to specify which prims
                                                                                    to query. Shape (M,).
                                                                                    Where M <= size of the encapsulated prims in the view.
                                                                                    Defaults to None (i.e: all prims in the view)

        Returns:
            Union[Tuple[np.ndarray, np.ndarray], Tuple[torch.Tensor, torch.Tensor], Tuple[wp.indexedarray, wp.indexedarray]]:
                                                            first index is positions in the local frame of the prims. shape is (M, 3).
                                                        second index is quaternion orientations in the local frame of the prims.
                                                        quaternion is scalar-first (w, x, y, z). shape is (M, 4).
        """
        if not omni.timeline.get_timeline_interface().is_stopped() and self._physics_view is not None:
            indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
            world_positions, world_orientations = self.get_world_poses(indices=indices)
            parent_transforms = np.zeros(shape=(indices.shape[0], 4, 4), dtype="float32")
            write_idx = 0
            indices = self._backend_utils.to_list(indices)
            for i in indices:
                parent_transforms[write_idx] = np.array(
                    UsdGeom.Xformable(get_prim_parent(self._prims[i])).ComputeLocalToWorldTransform(
                        Usd.TimeCode.Default()
                    ),
                    dtype="float32",
                )
                write_idx += 1
            parent_transforms = self._backend_utils.convert(parent_transforms, dtype="float32", device=self._device)
            res = self._backend_utils.get_local_from_world(
                parent_transforms, world_positions, world_orientations, self._device
            )
            return res
        else:
            return XFormPrimView.get_local_poses(self, indices=indices)

    def set_local_poses(
        self,
        translations: Optional[Union[np.ndarray, torch.Tensor, wp.array]] = None,
        orientations: Optional[Union[np.ndarray, torch.Tensor, wp.array]] = None,
        indices: Optional[Union[np.ndarray, list, torch.Tensor, wp.array]] = None,
    ) -> None:
        """Sets prim poses in the view with respect to the local frame (the prim's parent frame).

        Args:
            translations (Optional[Union[np.ndarray, torch.Tensor, wp.array]], optional):
                                                          translations in the local frame of the prims
                                                          (with respect to its parent prim). shape is (M, 3).
                                                          Defaults to None, which means left unchanged.
            orientations (Optional[Union[np.ndarray, torch.Tensor, wp.array]], optional):
                                                          quaternion orientations in the local frame of the prims.
                                                          quaternion is scalar-first (w, x, y, z). shape is (M, 4).
                                                          Defaults to None, which means left unchanged.
            indices (Optional[Union[np.ndarray, list, torch.Tensor, wp.array]], optional): indicies to specify which prims
                                                                                 to manipulate. Shape (M,).
                                                                                 Where M <= size of the encapsulated prims in the view.
                                                                                 Defaults to None (i.e: all prims in the view).
        """
        if not omni.timeline.get_timeline_interface().is_stopped() and self._physics_view is not None:
            if translations is None or orientations is None:
                current_translations, current_orientations = ArticulationView.get_local_poses(self)
                if translations is None:
                    translations = current_translations
                if orientations is None:
                    orientations = current_orientations
            indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
            parent_transforms = np.zeros(shape=(indices.shape[0], 4, 4), dtype="float32")
            write_idx = 0
            indices = self._backend_utils.to_list(indices)
            for i in indices:
                parent_transforms[write_idx] = np.array(
                    UsdGeom.Xformable(get_prim_parent(self._prims[i])).ComputeLocalToWorldTransform(
                        Usd.TimeCode.Default()
                    ),
                    dtype="float32",
                )
                write_idx += 1
            parent_transforms = self._backend_utils.convert(parent_transforms, dtype="float32", device=self._device)
            calculated_positions, calculated_orientations = self._backend_utils.get_world_from_local(
                parent_transforms, translations, orientations, self._device
            )
            ArticulationView.set_world_poses(
                self, positions=calculated_positions, orientations=calculated_orientations, indices=indices
            )
        else:
            XFormPrimView.set_local_poses(self, translations=translations, orientations=orientations, indices=indices)
        return

    def set_velocities(
        self,
        velocities: Optional[Union[np.ndarray, torch.Tensor, wp.array]] = None,
        indices: Optional[Union[np.ndarray, list, torch.Tensor, wp.array]] = None,
    ) -> None:
        """Sets the linear and angular velocities of the prims in the view at once. The method does this through the physx API only.
            i.e: It has to be called after initialization.

        Args:
            velocities (Optional[Union[np.ndarray, torch.Tensor, wp.array]]): linear and angular velocities respectively to set the rigid prims to. shape is (M, 6).
            indices (Optional[Union[np.ndarray, list, torch.Tensor, wp.array]], optional): indicies to specify which prims
                                                                                 to manipulate. Shape (M,).
                                                                                 Where M <= size of the encapsulated prims in the view.
                                                                                 Defaults to None (i.e: all prims in the view).
        """
        if not self._is_initialized:
            carb.log_warn("ArticulationView needs to be initialized.")
        indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
        if not omni.timeline.get_timeline_interface().is_stopped() and self._physics_view is not None:
            root_vel = self._physics_view.get_root_velocities()
            root_vel = self._backend_utils.assign(
                self._backend_utils.move_data(velocities, self._device), root_vel, indices
            )
            self._physics_view.set_root_velocities(root_vel, indices)
        else:
            self.set_linear_velocities(velocities[:, 0:3], indices=indices)
            self.set_angular_velocities(velocities[:, 3:6], indices=indices)

    def get_velocities(
        self, indices: Optional[Union[np.ndarray, list, torch.Tensor, wp.array]] = None, clone: bool = True
    ) -> Union[np.ndarray, torch.Tensor, wp.indexedarray]:
        """Gets the linear and angular velocities of prims in the view.

        Args:
            indices (Optional[Union[np.ndarray, list, torch.Tensor, wp.array]], optional): indicies to specify which prims
                                                                                    to query. Shape (M,).
                                                                                    Where M <= size of the encapsulated prims in the view.
                                                                                    Defaults to None (i.e: all prims in the view)
            clone (bool, optional): True to return a clone of the internal buffer. Otherwise False. Defaults to True.

        Returns:
            Union[np.ndarray, torch.Tensor, wp.indexedarray]: linear and angular velocities of the prims in the view concatenated. shape is (M, 6).
        """
        if not self._is_initialized:
            carb.log_warn("ArticulationView needs to be initialized.")
        indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
        if not omni.timeline.get_timeline_interface().is_stopped() and self._physics_view is not None:
            velocities = self._physics_view.get_root_velocities()
            if clone:
                velocities = self._backend_utils.clone_tensor(velocities, device=self._device)
            return velocities[indices]
        else:
            linear_velocities = self.get_linear_velocities(indices, clone)
            angular_velocities = self.get_angular_velocities(indices, clone)
            return self._backend_utils.tensor_cat([linear_velocities, angular_velocities], dim=-1, device=self._device)

    def set_linear_velocities(
        self,
        velocities: Optional[Union[np.ndarray, torch.Tensor, wp.array]] = None,
        indices: Optional[Union[np.ndarray, list, torch.Tensor, wp.array]] = None,
    ) -> None:
        """Sets the linear velocities of the prims in the view. The method does this through the physx API only.
            i.e: It has to be called after initialization.
            Note: This method is not supported for the gpu pipeline. set_velocities method should be used instead.

        Args:
            velocities (Optional[Union[np.ndarray, torch.Tensor, wp.array]]): linear velocities to set the rigid prims to. shape is (M, 3).
            indices (Optional[Union[np.ndarray, list, torch.Tensor, wp.array]], optional): indicies to specify which prims
                                                                                 to manipulate. Shape (M,).
                                                                                 Where M <= size of the encapsulated prims in the view.
                                                                                 Defaults to None (i.e: all prims in the view).
        """
        if not self._is_initialized:
            carb.log_warn("ArticulationView needs to be initialized.")
            return
        if self._device is not None and "cuda" in self._device:
            carb.log_warn(
                "set_linear_velocities function is not supported for the gpu pipeline, use set_velocities instead."
            )
        indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
        if not omni.timeline.get_timeline_interface().is_stopped() and self._physics_view is not None:
            root_velocities = self._physics_view.get_root_velocities()
            if self._backend == "warp":
                root_velocities = self._backend_utils.assign(
                    self._backend_utils.move_data(velocities, device=self._device),
                    root_velocities,
                    [indices, wp.array([0, 1, 2], device=self._device, dtype=wp.int32)],
                )
            else:
                root_velocities[indices, 0:3] = self._backend_utils.move_data(velocities, device=self._device)
            self._physics_view.set_root_velocities(root_velocities, indices)
        else:
            carb.log_warn("Physics Simulation View is not created yet in order to use set_linear_velocities")

    def get_linear_velocities(
        self, indices: Optional[Union[np.ndarray, list, torch.Tensor, wp.array]] = None, clone=True
    ) -> Union[np.ndarray, torch.Tensor, wp.indexedarray]:
        """Gets the linear velocities of prims in the view.

        Args:
            indices (Optional[Union[np.ndarray, list, torch.Tensor, wp.array]], optional): indicies to specify which prims
                                                                                    to query. Shape (M,).
                                                                                    Where M <= size of the encapsulated prims in the view.
                                                                                    Defaults to None (i.e: all prims in the view)
            clone (bool, optional): True to return a clone of the internal buffer. Otherwise False. Defaults to True.

        Returns:
            Union[np.ndarray, torch.Tensor, wp.indexedarray]: linear velocities of the prims in the view. shape is (M, 3).
        """
        if not self._is_initialized:
            carb.log_warn("ArticulationView needs to be initialized.")
        indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
        if not omni.timeline.get_timeline_interface().is_stopped() and self._physics_view is not None:
            linear_velocities = self._physics_view.get_root_velocities()
            if clone:
                linear_velocities = self._backend_utils.clone_tensor(linear_velocities, device=self._device)
            return linear_velocities[indices, 0:3]
        else:
            carb.log_warn("Physics Simulation View is not created yet in order to use get_linear_velocities")
            return None

    def set_angular_velocities(
        self,
        velocities: Optional[Union[np.ndarray, torch.Tensor, wp.array]] = None,
        indices: Optional[Union[np.ndarray, list, torch.Tensor, wp.array]] = None,
    ) -> None:
        """Sets the angular velocities of the prims in the view. The method does this through the physx API only.
            i.e: It has to be called after initialization.
            Note: This method is not supported for the gpu pipeline. set_velocities method should be used instead.

        Args:
            velocities (Optional[Union[np.ndarray, torch.Tensor, wp.array]]): angular velocities to set the rigid prims to. shape is (M, 3).
            indices (Optional[Union[np.ndarray, list, torch.Tensor, wp.array]], optional): indicies to specify which prims
                                                                                 to manipulate. Shape (M,).
                                                                                 Where M <= size of the encapsulated prims in the view.
                                                                                 Defaults to None (i.e: all prims in the view).
        """
        if not self._is_initialized:
            carb.log_warn("ArticulationView needs to be initialized.")
        if self._device is not None and "cuda" in self._device:
            carb.log_warn(
                "set_angular_velocities function is not supported for the gpu pipeline, use set_velocities instead."
            )
        indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
        if not omni.timeline.get_timeline_interface().is_stopped() and self._physics_view is not None:
            root_velocities = self._physics_view.get_root_velocities()
            if self._backend == "warp":
                root_velocities = self._backend_utils.assign(
                    self._backend_utils.move_data(velocities, device=self._device),
                    root_velocities,
                    [indices, wp.array([3, 4, 5], device=self._device, dtype=wp.int32)],
                )
            else:
                root_velocities[indices, 3:6] = self._backend_utils.move_data(velocities, device=self._device)
            self._physics_view.set_root_velocities(root_velocities, indices)
        else:
            carb.log_warn("Physics Simulation View is not created yet in order to use set_angular_velocities")
        return

    def get_angular_velocities(
        self, indices: Optional[Union[np.ndarray, list, torch.Tensor, wp.array]] = None, clone: bool = True
    ) -> Union[np.ndarray, torch.Tensor, wp.indexedarray]:
        """Gets the angular velocities of prims in the view.

        Args:
            indices (Optional[Union[np.ndarray, list, torch.Tensor, wp.array]], optional): indicies to specify which prims
                                                                                    to query. Shape (M,).
                                                                                    Where M <= size of the encapsulated prims in the view.
                                                                                    Defaults to None (i.e: all prims in the view)
            clone (bool, optional): True to return a clone of the internal buffer. Otherwise False. Defaults to True.

        Returns:
            Union[np.ndarray, torch.Tensor, wp.indexedarray]: angular velocities of the prims in the view. shape is (M, 3).
        """
        if not self._is_initialized:
            carb.log_warn("ArticulationView needs to be initialized.")
        indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
        if not omni.timeline.get_timeline_interface().is_stopped() and self._physics_view is not None:
            angular_velocities = self._physics_view.get_root_velocities()
            if clone:
                angular_velocities = self._backend_utils.clone_tensor(angular_velocities, device=self._device)
            return angular_velocities[indices, 3:6]
        else:
            carb.log_warn("Physics Simulation View is not created yet in order to use get_angular_velocities")
            return None

    def set_joints_default_state(
        self,
        positions: Optional[Union[np.ndarray, torch.Tensor, wp.array]] = None,
        velocities: Optional[Union[np.ndarray, torch.Tensor, wp.array]] = None,
        efforts: Optional[Union[np.ndarray, torch.Tensor, wp.array]] = None,
    ) -> None:
        """Sets the joints default state (joint positions, velocities and efforts) to be applied after each reset.

        Args:
            positions (Optional[Union[np.ndarray, torch.Tensor, wp.array]], optional): default joint positions.
                                                                             shape is (N, num of dofs). Defaults to None.
            velocities (Optional[Union[np.ndarray, torch.Tensor, wp.array]], optional): default joint velocities.
                                                                             shape is (N, num of dofs). Defaults to None.
            efforts (Optional[Union[np.ndarray, torch.Tensor, wp.array]], optional): default joint efforts.
                                                                             shape is (N, num of dofs). Defaults to None.
        """
        if self._default_joints_state is None:
            self._default_joints_state = JointsState(positions=None, velocities=None, efforts=None)
        if positions is not None:
            self._default_joints_state.positions = positions
        if velocities is not None:
            self._default_joints_state.velocities = velocities
        if efforts is not None:
            self._default_joints_state.efforts = efforts
        return

    def get_joints_default_state(self) -> JointsState:
        """
        Returns:
            JointsState: current joints default state. (i.e: the joint positions and velocities after a reset).
        """
        return self._default_joints_state

    def get_joints_state(self) -> JointsState:
        """
        Returns:
            JointsState: current joint positions and velocities.
        """
        if not self._is_initialized:
            carb.log_warn("ArticulationView needs to be initialized.")
        # TODO: implement effort part
        if not omni.timeline.get_timeline_interface().is_stopped() and self._physics_view is not None:
            return JointsState(
                positions=self.get_joint_positions(), velocities=self.get_joint_velocities(), efforts=None
            )
        else:
            carb.log_warn("Physics Simulation View is not created yet in order to use get_joints_state")
            return None

    def post_reset(self) -> None:
        """Resets the prims to its default state."""
        XFormPrimView.post_reset(self)
        ArticulationView.set_joint_positions(self, self._default_joints_state.positions)
        ArticulationView.set_joint_velocities(self, self._default_joints_state.velocities)
        ArticulationView.set_joint_efforts(self, self._default_joints_state.efforts)
        ArticulationView.set_gains(self, kps=self._default_kps, kds=self._default_kds)
        return

    def get_effort_modes(
        self,
        indices: Optional[Union[np.ndarray, List, torch.Tensor, wp.array]] = None,
        joint_indices: Optional[Union[np.ndarray, List, torch.Tensor, wp.array]] = None,
    ) -> List[str]:
        """
        Gets effort modes for articulations in the view.

        Args:
            indices (Optional[Union[np.ndarray, List, torch.Tensor, wp.array]], optional): indicies to specify which prims
                                                                                 to query. Shape (M,).
                                                                                 Where M <= size of the encapsulated prims in the view.
                                                                                 Defaults to None (i.e: all prims in the view).
            joint_indices (Optional[Union[np.ndarray, List, torch.Tensor, wp.array]], optional): joint indicies to specify which joints
                                                                                 to query. Shape (K,).
                                                                                 Where K <= num of dofs.
                                                                                 Defaults to None (i.e: all dofs).

        Returns:
            List: Returns a List of size (M, K) indicating the effort modes. accelaration or force.
        """
        if not self._is_initialized:
            carb.log_warn("Physics Simulation View was never created in order to use get_effort_modes")
            return None
        indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
        dof_types = self.get_dof_types()
        joint_indices = self._backend_utils.resolve_indices(joint_indices, self.num_dof, self._device)
        result = [[None for i in range(joint_indices.shape[0])] for j in range(indices.shape[0])]
        articulation_write_idx = 0
        indices = self._backend_utils.to_list(indices)
        joint_indices = self._backend_utils.to_list(joint_indices)
        for i in indices:
            dof_write_idx = 0
            for dof_index in joint_indices:
                drive_type = "angular" if dof_types[dof_index] == omni.physics.tensors.DofType.Rotation else "linear"
                prim = get_prim_at_path(self._dof_paths[i][dof_index])
                if prim.HasAPI(UsdPhysics.DriveAPI):
                    drive = UsdPhysics.DriveAPI(prim, drive_type)
                else:
                    drive = UsdPhysics.DriveAPI.Apply(prim, drive_type)
                result[articulation_write_idx][dof_write_idx] = drive.GetTypeAttr().Get()
                dof_write_idx += 1
            articulation_write_idx += 1
        return result

    def set_effort_modes(
        self,
        mode: str,
        indices: Optional[Union[np.ndarray, List, torch.Tensor, wp.array]] = None,
        joint_indices: Optional[Union[np.ndarray, List, torch.Tensor]] = None,
    ) -> None:
        """
        Sets effort modes for articulations in the view.

        Args:
            mode (str): effort mode to be applied to prims in the vie, wp.arrayw. force or acceleration.
            indices (Optional[Union[np.ndarray, List, torch.Tensor, wp.array]], optional): indicies to specify which prims
                                                                                 to manipulate. Shape (M,).
                                                                                 Where M <= size of the encapsulated prims in the view.
                                                                                 Defaults to None (i.e: all prims in the view).
            joint_indices (Optional[Union[np.ndarray, List, torch.Tensor, wp.array]], optional): joint indicies to specify which joints
                                                                                 to manipulate. Shape (K,).
                                                                                 Where K <= num of dofs.
                                                                                 Defaults to None (i.e: all dofs).

        Raises:
            Exception: _description_
        """
        if not self._is_initialized:
            carb.log_warn("ArticulationView needs to be initialized.")
            return
        if mode not in ["force", "acceleration"]:
            raise Exception("Effort Mode specified {} is not recognized".format(mode))
        indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
        dof_types = self.get_dof_types()
        joint_indices = self._backend_utils.resolve_indices(joint_indices, self.num_dof, self._device)
        indices = self._backend_utils.to_list(indices)
        joint_indices = self._backend_utils.to_list(joint_indices)
        for i in indices:
            for dof_index in joint_indices:
                drive_type = "angular" if dof_types[dof_index] == omni.physics.tensors.DofType.Rotation else "linear"
                prim = get_prim_at_path(self._dof_paths[i][dof_index])
                if prim.HasAPI(UsdPhysics.DriveAPI):
                    drive = UsdPhysics.DriveAPI(prim, drive_type)
                else:
                    drive = UsdPhysics.DriveAPI.Apply(prim, drive_type)
                if not drive.GetTypeAttr():
                    drive.CreateTypeAttr().Set(mode)
                else:
                    drive.GetTypeAttr().Set(mode)
        return

    def set_max_efforts(
        self,
        values: Union[np.ndarray, torch.Tensor, wp.array],
        indices: Optional[Union[np.ndarray, List, torch.Tensor, wp.array]] = None,
        joint_indices: Optional[Union[np.ndarray, List, torch.Tensor, wp.array]] = None,
    ) -> None:
        """Sets maximum efforts for articulation in the view.

        Args:
            values (Union[np.ndarray, torch.Tensor, wp.array]): maximum efforts for articulations in the view. shape (M, K).
            indices (Optional[Union[np.ndarray, List, torch.Tensor, wp.array]], optional): indicies to specify which prims
                                                                                 to manipulate. Shape (M,).
                                                                                 Where M <= size of the encapsulated prims in the view.
                                                                                 Defaults to None (i.e: all prims in the view).
            joint_indices (Optional[Union[np.ndarray, List, torch.Tensor, wp.array]], optional): joint indicies to specify which joints
                                                                                 to manipulate. Shape (K,).
                                                                                 Where K <= num of dofs.
                                                                                 Defaults to None (i.e: all dofs).
        """
        if not self._is_initialized:
            carb.log_warn("ArticulationView needs to be initialized.")
            return
        if not omni.timeline.get_timeline_interface().is_stopped() and self._physics_view is not None:
            indices = self._backend_utils.resolve_indices(indices, self.count, "cpu")
            joint_indices = self._backend_utils.resolve_indices(joint_indices, self.num_dof, "cpu")
            new_values = self._physics_view.get_dof_max_forces()
            new_values = self._backend_utils.assign(
                self._backend_utils.move_data(values, device="cpu"),
                new_values,
                [self._backend_utils.expand_dims(indices, 1) if self._backend != "warp" else indices, joint_indices],
            )
            self._physics_view.set_dof_max_forces(new_values, indices)
        else:
            indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
            dof_types = self.get_dof_types()
            joint_indices = self._backend_utils.resolve_indices(joint_indices, self.num_dof, self._device)
            articulation_read_idx = 0
            indices = self._backend_utils.to_list(indices)
            joint_indices = self._backend_utils.to_list(joint_indices)
            values = self._backend_utils.to_list(values)
            for i in indices:
                dof_read_idx = 0
                for dof_index in joint_indices:
                    drive_type = (
                        "angular" if dof_types[dof_index] == omni.physics.tensors.DofType.Rotation else "linear"
                    )
                    prim = get_prim_at_path(self._dof_paths[i][dof_index])
                    if prim.HasAPI(UsdPhysics.DriveAPI):
                        drive = UsdPhysics.DriveAPI(prim, drive_type)
                    else:
                        drive = UsdPhysics.DriveAPI.Apply(prim, drive_type)
                    if not drive.GetMaxForceAttr():
                        drive.CreateMaxForceAttr().Set(values[articulation_read_idx][dof_read_idx])
                    else:
                        drive.GetMaxForceAttr().Set(values[articulation_read_idx][dof_read_idx])
                    dof_read_idx += 1
                articulation_read_idx += 1
        return

    def get_max_efforts(
        self,
        indices: Optional[Union[np.ndarray, List, torch.Tensor, wp.array]] = None,
        joint_indices: Optional[Union[np.ndarray, List, torch.Tensor, wp.array]] = None,
        clone: bool = True,
    ) -> Union[np.ndarray, torch.Tensor, wp.indexedarray]:
        """Gets maximum efforts for articulation in the view.

        Args:
            indices (Optional[Union[np.ndarray, List, torch.Tensor, wp.array]], optional): indicies to specify which prims
                                                                                 to query. Shape (M,).
                                                                                 Where M <= size of the encapsulated prims in the view.
                                                                                 Defaults to None (i.e: all prims in the view).
            joint_indices (Optional[Union[np.ndarray, List, torch.Tensor, wp.array]], optional): joint indicies to specify which joints
                                                                                 to query. Shape (K,).
                                                                                 Where K <= num of dofs.
                                                                                 Defaults to None (i.e: all dofs).
            clone (Optional[bool]): True to return a clone of the internal buffer. Otherwise False. Defaults to True.

        Returns:
            Union[np.ndarray, torch.Tensor, wp.indexedarray]: maximum efforts for articulations in the view. shape (M, K).
        """
        if not self._is_initialized:
            carb.log_warn("ArticulationView needs to be initialized.")
            return None
        if not omni.timeline.get_timeline_interface().is_stopped() and self._physics_view is not None:
            indices = self._backend_utils.resolve_indices(indices, self.count, "cpu")
            joint_indices = self._backend_utils.resolve_indices(joint_indices, self.num_dof, "cpu")
            max_efforts = self._physics_view.get_dof_max_forces()
            if clone:
                max_efforts = self._backend_utils.clone_tensor(max_efforts, device="cpu")
            result = self._backend_utils.move_data(
                max_efforts[
                    self._backend_utils.expand_dims(indices, 1) if self._backend != "warp" else indices, joint_indices
                ],
                device=self._device,
            )
            return result
        else:
            indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
            dof_types = self.get_dof_types()
            joint_indices = self._backend_utils.resolve_indices(joint_indices, self.num_dof, self._device)
            max_efforts = np.zeros(shape=(indices.shape[0], joint_indices.shape[0]), dtype="float32")
            indices = self._backend_utils.to_list(indices)
            joint_indices = self._backend_utils.to_list(joint_indices)
            articulation_write_idx = 0
            for i in indices:
                dof_write_idx = 0
                for dof_index in joint_indices:
                    drive_type = (
                        "angular" if dof_types[dof_index] == omni.physics.tensors.DofType.Rotation else "linear"
                    )
                    prim = get_prim_at_path(self._dof_paths[i][dof_index])
                    if prim.HasAPI(UsdPhysics.DriveAPI):
                        drive = UsdPhysics.DriveAPI(prim, drive_type)
                    else:
                        drive = UsdPhysics.DriveAPI.Apply(prim, drive_type)
                    max_efforts[articulation_write_idx][dof_write_idx] = drive.GetMaxForceAttr().Get()
                    dof_write_idx += 1
                articulation_write_idx += 1
            max_efforts = self._backend_utils.convert(max_efforts, dtype="float32", device=self._device, indexed=True)
            return max_efforts

    def set_gains(
        self,
        kps: Optional[Union[np.ndarray, torch.Tensor, wp.array]] = None,
        kds: Optional[Union[np.ndarray, torch.Tensor, wp.array]] = None,
        indices: Optional[Union[np.ndarray, List, torch.Tensor, wp.array]] = None,
        joint_indices: Optional[Union[np.ndarray, List, torch.Tensor, wp.array]] = None,
        save_to_usd: bool = False,
    ) -> None:
        """
        Sets stiffness and damping of articulations in the view.

        Args:
            kps (Optional[Union[np.ndarray, torch.Tensor, wp.array]], optional): stiffness of the drives. shape is (M, K). Defaults to None.
            kds (Optional[Union[np.ndarray, torch.Tensor, wp.array]], optional): damping of the drives. shape is (M, K).. Defaults to None.
            indices (Optional[Union[np.ndarray, List, torch.Tensor, wp.array]], optional): indicies to specify which prims
                                                                                 to manipulate. Shape (M,).
                                                                                 Where M <= size of the encapsulated prims in the view.
                                                                                 Defaults to None (i.e: all prims in the view).
            joint_indices (Optional[Union[np.ndarray, List, torch.Tensor, wp.array]], optional): joint indicies to specify which joints
                                                                                 to manipulate. Shape (K,).
                                                                                 Where K <= num of dofs.
                                                                                 Defaults to None (i.e: all dofs).
            save_to_usd (bool, optional): True to save the gains in the usd. otherwise False.
        """
        if not self._is_initialized:
            carb.log_warn("ArticulationView needs to be initialized.")
            return
        if (
            not omni.timeline.get_timeline_interface().is_stopped()
            and self._physics_view is not None
            and not save_to_usd
        ):
            indices = self._backend_utils.resolve_indices(indices, self.count, device="cpu")
            joint_indices = self._backend_utils.resolve_indices(joint_indices, self.num_dof, device="cpu")
            if kps is None:
                kps = self._physics_view.get_dof_stiffnesses()[
                    self._backend_utils.expand_dims(indices, 1) if self._backend != "warp" else indices, joint_indices
                ]
            else:
                kps = self._backend_utils.move_data(kps, device="cpu")
            if kds is None:
                kds = self._physics_view.get_dof_dampings()[
                    self._backend_utils.expand_dims(indices, 1) if self._backend != "warp" else indices, joint_indices
                ]
            else:
                kds = self._backend_utils.move_data(kds, device="cpu")
            stiffnesses = self._physics_view.get_dof_stiffnesses()
            stiffnesses = self._backend_utils.assign(
                kps,
                stiffnesses,
                [self._backend_utils.expand_dims(indices, 1) if self._backend != "warp" else indices, joint_indices],
            )
            dampings = self._physics_view.get_dof_dampings()
            dampings = self._backend_utils.assign(
                kds,
                dampings,
                [self._backend_utils.expand_dims(indices, 1) if self._backend != "warp" else indices, joint_indices],
            )
            self._physics_view.set_dof_stiffnesses(stiffnesses, indices)
            self._physics_view.set_dof_dampings(dampings, indices)
        else:
            indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
            dof_types = self.get_dof_types()
            joint_indices = self._backend_utils.resolve_indices(joint_indices, self.num_dof, self._device)
            articulation_read_idx = 0
            indices = self._backend_utils.to_list(indices)
            joint_indices = self._backend_utils.to_list(joint_indices)
            if kps is not None:
                kps = self._backend_utils.to_list(kps)
            if kds is not None:
                kds = self._backend_utils.to_list(kds)
            for i in indices:
                dof_read_idx = 0
                for dof_index in joint_indices:
                    drive_type = (
                        "angular" if dof_types[dof_index] == omni.physics.tensors.DofType.Rotation else "linear"
                    )
                    prim = get_prim_at_path(self._dof_paths[i][dof_index])
                    if prim.HasAPI(UsdPhysics.DriveAPI):
                        drive = UsdPhysics.DriveAPI(prim, drive_type)
                    else:
                        drive = UsdPhysics.DriveAPI.Apply(prim, drive_type)
                    if kps is not None:
                        if not drive.GetStiffnessAttr():
                            if kps[articulation_read_idx][dof_read_idx] == 0 or drive_type == "linear":
                                drive.CreateStiffnessAttr(kps[articulation_read_idx][dof_read_idx])
                            else:
                                drive.CreateStiffnessAttr(
                                    1.0
                                    / omni.isaac.core.utils.numpy.rad2deg(
                                        float(1.0 / kps[articulation_read_idx][dof_read_idx])
                                    )
                                )
                        else:
                            if kps[articulation_read_idx][dof_read_idx] == 0 or drive_type == "linear":
                                drive.GetStiffnessAttr().Set(kps[articulation_read_idx][dof_read_idx])
                            else:
                                drive.GetStiffnessAttr().Set(
                                    1.0
                                    / omni.isaac.core.utils.numpy.rad2deg(
                                        float(1.0 / kps[articulation_read_idx][dof_read_idx])
                                    )
                                )
                    if kds is not None:
                        if not drive.GetDampingAttr():
                            if kds[articulation_read_idx][dof_read_idx] == 0 or drive_type == "linear":
                                drive.CreateDampingAttr(kds[articulation_read_idx][dof_read_idx])
                            else:
                                drive.CreateDampingAttr(
                                    1.0
                                    / omni.isaac.core.utils.numpy.rad2deg(
                                        float(1.0 / kds[articulation_read_idx][dof_read_idx])
                                    )
                                )
                        else:
                            if kds[articulation_read_idx][dof_read_idx] == 0 or drive_type == "linear":
                                drive.GetDampingAttr().Set(kds[articulation_read_idx][dof_read_idx])
                            else:
                                drive.GetDampingAttr().Set(
                                    1.0
                                    / omni.isaac.core.utils.numpy.rad2deg(
                                        float(1.0 / kds[articulation_read_idx][dof_read_idx])
                                    )
                                )
                    dof_read_idx += 1
                articulation_read_idx += 1
        self._default_kps, self._default_kds = self.get_gains(clone=True)
        return

    def get_gains(
        self,
        indices: Optional[Union[np.ndarray, List, torch.Tensor, wp.array]] = None,
        joint_indices: Optional[Union[np.ndarray, List, torch.Tensor, wp.array]] = None,
        clone: bool = True,
    ) -> Tuple[Union[np.ndarray, torch.Tensor], Union[np.ndarray, torch.Tensor], Union[wp.indexedarray, wp.index]]:
        """
        Gets stiffness and damping of articulations in the view.

        Args:
            indices (Optional[Union[np.ndarray, List, torch.Tensor, wp.array]], optional): indicies to specify which prims
                                                                                 to query. Shape (M,).
                                                                                 Where M <= size of the encapsulated prims in the view.
                                                                                 Defaults to None (i.e: all prims in the view).
            joint_indices (Optional[Union[np.ndarray, List, torch.Tensor, wp.array]], optional): joint indicies to specify which joints
                                                                                 to query. Shape (K,).
                                                                                 Where K <= num of dofs.
                                                                                 Defaults to None (i.e: all dofs).
            clone (bool, optional): True to return clones of the internal buffers. Otherwise False. Defaults to True.

        Returns:
            Tuple[Union[np.ndarray, torch.Tensor], Union[np.ndarray, torch.Tensor], Union[wp.indexedarray, wp.index]]: stiffness and damping of
                                                             articulations in the view respectively. shapes are (M, K).
        """
        if not self._is_initialized:
            carb.log_warn("ArticulationView needs to be initialized.")
            return None
        if not omni.timeline.get_timeline_interface().is_stopped() and self._physics_view is not None:
            indices = self._backend_utils.resolve_indices(indices, self.count, device=self._device)
            joint_indices = self._backend_utils.resolve_indices(joint_indices, self.num_dof, device=self._device)
            kps = self._physics_view.get_dof_stiffnesses()
            kds = self._physics_view.get_dof_dampings()
            kps = self._backend_utils.move_data(kps, device=self._device)
            kds = self._backend_utils.move_data(kds, device=self._device)
            if clone:
                kps = self._backend_utils.clone_tensor(kps, device=self._device)
                kds = self._backend_utils.clone_tensor(kds, device=self._device)
            result_kps = kps[
                self._backend_utils.expand_dims(indices, 1) if self._backend != "warp" else indices, joint_indices
            ]
            result_kds = kds[
                self._backend_utils.expand_dims(indices, 1) if self._backend != "warp" else indices, joint_indices
            ]
            return result_kps, result_kds
        else:
            indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
            dof_types = self.get_dof_types()
            joint_indices = self._backend_utils.resolve_indices(joint_indices, self.num_dof, self._device)
            kps = np.zeros(shape=[indices.shape[0], joint_indices.shape[0]], dtype="float32")
            kds = np.zeros(shape=[indices.shape[0], joint_indices.shape[0]], dtype="float32")
            indices = self._backend_utils.to_list(indices)
            joint_indices = self._backend_utils.to_list(joint_indices)
            articulation_write_idx = 0
            for i in indices:
                dof_write_idx = 0
                for dof_index in joint_indices:
                    drive_type = (
                        "angular" if dof_types[dof_index] == omni.physics.tensors.DofType.Rotation else "linear"
                    )
                    prim = get_prim_at_path(self._dof_paths[i][dof_index])
                    if prim.HasAPI(UsdPhysics.DriveAPI):
                        drive = UsdPhysics.DriveAPI(prim, drive_type)
                    else:
                        drive = UsdPhysics.DriveAPI.Apply(prim, drive_type)
                    if drive.GetStiffnessAttr().Get() == 0.0 or drive_type == "linear":
                        kps[articulation_write_idx][dof_write_idx] = drive.GetStiffnessAttr().Get()
                    else:
                        kps[articulation_write_idx][dof_write_idx] = 1.0 / omni.isaac.core.utils.numpy.deg2rad(
                            float(1.0 / drive.GetStiffnessAttr().Get())
                        )
                    if drive.GetDampingAttr().Get() == 0.0 or drive_type == "linear":
                        kds[articulation_write_idx][dof_write_idx] = drive.GetDampingAttr().Get()
                    else:
                        kds[articulation_write_idx][dof_write_idx] = 1.0 / omni.isaac.core.utils.numpy.deg2rad(
                            float(1.0 / drive.GetDampingAttr().Get())
                        )
                    dof_write_idx += 1
                articulation_write_idx += 1
            result_kps = self._backend_utils.convert(kps, dtype="float32", device=self._device, indexed=True)
            result_kds = self._backend_utils.convert(kds, dtype="float32", device=self._device, indexed=True)
            return result_kps, result_kds

    def switch_control_mode(
        self,
        mode: str,
        indices: Optional[Union[np.ndarray, List, torch.Tensor, wp.array]] = None,
        joint_indices: Optional[Union[np.ndarray, List, torch.Tensor, wp.array]] = None,
    ) -> None:
        """Switches control mode between velocity, position or effort.

        Args:
            mode (str): control mode to switch the articulations specified to. mode can be velocity, position or effort.
            indices (Optional[Union[np.ndarray, List, torch.Tensor, wp.array]], optional): indicies to specify which prims
                                                                                 to manipulate. Shape (M,).
                                                                                 Where M <= size of the encapsulated prims in the view.
                                                                                 Defaults to None (i.e: all prims in the view).
            joint_indices (Optional[Union[np.ndarray, List, torch.Tensor, wp.array]], optional): joint indicies to specify which joints
                                                                                 to manipulate. Shape (K,).
                                                                                 Where K <= num of dofs.
                                                                                 Defaults to None (i.e: all dofs).
        """
        if not self._is_initialized:
            carb.log_warn("ArticulationView needs to be initialized.")
            return
        indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
        joint_indices = self._backend_utils.resolve_indices(joint_indices, self.num_dof, self._device)
        if mode == "velocity":
            self.set_gains(
                kps=self._backend_utils.create_zeros_tensor(
                    shape=[indices.shape[0], joint_indices.shape[0]], dtype="float32", device=self._device
                ),
                kds=self._default_kds[indices][:, joint_indices]
                if self._backend != "warp"
                else self._default_kps.data[indices, joint_indices],
                indices=indices,
                joint_indices=joint_indices,
            )
        elif mode == "position":
            self.set_gains(
                kps=self._default_kps[indices][:, joint_indices]
                if self._backend != "warp"
                else self._default_kps.data[indices, joint_indices],
                kds=self._default_kds[indices][:, joint_indices]
                if self._backend != "warp"
                else self._default_kds.data[indices, joint_indices],
                indices=indices,
                joint_indices=joint_indices,
            )
        elif mode == "effort":
            self.set_gains(
                kps=self._backend_utils.create_zeros_tensor(
                    shape=[indices.shape[0], joint_indices.shape[0]], dtype="float32", device=self._device
                ),
                kds=self._backend_utils.create_zeros_tensor(
                    shape=[indices.shape[0], joint_indices.shape[0]], dtype="float32", device=self._device
                ),
                indices=indices,
                joint_indices=joint_indices,
            )
        return

    def switch_dof_control_mode(
        self, mode: str, dof_index: int, indices: Optional[Union[np.ndarray, List, torch.Tensor, wp.array]] = None
    ) -> None:
        """Switches dof control mode between velocity, position or effort.

        Args:
            mode (str): control mode to switch the dof in articulations specified to. mode an be velocity, position or effort.
            dof_index (int): dof index to swith the control mode of.
            indices (Optional[Union[np.ndarray, List, torch.Tensor, wp.array]], optional): indicies to specify which prims
                                                                                 to manipulate. Shape (M,).
                                                                                 Where M <= size of the encapsulated prims in the view.
                                                                                 Defaults to None (i.e: all prims in the view).
        """
        if not self._is_initialized:
            carb.log_warn("ArticulationView needs to be initialized.")
            return
        indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
        if mode == "velocity":
            self.set_gains(
                kps=self._backend_utils.create_zeros_tensor(
                    shape=[indices.shape[0], 1], dtype="float32", device=self._device
                ),
                kds=self._backend_utils.expand_dims(self._default_kds[indices, dof_index], 1)
                if self._backend != "warp"
                else self._default_kds.data[
                    indices, wp.array([dof_index], dtype=wp.int32, device=self._default_kds.device)
                ],
                indices=indices,
                joint_indices=[dof_index],
            )
        elif mode == "position":
            self.set_gains(
                kps=self._backend_utils.expand_dims(self._default_kps[indices, dof_index], 1)
                if self._backend != "warp"
                else self._default_kps.data[
                    indices, wp.array(dof_index, dtype=wp.int32, device=self._default_kds.device)
                ],
                kds=self._backend_utils.expand_dims(self._default_kds[indices, dof_index], 1)
                if self._backend != "warp"
                else self._default_kds.data[
                    indices, wp.array([dof_index], dtype=wp.int32, device=self._default_kds.device)
                ],
                indices=indices,
                joint_indices=[dof_index],
            )
        elif mode == "effort":
            self.set_gains(
                kps=self._backend_utils.create_zeros_tensor(
                    shape=[indices.shape[0], 1], dtype="float32", device=self._device
                ),
                kds=self._backend_utils.create_zeros_tensor(
                    shape=[indices.shape[0], 1], dtype="float32", device=self._device
                ),
                indices=indices,
                joint_indices=[dof_index],
            )
        return

    def set_solver_position_iteration_counts(
        self,
        counts: Union[np.ndarray, torch.Tensor, wp.array],
        indices: Optional[Union[np.ndarray, List, torch.Tensor, wp.array]] = None,
    ) -> None:
        """
        Sets the physics solver itertion counts for joint positions.

        Args:
            counts (Union[np.ndarray, torch.Tensor, wp.array]): number of iterations for the solver. Shape (M,).
            indices (Optional[Union[np.ndarray, List, torch.Tensor, wp.array]], optional): indicies to specify which prims
                                                                                 to manipulate. Shape (M,).
                                                                                 Where M <= size of the encapsulated prims in the view.
                                                                                 Defaults to None (i.e: all prims in the view).
        """
        indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
        read_idx = 0
        indices = self._backend_utils.to_list(indices)
        counts = self._backend_utils.to_list(counts)
        for i in indices:
            set_prim_property(self.prim_paths[i], "physxArticulation:solverPositionIterationCount", counts[read_idx])
            read_idx += 1
        return

    def get_solver_position_iteration_counts(
        self, indices: Optional[Union[np.ndarray, List, torch.Tensor, wp.array]] = None
    ) -> Union[np.ndarray, torch.Tensor, wp.indexedarray]:
        """Gets the physics solver itertion counts for joint positions.

        Args:
            indices (Optional[Union[np.ndarray, List, torch.Tensor, wp.array]], optional): indicies to specify which prims
                                                                                 to query. Shape (M,).
                                                                                 Where M <= size of the encapsulated prims in the view.
                                                                                 Defaults to None (i.e: all prims in the view).

        Returns:
            Union[np.ndarray, torch.Tensor, wp.indexedarray]: number of iterations for the solver. Shape (M,).
        """
        indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
        result = np.zeros(shape=indices.shape[0], dtype="int32")
        write_idx = 0
        indices = self._backend_utils.to_list(indices)
        for i in indices:
            result[write_idx] = get_prim_property(self.prim_paths[i], "physxArticulation:solverPositionIterationCount")
            write_idx += 1
        result = self._backend_utils.convert(result, device=self._device, dtype="int32", indexed=True)
        return result

    def set_solver_velocity_iteration_counts(
        self,
        counts: Union[np.ndarray, torch.Tensor, wp.array],
        indices: Optional[Union[np.ndarray, List, torch.Tensor, wp.array]] = None,
    ) -> None:
        """
        Sets the physics solver itertion counts for joint velocities.

        Args:
            counts (Union[np.ndarray, torch.Tensor, wp.array]): number of iterations for the solver. Shape (M,).
            indices (Optional[Union[np.ndarray, List, torch.Tensor, wp.array]], optional): indicies to specify which prims
                                                                                 to manipulate. Shape (M,).
                                                                                 Where M <= size of the encapsulated prims in the view.
                                                                                 Defaults to None (i.e: all prims in the view).
        """
        indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
        read_idx = 0
        indices = self._backend_utils.to_list(indices)
        counts = self._backend_utils.to_list(counts)
        for i in indices:
            set_prim_property(self.prim_paths[i], "physxArticulation:solverVelocityIterationCount", counts[read_idx])
            read_idx += 1
        return

    def get_solver_velocity_iteration_counts(
        self, indices: Optional[Union[np.ndarray, List, torch.Tensor, wp.array]] = None
    ) -> Union[np.ndarray, torch.Tensor, wp.indexedarray]:
        """
        Gets the physics solver itertion counts for joint velocities.

        Args:
            indices (Optional[Union[np.ndarray, List, torch.Tensor, wp.array]], optional): indicies to specify which prims
                                                                                 to query. Shape (M,).
                                                                                 Where M <= size of the encapsulated prims in the view.
                                                                                 Defaults to None (i.e: all prims in the view).

        Returns:
            Union[np.ndarray, torch.Tensor, wp.indexedarray]: number of iterations for the solver. Shape (M,).
        """
        indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
        result = np.zeros(shape=indices.shape[0], dtype="int32")
        write_idx = 0
        indices = self._backend_utils.to_list(indices)
        for i in indices:
            result[write_idx] = get_prim_property(self.prim_paths[i], "physxArticulation:solverVelocityIterationCount")
            write_idx += 1
        result = self._backend_utils.convert(result, device=self._device, dtype="int32", indexed=True)
        return result

    def set_stabilization_thresholds(
        self,
        thresholds: Union[np.ndarray, torch.Tensor, wp.array],
        indices: Optional[Union[np.ndarray, List, torch.Tensor, wp.array]] = None,
    ) -> None:
        """Sets the stabilizaion thresholds.

        Args:
            thresholds (Union[np.ndarray, torch.Tensor, wp.array]): stabilization thresholds to be applied. Shape (M,).
            indices (Optional[Union[np.ndarray, List, torch.Tensor, wp.array]], optional): indicies to specify which prims
                                                                                 to manipulate. Shape (M,).
                                                                                 Where M <= size of the encapsulated prims in the view.
                                                                                 Defaults to None (i.e: all prims in the view).
        """
        indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
        read_idx = 0
        indices = self._backend_utils.to_list(indices)
        thresholds = self._backend_utils.to_list(thresholds)
        for i in indices:
            set_prim_property(self.prim_paths[i], "physxArticulation:stabilizationThreshold", thresholds[read_idx])
            read_idx += 1
        return

    def get_stabilization_thresholds(
        self, indices: Optional[Union[np.ndarray, List, torch.Tensor, wp.array]] = None
    ) -> Union[np.ndarray, torch.Tensor, wp.indexedarray]:
        """Gets the stabilizaion thresholds.

        Args:
            indices (Optional[Union[np.ndarray, List, torch.Tensor, wp.array]], optional): indicies to specify which prims
                                                                                 to query. Shape (M,).
                                                                                 Where M <= size of the encapsulated prims in the view.
                                                                                 Defaults to None (i.e: all prims in the view).

        Returns:
            Union[np.ndarray, torch.Tensor, wp.indexedarray]: current stabilization thresholds. Shape (M,).
        """
        indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
        result = np.zeros(shape=indices.shape[0], dtype="float32")
        write_idx = 0
        indices = self._backend_utils.to_list(indices)
        for i in indices:
            result[write_idx] = get_prim_property(self.prim_paths[i], "physxArticulation:stabilizationThreshold")
            write_idx += 1
        result = self._backend_utils.convert(result, dtype="float32", device=self._device, indexed=True)
        return result

    def set_enabled_self_collisions(
        self,
        flags: Union[np.ndarray, torch.Tensor, wp.array],
        indices: Optional[Union[np.ndarray, List, torch.Tensor, wp.array]] = None,
    ) -> None:
        """Sets the enable self collisions flag

        Args:
            flags (Union[np.ndarray, torch.Tensor, wp.array]): true to enable self collision. otherwise false. shape (M,)
            indices (Optional[Union[np.ndarray, List, torch.Tensor, wp.array]], optional): indicies to specify which prims
                                                                                 to manipulate. Shape (M,).
                                                                                 Where M <= size of the encapsulated prims in the view.
                                                                                 Defaults to None (i.e: all prims in the view).
        """
        indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
        read_idx = 0
        indices = self._backend_utils.to_list(indices)
        flags = self._backend_utils.to_list(flags)
        for i in indices:
            set_prim_property(self.prim_paths[i], "physxArticulation:enabledSelfCollisions", flags[read_idx])
            read_idx += 1
        return

    def get_enabled_self_collisions(
        self, indices: Optional[Union[np.ndarray, List, torch.Tensor, wp.array]] = None
    ) -> Union[np.ndarray, torch.Tensor, wp.indexedarray]:
        """
        Gets the enable self collisions flag

        Args:
            indices (Optional[Union[np.ndarray, List, torch.Tensor, wp.array]], optional): indicies to specify which prims
                                                                                 to query. Shape (M,).
                                                                                 Where M <= size of the encapsulated prims in the view.
                                                                                 Defaults to None (i.e: all prims in the view).

        Returns:
            Union[np.ndarray, torch.Tensor, wp.indexedarray]: true if self collisions enabled. otherwise false. shape (M,)
        """
        indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
        result = np.zeros(shape=indices.shape[0], dtype="bool")
        write_idx = 0
        indices = self._backend_utils.to_list(indices)
        for i in indices:
            result[write_idx] = get_prim_property(self.prim_paths[i], "physxArticulation:enabledSelfCollisions")
            write_idx += 1
        result = self._backend_utils.convert(result, device=self._device, dtype="uint8", indexed=True)
        return result

    def set_sleep_thresholds(
        self,
        thresholds: Union[np.ndarray, torch.Tensor, wp.array],
        indices: Optional[Union[np.ndarray, List, torch.Tensor, wp.array]] = None,
    ) -> None:
        """Sets sleep thresholds for articulations in the view.

        Args:
            thresholds (Union[np.ndarray, torch.Tensor, wp.array]): sleep thresholds to be applied. shape (M,).
            indices (Optional[Union[np.ndarray, List, torch.Tensor, wp.array]], optional): indicies to specify which prims
                                                                                 to manipulate. Shape (M,).
                                                                                 Where M <= size of the encapsulated prims in the view.
                                                                                 Defaults to None (i.e: all prims in the view).
        """
        indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
        read_idx = 0
        indices = self._backend_utils.to_list(indices)
        thresholds = self._backend_utils.to_list(thresholds)
        for i in indices:
            set_prim_property(self.prim_paths[i], "physxArticulation:sleepThreshold", thresholds[read_idx])
            read_idx += 1
        return

    def get_sleep_thresholds(
        self, indices: Optional[Union[np.ndarray, List, torch.Tensor, wp.array]] = None
    ) -> Union[np.ndarray, torch.Tensor, wp.indexedarray]:
        """Gets sleep thresholds for articulations in the view.

        Args:
            indices (Optional[Union[np.ndarray, List, torch.Tensor, wp.array]], optional): indicies to specify which prims
                                                                                 to query. Shape (M,).
                                                                                 Where M <= size of the encapsulated prims in the view.
                                                                                 Defaults to None (i.e: all prims in the view).

        Returns:
            Union[np.ndarray, torch.Tensor, wp.indexedarray]: current sleep thresholds. shape (M,).
        """
        indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
        result = np.zeros(shape=indices.shape[0], dtype="float32")
        write_idx = 0
        indices = self._backend_utils.to_list(indices)
        for i in indices:
            result[write_idx] = get_prim_property(self.prim_paths[i], "physxArticulation:sleepThreshold")
            write_idx += 1
        result = self._backend_utils.convert(result, dtype="float32", device=self._device, indexed=True)
        return result

    def get_jacobian_shape(self) -> Union[np.ndarray, torch.Tensor, wp.array]:
        """
        Returns:
            Union[np.ndarray, torch.Tensor, wp.array]: shape of jacobian for a single articulation.
        """
        if not self._is_initialized:
            carb.log_warn("ArticulationView needs to be initialized.")
            return None
        shape = self._physics_view.jacobian_shape
        return (shape[0] // 6, 6, shape[1])

    def get_mass_matrix_shape(self) -> Union[np.ndarray, torch.Tensor, wp.array]:
        """
        Returns:
            Union[np.ndarray, torch.Tensor, wp.array]: shape of mass matrix for a single articulation.
        """
        if not self._is_initialized:
            carb.log_warn("ArticulationView needs to be initialized.")
            return None
        return self._physics_view.mass_matrix_shape

    def get_jacobians(
        self, indices: Optional[Union[np.ndarray, List, torch.Tensor, wp.array]] = None, clone: bool = True
    ) -> Union[np.ndarray, torch.Tensor, wp.indexedarray]:
        """Gets the jacobians of articulations in the view.

        Args:
            indices (Optional[Union[np.ndarray, List, torch.Tensor, wp.array]], optional): indicies to specify which prims
                                                                                 to query. Shape (M,).
                                                                                 Where M <= size of the encapsulated prims in the view.
                                                                                 Defaults to None (i.e: all prims in the view).
            clone (bool, optional): True to return a clone of the internal buffer. Otherwise False. Defaults to True.

        Returns:
            Union[np.ndarray, torch.Tensor, wp.indexedarray]: jacobians of articulations in the view.
                                                    shape is (M, jacobian_shape).
        """
        if not self._is_initialized:
            carb.log_warn("ArticulationView needs to be initialized.")
            return None
        if not omni.timeline.get_timeline_interface().is_stopped() and self._physics_view is not None:
            indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
            current_values = self._physics_view.get_jacobians()
            if clone:
                current_values = self._backend_utils.clone_tensor(current_values, device=self._device)
            result = current_values[indices]
            return result
        else:
            carb.log_warn("Physics Simulation View is not created yet in order to use get_jacobians")
            return None

    def get_mass_matrices(
        self, indices: Optional[Union[np.ndarray, List, torch.Tensor, wp.array]] = None, clone: bool = True
    ) -> Union[np.ndarray, torch.Tensor, wp.indexedarray]:
        """Gets the mass matrices of articulations in the view.

        Args:
            indices (Optional[Union[np.ndarray, List, torch.Tensor, wp.array]], optional): indicies to specify which prims
                                                                                 to query. Shape (M,).
                                                                                 Where M <= size of the encapsulated prims in the view.
                                                                                 Defaults to None (i.e: all prims in the view).
            clone (bool, optional): True to return a clone of the internal buffer. Otherwise False. Defaults to True.

        Returns:
            Union[np.ndarray, torch.Tensor, wp.indexedarray]: mass matrices of articulations in the view.
                                                    shape is (M, mass_matrix_shape).
        """
        if not self._is_initialized:
            carb.log_warn("ArticulationView needs to be initialized.")
            return None
        if not omni.timeline.get_timeline_interface().is_stopped() and self._physics_view is not None:
            indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
            current_values = self._physics_view.get_mass_matrices()
            if clone:
                current_values = self._backend_utils.clone_tensor(current_values, device=self._device)
            result = current_values[indices]
            return result
        else:
            carb.log_warn("Physics Simulation View is not created yet in order to use get_mass_matrices")
            return None

    def get_coriolis_and_centrifugal_forces(
        self,
        indices: Optional[Union[np.ndarray, List, torch.Tensor, wp.array]] = None,
        joint_indices: Optional[Union[np.ndarray, List, torch.Tensor, wp.array]] = None,
        clone: bool = True,
    ) -> Union[np.ndarray, torch.Tensor, wp.indexedarray]:
        """Gets the coriolis and centrifugal forces of articulations in the view.

        Args:
            indices (Optional[Union[np.ndarray, List, torch.Tensor, wp.array]], optional): indicies to specify which prims
                                                                                 to query. Shape (M,).
                                                                                 Where M <= size of the encapsulated prims in the view.
                                                                                 Defaults to None (i.e: all prims in the view).
            joint_indices (Optional[Union[np.ndarray, List, torch.Tensor, wp.array]], optional): joint indicies to specify which joints
                                                                                 to query. Shape (K,).
                                                                                 Where K <= num of dofs.
                                                                                 Defaults to None (i.e: all dofs).
            clone (bool, optional): True to return a clone of the internal buffer. Otherwise False. Defaults to True.

        Returns:
            Union[np.ndarray, torch.Tensor, wp.indexedarray]: Coriolis and centrifugal forces of articulations in the view.
                                                    shape is (M, K).
        """
        if not self._is_initialized:
            carb.log_warn("ArticulationView needs to be initialized.")
            return None
        if not omni.timeline.get_timeline_interface().is_stopped() and self._physics_view is not None:
            indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
            joint_indices = self._backend_utils.resolve_indices(joint_indices, self.num_dof, self._device)
            current_values = self._physics_view.get_coriolis_and_centrifugal_forces()
            if clone:
                current_values = self._backend_utils.clone_tensor(current_values, device=self._device)
            result = current_values[
                self._backend_utils.expand_dims(indices, 1) if self._backend != "warp" else indices, joint_indices
            ]
            return result
        else:
            carb.log_warn(
                "Physics Simulation View is not created yet in order to use get_coriolis_and_centrifugal_forces"
            )
            return None

    def get_generalized_gravity_forces(
        self,
        indices: Optional[Union[np.ndarray, List, torch.Tensor, wp.array]] = None,
        joint_indices: Optional[Union[np.ndarray, List, torch.Tensor, wp.array]] = None,
        clone: bool = True,
    ) -> Union[np.ndarray, torch.Tensor, wp.indexedarray]:
        """Gets the generalized gravity forces of articulations in the view.

        Args:
            indices (Optional[Union[np.ndarray, List, torch.Tensor, wp.array]], optional): indicies to specify which prims
                                                                                 to query. Shape (M,).
                                                                                 Where M <= size of the encapsulated prims in the view.
                                                                                 Defaults to None (i.e: all prims in the view).
            joint_indices (Optional[Union[np.ndarray, List, torch.Tensor, wp.array]], optional): joint indicies to specify which joints
                                                                                 to query. Shape (K,).
                                                                                 Where K <= num of dofs.
                                                                                 Defaults to None (i.e: all dofs).
            clone (bool, optional): True to return a clone of the internal buffer. Otherwise False. Defaults to True.

        Returns:
            Union[np.ndarray, torch.Tensor, wp.indexedarray]: generalized gravity forces of articulations in the view.
                                                    shape is (M, K).
        """
        if not self._is_initialized:
            carb.log_warn("ArticulationView needs to be initialized.")
            return None
        if not omni.timeline.get_timeline_interface().is_stopped() and self._physics_view is not None:
            indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
            joint_indices = self._backend_utils.resolve_indices(joint_indices, self.num_dof, self._device)
            current_values = self._physics_view.get_generalized_gravity_forces()
            if clone:
                current_values = self._backend_utils.clone_tensor(current_values, device=self._device)
            result = current_values[
                self._backend_utils.expand_dims(indices, 1) if self._backend != "warp" else indices, joint_indices
            ]
            return result
        else:
            carb.log_warn("Physics Simulation View is not created yet in order to use get_generalized_gravity_forces")
            return None

    def get_body_masses(
        self,
        indices: Optional[Union[np.ndarray, List, torch.Tensor, wp.array]] = None,
        body_indices: Optional[Union[np.ndarray, List, torch.Tensor, wp.array]] = None,
        clone: bool = True,
    ) -> Union[np.ndarray, torch.Tensor, wp.indexedarray]:
        """Gets rigid body masses of articulations in the view.

        Args:
            indices (Optional[Union[np.ndarray, List, torch.Tensor, wp.array]], optional): indicies to specify which prims
                                                                                 to query. Shape (M,).
                                                                                 Where M <= size of the encapsulated prims in the view.
                                                                                 Defaults to None (i.e: all prims in the view).
            body_indices (Optional[Union[np.ndarray, List, torch.Tensor, wp.array]], optional): body indicies to specify which bodies
                                                                                 to query. Shape (K,).
                                                                                 Where K <= num of bodies.
                                                                                 Defaults to None (i.e: all bodies).
            clone (bool, optional): True to return a clone of the internal buffer. Otherwise False. Defaults to True.

        Returns:
            Union[np.ndarray, torch.Tensor, wp.indexedarray]: rigid body masses of articulations in the view.
                                                    shape is (M, K).
        """
        if not self._is_initialized:
            carb.log_warn("ArticulationView needs to be initialized.")
            return None
        if not omni.timeline.get_timeline_interface().is_stopped() and self._physics_view is not None:
            indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
            body_indices = self._backend_utils.resolve_indices(body_indices, self.num_bodies, self._device)
            current_values = self._backend_utils.move_data(self._physics_view.get_masses(), self._device)
            if clone:
                current_values = self._backend_utils.clone_tensor(current_values, device=self._device)
            result = current_values[
                self._backend_utils.expand_dims(indices, 1) if self._backend != "warp" else indices, body_indices
            ]
            return result
        else:
            carb.log_warn("Physics Simulation View is not created yet in order to use get_body_masses")
            return None

    def get_body_inv_masses(
        self,
        indices: Optional[Union[np.ndarray, List, torch.Tensor, wp.array]] = None,
        body_indices: Optional[Union[np.ndarray, List, torch.Tensor, wp.array]] = None,
        clone: bool = True,
    ) -> Union[np.ndarray, torch.Tensor, wp.indexedarray]:
        """Gets rigid body inverse masses of articulations in the view.

        Args:
            indices (Optional[Union[np.ndarray, List, torch.Tensor, wp.array]], optional): indicies to specify which prims
                                                                                 to query. Shape (M,).
                                                                                 Where M <= size of the encapsulated prims in the view.
                                                                                 Defaults to None (i.e: all prims in the view).
            body_indices (Optional[Union[np.ndarray, List, torch.Tensor, wp.array]], optional): body indicies to specify which bodies
                                                                                 to query. Shape (K,).
                                                                                 Where K <= num of bodies.
                                                                                 Defaults to None (i.e: all bodies).
            clone (bool, optional): True to return a clone of the internal buffer. Otherwise False. Defaults to True.

        Returns:
            Union[np.ndarray, torch.Tensor, wp.indexedarray]: rigid body inverse masses of articulations in the view.
                                                    shape is (M, K).
        """
        if not self._is_initialized:
            carb.log_warn("ArticulationView needs to be initialized.")
            return None
        if not omni.timeline.get_timeline_interface().is_stopped() and self._physics_view is not None:
            indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
            body_indices = self._backend_utils.resolve_indices(body_indices, self._num_bodies, self._device)
            current_values = self._backend_utils.move_data(self._physics_view.get_inv_masses(), self._device)
            if clone:
                current_values = self._backend_utils.clone_tensor(current_values, device=self._device)
            result = current_values[
                self._backend_utils.expand_dims(indices, 1) if self._backend != "warp" else indices, body_indices
            ]
            return result
        else:
            carb.log_warn("Physics Simulation View is not created yet in order to use get_body_inv_masses")
            return None

    def get_body_coms(
        self,
        indices: Optional[Union[np.ndarray, List, torch.Tensor, wp.array]] = None,
        body_indices: Optional[Union[np.ndarray, List, torch.Tensor, wp.array]] = None,
        clone: bool = True,
    ) -> Union[np.ndarray, torch.Tensor, wp.indexedarray]:
        """Gets rigid body center of mass of articulations in the view.

        Args:
            indices (Optional[Union[np.ndarray, List, torch.Tensor, wp.array]], optional): indicies to specify which prims
                                                                                 to query. Shape (M,).
                                                                                 Where M <= size of the encapsulated prims in the view.
                                                                                 Defaults to None (i.e: all prims in the view).
            body_indices (Optional[Union[np.ndarray, List, torch.Tensor, wp.array]], optional): body indicies to specify which bodies
                                                                                 to query. Shape (K,).
                                                                                 Where K <= num of bodies.
                                                                                 Defaults to None (i.e: all bodies).
            clone (bool, optional): True to return a clone of the internal buffer. Otherwise False. Defaults to True.

        Returns:
            Union[np.ndarray, torch.Tensor, wp.indexedarray]: rigid body center of mass positions and orientations of articulations in the view.
                                                    position shape is (M, K, 3), orientation shape is (M, k, 4).
        """
        if not self._is_initialized:
            carb.log_warn("ArticulationView needs to be initialized.")
            return None
        if not omni.timeline.get_timeline_interface().is_stopped() and self._physics_view is not None:
            indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
            body_indices = self._backend_utils.resolve_indices(body_indices, self._num_bodies, self._device)
            current_values = self._backend_utils.move_data(
                self._physics_view.get_coms().reshape((self.count, self.num_bodies, 7)), self._device
            )
            if clone:
                current_values = self._backend_utils.clone_tensor(current_values, device=self._device)
            positions = current_values[
                self._backend_utils.expand_dims(indices, 1) if self._backend != "warp" else indices, body_indices, 0:3
            ]
            orientations = self._backend_utils.xyzw2wxyz(
                current_values[
                    self._backend_utils.expand_dims(indices, 1) if self._backend != "warp" else indices,
                    body_indices,
                    3:7,
                ]
            )
            return positions, orientations
        else:
            carb.log_warn("Physics Simulation View is not created yet in order to use get_body_coms")
            return None

    def get_body_inertias(
        self,
        indices: Optional[Union[np.ndarray, List, torch.Tensor, wp.array]] = None,
        body_indices: Optional[Union[np.ndarray, List, torch.Tensor, wp.array]] = None,
        clone: bool = True,
    ) -> Union[np.ndarray, torch.Tensor, wp.indexedarray]:
        """Gets rigid body inertias of articulations in the view.

        Args:
            indices (Optional[Union[np.ndarray, List, torch.Tensor, wp.array]], optional): indicies to specify which prims
                                                                                 to query. Shape (M,).
                                                                                 Where M <= size of the encapsulated prims in the view.
                                                                                 Defaults to None (i.e: all prims in the view).
            body_indices (Optional[Union[np.ndarray, List, torch.Tensor, wp.array]], optional): body indicies to specify which bodies
                                                                                 to query. Shape (K,).
                                                                                 Where K <= num of bodies.
                                                                                 Defaults to None (i.e: all bodies).
            clone (bool, optional): True to return a clone of the internal buffer. Otherwise False. Defaults to True.

        Returns:
            Union[np.ndarray, torch.Tensor, wp.indexedarray]: rigid body inertias of articulations in the view.
                                                    shape is (M, K, 9).
        """
        if not self._is_initialized:
            carb.log_warn("ArticulationView needs to be initialized.")
            return None
        if not omni.timeline.get_timeline_interface().is_stopped() and self._physics_view is not None:
            indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
            body_indices = self._backend_utils.resolve_indices(body_indices, self.num_bodies, self._device)
            current_values = self._backend_utils.move_data(
                self._physics_view.get_inertias().reshape((self.count, self.num_bodies, 9)), self._device
            )
            if clone:
                current_values = self._backend_utils.clone_tensor(current_values, device=self._device)
            result = current_values[
                self._backend_utils.expand_dims(indices, 1) if self._backend != "warp" else indices, body_indices
            ]
            return result
        else:
            carb.log_warn("Physics Simulation View is not created yet in order to use get_body_inertias")
            return None

    def get_body_inv_inertias(
        self,
        indices: Optional[Union[np.ndarray, List, torch.Tensor, wp.array]] = None,
        body_indices: Optional[Union[np.ndarray, List, torch.Tensor, wp.array]] = None,
        clone: bool = True,
    ) -> Union[np.ndarray, torch.Tensor, wp.indexedarray]:
        """Gets rigid body inverse inertias of articulations in the view.

        Args:
            indices (Optional[Union[np.ndarray, List, torch.Tensor, wp.array]], optional): indicies to specify which prims
                                                                                 to query. Shape (M,).
                                                                                 Where M <= size of the encapsulated prims in the view.
                                                                                 Defaults to None (i.e: all prims in the view).
            body_indices (Optional[Union[np.ndarray, List, torch.Tensor, wp.array]], optional): body indicies to specify which bodies
                                                                                 to query. Shape (K,).
                                                                                 Where K <= num of bodies.
                                                                                 Defaults to None (i.e: all bodies).
            clone (bool, optional): True to return a clone of the internal buffer. Otherwise False. Defaults to True.

        Returns:
            Union[np.ndarray, torch.Tensor, wp.indexedarray]: rigid body inverse inertias of articulations in the view.
                                                    shape is (M, K, 9).
        """
        if not self._is_initialized:
            carb.log_warn("ArticulationView needs to be initialized.")
            return None
        if not omni.timeline.get_timeline_interface().is_stopped() and self._physics_view is not None:
            indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
            body_indices = self._backend_utils.resolve_indices(body_indices, self._num_bodies, self._device)
            current_values = self._backend_utils.move_data(
                self._physics_view.get_inv_inertias().reshape((self.count, self.num_bodies, 9)), self._device
            )
            if clone:
                current_values = self._backend_utils.clone_tensor(current_values, device=self._device)
            result = current_values[
                self._backend_utils.expand_dims(indices, 1) if self._backend != "warp" else indices, body_indices
            ]
            return result
        else:
            carb.log_warn("Physics Simulation View is not created yet in order to use get_body_inv_inertias")
            return None

    def set_body_masses(
        self,
        values: Union[np.ndarray, torch.Tensor, wp.array],
        indices: Optional[Union[np.ndarray, List, torch.Tensor, wp.array]] = None,
        body_indices: Optional[Union[np.ndarray, List, torch.Tensor, wp.array]] = None,
    ) -> None:
        """Sets body masses for articulation bodies in the view.

        Args:
            values (Union[np.ndarray, torch.Tensor, wp.array]): body masses for articulations in the view. shape (M, K).
            indices (Optional[Union[np.ndarray, List, torch.Tensor, wp.array]], optional): indicies to specify which prims
                                                                                 to manipulate. Shape (M,).
                                                                                 Where M <= size of the encapsulated prims in the view.
                                                                                 Defaults to None (i.e: all prims in the view).
            body_indices (Optional[Union[np.ndarray, List, torch.Tensor, wp.array]], optional): body indicies to specify which bodies
                                                                                 to manipulate. Shape (K,).
                                                                                 Where K <= num of bodies.
                                                                                 Defaults to None (i.e: all bodies).
        """
        if not self._is_initialized:
            carb.log_warn("ArticulationView needs to be initialized.")
            return

        indices = self._backend_utils.resolve_indices(indices, self.count, "cpu")
        if not omni.timeline.get_timeline_interface().is_stopped() and self._physics_view is not None:
            body_indices = self._backend_utils.resolve_indices(body_indices, self.num_bodies, self._device)
            data = self._backend_utils.clone_tensor(self._physics_view.get_masses(), device="cpu")
            data = self._backend_utils.assign(
                self._backend_utils.move_data(values, device="cpu"),
                data,
                [self._backend_utils.expand_dims(indices, 1) if self._backend != "warp" else indices, body_indices],
            )
            self._physics_view.set_masses(data, indices)
        else:
            carb.log_warn("Physics Simulation View is not created yet in order to use set_body_masses")

    def set_body_inertias(
        self,
        values: Union[np.ndarray, torch.Tensor, wp.array],
        indices: Optional[Union[np.ndarray, List, torch.Tensor, wp.array]] = None,
        body_indices: Optional[Union[np.ndarray, List, torch.Tensor, wp.array]] = None,
    ) -> None:
        """Sets body inertias for articulation bodies in the view.

        Args:
            values (Union[np.ndarray, torch.Tensor, wp.array]): body inertias for articulations in the view. shape (M, K, 9).
            indices (Optional[Union[np.ndarray, List, torch.Tensor, wp.array]], optional): indicies to specify which prims
                                                                                 to manipulate. Shape (M,).
                                                                                 Where M <= size of the encapsulated prims in the view.
                                                                                 Defaults to None (i.e: all prims in the view).
            body_indices (Optional[Union[np.ndarray, List, torch.Tensor, wp.array]], optional): body indicies to specify which bodies
                                                                                 to manipulate. Shape (K,).
                                                                                 Where K <= num of bodies.
                                                                                 Defaults to None (i.e: all bodies).
        """
        if not self._is_initialized:
            carb.log_warn("ArticulationView needs to be initialized.")
            return

        indices = self._backend_utils.resolve_indices(indices, self.count, "cpu")
        if not omni.timeline.get_timeline_interface().is_stopped() and self._physics_view is not None:
            body_indices = self._backend_utils.resolve_indices(body_indices, self.num_bodies, self._device)
            data = self._backend_utils.clone_tensor(self._physics_view.get_inertias(), device="cpu")
            data = self._backend_utils.assign(
                self._backend_utils.move_data(values, device="cpu"),
                data,
                [self._backend_utils.expand_dims(indices, 1) if self._backend != "warp" else indices, body_indices],
            )
            self._physics_view.set_inertias(data, indices)
        else:
            carb.log_warn("Physics Simulation View is not created yet in order to use set_body_inertias")

    def set_body_coms(
        self,
        positions: Union[np.ndarray, torch.Tensor, wp.array] = None,
        orientations: Union[np.ndarray, torch.Tensor, wp.array] = None,
        indices: Optional[Union[np.ndarray, List, torch.Tensor, wp.array]] = None,
        body_indices: Optional[Union[np.ndarray, List, torch.Tensor, wp.array]] = None,
    ) -> None:
        """Sets body center of mass positions and orientations for articulation bodies in the view.

        Args:
            positions (Union[np.ndarray, torch.Tensor, wp.array]): body center of mass positions for articulations in the view. shape (M, K, 3).
            orientations (Union[np.ndarray, torch.Tensor, wp.array]): body center of mass orientations for articulations in the view. shape (M, K, 4).
            indices (Optional[Union[np.ndarray, List, torch.Tensor, wp.array]], optional): indicies to specify which prims
                                                                                 to manipulate. Shape (M,).
                                                                                 Where M <= size of the encapsulated prims in the view.
                                                                                 Defaults to None (i.e: all prims in the view).
            body_indices (Optional[Union[np.ndarray, List, torch.Tensor, wp.array]], optional): body indicies to specify which bodies
                                                                                 to manipulate. Shape (K,).
                                                                                 Where K <= num of bodies.
                                                                                 Defaults to None (i.e: all bodies).
        """
        if not self._is_initialized:
            carb.log_warn("ArticulationView needs to be initialized.")
            return
        if self._device is not None and "cuda" in self._device:
            carb.log_warn("set_body_coms function is not supported for the gpu pipeline.")
            return

        indices = self._backend_utils.resolve_indices(indices, self.count, "cpu")
        if not omni.timeline.get_timeline_interface().is_stopped() and self._physics_view is not None:
            body_indices = self._backend_utils.resolve_indices(body_indices, self.num_bodies, self._device)
            coms = self._physics_view.get_coms().reshape((self.count, self.num_bodies, 7))
            if positions is not None:
                if self._backend == "warp":
                    coms = self._backend_utils.assign(
                        self._backend_utils.move_data(positions, device="cpu"),
                        coms,
                        [indices, body_indices, wp.array([0, 1, 2], dtype=wp.int32, device="cpu")],
                    )
                else:
                    coms[
                        self._backend_utils.expand_dims(indices, 1), body_indices, 0:3
                    ] = self._backend_utils.move_data(positions, device="cpu")
            if orientations is not None:
                if self._backend == "warp":
                    coms = self._backend_utils.assign(
                        self._backend_utils.move_data(self._backend_utils.wxyz2xyzw(orientations), device="cpu"),
                        coms,
                        [indices, body_indices, wp.array([3, 4, 5, 6], dtype=wp.int32, device="cpu")],
                    )
                else:
                    coms[
                        self._backend_utils.expand_dims(indices, 1), body_indices, 3:7
                    ] = self._backend_utils.move_data(orientations[:, :, [1, 2, 3, 0]], device="cpu")
            self._physics_view.set_coms(coms, indices)
        else:
            carb.log_warn("Physics Simulation View is not created yet in order to use set_body_coms")

    def get_fixed_tendon_stiffnesses(
        self, indices: Optional[Union[np.ndarray, List, torch.Tensor, wp.array]] = None, clone: bool = True
    ) -> Union[np.ndarray, torch.Tensor, wp.indexedarray]:
        """Gets the stiffness of fixed tendons for articulations in the view.

        Args:
            indices (Optional[Union[np.ndarray, List, torch.Tensor, wp.array]], optional): indicies to specify which prims
                                                                                 to query. Shape (M,).
                                                                                 Where M <= size of the encapsulated prims in the view.
                                                                                 Defaults to None (i.e: all prims in the view).
            clone (bool, optional): True to return a clone of the internal buffer. Otherwise False. Defaults to True.

        Returns:
            Union[np.ndarray, torch.Tensor, wp.indexedarray]: fixed tendon stiffnesses of articulations in the view.
                                                    shape is (M, K).
        """
        if not self._is_initialized:
            carb.log_warn("ArticulationView needs to be initialized.")
            return None
        if not omni.timeline.get_timeline_interface().is_stopped() and self._physics_view is not None:
            indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
            current_values = self._physics_view.get_fixed_tendon_stiffnesses()
            if clone:
                current_values = self._backend_utils.clone_tensor(current_values, device=self._device)
            result = current_values[indices]
            return result
        else:
            carb.log_warn("Physics Simulation View is not created yet in order to use get_fixed_tendon_stiffnesses")
            return None

    def get_fixed_tendon_dampings(
        self, indices: Optional[Union[np.ndarray, List, torch.Tensor, wp.array]] = None, clone: bool = True
    ) -> Union[np.ndarray, torch.Tensor, wp.indexedarray]:
        """Gets the dampings of fixed tendons for articulations in the view.

        Args:
            indices (Optional[Union[np.ndarray, List, torch.Tensor, wp.array]], optional): indicies to specify which prims
                                                                                 to query. Shape (M,).
                                                                                 Where M <= size of the encapsulated prims in the view.
                                                                                 Defaults to None (i.e: all prims in the view).
            clone (bool, optional): True to return a clone of the internal buffer. Otherwise False. Defaults to True.

        Returns:
            Union[np.ndarray, torch.Tensor, wp.indexedarray]: fixed tendon dampings of articulations in the view.
                                                    shape is (M, K).
        """
        if not self._is_initialized:
            carb.log_warn("ArticulationView needs to be initialized.")
            return None
        if not omni.timeline.get_timeline_interface().is_stopped() and self._physics_view is not None:
            indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
            current_values = self._physics_view.get_fixed_tendon_dampings()
            if clone:
                current_values = self._backend_utils.clone_tensor(current_values, device=self._device)
            result = current_values[indices]
            return result
        else:
            carb.log_warn("Physics Simulation View is not created yet in order to use get_fixed_tendon_dampings")
            return None

    def get_fixed_tendon_limit_stiffnesses(
        self, indices: Optional[Union[np.ndarray, List, torch.Tensor, wp.array]] = None, clone: bool = True
    ) -> Union[np.ndarray, torch.Tensor, wp.indexedarray]:
        """Gets the limit stiffness of fixed tendons for articulations in the view.

        Args:
            indices (Optional[Union[np.ndarray, List, torch.Tensor, wp.array]], optional): indicies to specify which prims
                                                                                 to query. Shape (M,).
                                                                                 Where M <= size of the encapsulated prims in the view.
                                                                                 Defaults to None (i.e: all prims in the view).
            clone (bool, optional): True to return a clone of the internal buffer. Otherwise False. Defaults to True.

        Returns:
            Union[np.ndarray, torch.Tensor, wp.indexedarray]: fixed tendon stiffnesses of articulations in the view.
                                                    shape is (M, K).
        """
        if not self._is_initialized:
            carb.log_warn("ArticulationView needs to be initialized.")
            return None
        if not omni.timeline.get_timeline_interface().is_stopped() and self._physics_view is not None:
            indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
            current_values = self._physics_view.get_fixed_tendon_limit_stiffnesses()
            if clone:
                current_values = self._backend_utils.clone_tensor(current_values, device=self._device)
            result = current_values[indices]
            return result
        else:
            carb.log_warn(
                "Physics Simulation View is not created yet in order to use get_fixed_tendon_limit_stiffnesses"
            )
            return None

    def get_fixed_tendon_limits(
        self, indices: Optional[Union[np.ndarray, List, torch.Tensor, wp.array]] = None, clone: bool = True
    ) -> Union[np.ndarray, torch.Tensor, wp.indexedarray]:
        """Gets the limits of fixed tendons for articulations in the view.

        Args:
            indices (Optional[Union[np.ndarray, List, torch.Tensor, wp.array]], optional): indicies to specify which prims
                                                                                 to query. Shape (M,).
                                                                                 Where M <= size of the encapsulated prims in the view.
                                                                                 Defaults to None (i.e: all prims in the view).
            clone (bool, optional): True to return a clone of the internal buffer. Otherwise False. Defaults to True.

        Returns:
            Union[np.ndarray, torch.Tensor, wp.indexedarray]: fixed tendon stiffnesses of articulations in the view.
                                                    shape is (M, K, 2).
        """
        if not self._is_initialized:
            carb.log_warn("ArticulationView needs to be initialized.")
            return None
        if not omni.timeline.get_timeline_interface().is_stopped() and self._physics_view is not None:
            indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
            current_values = self._physics_view.get_fixed_tendon_limits().reshape(
                (self.count, self.num_fixed_tendons, 2)
            )
            if clone:
                current_values = self._backend_utils.clone_tensor(current_values, device=self._device)
            result = current_values[indices]
            return result
        else:
            carb.log_warn("Physics Simulation View is not created yet in order to use get_fixed_tendon_limits")
            return None

    def get_fixed_tendon_rest_lengths(
        self, indices: Optional[Union[np.ndarray, List, torch.Tensor, wp.array]] = None, clone: bool = True
    ) -> Union[np.ndarray, torch.Tensor, wp.indexedarray]:
        """Gets the rest length of fixed tendons for articulations in the view.

        Args:
            indices (Optional[Union[np.ndarray, List, torch.Tensor, wp.array]], optional): indicies to specify which prims
                                                                                 to query. Shape (M,).
                                                                                 Where M <= size of the encapsulated prims in the view.
                                                                                 Defaults to None (i.e: all prims in the view).
            clone (bool, optional): True to return a clone of the internal buffer. Otherwise False. Defaults to True.

        Returns:
            Union[np.ndarray, torch.Tensor, wp.indexedarray]: fixed tendon stiffnesses of articulations in the view.
                                                    shape is (M, K).
        """
        if not self._is_initialized:
            carb.log_warn("ArticulationView needs to be initialized.")
            return None
        if not omni.timeline.get_timeline_interface().is_stopped() and self._physics_view is not None:
            indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
            current_values = self._physics_view.get_fixed_tendon_rest_lengths()
            if clone:
                current_values = self._backend_utils.clone_tensor(current_values, device=self._device)
            result = current_values[indices]
            return result
        else:
            carb.log_warn("Physics Simulation View is not created yet in order to use get_fixed_tendon_rest_lengths")
            return None

    def get_fixed_tendon_offsets(
        self, indices: Optional[Union[np.ndarray, List, torch.Tensor, wp.array]] = None, clone: bool = True
    ) -> Union[np.ndarray, torch.Tensor, wp.indexedarray]:
        """Gets the offsets of fixed tendons for articulations in the view.

        Args:
            indices (Optional[Union[np.ndarray, List, torch.Tensor, wp.array]], optional): indicies to specify which prims
                                                                                 to query. Shape (M,).
                                                                                 Where M <= size of the encapsulated prims in the view.
                                                                                 Defaults to None (i.e: all prims in the view).
            clone (bool, optional): True to return a clone of the internal buffer. Otherwise False. Defaults to True.

        Returns:
            Union[np.ndarray, torch.Tensor, wp.indexedarray]: fixed tendon stiffnesses of articulations in the view.
                                                    shape is (M, K).
        """
        if not self._is_initialized:
            carb.log_warn("ArticulationView needs to be initialized.")
            return None
        if not omni.timeline.get_timeline_interface().is_stopped() and self._physics_view is not None:
            indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
            current_values = self._physics_view.get_fixed_tendon_offsets()
            if clone:
                current_values = self._backend_utils.clone_tensor(current_values, device=self._device)
            result = current_values[indices]
            return result
        else:
            carb.log_warn("Physics Simulation View is not created yet in order to use get_fixed_tendon_offsets")
            return None

    def set_fixed_tendon_properties(
        self,
        stiffnesses: Union[np.ndarray, torch.Tensor, wp.array] = None,
        dampings: Union[np.ndarray, torch.Tensor, wp.array] = None,
        limit_stiffnesses: Union[np.ndarray, torch.Tensor, wp.array] = None,
        limits: Union[np.ndarray, torch.Tensor, wp.array] = None,
        rest_lengths: Union[np.ndarray, torch.Tensor, wp.array] = None,
        offsets: Union[np.ndarray, torch.Tensor, wp.array] = None,
        indices: Optional[Union[np.ndarray, List, torch.Tensor, wp.array]] = None,
    ) -> None:
        """Sets fixed tendon properties for articulations in the view.

        Args:
            stiffnesses (Union[np.ndarray, torch.Tensor, wp.array]): fixed tendon stiffnesses for articulations in the view. shape (M, K).
            dampings (Union[np.ndarray, torch.Tensor, wp.array]): fixed tendon dampings for articulations in the view. shape (M, K).
            limit_stiffnesses (Union[np.ndarray, torch.Tensor, wp.array]): fixed tendon limit stiffnesses for articulations in the view. shape (M, K).
            limits (Union[np.ndarray, torch.Tensor, wp.array]): fixed tendon limits for articulations in the view. shape (M, K, 2).
            rest_lengths (Union[np.ndarray, torch.Tensor, wp.array]): fixed tendon rest lengths for articulations in the view. shape (M, K).
            offsets (Union[np.ndarray, torch.Tensor, wp.array]): fixed tendon offsets for articulations in the view. shape (M, K).
            indices (Optional[Union[np.ndarray, List, torch.Tensor, wp.array]], optional): indicies to specify which prims
                                                                                 to manipulate. Shape (M,).
                                                                                 Where M <= size of the encapsulated prims in the view.
                                                                                 Defaults to None (i.e: all prims in the view).
        """
        if not self._is_initialized:
            carb.log_warn("ArticulationView needs to be initialized.")
            return

        indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
        if not omni.timeline.get_timeline_interface().is_stopped() and self._physics_view is not None:
            current_stiffnesses = self._physics_view.get_fixed_tendon_stiffnesses()
            current_dampings = self._physics_view.get_fixed_tendon_dampings()
            current_limit_stiffnesses = self._physics_view.get_fixed_tendon_limit_stiffnesses()
            current_limits = self._physics_view.get_fixed_tendon_limits().reshape(
                (self.count, self.num_fixed_tendons, 2)
            )
            current_rest_lengths = self._physics_view.get_fixed_tendon_rest_lengths()
            current_offsets = self._physics_view.get_fixed_tendon_offsets()
            if stiffnesses is not None:
                current_stiffnesses = self._backend_utils.assign(
                    self._backend_utils.move_data(stiffnesses, device=self._device), current_stiffnesses, indices
                )
            if dampings is not None:
                current_dampings = self._backend_utils.assign(
                    self._backend_utils.move_data(dampings, device=self._device), current_dampings, indices
                )
            if limit_stiffnesses is not None:
                current_limit_stiffnesses = self._backend_utils.assign(
                    self._backend_utils.move_data(limit_stiffnesses, device=self._device),
                    current_limit_stiffnesses,
                    indices,
                )
            if limits is not None:
                current_limits = self._backend_utils.assign(
                    self._backend_utils.move_data(limits, device=self._device), current_limits, indices
                )
            if rest_lengths is not None:
                current_rest_lengths = self._backend_utils.assign(
                    self._backend_utils.move_data(rest_lengths, device=self._device), current_rest_lengths, indices
                )
            if offsets is not None:
                current_offsets = self._backend_utils.assign(
                    self._backend_utils.move_data(offsets, device=self._device), current_offsets, indices
                )
            self._physics_view.set_fixed_tendon_properties(
                current_stiffnesses,
                current_dampings,
                current_limit_stiffnesses,
                current_limits,
                current_rest_lengths,
                current_offsets,
                indices,
            )
        else:
            carb.log_warn("Physics Simulation View is not created yet in order to use set_fixed_tendon_properties")
