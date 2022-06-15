# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
from typing import Optional, Tuple, Union
from omni.isaac.core.prims import XFormPrimView
from omni.isaac.core.utils.types import DynamicsViewState
import omni.kit.app
import numpy as np
from omni.isaac.core.utils.prims import get_prim_parent
from pxr import Gf, Usd, UsdGeom, UsdPhysics, PhysxSchema
import torch
import carb


class RigidPrimView(XFormPrimView):
    """Provides high level functions to deal with prims that has rigid body api applied to it (1 or more rigid body prims) 
        as well as its attributes/ properties.
        This object wraps all matching Rigid Prims found at the regex provided at the prim_paths_expr.

        Note: - each prim will have "xformOp:orient", "xformOp:translate" and "xformOp:scale" only post init,
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
            positions (Optional[Union[np.ndarray, torch.Tensor]], optional): 
                                                            default positions in the world frame of the prims. 
                                                            shape is (N, 3).
                                                            Defaults to None, which means left unchanged.
            translations (Optional[Union[np.ndarray, torch.Tensor]], optional): 
                                                            default translations in the local frame of the prims
                                                            (with respect to its parent prims). shape is (N, 3).
                                                            Defaults to None, which means left unchanged.
            orientations (Optional[Union[np.ndarray, torch.Tensor]], optional): 
                                                            default quaternion orientations in the world/ local frame of the prims
                                                            (depends if translation or position is specified).
                                                            quaternion is scalar-first (w, x, y, z). shape is (N, 4).
                                                            Defaults to None, which means left unchanged.
            scales (Optional[Union[np.ndarray, torch.Tensor]], optional): local scales to be applied to 
                                                            the prim's dimensions in the view. shape is (N, 3).
                                                            Defaults to None, which means left unchanged.
            visibilities (Optional[Union[np.ndarray, torch.Tensor]], optional): set to false for an invisible prim in 
                                                                                the stage while rendering. shape is (N,). 
                                                                                Defaults to None.
            masses (Optional[Union[np.ndarray, torch.Tensor]], optional): mass in kg specified for each prim in the view. 
                                                                          shape is (N,). Defaults to None.
            densities (Optional[Union[np.ndarray, torch.Tensor]], optional): density in kg/m^3 specified for each prim in the view. 
                                                                          shape is (N,). Defaults to None.
            linear_velocities (Optional[Union[np.ndarray, torch.Tensor]], optional): default linear velocity of each prim in the view
                                                                                     (to be applied in the first frame and on resets). 
                                                                                     Shape is (N, 3). Defaults to None.
            angular_velocities (Optional[Union[np.ndarray, torch.Tensor]], optional): default angular velocity of each prim in the view
                                                                                     (to be applied in the first frame and on resets). 
                                                                                     Shape is (N, 3). Defaults to None.
        """

    def __init__(
        self,
        prim_paths_expr: str,
        name: str = "rigid_prim_view",
        positions: Optional[Union[np.ndarray, torch.Tensor]] = None,
        translations: Optional[Union[np.ndarray, torch.Tensor]] = None,
        orientations: Optional[Union[np.ndarray, torch.Tensor]] = None,
        scales: Optional[Union[np.ndarray, torch.Tensor]] = None,
        visibilities: Optional[Union[np.ndarray, torch.Tensor]] = None,
        masses: Optional[Union[np.ndarray, torch.Tensor]] = None,
        densities: Optional[Union[np.ndarray, torch.Tensor]] = None,
        linear_velocities: Optional[Union[np.ndarray, torch.Tensor]] = None,
        angular_velocities: Optional[Union[np.ndarray, torch.Tensor]] = None,
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
        )
        self._rigid_body_apis = []
        self._mass_apis = []
        self._regex_prim_paths = prim_paths_expr
        self._physx_rigid_body_apis = []
        for prim in self._prims:
            if prim.HasAPI(UsdPhysics.RigidBodyAPI):
                rigid_api = UsdPhysics.RigidBodyAPI(prim)
            else:
                rigid_api = UsdPhysics.RigidBodyAPI.Apply(prim)
            rigid_api.CreateRigidBodyEnabledAttr(True)
            self._rigid_body_apis.append(rigid_api)
            if prim.HasAPI(UsdPhysics.MassAPI):
                self._mass_apis.append(UsdPhysics.MassAPI(prim))
            else:
                self._mass_apis.append(UsdPhysics.MassAPI.Apply(prim))
            if prim.HasAPI(PhysxSchema.PhysxRigidBodyAPI):
                self._physx_rigid_body_apis.append(PhysxSchema.PhysxRigidBodyAPI(prim))
            else:
                self._physx_rigid_body_apis.append(PhysxSchema.PhysxRigidBodyAPI.Apply(prim))
        if linear_velocities is not None:
            self.set_linear_velocities(linear_velocities)
        if angular_velocities is not None:
            self.set_angular_velocities(angular_velocities)
        if masses is not None:
            RigidPrimView.set_masses(self, masses)
        if densities is not None:
            RigidPrimView.set_densities(self, densities)
        linear_velocities = self.get_linear_velocities()
        angular_velocities = self.get_angular_velocities()
        self._dynamics_default_state = DynamicsViewState(
            self._default_state.positions, self._default_state.orientations, linear_velocities, angular_velocities
        )
        timeline = omni.timeline.get_timeline_interface()
        self._invalidate_physics_handle_event = timeline.get_timeline_event_stream().create_subscription_to_pop(
            self._invalidate_physics_handle_callback
        )
        return

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
        carb.log_info("Rigid Prim View Device: {}".format(self._device))
        return

    def _invalidate_physics_handle_callback(self, event):
        if event.type == int(omni.timeline.TimelineEventType.STOP):
            self._physics_view = None
        return

    def set_world_poses(
        self,
        positions: Optional[Union[np.ndarray, torch.Tensor]] = None,
        orientations: Optional[Union[np.ndarray, torch.Tensor]] = None,
        indices: Optional[Union[np.ndarray, list, torch.Tensor]] = None,
    ) -> None:
        """Sets poses of prims in the view with respect to the world's frame.

        Args:
            positions (Optional[Union[np.ndarray, torch.Tensor]], optional): positions in the world frame of the prim. shape is (M, 3).
                                                                             Defaults to None, which means left unchanged.
            orientations (Optional[Union[np.ndarray, torch.Tensor]], optional): quaternion orientations in the world frame of the prims. 
                                                                                quaternion is scalar-first (w, x, y, z). shape is (M, 4).
                                                                                Defaults to None, which means left unchanged.
            indices (Optional[Union[np.ndarray, list, torch.Tensor]], optional): indicies to specify which prims 
                                                                                 to manipulate. Shape (M,).
                                                                                 Where M <= size of the encapsulated prims in the view.
                                                                                 Defaults to None (i.e: all prims in the view).
        """
        if not omni.timeline.get_timeline_interface().is_stopped() and self._physics_view is not None:
            self._physics_sim_view.enable_warnings(False)
            indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
            current_positions, current_orientations = self.get_world_poses(clone=False)
            if positions is None:
                positions = current_positions[indices]
            if orientations is None:
                orientations = current_orientations[indices]
            orientations = orientations[:, [1, 2, 3, 0]]
            current_orientations = current_orientations[:, [1, 2, 3, 0]]
            old_pose = self._backend_utils.get_pose(current_positions, current_orientations, device=self._device)
            new_pose = self._backend_utils.get_pose(positions, orientations, device=self._device)
            old_pose[indices] = new_pose
            self._physics_view.set_transforms(old_pose, indices)
            self._physics_sim_view.enable_warnings(True)
            return
        else:
            XFormPrimView.set_world_poses(self, positions=positions, orientations=orientations, indices=indices)
        return

    def get_world_poses(
        self, indices: Optional[Union[np.ndarray, list, torch.Tensor]] = None, clone: bool = True
    ) -> Union[Tuple[np.ndarray, np.ndarray], Tuple[torch.Tensor, torch.Tensor]]:
        """Gets the poses of the prims in the view with respect to the world's frame.

        Args:
            indices (Optional[Union[np.ndarray, list, torch.Tensor]], optional): indicies to specify which prims 
                                                                                 to query. Shape (M,).
                                                                                 Where M <= size of the encapsulated prims in the view.
                                                                                 Defaults to None (i.e: all prims in the view).
            clone (bool, optional): True to return a clone of the internal buffer. Otherwise False. Defaults to True.

        Returns:
            Union[Tuple[np.ndarray, np.ndarray], Tuple[torch.Tensor, torch.Tensor]]: 
                                        first index is positions in the world frame of the prims. shape is (M, 3). 
                                           second index is quaternion orientations in the world frame of the prims.
                                           quaternion is scalar-first (w, x, y, z). shape is (M, 4).
        """
        if not omni.timeline.get_timeline_interface().is_stopped() and self._physics_view is not None:
            self._physics_sim_view.enable_warnings(False)
            indices = self._backend_utils.resolve_indices(indices, self.count, self._device)

            pose = self._physics_view.get_transforms()
            self._physics_sim_view.enable_warnings(True)
            if not clone:
                return pose[indices, 0:3], pose[indices, 3:7][:, [3, 0, 1, 2]]
            else:
                return (
                    self._backend_utils.clone_tensor(pose[indices, 0:3], device=self._device),
                    self._backend_utils.clone_tensor(pose[indices, 3:7][:, [3, 0, 1, 2]], device=self._device),
                )
        else:
            return XFormPrimView.get_world_poses(self, indices=indices)

    def get_local_poses(
        self, indices: Optional[Union[np.ndarray, list, torch.Tensor]] = None, clone: bool = True
    ) -> Union[Tuple[np.ndarray, np.ndarray], Tuple[torch.Tensor, torch.Tensor]]:
        """Gets prim poses in the view with respect to the local frame (the prim's parent frame).
        Args:
            indices (Optional[Union[np.ndarray, list, torch.Tensor]], optional): indicies to specify which prims 
                                                                                    to query. Shape (M,).
                                                                                    Where M <= size of the encapsulated prims in the view.
                                                                                    Defaults to None (i.e: all prims in the view)
            clone (bool, optional): True to return a clone of the internal buffer. Otherwise False. Defaults to True.

        Returns:
            Union[Tuple[np.ndarray, np.ndarray], Tuple[torch.Tensor, torch.Tensor]]: 
                                                            first index is positions in the local frame of the prims. shape is (M, 3). 
                                                        second index is quaternion orientations in the local frame of the prims.
                                                        quaternion is scalar-first (w, x, y, z). shape is (M, 4).
        """
        if not omni.timeline.get_timeline_interface().is_stopped() and self._physics_view is not None:
            indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
            world_positions, world_orientations = self.get_world_poses(indices=indices)
            parent_transforms = self._backend_utils.create_zeros_tensor(
                shape=[indices.shape[0], 4, 4], dtype="float32", device=self._device
            )
            write_idx = 0
            for i in indices:
                parent_transforms[write_idx] = self._backend_utils.create_tensor_from_list(
                    UsdGeom.Xformable(get_prim_parent(self._prims[i.tolist()])).ComputeLocalToWorldTransform(
                        Usd.TimeCode.Default()
                    ),
                    dtype="float32",
                    device=self._device,
                )
                write_idx += 1
            return self._backend_utils.get_local_from_world(
                parent_transforms, world_positions, world_orientations, self._device
            )
        else:
            return XFormPrimView.get_local_poses(self, indices=indices)

    def set_local_poses(
        self,
        translations: Optional[Union[np.ndarray, torch.Tensor]] = None,
        orientations: Optional[Union[np.ndarray, torch.Tensor]] = None,
        indices: Optional[Union[np.ndarray, list, torch.Tensor]] = None,
    ) -> None:
        """Sets prim poses in the view with respect to the local frame (the prim's parent frame).

        Args:
            translations (Optional[Union[np.ndarray, torch.Tensor]], optional): 
                                                          translations in the local frame of the prims
                                                          (with respect to its parent prim). shape is (M, 3).
                                                          Defaults to None, which means left unchanged.
            orientations (Optional[Union[np.ndarray, torch.Tensor]], optional): 
                                                          quaternion orientations in the local frame of the prims. 
                                                          quaternion is scalar-first (w, x, y, z). shape is (M, 4).
                                                          Defaults to None, which means left unchanged.
            indices (Optional[Union[np.ndarray, list, torch.Tensor]], optional): indicies to specify which prims 
                                                                                 to manipulate. Shape (M,).
                                                                                 Where M <= size of the encapsulated prims in the view.
                                                                                 Defaults to None (i.e: all prims in the view).
        """
        if not omni.timeline.get_timeline_interface().is_stopped() and self._physics_view is not None:
            if translations is None or orientations is None:
                current_translations, current_orientations = RigidPrimView.get_local_poses(self)
                if translations is None:
                    translations = current_translations
                if orientations is None:
                    orientations = current_orientations
            self._physics_sim_view.enable_warnings(False)
            indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
            parent_transforms = self._backend_utils.create_zeros_tensor(
                shape=[indices.shape[0], 4, 4], dtype="float32", device=self._device
            )
            write_idx = 0
            for i in indices:
                parent_transforms[write_idx] = self._backend_utils.create_tensor_from_list(
                    UsdGeom.Xformable(get_prim_parent(self._prims[i.tolist()])).ComputeLocalToWorldTransform(
                        Usd.TimeCode.Default()
                    ),
                    dtype="float32",
                    device=self._device,
                )
                write_idx += 1
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
        velocities: Optional[Union[np.ndarray, torch.Tensor]],
        indices: Optional[Union[np.ndarray, list, torch.Tensor]] = None,
    ):
        """Sets the linear velocities of the prims in the view. The method does this through the physx API only.
            i.e: It has to be called after initialization.
            Note: This method is not supported for the gpu pipeline. set_velocities method should be used instead.

        Args:
            velocities (Optional[Union[np.ndarray, torch.Tensor]]): linear velocities to set the rigid prims to. shape is (M, 3).
            indices (Optional[Union[np.ndarray, list, torch.Tensor]], optional): indicies to specify which prims 
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
            current_velocities = self._backend_utils.clone_tensor(
                self._physics_view.get_velocities(), device=self._device
            )
            current_velocities[indices, 0:3] = self._backend_utils.move_data(velocities, device=self._device)
            self._physics_view.set_velocities(current_velocities, indices)
            self._physics_sim_view.enable_warnings(True)
        else:
            idx_count = 0
            for i in indices:
                self._rigid_body_apis[i.tolist()].GetVelocityAttr().Set(Gf.Vec3f(velocities[idx_count].tolist()))
                idx_count += 1
            return

    def get_linear_velocities(
        self, indices: Optional[Union[np.ndarray, list, torch.Tensor]] = None, clone: bool = True
    ) -> Union[np.ndarray, torch.Tensor]:
        """Gets the linear velocities of prims in the view.

        Args:
            indices (Optional[Union[np.ndarray, list, torch.Tensor]], optional): indicies to specify which prims 
                                                                                    to query. Shape (M,).
                                                                                    Where M <= size of the encapsulated prims in the view.
                                                                                    Defaults to None (i.e: all prims in the view)
            clone (bool, optional): True to return a clone of the internal buffer. Otherwise False. Defaults to True.

        Returns:
            Union[np.ndarray, torch.Tensor]: linear velocities of the prims in the view. shape is (M, 3).
        """
        indices = self._backend_utils.resolve_indices(indices, self.count, self._device)

        if not omni.timeline.get_timeline_interface().is_stopped() and self._physics_view is not None:
            self._physics_sim_view.enable_warnings(False)
            linear_velocities = self._physics_view.get_velocities()
            self._physics_sim_view.enable_warnings(True)
            if not clone:
                return linear_velocities[indices, 0:3]
            else:
                return self._backend_utils.clone_tensor(linear_velocities[indices, 0:3], device=self._device)
        else:
            linear_velocities = self._backend_utils.create_zeros_tensor(
                [indices.shape[0], 3], dtype="float32", device=self._device
            )
            write_idx = 0
            for i in indices:
                linear_velocities[write_idx] = self._backend_utils.create_tensor_from_list(
                    self._rigid_body_apis[i.tolist()].GetVelocityAttr().Get(), dtype="float32", device=self._device
                )
                write_idx += 1
            return linear_velocities

    def set_angular_velocities(
        self,
        velocities: Optional[Union[np.ndarray, torch.Tensor]],
        indices: Optional[Union[np.ndarray, list, torch.Tensor]] = None,
    ) -> None:
        """Sets the angular velocities of the prims in the view. The method does this through the physx API only.
            i.e: It has to be called after initialization.
            Note: This method is not supported for the gpu pipeline. set_velocities method should be used instead.

        Args:
            velocities (Optional[Union[np.ndarray, torch.Tensor]]): angular velocities to set the rigid prims to. shape is (M, 3).
            indices (Optional[Union[np.ndarray, list, torch.Tensor]], optional): indicies to specify which prims 
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
            current_velocities = self._backend_utils.clone_tensor(
                self._physics_view.get_velocities(), device=self._device
            )
            current_velocities[indices, 3:6] = self._backend_utils.move_data(velocities, self._device)
            self._physics_view.set_velocities(current_velocities, indices)
            self._physics_sim_view.enable_warnings(True)
        else:
            idx_count = 0
            for i in indices:
                self._rigid_body_apis[i].GetAngularVelocityAttr().Set(Gf.Vec3f(velocities[idx_count].tolist()))
                idx_count += 1
        return

    def get_angular_velocities(
        self, indices: Optional[Union[np.ndarray, list, torch.Tensor]] = None, clone: bool = True
    ) -> Union[np.ndarray, torch.Tensor]:
        """Gets the angular velocities of prims in the view.

        Args:
            indices (Optional[Union[np.ndarray, list, torch.Tensor]], optional): indicies to specify which prims 
                                                                                    to query. Shape (M,).
                                                                                    Where M <= size of the encapsulated prims in the view.
                                                                                    Defaults to None (i.e: all prims in the view)
            clone (bool, optional): True to return a clone of the internal buffer. Otherwise False. Defaults to True.

        Returns:
            Union[np.ndarray, torch.Tensor]: angular velocities of the prims in the view. shape is (M, 3).
        """
        indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
        if not omni.timeline.get_timeline_interface().is_stopped() and self._physics_view is not None:
            self._physics_sim_view.enable_warnings(False)
            angular_velocities = self._physics_view.get_velocities()
            self._physics_sim_view.enable_warnings(True)
            if not clone:
                return angular_velocities[indices, 3:6]
            else:
                return self._backend_utils.clone_tensor(angular_velocities[indices, 3:6], device=self._device)
        else:
            angular_velocities = self._backend_utils.create_zeros_tensor(
                [indices.shape[0], 3], dtype="float32", device=self._device
            )
            write_idx = 0
            for i in indices:
                angular_velocities[write_idx] = self._backend_utils.create_tensor_from_list(
                    self._rigid_body_apis[i.tolist()].GetAngularVelocityAttr().Get(),
                    dtype="float32",
                    device=self._device,
                )
                write_idx += 1
            return angular_velocities

    def set_velocities(
        self,
        velocities: Union[np.ndarray, torch.Tensor],
        indices: Optional[Union[np.ndarray, list, torch.Tensor]] = None,
    ) -> Union[np.ndarray, torch.Tensor]:
        """Sets the linear and angular velocities of the prims in the view at once. The method does this through the physx API only.
            i.e: It has to be called after initialization.

        Args:
            velocities (Optional[Union[np.ndarray, torch.Tensor]]): linear and angular velocities respectively to set the rigid prims to. shape is (M, 6).
            indices (Optional[Union[np.ndarray, list, torch.Tensor]], optional): indicies to specify which prims 
                                                                                 to manipulate. Shape (M,).
                                                                                 Where M <= size of the encapsulated prims in the view.
                                                                                 Defaults to None (i.e: all prims in the view).
        """
        indices = self._backend_utils.resolve_indices(indices, self.count, self._device)

        if not omni.timeline.get_timeline_interface().is_stopped() and self._physics_view is not None:
            self._physics_sim_view.enable_warnings(False)
            new_velocities = self._backend_utils.clone_tensor(self._physics_view.get_velocities(), device=self._device)
            new_velocities[indices] = self._backend_utils.move_data(velocities, self._device)
            self._physics_view.set_velocities(new_velocities, indices)
            self._physics_sim_view.enable_warnings(True)
        else:
            self.set_linear_velocities(velocities[:, 0:3], indices)
            self.set_angular_velocities(velocities[:, 3:6], indices)
        return

    def get_velocities(
        self, indices: Optional[Union[np.ndarray, list, torch.Tensor]] = None, clone: bool = True
    ) -> Union[np.ndarray, torch.Tensor]:
        """Gets the linear and angular velocities of prims in the view.

        Args:
            indices (Optional[Union[np.ndarray, list, torch.Tensor]], optional): indicies to specify which prims 
                                                                                    to query. Shape (M,).
                                                                                    Where M <= size of the encapsulated prims in the view.
                                                                                    Defaults to None (i.e: all prims in the view)
            clone (bool, optional): True to return a clone of the internal buffer. Otherwise False. Defaults to True.

        Returns:
            Union[np.ndarray, torch.Tensor]: linear and angular velocities of the prims in the view concatenated. shape is (M, 6).
        """
        indices = self._backend_utils.resolve_indices(indices, self.count, self._device)

        if not omni.timeline.get_timeline_interface().is_stopped() and self._physics_view is not None:
            self._physics_sim_view.enable_warnings(False)
            velocities = self._physics_view.get_velocities()
            self._physics_sim_view.enable_warnings(True)
            if not clone:
                return velocities[indices]
            else:
                return self._backend_utils.clone_tensor(velocities, device=self._device)[indices]
        else:
            return self._backend_utils.tensor_cat(
                [self.get_linear_velocities(indices, clone), self.get_angular_velocities(indices, clone)], dim=-1
            )

    def apply_forces(
        self,
        forces: Optional[Union[np.ndarray, torch.Tensor]],
        indices: Optional[Union[np.ndarray, list, torch.Tensor]] = None,
    ) -> None:
        """Applies forces to prims in the view.

        Args:
            forces (Optional[Union[np.ndarray, torch.Tensor]]): forces to be applied to the prims.
            indices (Optional[Union[np.ndarray, list, torch.Tensor]], optional): indicies to specify which prims 
                                                                                 to manipulate. Shape (M,).
                                                                                 Where M <= size of the encapsulated prims in the view.
                                                                                 Defaults to None (i.e: all prims in the view).
        """
        if not omni.timeline.get_timeline_interface().is_stopped() and self._physics_view is not None:
            self._physics_sim_view.enable_warnings(False)
            forces = forces.reshape(-1, 3)
            indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
            new_forces = self._backend_utils.create_zeros_tensor([self.count, 3], device=self._device, dtype="float32")
            new_forces[indices] = self._backend_utils.move_data(forces, self._device)
            self._physics_view.apply_forces(new_forces, indices)
            self._physics_sim_view.enable_warnings(True)
        else:
            carb.log_warn("Physics Simulation View is not created yet")

    def set_masses(
        self,
        masses: Optional[Union[np.ndarray, torch.Tensor]],
        indices: Optional[Union[np.ndarray, list, torch.Tensor]] = None,
    ) -> None:
        """Sets masses of prims in the view.

        Args:
            masses (Optional[Union[np.ndarray, torch.Tensor]]): masses of the prims in kg. shape (M,).
            indices (Optional[Union[np.ndarray, list, torch.Tensor]], optional): indicies to specify which prims 
                                                                                 to manipulate. Shape (M,).
                                                                                 Where M <= size of the encapsulated prims in the view.
                                                                                 Defaults to None (i.e: all prims in the view).
        """
        indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
        read_idx = 0
        for i in indices:
            self._mass_apis[i.tolist()].GetMassAttr().Set(masses[read_idx].tolist())
            read_idx += 1
        return

    def get_masses(
        self, indices: Optional[Union[np.ndarray, list, torch.Tensor]] = None
    ) -> Union[np.ndarray, torch.Tensor]:
        """Gets masses of prims in the view.

        Args:
            indices (Optional[Union[np.ndarray, list, torch.Tensor]], optional): indicies to specify which prims 
                                                                                    to query. Shape (M,).
                                                                                    Where M <= size of the encapsulated prims in the view.
                                                                                    Defaults to None (i.e: all prims in the view)
        Returns:
            Union[np.ndarray, torch.Tensor]: masses of the prims in kg. shape (M,)
        """
        indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
        masses = self._backend_utils.create_zeros_tensor([indices.shape[0]], dtype="float32", device=self._device)
        write_idx = 0
        for i in indices:
            masses[write_idx] = self._backend_utils.create_tensor_from_list(
                self._mass_apis[i.tolist()].GetMassAttr().Get(), dtype="float32", device=self._device
            )
            write_idx += 1
        return masses

    def set_densities(
        self,
        densities: Optional[Union[np.ndarray, torch.Tensor]],
        indices: Optional[Union[np.ndarray, list, torch.Tensor]] = None,
    ) -> None:
        """Sets densities of prims in the view.

        Args:
            densities (Optional[Union[np.ndarray, torch.Tensor]]): density in kg/m^3 specified for each prim in the view. 
                                                                    shape is (M,). Defaults to None.
            indices (Optional[Union[np.ndarray, list, torch.Tensor]], optional): indicies to specify which prims 
                                                                                 to manipulate. Shape (M,).
                                                                                 Where M <= size of the encapsulated prims in the view.
                                                                                 Defaults to None (i.e: all prims in the view).
        """
        indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
        read_idx = 0
        for i in indices:
            self._mass_apis[i.tolist()].GetMassAttr().Set(densities[read_idx].tolist())
            read_idx += 1
        return

    def get_densities(
        self, indices: Optional[Union[np.ndarray, list, torch.Tensor]] = None
    ) -> Union[np.ndarray, torch.Tensor]:
        """Gets densities of prims in the view.

        Args:
            indices (Optional[Union[np.ndarray, list, torch.Tensor]], optional): indicies to specify which prims 
                                                                                    to query. Shape (M,).
                                                                                    Where M <= size of the encapsulated prims in the view.
                                                                                    Defaults to None (i.e: all prims in the view)
            
        Returns:
            Union[np.ndarray, torch.Tensor]: densities of prims in the view in kg/m^3. shape (M,).
        """
        indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
        densities = self._backend_utils.create_zeros_tensor([indices.shape[0]], dtype="float32", device=self._device)
        write_idx = 0
        for i in indices:
            densities[write_idx] = self._backend_utils.create_tensor_from_list(
                self._mass_apis[i.tolist()].GetMassAttr().Get(), dtype="float32", device=self._device
            )
            write_idx += 1
        return densities

    def enable_rigid_body_physics(self, indices: Optional[Union[np.ndarray, list, torch.Tensor]] = None) -> None:
        """
            enable rigid body physics (enabled by default):
            Object will be moved by external forces such as gravity and collisions

        Args:
            indices (Optional[Union[np.ndarray, list, torch.Tensor]], optional): indicies to specify which prims 
                                                                                 to manipulate. Shape (M,).
                                                                                 Where M <= size of the encapsulated prims in the view.
                                                                                 Defaults to None (i.e: all prims in the view).
        """
        indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
        for i in indices:
            self._rigid_body_apis[i.tolist()].GetRigidBodyEnabledAttr().Set(True)
        return

    def disable_rigid_body_physics(self, indices: Optional[Union[np.ndarray, list, torch.Tensor]] = None) -> None:
        """ disable rigid body physics (enabled by default):
            Object will not be moved by external forces such as gravity and collisions

        Args:
            indices (Optional[Union[np.ndarray, list, torch.Tensor]], optional): indicies to specify which prims 
                                                                                 to manipulate. Shape (M,).
                                                                                 Where M <= size of the encapsulated prims in the view.
                                                                                 Defaults to None (i.e: all prims in the view).
        """
        indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
        for i in indices:
            self._rigid_body_apis[i.tolist()].GetRigidBodyEnabledAttr().Set(False)
        return

    def set_default_state(
        self,
        positions: Optional[np.ndarray] = None,
        orientations: Optional[np.ndarray] = None,
        linear_velocities: Optional[np.ndarray] = None,
        angular_velocities: Optional[np.ndarray] = None,
        indices: Optional[Union[np.ndarray, list, torch.Tensor]] = None,
    ) -> None:
        """Sets the default state of prims in the view, that will be used after each reset. 

        Args:
            positions (Optional[np.ndarray], optional): default positions in the world frame of the prim. shape is (M, 3).
            orientations (Optional[np.ndarray], optional): default quaternion orientations in the world frame of the prims.
                                                        quaternion is scalar-first (w, x, y, z). shape is (M, 4).
            linear_velocities (Optional[np.ndarray], optional): default linear velocities of each prim in the view
                                                                    (to be applied in the first frame and on resets).
                                                                     Shape is (M, 3). Defaults to None.
            angular_velocities (Optional[np.ndarray], optional): default angular velocities of each prim in the view
                                                                    (to be applied in the first frame and on resets).
                                                                     Shape is (M, 3). Defaults to None.
            indices (Optional[Union[np.ndarray, list, torch.Tensor]], optional): indicies to specify which prims 
                                                                                 to manipulate. Shape (M,).
                                                                                 Where M <= size of the encapsulated prims in the view.
                                                                                 Defaults to None (i.e: all prims in the view).
        """
        XFormPrimView.set_default_state(self, positions=positions, orientations=orientations)
        if positions is not None:
            if indices is None:
                self._dynamics_default_state.positions = positions
            else:
                self._dynamics_default_state.positions[indices] = positions
        if orientations is not None:
            if indices is None:
                self._dynamics_default_state.orientations = orientations
            else:
                self._dynamics_default_state.orientations[indices] = orientations
        if linear_velocities is not None:
            if indices is None:
                self._dynamics_default_state.linear_velocities = linear_velocities
            else:
                self._dynamics_default_state.linear_velocities[indices] = linear_velocities
        if angular_velocities is not None:
            if indices is None:
                self._dynamics_default_state.angular_velocities = angular_velocities
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
        """Resets the prims to its default state.
        """
        XFormPrimView.post_reset(self)
        if not self._non_root_link:
            self.set_velocities(
                velocities=self._backend_utils.tensor_cat(
                    [self._dynamics_default_state.linear_velocities, self._dynamics_default_state.angular_velocities],
                    dim=-1,
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
