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

        # TODO: move to colner api?
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
        return

    def initialize(self, physics_sim_view=None) -> None:
        """[summary]
        """
        if physics_sim_view is None:
            physics_sim_view = omni.physics.tensors.create_simulation_view(self._backend)
            physics_sim_view.set_subspace_roots("/")
        carb.log_info("initializing view for {}".format(self._name))
        self._physics_sim_view = physics_sim_view
        self._physics_view = physics_sim_view.create_rigid_body_view(self._regex_prim_paths.replace(".*", "*"))
        carb.log_info("Rigid Prim View Device: {}".format(self._device))
        return

    def set_world_poses(
        self,
        positions: Optional[Union[np.ndarray, torch.Tensor]] = None,
        orientations: Optional[Union[np.ndarray, torch.Tensor]] = None,
        indices: Optional[Union[np.ndarray, list, torch.Tensor]] = None,
    ) -> None:
        """Sets prim's pose in the view with respect to the world's frame.

        Args:
            positions (Optional[Union[np.ndarray, torch.Tensor]], optional): positions in the world frame of the prim. shape is (M, 3).
                                                                             Defaults to None, which means left unchanged.
            orientations (Optional[Union[np.ndarray, torch.Tensor]], optional): quaternion orientations in the world frame of the prims. 
                                                                                quaternion is scalar-first (w, x, y, z). shape is (M, 4).
                                                                                Defaults to None, which means left unchanged.
            indices (Optional[Union[np.ndarray, list, torch.Tensor]], optional): indicies to specify which prims 
                                                                                 to query. Shape (M,).
                                                                                 Where M <= size of the encapsulated prims in the view.
                                                                                 Defaults to None (i.e: all prims in the view).

        Raises:
            Exception: [description]
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
        self, indices: Optional[Union[np.ndarray, list, torch.Tensor]] = None, clone=True
    ) -> Union[Tuple[np.ndarray, np.ndarray], Tuple[torch.Tensor, torch.Tensor]]:
        """Gets prim's pose in the view with respect to the world's frame.

        Args:
            indices (Optional[Union[np.ndarray, list, torch.Tensor]], optional): indicies to specify which prims 
                                                                                 to query. Shape (M,).
                                                                                 Where M <= size of the encapsulated prims in the view.
                                                                                 Defaults to None (i.e: all prims in the view).

        Raises:
            Exception: [description]

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
        self, indices: Optional[Union[np.ndarray, list, torch.Tensor]] = None, clone=True
    ) -> Union[Tuple[np.ndarray, np.ndarray], Tuple[torch.Tensor, torch.Tensor]]:
        """Gets prim's pose in the view with respect to the local frame (the prim's parent frame).

        Args:
            indices (Optional[Union[np.ndarray, list, torch.Tensor]], optional): indicies to specify which prims 
                                                                                 to query. Shape (M,).
                                                                                 Where M <= size of the encapsulated prims in the view.
                                                                                 Defaults to None (i.e: all prims in the view).
        Raises:
            Exception: [description]

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
        """Sets prim's pose in the view with respect to the local frame (the prim's parent frame).

        Args:
            translations (Optional[Union[np.ndarray, torch.Tensor]], optional): 
                                                          translations in the local frame of the prims
                                                          (with respect to its parent prim). shape is (M, 3).
                                                          Defaults to None, which means left unchanged.
            orientations (Optional[Union[np.ndarray, torch.Tensor]], optional): 
                                                          quaternion orientations in the world frame of the prims. 
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
            self.set_world_poses(positions=calculated_positions, orientations=calculated_orientations, indices=indices)
            self._physics_sim_view.enable_warnings(True)
        else:
            XFormPrimView.set_local_poses(self, translations=translations, orientations=orientations, indices=indices)
        return

    def set_linear_velocities(
        self,
        velocities: Optional[Union[np.ndarray, torch.Tensor]],
        indices: Optional[Union[np.ndarray, list, torch.Tensor]] = None,
    ):
        """Sets the linear velocity of the prim in stage. The method does this through the physx API.
            Note: It has to be called while simulating i.e after .play() or .reset() is called

        Args:
            velocities (np.ndarray): linear velocity to set the rigid prim to. Shape (3,).
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
        self, indices: Optional[Union[np.ndarray, list, torch.Tensor]] = None, clone=True
    ) -> Union[np.ndarray, torch.Tensor]:
        """
        Returns:
            np.ndarray: current linear velocity of the the rigid prim. Shape (3,).
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
        self, indices: Optional[Union[np.ndarray, list, torch.Tensor]] = None, clone=True
    ) -> Union[np.ndarray, torch.Tensor]:

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
        self, indices: Optional[Union[np.ndarray, list, torch.Tensor]] = None, clone=True
    ) -> Union[np.ndarray, torch.Tensor]:
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
        if not omni.timeline.get_timeline_interface().is_stopped() and self._physics_view is not None:
            self._physics_sim_view.enable_warnings(False)
            forces = forces.reshape(-1, 3)
            indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
            new_forces = self._backend_utils.create_zeros_tensor([self.count, 3], device=self._device, dtype="float32")
            new_forces[indices] = self._backend_utils.move_data(forces, self._device)
            self._physics_view.apply_forces(new_forces, indices)
            self._physics_sim_view.enable_warnings(True)
        else:
            raise Exception("Physics Simulation View is not created yet")

    def set_masses(
        self,
        masses: Optional[Union[np.ndarray, torch.Tensor]],
        indices: Optional[Union[np.ndarray, list, torch.Tensor]] = None,
    ) -> None:
        """
        Args:
            mass (float): mass of the rigid body in kg.
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
        """
        Returns:
            float: mass of the rigid body in kg.
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
        """_summary_

        Args:
            densities (Optional[Union[np.ndarray, torch.Tensor]]): _description_
            indices (Optional[Union[np.ndarray, list, torch.Tensor]], optional): _description_. Defaults to None.
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
        """
        Returns:
            float: mass of the rigid body in kg.
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
        """ enable rigid body physics (enabled by default):
            Object will be moved by external forces such as gravity and collisions
        """
        indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
        for i in indices:
            self._rigid_body_apis[i.tolist()].GetRigidBodyEnabledAttr().Set(True)
        return

    def disable_rigid_body_physics(self, indices: Optional[Union[np.ndarray, list, torch.Tensor]] = None) -> None:
        """ disable rigid body physics (enabled by default):
            Object will not be moved by external forces such as gravity and collisions
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
        """Sets the default state of the prim, that will be used after each reset. 

        Args:
            position (np.ndarray): position in the world frame of the prim. shape is (3, ).
                                   Defaults to None, which means left unchanged.
            orientation (np.ndarray): quaternion orientation in the world frame of the prim. 
                                      quaternion is scalar-first (w, x, y, z). shape is (4, ).
                                      Defaults to None, which means left unchanged.
            linear_velocity (np.ndarray): linear velocity to set the rigid prim to. Shape (3,).
            angular_velocity (np.ndarray): angular velocity to set the rigid prim to. Shape (3,).
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
        """
        Returns:
            DynamicState: returns the default state of the prim (position, orientation, linear_velocity and 
                          angular_velocity) that is used after each reset.
        """
        return self._dynamics_default_state

    def post_reset(self) -> None:
        """Resets the prim to its default state.
        """
        if not self._non_root_link:
            XFormPrimView.post_reset(self)
            self.set_angular_velocities(self._dynamics_default_state.angular_velocities)
            self.set_linear_velocities(self._dynamics_default_state.linear_velocities)
        return

    def get_current_dynamic_state(self) -> DynamicsViewState:
        """ 
        Returns:
            DynamicState: the dynamic state of the rigid body including position, orientation, linear_velocity and angular_velocity.
        """
        positions, orientations = self.get_world_poses()
        return DynamicsViewState(
            positions=positions,
            orientations=orientations,
            linear_velocities=self.get_linear_velocities(),
            angular_velocities=self.get_angular_velocities(),
        )
