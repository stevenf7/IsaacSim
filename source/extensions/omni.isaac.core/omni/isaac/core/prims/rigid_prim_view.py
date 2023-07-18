# Copyright (c) 2021-2023, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
from typing import List, Optional, Tuple, Union

import carb
import numpy as np
import omni.kit.app
import torch
import warp as wp
from omni.isaac.core.prims.rigid_contact_view import RigidContactView
from omni.isaac.core.prims.xform_prim_view import XFormPrimView
from omni.isaac.core.utils.prims import get_prim_parent
from omni.isaac.core.utils.types import DynamicsViewState
from pxr import Gf, PhysxSchema, Usd, UsdGeom, UsdPhysics


class RigidPrimView(XFormPrimView):
    """Provides high level functions to deal with prims that has rigid body api applied to it (1 or more rigid body prims)
    as well as its attributes/ properties.
    This object wraps all matching Rigid Prims found at the regex provided at the prim_paths_expr.
    Note:
        - each prim will have "xformOp:orient", "xformOp:translate" and "xformOp:scale" only post init,
            unless it is a non-root articulation link.
        - if the prim does not already have a rigid body api applied to it before init, it will apply it.

    Args:
        prim_paths_expr (str): prim paths regex to encapsulate all prims that match it.
                                example: "/World/Env[1-5]/Cube" will match /World/Env1/Cube,
                                /World/Env2/Cube..etc.
                                (a non regex prim path can also be used to encapsulate one rigid prim).
        name (str, optional): shortname to be used as a key by Scene class.
                                Note: needs to be unique if the object is added to the Scene.
                                Defaults to "rigid_prim_view".
        positions (Optional[Union[np.ndarray, torch.Tensor, wp.array]], optional):
                                                        default positions in the world frame of the prims.
                                                        shape is (N, 3).
                                                        Defaults to None, which means left unchanged.
        translations (Optional[Union[np.ndarray, torch.Tensor, wp.array]], optional):
                                                        default translations in the local frame of the prims
                                                        (with respect to its parent prims). shape is (N, 3).
                                                        Defaults to None, which means left unchanged.
        orientations (Optional[Union[np.ndarray, torch.Tensor, wp.array]], optional):
                                                        default quaternion orientations in the world/ local frame of the prims
                                                        (depends if translation or position is specified).
                                                        quaternion is scalar-first (w, x, y, z). shape is (N, 4).
                                                        Defaults to None, which means left unchanged.
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
        masses (Optional[Union[np.ndarray, torch.Tensor, wp.array]], optional): mass in kg specified for each prim in the view.
                                                                        shape is (N,). Defaults to None.
        densities (Optional[Union[np.ndarray, torch.Tensor, wp.array]], optional): density in kg/m^3 specified for each prim in the view.
                                                                        shape is (N,). Defaults to None.
        linear_velocities (Optional[Union[np.ndarray, torch.Tensor, wp.array]], optional): default linear velocity of each prim in the view
                                                                                    (to be applied in the first frame and on resets).
                                                                                    Shape is (N, 3). Defaults to None.
        angular_velocities (Optional[Union[np.ndarray, torch.Tensor, wp.array]], optional): default angular velocity of each prim in the view
                                                                                    (to be applied in the first frame and on resets).
                                                                                    Shape is (N, 3). Defaults to None.
        track_contact_forces (bool, Optional) : if enabled, the view will track the net contact forces on each rigid prim in the view
        prepare_contact_sensors (bool, Optional): if rigid prims in the view are not cloned from a prim in a prepared state,
                                                    (although slow for large number of prims) this ensures that
                                                    appropriate physics settings are applied on all the prim in the view.
        disable_stablization (bool, optional): disables the contact stablization parameter in the physics context
        contact_filter_prim_paths_expr (Optional[List[str]], Optional): a list of filter expressions which allows for tracking contact forces
                                                                between prims and this subset through get_contact_force_matrix().
    """

    def __init__(
        self,
        prim_paths_expr: str,
        name: str = "rigid_prim_view",
        positions: Optional[Union[np.ndarray, torch.Tensor, wp.array]] = None,
        translations: Optional[Union[np.ndarray, torch.Tensor, wp.array]] = None,
        orientations: Optional[Union[np.ndarray, torch.Tensor, wp.array]] = None,
        scales: Optional[Union[np.ndarray, torch.Tensor, wp.array]] = None,
        visibilities: Optional[Union[np.ndarray, torch.Tensor, wp.array]] = None,
        reset_xform_properties: bool = True,
        masses: Optional[Union[np.ndarray, torch.Tensor, wp.array]] = None,
        densities: Optional[Union[np.ndarray, torch.Tensor, wp.array]] = None,
        linear_velocities: Optional[Union[np.ndarray, torch.Tensor, wp.array]] = None,
        angular_velocities: Optional[Union[np.ndarray, torch.Tensor, wp.array]] = None,
        track_contact_forces: bool = False,
        prepare_contact_sensors: bool = True,
        disable_stablization: bool = True,
        contact_filter_prim_paths_expr: Optional[List[str]] = [],
    ) -> None:
        self._physics_view = None
        self._num_shapes = None
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
        self._rigid_body_apis = [None] * self._count
        self._physx_rigid_body_apis = [None] * self._count
        self._mass_apis = [None] * self._count
        self._contact_filter_prim_paths_expr = contact_filter_prim_paths_expr
        if not self._non_root_link:
            if linear_velocities is not None:
                self.set_linear_velocities(linear_velocities)
            if angular_velocities is not None:
                self.set_angular_velocities(angular_velocities)
        if masses is not None:
            RigidPrimView.set_masses(self, masses)
        if densities is not None:
            RigidPrimView.set_densities(self, densities)
        self._dynamics_default_state = None
        if not self._non_root_link:
            linear_velocities = self.get_linear_velocities()
            angular_velocities = self.get_angular_velocities()
            if self._backend == "warp":
                self._dynamics_default_state = DynamicsViewState(
                    self._default_state.positions,
                    self._default_state.orientations,
                    linear_velocities.data,
                    angular_velocities.data,
                )
            else:
                self._dynamics_default_state = DynamicsViewState(
                    self._default_state.positions,
                    self._default_state.orientations,
                    linear_velocities,
                    angular_velocities,
                )
        self._track_contact_forces = track_contact_forces or len(contact_filter_prim_paths_expr) != 0
        if self._track_contact_forces:
            self._contact_view = RigidContactView(
                prim_paths_expr,
                contact_filter_prim_paths_expr,
                name + "_contact",
                prepare_contact_sensors,
                disable_stablization,
            )

        timeline = omni.timeline.get_timeline_interface()
        self._invalidate_physics_handle_event = timeline.get_timeline_event_stream().create_subscription_to_pop(
            self._invalidate_physics_handle_callback
        )
        return

    @property
    def num_shapes(self) -> int:
        """
        Returns:
            int: number of rigid shapes for the prims in the view.
        """
        return self._num_shapes

    def is_physics_handle_valid(self) -> bool:
        """
        Returns:
            bool: True if the physics handle of the view is valid (i.e physics is initialized for the view). Otherwise False.
        """
        return self._physics_view is not None

    def initialize(self, physics_sim_view: omni.physics.tensors.SimulationView = None) -> None:
        """Create a physics simulation view if not passed and creates a rigid body view in physX.

        Args:
            physics_sim_view (omni.physics.tensors.SimulationView, optional): current physics simulation view. Defaults to None.
        """
        if physics_sim_view is None:
            physics_sim_view = omni.physics.tensors.create_simulation_view(self._backend)
            physics_sim_view.set_subspace_roots("/")
        carb.log_info("initializing view for {}".format(self._name))
        self._physics_sim_view = physics_sim_view
        self._physics_view = physics_sim_view.create_rigid_body_view(self._regex_prim_paths.replace(".*", "*"))
        self._num_shapes = self._physics_view.max_shapes
        carb.log_info("Rigid Prim View Device: {}".format(self._device))
        if self._track_contact_forces:
            self._contact_view.initialize(self._physics_sim_view)

    def _invalidate_physics_handle_callback(self, event):
        if event.type == int(omni.timeline.TimelineEventType.STOP):
            self._physics_view = None
        return

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
            self._physics_sim_view.enable_warnings(False)
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
            self._physics_view.set_transforms(pose, indices)
            self._physics_sim_view.enable_warnings(True)
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
            self._physics_sim_view.enable_warnings(False)
            indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
            pose = self._physics_view.get_transforms()
            self._physics_sim_view.enable_warnings(True)
            if clone:
                pose = self._backend_utils.clone_tensor(pose, device=self._device)
            pos = pose[indices, 0:3]
            rot = self._backend_utils.xyzw2wxyz(pose[indices, 3:7])
            return pos, rot
        else:
            return XFormPrimView.get_world_poses(self, indices=indices)

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
            parent_transforms = np.zeros(shape=(indices.shape[0], 4, 4), dtype=np.float32)
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
            return self._backend_utils.get_local_from_world(
                parent_transforms, world_positions, world_orientations, self._device
            )
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
                current_translations, current_orientations = RigidPrimView.get_local_poses(self, indices=indices)
                if translations is None:
                    translations = current_translations
                if orientations is None:
                    orientations = current_orientations
            self._physics_sim_view.enable_warnings(False)
            indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
            parent_transforms = np.zeros(shape=(indices.shape[0], 4, 4), dtype=np.float32)
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
            RigidPrimView.set_world_poses(
                self, positions=calculated_positions, orientations=calculated_orientations, indices=indices
            )
            self._physics_sim_view.enable_warnings(True)
        else:
            XFormPrimView.set_local_poses(self, translations=translations, orientations=orientations, indices=indices)
        return

    def set_linear_velocities(
        self,
        velocities: Optional[Union[np.ndarray, torch.Tensor, wp.array]],
        indices: Optional[Union[np.ndarray, list, torch.Tensor, wp.array]] = None,
    ):
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

        if self._device is not None and "cuda" in self._device:
            carb.log_warn(
                "set_linear_velocities function is not supported for the gpu pipeline, use set_velocities instead."
            )
        indices = self._backend_utils.resolve_indices(indices, self.count, self._device)

        if not omni.timeline.get_timeline_interface().is_stopped() and self._physics_view is not None:
            self._physics_sim_view.enable_warnings(False)
            current_velocities = self._physics_view.get_velocities()
            if self._backend == "warp":
                current_velocities = self._backend_utils.assign(
                    self._backend_utils.move_data(velocities, device=self._device),
                    current_velocities,
                    [indices, wp.array([0, 1, 2], device=self._device, dtype=wp.int32)],
                )
            else:
                current_velocities[indices, 0:3] = self._backend_utils.move_data(velocities, device=self._device)
            self._physics_view.set_velocities(current_velocities, indices)
            self._physics_sim_view.enable_warnings(True)
        else:
            idx_count = 0
            indices = self._backend_utils.to_list(indices)
            velocities = self._backend_utils.to_list(velocities)
            for i in indices:
                if self._rigid_body_apis[i] is None:
                    if self._prims[i].HasAPI(UsdPhysics.RigidBodyAPI):
                        rigid_api = UsdPhysics.RigidBodyAPI(self._prims[i])
                    else:
                        rigid_api = UsdPhysics.RigidBodyAPI.Apply(self._prims[i])
                    self._rigid_body_apis[i] = rigid_api
                self._rigid_body_apis[i].GetVelocityAttr().Set(Gf.Vec3f(*velocities[idx_count]))
                idx_count += 1
            return

    def get_linear_velocities(
        self, indices: Optional[Union[np.ndarray, list, torch.Tensor, wp.array]] = None, clone: bool = True
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
        indices = self._backend_utils.resolve_indices(indices, self.count, self._device)

        if not omni.timeline.get_timeline_interface().is_stopped() and self._physics_view is not None:
            self._physics_sim_view.enable_warnings(False)
            linear_velocities = self._physics_view.get_velocities()
            self._physics_sim_view.enable_warnings(True)
            if clone:
                velocities = self._backend_utils.clone_tensor(linear_velocities, device=self._device)
            return velocities[indices, 0:3]
        else:
            linear_velocities = np.zeros(shape=(indices.shape[0], 3), dtype=np.float32)
            write_idx = 0
            indices = self._backend_utils.to_list(indices)
            for i in indices:
                if self._rigid_body_apis[i] is None:
                    if self._prims[i].HasAPI(UsdPhysics.RigidBodyAPI):
                        rigid_api = UsdPhysics.RigidBodyAPI(self._prims[i])
                    else:
                        rigid_api = UsdPhysics.RigidBodyAPI.Apply(self._prims[i])
                    self._rigid_body_apis[i] = rigid_api
                linear_velocities[write_idx] = np.array(
                    self._rigid_body_apis[i].GetVelocityAttr().Get(), dtype=np.float32
                )
                write_idx += 1
            linear_velocities = self._backend_utils.convert(
                linear_velocities, dtype="float32", device=self._device, indexed=True
            )
            return linear_velocities

    def set_angular_velocities(
        self,
        velocities: Optional[Union[np.ndarray, torch.Tensor, wp.array]],
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
        indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
        if self._device is not None and "cuda" in self._device:
            carb.log_warn(
                "set_angular_velocities function is not supported for the gpu pipeline, use set_velocities instead."
            )
        if not omni.timeline.get_timeline_interface().is_stopped() and self._physics_view is not None:
            self._physics_sim_view.enable_warnings(False)
            current_velocities = self._physics_view.get_velocities()
            if self._backend == "warp":
                current_velocities = self._backend_utils.assign(
                    self._backend_utils.move_data(velocities, device=self._device),
                    current_velocities,
                    [indices, wp.array([3, 4, 5], device=self._device, dtype=wp.int32)],
                )
            else:
                current_velocities[indices, 3:6] = self._backend_utils.move_data(velocities, self._device)
            self._physics_view.set_velocities(current_velocities, indices)
            self._physics_sim_view.enable_warnings(True)
        else:
            idx_count = 0
            indices = self._backend_utils.to_list(indices)
            velocities = self._backend_utils.to_list(velocities)
            for i in indices:
                if self._rigid_body_apis[i] is None:
                    if self._prims[i].HasAPI(UsdPhysics.RigidBodyAPI):
                        rigid_api = UsdPhysics.RigidBodyAPI(self._prims[i])
                    else:
                        rigid_api = UsdPhysics.RigidBodyAPI.Apply(self._prims[i])
                    self._rigid_body_apis[i] = rigid_api
                self._rigid_body_apis[i].GetAngularVelocityAttr().Set(Gf.Vec3f(*velocities[idx_count]))
                idx_count += 1
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
        indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
        if not omni.timeline.get_timeline_interface().is_stopped() and self._physics_view is not None:
            self._physics_sim_view.enable_warnings(False)
            angular_velocities = self._physics_view.get_velocities()
            self._physics_sim_view.enable_warnings(True)
            if clone:
                velocities = self._backend_utils.clone_tensor(angular_velocities, device=self._device)
            return angular_velocities[indices, 3:6]
        else:
            angular_velocities = np.zeros(shape=(indices.shape[0], 3), dtype=np.float32)
            write_idx = 0
            indices = self._backend_utils.to_list(indices)
            for i in indices:
                if self._rigid_body_apis[i] is None:
                    if self._prims[i].HasAPI(UsdPhysics.RigidBodyAPI):
                        rigid_api = UsdPhysics.RigidBodyAPI(self._prims[i])
                    else:
                        rigid_api = UsdPhysics.RigidBodyAPI.Apply(self._prims[i])
                    self._rigid_body_apis[i] = rigid_api
                angular_velocities[write_idx] = np.array(
                    self._rigid_body_apis[i].GetAngularVelocityAttr().Get(), dtype="float32"
                )
                write_idx += 1
            angular_velocities = self._backend_utils.convert(
                angular_velocities, dtype="float32", device=self._device, indexed=True
            )
            return angular_velocities

    def set_velocities(
        self,
        velocities: Union[np.ndarray, torch.Tensor, wp.array],
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
        indices = self._backend_utils.resolve_indices(indices, self.count, self._device)

        if not omni.timeline.get_timeline_interface().is_stopped() and self._physics_view is not None:
            self._physics_sim_view.enable_warnings(False)
            new_velocities = self._physics_view.get_velocities()
            new_velocities = self._backend_utils.assign(
                self._backend_utils.move_data(velocities, self._device), new_velocities, indices
            )
            self._physics_view.set_velocities(new_velocities, indices)
            self._physics_sim_view.enable_warnings(True)
        else:
            self.set_linear_velocities(velocities[:, 0:3], indices)
            self.set_angular_velocities(velocities[:, 3:6], indices)
        return

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
        indices = self._backend_utils.resolve_indices(indices, self.count, self._device)

        if not omni.timeline.get_timeline_interface().is_stopped() and self._physics_view is not None:
            self._physics_sim_view.enable_warnings(False)
            velocities = self._physics_view.get_velocities()
            self._physics_sim_view.enable_warnings(True)
            if clone:
                velocities = self._backend_utils.clone_tensor(velocities, device=self._device)
            return velocities[indices]
        else:
            linear_velocities = self.get_linear_velocities(indices, clone)
            angular_velocities = self.get_angular_velocities(indices, clone)
            return self._backend_utils.tensor_cat([linear_velocities, angular_velocities], dim=-1, device=self._device)

    def apply_forces(
        self,
        forces: Optional[Union[np.ndarray, torch.Tensor, wp.array]],
        indices: Optional[Union[np.ndarray, list, torch.Tensor, wp.array]] = None,
        is_global: bool = True,
    ) -> None:
        """Applies forces to prims in the view.

        Args:
            forces (Optional[Union[np.ndarray, torch.Tensor, wp.array]]): forces to be applied to the prims.
            indices (Optional[Union[np.ndarray, list, torch.Tensor, wp.array]], optional): indicies to specify which prims
                                                                                 to manipulate. Shape (M,).
                                                                                 Where M <= size of the encapsulated prims in the view.
                                                                                 Defaults to None (i.e: all prims in the view).
            is_global (bool, optional): True if forces are in the global frame. Otherwise False. Defaults to True.

        """
        if not omni.timeline.get_timeline_interface().is_stopped() and self._physics_view is not None:
            self._physics_sim_view.enable_warnings(False)
            indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
            new_forces = self._backend_utils.create_zeros_tensor([self.count, 3], device=self._device, dtype="float32")
            new_forces = self._backend_utils.assign(
                self._backend_utils.move_data(forces.reshape((indices.shape[0], 3)), self._device), new_forces, indices
            )
            self._physics_view.apply_forces(new_forces, indices, is_global)
            self._physics_sim_view.enable_warnings(True)
        else:
            carb.log_warn("Physics Simulation View is not created yet")

    def apply_forces_and_torques_at_pos(
        self,
        forces: Optional[Union[np.ndarray, torch.Tensor, wp.array]] = None,
        torques: Optional[Union[np.ndarray, torch.Tensor, wp.array]] = None,
        positions: Optional[Union[np.ndarray, torch.Tensor, wp.array]] = None,
        indices: Optional[Union[np.ndarray, list, torch.Tensor, wp.array]] = None,
        is_global: bool = True,
    ) -> None:
        """Applies forces and torques to prims in the view. The forces and/or torques can be in local or global coordinates.
        The forces can applied at a location given by positions variable.

            Args:
                forces (Optional[Union[np.ndarray, torch.Tensor, wp.array]]): forces to be applied to the prims. If not specified, no force will be applied.
                                                                                     Defaults to None (i.e: no forces will be applied).
                torques (Optional[Union[np.ndarray, torch.Tensor, wp.array]]): torques to be applied to the prims. If not specified, no torque will be applied.
                                                                     Defaults to None (i.e: no torques will be applied).
                positions (Optional[Union[np.ndarray, torch.Tensor, wp.array]]): position of the forces with respect to the body frame.
                                                                        If not specified, the forces are applied at the origin of the body frame.
                                                                        Defaults to None (i.e: applied forces will be at the origin of the body frame).
                indices (Optional[Union[np.ndarray, list, torch.Tensor, wp.array]], optional): indicies to specify which prims
                                                                                    to manipulate. Shape (M,).
                                                                                    Where M <= size of the encapsulated prims in the view.
                                                                                    Defaults to None (i.e: all prims in the view).
                is_global (bool, optional): True if forces, torques, and positions are in the global frame.
                                            False if forces, torques, and positions are in the local frame.  Defaults to True.
        """
        if not omni.timeline.get_timeline_interface().is_stopped() and self._physics_view is not None:
            self._physics_sim_view.enable_warnings(False)
            indices = self._backend_utils.resolve_indices(indices, self.count, self._device)

            new_forces = new_torques = new_positions = None
            if forces is not None:
                new_forces = self._backend_utils.create_zeros_tensor(
                    [self.count, 3], device=self._device, dtype="float32"
                )
                new_forces = self._backend_utils.assign(
                    self._backend_utils.move_data(forces, self._device), new_forces, indices
                )
                if positions is not None:
                    new_positions = self._backend_utils.create_zeros_tensor(
                        [self.count, 3], device=self._device, dtype="float32"
                    )
                    new_positions = self._backend_utils.assign(
                        self._backend_utils.move_data(positions, self._device), new_positions, indices
                    )

            if torques is not None:
                new_torques = self._backend_utils.create_zeros_tensor(
                    [self.count, 3], device=self._device, dtype="float32"
                )
                new_torques = self._backend_utils.assign(
                    self._backend_utils.move_data(torques, self._device), new_torques, indices
                )

            self._physics_view.apply_forces_and_torques_at_position(
                force_data=new_forces,
                torque_data=new_torques,
                position_data=new_positions,
                indices=indices,
                is_global=is_global,
            )

            self._physics_sim_view.enable_warnings(True)
        else:
            carb.log_warn("Physics Simulation View is not created yet")

    def get_masses(
        self, indices: Optional[Union[np.ndarray, List, torch.Tensor, wp.array]] = None, clone: bool = True
    ) -> Union[np.ndarray, torch.Tensor, wp.indexedarray]:
        """Gets rigid body masses of prims in the view.

        Args:
            indices (Optional[Union[np.ndarray, List, torch.Tensor, wp.array]], optional): indicies to specify which prims
                                                                                 to query. Shape (M,).
                                                                                 Where M <= size of the encapsulated prims in the view.
                                                                                 Defaults to None (i.e: all prims in the view).
            clone (bool, optional): True to return a clone of the internal buffer. Otherwise False. Defaults to True.

        Returns:
            Union[np.ndarray, torch.Tensor, wp.indexedarray]: masses of in kg of prims in the view. shape is (M,).
        """

        indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
        if not omni.timeline.get_timeline_interface().is_stopped() and self._physics_view is not None:
            current_values = self._backend_utils.move_data(
                self._physics_view.get_masses().reshape(self._count), self._device
            )
            if clone:
                current_values = self._backend_utils.clone_tensor(current_values, device=self._device)
            return current_values[indices]
        else:
            masses = np.zeros(shape=indices.shape[0], dtype=np.float32)
            write_idx = 0
            indices = self._backend_utils.to_list(indices)
            for i in indices:
                if self._mass_apis[i] is None:
                    if self._prims[i].HasAPI(UsdPhysics.MassAPI):
                        self._mass_apis[i] = UsdPhysics.MassAPI(self._prims[i])
                    else:
                        self._mass_apis[i] = UsdPhysics.MassAPI.Apply(self._prims[i])
                masses[write_idx] = self._mass_apis[i].GetMassAttr().Get()
                write_idx += 1
            masses = self._backend_utils.convert(masses, dtype="float32", device=self._device, indexed=True)
            return masses

    def get_inv_masses(
        self, indices: Optional[Union[np.ndarray, List, torch.Tensor, wp.array]] = None, clone: bool = True
    ) -> Union[np.ndarray, torch.Tensor, wp.indexedarray]:
        """Gets rigid body inverse masses of prims in the view.

        Args:
            indices (Optional[Union[np.ndarray, List, torch.Tensor, wp.array]], optional): indicies to specify which prims
                                                                                 to query. Shape (M,).
                                                                                 Where M <= size of the encapsulated prims in the view.
                                                                                 Defaults to None (i.e: all prims in the view).
            clone (bool, optional): True to return a clone of the internal buffer. Otherwise False. Defaults to True.

        Returns:
            Union[np.ndarray, torch.Tensor, wp.indexedarray]: rigid body inverse masses of prims in the view.
                                                    shape is (M,).
        """

        if not omni.timeline.get_timeline_interface().is_stopped() and self._physics_view is not None:
            indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
            current_values = self._backend_utils.move_data(self._physics_view.get_inv_masses(), self._device)
            if clone:
                current_values = self._backend_utils.clone_tensor(current_values, device=self._device)
            return current_values[indices]
        else:
            carb.log_warn("Physics Simulation View is not created yet in order to use get_inv_masses")
            return None

    def get_coms(
        self, indices: Optional[Union[np.ndarray, List, torch.Tensor, wp.array]] = None, clone: bool = True
    ) -> Union[np.ndarray, torch.Tensor, wp.indexedarray]:
        """Gets rigid body center of mass of articulations in the view.

        Args:
            indices (Optional[Union[np.ndarray, List, torch.Tensor, wp.array]], optional): indicies to specify which prims
                                                                                 to query. Shape (M,).
                                                                                 Where M <= size of the encapsulated prims in the view.
                                                                                 Defaults to None (i.e: all prims in the view).
            clone (bool, optional): True to return a clone of the internal buffer. Otherwise False. Defaults to True.

        Returns:
            Union[np.ndarray, torch.Tensor, wp.indexedarray]: rigid body center of mass positions and orientations of prims in the view.
                                                    position shape is (M, 3), orientation shape is (M, 4).
        """

        if not omni.timeline.get_timeline_interface().is_stopped() and self._physics_view is not None:
            indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
            current_values = self._backend_utils.move_data(
                self._physics_view.get_coms().reshape((self.count, 7)), self._device
            )
            if clone:
                current_values = self._backend_utils.clone_tensor(current_values, device=self._device)
            positions = current_values[
                self._backend_utils.expand_dims(indices, 1) if self._backend != "warp" else indices, 0:3
            ]
            orientations = self._backend_utils.xyzw2wxyz(
                current_values[self._backend_utils.expand_dims(indices, 1) if self._backend != "warp" else indices, 3:7]
            )
            return positions, orientations
        else:
            carb.log_warn("Physics Simulation View is not created yet in order to use get_coms")
            return None

    def get_inertias(
        self, indices: Optional[Union[np.ndarray, List, torch.Tensor, wp.array]] = None, clone: bool = True
    ) -> Union[np.ndarray, torch.Tensor, wp.indexedarray]:
        """Gets rigid body inertias of prims in the view.

        Args:
            indices (Optional[Union[np.ndarray, List, torch.Tensor, wp.array]], optional): indicies to specify which prims
                                                                                 to query. Shape (M,).
                                                                                 Where M <= size of the encapsulated prims in the view.
                                                                                 Defaults to None (i.e: all prims in the view).
            clone (bool, optional): True to return a clone of the internal buffer. Otherwise False. Defaults to True.

        Returns:
            Union[np.ndarray, torch.Tensor, wp.indexedarray]: rigid body inertias of prims in the view.
                                                    shape is (M, 9).
        """

        if not omni.timeline.get_timeline_interface().is_stopped() and self._physics_view is not None:
            indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
            current_values = self._backend_utils.move_data(
                self._physics_view.get_inertias().reshape((self.count, 9)), self._device
            )
            if clone:
                current_values = self._backend_utils.clone_tensor(current_values, device=self._device)
            return current_values[indices]
        else:
            carb.log_warn("Physics Simulation View is not created yet in order to use get_inertias")
            return None

    def get_inv_inertias(
        self, indices: Optional[Union[np.ndarray, List, torch.Tensor, wp.array]] = None, clone: bool = True
    ) -> Union[np.ndarray, torch.Tensor, wp.indexedarray]:
        """Gets rigid body inverse inertias of prims in the view.

        Args:
            indices (Optional[Union[np.ndarray, List, torch.Tensor, wp.array]], optional): indicies to specify which prims
                                                                                 to query. Shape (M,).
                                                                                 Where M <= size of the encapsulated prims in the view.
                                                                                 Defaults to None (i.e: all prims in the view).
            clone (bool, optional): True to return a clone of the internal buffer. Otherwise False. Defaults to True.

        Returns:
            Union[np.ndarray, torch.Tensor, wp.indexedarray]: rigid body inverse inertias of prims in the view.
                                                    shape is (M, 9).
        """

        if not omni.timeline.get_timeline_interface().is_stopped() and self._physics_view is not None:
            indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
            current_values = self._backend_utils.move_data(
                self._physics_view.get_inv_inertias().reshape((self.count, 9)), self._device
            )
            if clone:
                current_values = self._backend_utils.clone_tensor(current_values, device=self._device)
            return current_values[indices]
        else:
            carb.log_warn("Physics Simulation View is not created yet in order to use get_inv_inertias")
            return None

    def set_masses(
        self,
        masses: Union[np.ndarray, torch.Tensor, wp.array],
        indices: Optional[Union[np.ndarray, List, torch.Tensor, wp.array]] = None,
    ) -> None:
        """Sets body masses for prims in the view.

        Args:
            masses (Union[np.ndarray, torch.Tensor, wp.array]): body masses for prims in kg. shape (M,).
            indices (Optional[Union[np.ndarray, List, torch.Tensor, wp.array]], optional): indicies to specify which prims
                                                                                 to manipulate. Shape (M,).
                                                                                 Where M <= size of the encapsulated prims in the view.
                                                                                 Defaults to None (i.e: all prims in the view).
        """

        indices = self._backend_utils.resolve_indices(indices, self.count, "cpu")
        if not omni.timeline.get_timeline_interface().is_stopped() and self._physics_view is not None:
            data = self._physics_view.get_masses().reshape(self.count)
            data = self._backend_utils.assign(self._backend_utils.move_data(masses, device="cpu"), data, indices)
            self._physics_view.set_masses(data, indices)
        else:
            indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
            read_idx = 0
            indices = self._backend_utils.to_list(indices)
            masses = self._backend_utils.to_list(masses)
            for i in indices:
                if self._mass_apis[i] is None:
                    if self._prims[i].HasAPI(UsdPhysics.MassAPI):
                        self._mass_apis[i] = UsdPhysics.MassAPI(self._prims[i])
                    else:
                        self._mass_apis[i] = UsdPhysics.MassAPI.Apply(self._prims[i])
                self._mass_apis[i].GetMassAttr().Set(masses[read_idx])
                read_idx += 1
            return

    def set_inertias(
        self,
        values: Union[np.ndarray, torch.Tensor, wp.array],
        indices: Optional[Union[np.ndarray, List, torch.Tensor, wp.array]] = None,
    ) -> None:
        """Sets body inertias for prims in the view.

        Args:
            values (Union[np.ndarray, torch.Tensor, wp.array]): body inertias for prims in the view. shape (M, K, 9).
            indices (Optional[Union[np.ndarray, List, torch.Tensor, wp.array]], optional): indicies to specify which prims
                                                                                 to manipulate. Shape (M,).
                                                                                 Where M <= size of the encapsulated prims in the view.
                                                                                 Defaults to None (i.e: all prims in the view).
        """

        indices = self._backend_utils.resolve_indices(indices, self.count, "cpu")
        if not omni.timeline.get_timeline_interface().is_stopped() and self._physics_view is not None:
            data = self._physics_view.get_inertias()
            data = self._backend_utils.assign(self._backend_utils.move_data(values, device="cpu"), data, indices)
            self._physics_view.set_inertias(data, indices)
        else:
            carb.log_warn("Physics Simulation View is not created yet in order to use set_inertias")

    def set_coms(
        self,
        positions: Union[np.ndarray, torch.Tensor, wp.array] = None,
        orientations: Union[np.ndarray, torch.Tensor, wp.array] = None,
        indices: Optional[Union[np.ndarray, List, torch.Tensor, wp.array]] = None,
    ) -> None:
        """Sets body center of mass positions and orientations for articulation bodies in the view.

        Args:
            positions (Union[np.ndarray, torch.Tensor, wp.array]): body center of mass positions for articulations in the view. shape (M, K, 3).
            orientations (Union[np.ndarray, torch.Tensor, wp.array]): body center of mass orientations for articulations in the view. shape (M, K, 4).
            indices (Optional[Union[np.ndarray, List, torch.Tensor, wp.array]], optional): indicies to specify which prims
                                                                                 to manipulate. Shape (M,).
                                                                                 Where M <= size of the encapsulated prims in the view.
                                                                                 Defaults to None (i.e: all prims in the view).
        """

        indices = self._backend_utils.resolve_indices(indices, self.count, "cpu")
        if not omni.timeline.get_timeline_interface().is_stopped() and self._physics_view is not None:
            coms = self._physics_view.get_coms().reshape((self.count, 7))
            if positions is not None:
                if self._backend == "warp":
                    coms = self._backend_utils.assign(
                        self._backend_utils.move_data(positions, device="cpu"),
                        coms,
                        [indices, wp.array([0, 1, 2], dtype=wp.int32, device="cpu")],
                    )
                else:
                    coms[self._backend_utils.expand_dims(indices, 1), 0:3] = self._backend_utils.move_data(
                        positions, device="cpu"
                    )
            if orientations is not None:
                if self._backend == "warp":
                    coms = self._backend_utils.assign(
                        self._backend_utils.move_data(self._backend_utils.wxyz2xyzw(orientations), device="cpu"),
                        coms,
                        [indices, wp.array([3, 4, 5, 6], dtype=wp.int32, device="cpu")],
                    )
                else:
                    coms[self._backend_utils.expand_dims(indices, 1), 3:7] = self._backend_utils.move_data(
                        orientations[:, :, [1, 2, 3, 0]], device="cpu"
                    )
            self._physics_view.set_coms(coms, indices)
        else:
            carb.log_warn("Physics Simulation View is not created yet in order to use set_coms")

    def set_densities(
        self,
        densities: Optional[Union[np.ndarray, torch.Tensor, wp.array]],
        indices: Optional[Union[np.ndarray, list, torch.Tensor, wp.array]] = None,
    ) -> None:
        """Sets densities of prims in the view.

        Args:
            densities (Optional[Union[np.ndarray, torch.Tensor, wp.array]]): density in kg/m^3 specified for each prim in the view.
                                                                    shape is (M,). Defaults to None.
            indices (Optional[Union[np.ndarray, list, torch.Tensor, wp.array]], optional): indicies to specify which prims
                                                                                 to manipulate. Shape (M,).
                                                                                 Where M <= size of the encapsulated prims in the view.
                                                                                 Defaults to None (i.e: all prims in the view).
        """
        indices = self._backend_utils.resolve_indices(indices, self.count, "cpu")
        read_idx = 0
        indices = self._backend_utils.to_list(indices)
        densities = self._backend_utils.to_list(densities)
        for i in indices:
            if self._mass_apis[i] is None:
                if self._prims[i].HasAPI(UsdPhysics.MassAPI):
                    self._mass_apis[i] = UsdPhysics.MassAPI(self._prims[i])
                else:
                    self._mass_apis[i] = UsdPhysics.MassAPI.Apply(self._prims[i])
            self._mass_apis[i].GetDensityAttr().Set(densities[read_idx])
            read_idx += 1
        return

    def get_densities(
        self, indices: Optional[Union[np.ndarray, list, torch.Tensor, wp.array]] = None
    ) -> Union[np.ndarray, torch.Tensor, wp.indexedarray]:
        """Gets densities of prims in the view.

        Args:
            indices (Optional[Union[np.ndarray, list, torch.Tensor, wp.array]], optional): indicies to specify which prims
                                                                                    to query. Shape (M,).
                                                                                    Where M <= size of the encapsulated prims in the view.
                                                                                    Defaults to None (i.e: all prims in the view)

        Returns:
            Union[np.ndarray, torch.Tensor, wp.indexedarray]: densities of prims in the view in kg/m^3. shape (M,).
        """
        indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
        densities = np.zeros(shape=(indices.shape[0]), dtype=np.float32)
        write_idx = 0
        indices = self._backend_utils.to_list(indices)
        for i in indices:
            if self._mass_apis[i] is None:
                if self._prims[i].HasAPI(UsdPhysics.MassAPI):
                    self._mass_apis[i] = UsdPhysics.MassAPI(self._prims[i])
                else:
                    self._mass_apis[i] = UsdPhysics.MassAPI.Apply(self._prims[i])
            densities[write_idx] = self._mass_apis[i].GetDensityAttr().Get()
            write_idx += 1
        densities = self._backend_utils.convert(densities, dtype="float32", device=self._device, indexed=True)
        return densities

    def set_sleep_thresholds(
        self,
        thresholds: Optional[Union[np.ndarray, torch.Tensor, wp.array]],
        indices: Optional[Union[np.ndarray, list, torch.Tensor, wp.array]] = None,
    ) -> None:
        """Sets sleep thresholds of prims in the view.


        Args:

            thresholds (Optional[Union[np.ndarray, torch.Tensor, wp.array]]):  Mass-normalized kinetic energy threshold below which
                                                                    an actor may go to sleep. Range: [0, inf)
                                                                    Defaults: 0.00005 * tolerancesSpeed* tolerancesSpeed
                                                                    Units: distance^2 / second^2. shape (M,).
            indices (Optional[Union[np.ndarray, list, torch.Tensor, wp.array]], optional): indicies to specify which prims
                                                                                 to manipulate. Shape (M,).
                                                                                 Where M <= size of the encapsulated prims in the view.
                                                                                 Defaults to None (i.e: all prims in the view).
        """
        indices = self._backend_utils.resolve_indices(indices, self.count, "cpu")
        read_idx = 0
        indices = self._backend_utils.to_list(indices)
        thresholds = self._backend_utils.to_list(thresholds)
        for i in indices:
            if self._physx_rigid_body_apis[i] is None:
                if self._prims[i].HasAPI(PhysxSchema.PhysxRigidBodyAPI):
                    rigid_api = PhysxSchema.PhysxRigidBodyAPI(self._prims[i])
                else:
                    rigid_api = PhysxSchema.PhysxRigidBodyAPI.Apply(self._prims[i])
                self._physx_rigid_body_apis[i] = rigid_api
            self._physx_rigid_body_apis[i].GetSleepThresholdAttr().Set(thresholds[read_idx])
            read_idx += 1
        return

    def get_sleep_thresholds(
        self, indices: Optional[Union[np.ndarray, list, torch.Tensor, wp.array]] = None
    ) -> Union[np.ndarray, torch.Tensor, wp.indexedarray]:
        """Gets sleep thresholds of prims in the view.

        Args:
            indices (Optional[Union[np.ndarray, list, torch.Tensor, wp.array]], optional): indicies to specify which prims
                                                                                    to query. Shape (M,).
                                                                                    Where M <= size of the encapsulated prims in the view.
                                                                                    Defaults to None (i.e: all prims in the view)

        Returns:
            Union[np.ndarray, torch.Tensor, wp.indexedarray]: Mass-normalized kinetic energy threshold below which
                                            an actor may go to sleep. Range: [0, inf)
                                            Defaults: 0.00005 * tolerancesSpeed* tolerancesSpeed
                                            Units: distance^2 / second^2. shape (M,).
        """
        indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
        thresholds = np.zeros(indices.shape[0], dtype=np.float32)
        write_idx = 0
        indices = self._backend_utils.to_list(indices)
        for i in indices:
            if self._physx_rigid_body_apis[i] is None:
                if self._prims[i].HasAPI(PhysxSchema.PhysxRigidBodyAPI):
                    rigid_api = PhysxSchema.PhysxRigidBodyAPI(self._prims[i])
                else:
                    rigid_api = PhysxSchema.PhysxRigidBodyAPI.Apply(self._prims[i])
                self._physx_rigid_body_apis[i] = rigid_api

            thresholds[write_idx] = self._physx_rigid_body_apis[i].GetSleepThresholdAttr().Get()
            write_idx += 1
        thresholds = self._backend_utils.convert(thresholds, dtype="float32", device=self._device, indexed=True)
        return thresholds

    def enable_rigid_body_physics(
        self, indices: Optional[Union[np.ndarray, list, torch.Tensor, wp.array]] = None
    ) -> None:
        """
            Enable rigid body physics (enabled by default).
            Object will be moved by external forces such as gravity and collisions

        Args:
            indices (Optional[Union[np.ndarray, list, torch.Tensor, wp.array]], optional): indicies to specify which prims
                                                                                 to manipulate. Shape (M,).
                                                                                 Where M <= size of the encapsulated prims in the view.
                                                                                 Defaults to None (i.e: all prims in the view).
        """
        if not omni.timeline.get_timeline_interface().is_stopped() and self._physics_view is not None:
            indices = self._backend_utils.resolve_indices(indices, self.count, "cpu")
            data = self._physics_view.get_disable_simulations().reshape(self._count)
            data = self._backend_utils.assign(
                self._backend_utils.create_tensor_from_list([False] * len(indices), dtype="uint8"), data, indices
            )
            self._physics_view.set_disable_simulations(data, indices)
        else:
            indices = self._backend_utils.resolve_indices(indices, self.count, "cpu")
            indices = self._backend_utils.to_list(indices)
            for i in indices:
                if self._rigid_body_apis[i] is None:
                    if self._prims[i].HasAPI(UsdPhysics.RigidBodyAPI):
                        rigid_api = UsdPhysics.RigidBodyAPI(self._prims[i])
                    else:
                        rigid_api = UsdPhysics.RigidBodyAPI.Apply(self._prims[i])
                    self._rigid_body_apis[i] = rigid_api
                self._rigid_body_apis[i].GetRigidBodyEnabledAttr().Set(True)
            return

    def disable_rigid_body_physics(
        self, indices: Optional[Union[np.ndarray, list, torch.Tensor, wp.array]] = None
    ) -> None:
        """Disable rigid body physics (enabled by default).
            Object will not be moved by external forces such as gravity and collisions

        Args:
            indices (Optional[Union[np.ndarray, list, torch.Tensor, wp.array]], optional): indicies to specify which prims
                                                                                 to manipulate. Shape (M,).
                                                                                 Where M <= size of the encapsulated prims in the view.
                                                                                 Defaults to None (i.e: all prims in the view).
        """
        indices = self._backend_utils.resolve_indices(indices, self.count, "cpu")
        if not omni.timeline.get_timeline_interface().is_stopped() and self._physics_view is not None:
            data = self._physics_view.get_disable_simulations().reshape(self._count)
            data = self._backend_utils.assign(
                self._backend_utils.create_tensor_from_list([True] * len(indices), dtype="uint8"), data, indices
            )
            self._physics_view.set_disable_simulations(data, indices)
        else:
            indices = self._backend_utils.to_list(indices)
            for i in indices:
                if self._rigid_body_apis[i] is None:
                    if self._prims[i].HasAPI(UsdPhysics.RigidBodyAPI):
                        rigid_api = UsdPhysics.RigidBodyAPI(self._prims[i])
                    else:
                        rigid_api = UsdPhysics.RigidBodyAPI.Apply(self._prims[i])
                    self._rigid_body_apis[i] = rigid_api
                self._rigid_body_apis[i].GetRigidBodyEnabledAttr().Set(False)
            return

    def enable_gravities(self, indices: Optional[Union[np.ndarray, list, torch.Tensor, wp.array]] = None) -> None:
        """Enable gravity on rigid bodies (enabled by default).

        Args:
            indices (Optional[Union[np.ndarray, list, torch.Tensor, wp.array]], optional): indicies to specify which prims
                                                                                 to manipulate. Shape (M,).
                                                                                 Where M <= size of the encapsulated prims in the view.
                                                                                 Defaults to None (i.e: all prims in the view).
        """
        if not omni.timeline.get_timeline_interface().is_stopped() and self._physics_view is not None:
            indices = self._backend_utils.resolve_indices(indices, self.count, "cpu")
            data = self._physics_view.get_disable_gravities().reshape(self._count)
            data = self._backend_utils.assign(
                self._backend_utils.create_tensor_from_list([False] * len(indices), dtype="uint8"), data, indices
            )
            self._physics_view.set_disable_gravities(data, indices)
        else:
            indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
            indices = self._backend_utils.to_list(indices)
            for i in indices:
                if self._physx_rigid_body_apis[i] is None:
                    if self._prims[i].HasAPI(PhysxSchema.PhysxRigidBodyAPI):
                        rigid_api = PhysxSchema.PhysxRigidBodyAPI(self._prims[i])
                    else:
                        rigid_api = PhysxSchema.PhysxRigidBodyAPI.Apply(self._prims[i])
                    self._physx_rigid_body_apis[i] = rigid_api
                self._physx_rigid_body_apis[i].GetDisableGravityAttr().Set(True)

    def disable_gravities(self, indices: Optional[Union[np.ndarray, list, torch.Tensor, wp.array]] = None) -> None:
        """Disable gravity on rigid bodies (enabled by default).

        Args:
            indices (Optional[Union[np.ndarray, list, torch.Tensor, wp.array]], optional): indicies to specify which prims
                                                                                 to manipulate. Shape (M,).
                                                                                 Where M <= size of the encapsulated prims in the view.
                                                                                 Defaults to None (i.e: all prims in the view).
        """
        indices = self._backend_utils.resolve_indices(indices, self.count, "cpu")
        if not omni.timeline.get_timeline_interface().is_stopped() and self._physics_view is not None:
            data = self._physics_view.get_disable_gravities().reshape(self._count)
            data = self._backend_utils.assign(
                self._backend_utils.create_tensor_from_list([True] * len(indices), dtype="uint8"), data, indices
            )
            self._physics_view.set_disable_gravities(data, indices)
        else:
            indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
            indices = self._backend_utils.to_list(indices)
            for i in indices:
                if self._physx_rigid_body_apis[i] is None:
                    if self._prims[i].HasAPI(PhysxSchema.PhysxRigidBodyAPI):
                        rigid_api = PhysxSchema.PhysxRigidBodyAPI(self._prims[i])
                    else:
                        rigid_api = PhysxSchema.PhysxRigidBodyAPI.Apply(self._prims[i])
                    self._physx_rigid_body_apis[i] = rigid_api
                self._physx_rigid_body_apis[i].GetDisableGravityAttr().Set(False)
            return

    def set_default_state(
        self,
        positions: Optional[Union[np.ndarray, torch.Tensor, wp.array]] = None,
        orientations: Optional[Union[np.ndarray, torch.Tensor, wp.array]] = None,
        linear_velocities: Optional[Union[np.ndarray, torch.Tensor, wp.array]] = None,
        angular_velocities: Optional[Union[np.ndarray, torch.Tensor, wp.array]] = None,
        indices: Optional[Union[np.ndarray, list, torch.Tensor, wp.array]] = None,
    ) -> None:
        """Sets the default state of prims in the view, that will be used after each reset.

        Args:
            positions (Optional[Union[np.ndarray, torch.Tensor, wp.array]], optional): default positions in the world frame of the prim. shape is (M, 3).
            orientations (Optional[Union[np.ndarray, torch.Tensor, wp.array]], optional): default quaternion orientations in the world frame of the prims.
                                                           quaternion is scalar-first (w, x, y, z). shape is (M, 4).
            linear_velocities (Optional[Union[np.ndarray, torch.Tensor, wp.array]], optional): default linear velocities of each prim in the view
                                                                (to be applied in the first frame and on resets).
                                                                Shape is (M, 3). Defaults to None.
            angular_velocities (Optional[Union[np.ndarray, torch.Tensor, wp.array]], optional): default angular velocities of each prim in the view
                                                                 (to be applied in the first frame and on resets).
                                                                 Shape is (M, 3). Defaults to None.
            indices (Optional[Union[np.ndarray, list, torch.Tensor, wp.array]], optional): indicies to specify which prims
                                                                                 to manipulate. Shape (M,).
                                                                                 Where M <= size of the encapsulated prims in the view.
                                                                                 Defaults to None (i.e: all prims in the view).
        """
        XFormPrimView.set_default_state(self, positions=positions, orientations=orientations)
        indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
        if self._non_root_link:
            return
        if positions is not None:
            if indices is None:
                self._dynamics_default_state.positions = positions
            else:
                if self._backend == "warp":
                    self._dynamics_default_state.positions = self._backend_utils.assign(
                        positions, self._dynamics_default_state.positions, indices
                    )
                else:
                    self._dynamics_default_state.positions[indices] = positions
        if orientations is not None:
            if indices is None:
                self._dynamics_default_state.orientations = orientations
            else:
                if self._backend == "warp":
                    self._dynamics_default_state.orientations = self._backend_utils.assign(
                        orientations, self._dynamics_default_state.orientations, indices
                    )
                else:
                    self._dynamics_default_state.orientations[indices] = orientations
        if linear_velocities is not None:
            if indices is None:
                self._dynamics_default_state.linear_velocities = linear_velocities
            else:
                if self._backend == "warp":
                    self._dynamics_default_state.linear_velocities = self._backend_utils.assign(
                        linear_velocities, self._dynamics_default_state.linear_velocities, indices
                    )
                else:
                    self._dynamics_default_state.linear_velocities[indices] = linear_velocities
        if angular_velocities is not None:
            if indices is None:
                self._dynamics_default_state.angular_velocities = angular_velocities
            else:
                if self._backend == "warp":
                    self._dynamics_default_state.angular_velocities = self._backend_utils.assign(
                        angular_velocities, self._dynamics_default_state.angular_velocities, indices
                    )
                else:
                    self._dynamics_default_state.angular_velocities[indices] = angular_velocities
        return

    def get_default_state(self) -> DynamicsViewState:
        """Gets the default state of prims in the view, that will be used after each reset.

        Returns:
            DynamicsViewState: returns the default state of the prims (positions, orientations, linear_velocities and
                          angular_velocities) that is used after each reset.
        """
        return self._dynamics_default_state

    def post_reset(self) -> None:
        """Resets the prims to its default state."""
        XFormPrimView.post_reset(self)
        if not self._non_root_link:
            self.set_velocities(
                velocities=self._backend_utils.tensor_cat(
                    [self._dynamics_default_state.linear_velocities, self._dynamics_default_state.angular_velocities],
                    dim=-1,
                    device=self._device,
                )
            )
        return

    def get_current_dynamic_state(self) -> DynamicsViewState:
        """
        Returns:
            DynamicState: the dynamic state of the rigid bodies including positions, orientations, linear_velocities and angular_velocities.
        """
        positions, orientations = self.get_world_poses()
        return DynamicsViewState(
            positions=positions,
            orientations=orientations,
            linear_velocities=self.get_linear_velocities(),
            angular_velocities=self.get_angular_velocities(),
        )

    def get_net_contact_forces(
        self,
        indices: Optional[Union[np.ndarray, List, torch.Tensor, wp.array]] = None,
        clone: bool = True,
        dt: float = 1.0,
    ) -> Union[np.ndarray, torch.Tensor, wp.indexedarray]:
        """
        If contact forces of the prims in the view are tracked, this method returns the net contact forces on prims.
        i.e., a matrix of dimension (self.count, 3)

        Args:
            indices (Optional[Union[np.ndarray, list, torch.Tensor, wp.array]], optional): indicies to specify which prims
                                                                                 to query. Shape (M,).
                                                                                 Where M <= size of the encapsulated prims in the view.
                                                                                 Defaults to None (i.e: all prims in the view).
            clone (bool, optional): True to return a clone of the internal buffer. Otherwise False. Defaults to True.
            dt (float): time step multiplier to convert the underlying impulses to forces. If the default value is used then the forces are in fact contact impulses

        Returns:
            Union[np.ndarray, torch.Tensor, wp.indexedarray]: Net contact forces of the prims with shape (M,3).

        """
        if self._track_contact_forces:
            return self._contact_view.get_net_contact_forces(indices, clone, dt)
        else:
            carb.log_warn(
                "contact forces cannot be retrieved with this API unless the RigidPrimView is initialized with track_contact_forces= True."
            )
            return None

    def get_contact_force_matrix(
        self,
        indices: Optional[Union[np.ndarray, List, torch.Tensor, wp.array]] = None,
        clone: bool = True,
        dt: float = 1.0,
    ) -> Union[np.ndarray, torch.Tensor, wp.indexedarray]:
        """
        If the object is initialized with filter_paths_expr list, this method returns the contact forces between the prims
        in the view and the filter prims. i.e., a matrix of dimension (self.count, self._contact_view.num_filters, 3)
        where num_filters is the determined according to the filter_paths_expr parameter.

        Args:
            indices (Optional[Union[np.ndarray, list, torch.Tensor, wp.array]], optional): indicies to specify which prims
                                                                                 to query. Shape (M,).
                                                                                 Where M <= size of the encapsulated prims in the view.
                                                                                 Defaults to None (i.e: all prims in the view).
            clone (bool, optional): True to return a clone of the internal buffer. Otherwise False. Defaults to True.
            dt (float): time step multiplier to convert the underlying impulses to forces. If the default value is used then the forces are in fact contact impulses

        Returns:
            Union[np.ndarray, torch.Tensor, wp.indexedarray]: Net contact forces of the prims with shape (M, self._contact_view.num_filters, 3).
        """
        if len(self._contact_filter_prim_paths_expr) != 0:
            return self._contact_view.get_contact_force_matrix(indices, clone, dt)
        else:
            carb.log_warn(
                "No filter is specified for get_contact_force_matrix. Initialize the RigidPrimView with the contact_filter_prim_paths_expr and specify a list of filters."
            )
            return None
