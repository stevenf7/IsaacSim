# Copyright (c) 2021-2023, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

from typing import List, Optional, Union

import numpy as np
import omni.kit.app
import torch
import warp as wp
from omni.isaac.core.materials.physics_material import PhysicsMaterial
from omni.isaac.core.prims.rigid_contact_view import RigidContactView
from omni.isaac.core.prims.xform_prim_view import XFormPrimView
from pxr import PhysxSchema, UsdGeom, UsdPhysics, UsdShade


class GeometryPrimView(XFormPrimView):
    """
    Provides high level functions to deal with geom prims (1 or more prims)
    as well as its attributes/ properties.
    This object wraps all matching geom prims found at the regex provided at the prim_paths_expr.

    Note: - each prim will have "xformOp:orient", "xformOp:translate" and "xformOp:scale" only post init,
            unless it is a non-root articulation link.

    Args:
        prim_paths_expr (str): prim paths regex to encapsulate all prims that match it.
                                example: "/World/Env[1-5]/Microwave" will match /World/Env1/Microwave,
                                /World/Env2/Microwave..etc.
                                (a non regex prim path can also be used to encapsulate one XForm).
        name (str, optional): shortname to be used as a key by Scene class.
                                Note: needs to be unique if the object is added to the Scene.
                                Defaults to "geometry_prim_view".
        positions (Optional[Union[np.ndarray, torch.Tensor, wp.array]], optional):
                                                        default positions in the world frame of the prim.
                                                        shape is (N, 3).
                                                        Defaults to None, which means left unchanged.
        translations (Optional[Union[np.ndarray, torch.Tensor, wp.array]], optional):
                                                        default translations in the local frame of the prims
                                                        (with respect to its parent prims). shape is (N, 3).
                                                        Defaults to None, which means left unchanged.
        orientations (Optional[Union[np.ndarray, torch.Tensor, wp.array]], optional):
                                                        default quaternion orientations in the world/ local frame of the prim
                                                        (depends if translation or position is specified).
                                                        quaternion is scalar-first (w, x, y, z). shape is (N, 4).
                                                        Defaults to None, which means left unchanged.
        scales (Optional[Union[np.ndarray, torch.Tensor, wp.array]], optional): local scales to be applied to
                                                        the prim's dimensions. shape is (N, 3).
                                                        Defaults to None, which means left unchanged.
        visibilities (Optional[Union[np.ndarray, torch.Tensor, wp.array], optional): set to false for an invisible prim in
                                                                            the stage while rendering. shape is (N,).
                                                                            Defaults to None.
        reset_xform_properties (bool, optional): True if the prims don't have the right set of xform properties
                                                (i.e: translate, orient and scale) ONLY and in that order.
                                                Set this parameter to False if the object were cloned using using
                                                the cloner api in omni.isaac.cloner. Defaults to True.
        collisions (Optional[Union[np.ndarray, torch.Tensor, wp.array]], optional): Set to True if the geometry already have/
                                                    should have a collider (i.e not only a visual geometry). shape is (N,).
                                                    Defaults to None.
        track_contact_forces (bool, Optional) : if enabled, the view will track the net contact forces on each geometry prim
                                                in the view. Note that the collision flag should be set to True to report
                                                contact forces. Defaults to False.
        prepare_contact_sensors (bool, Optional): applies contact reporter API to the prim if it already does not have one.
                                                    Defaults to False.
        disable_stablization (bool, optional): disables the contact stablization parameter in the physics context.
                                                Defaults to True.
        contact_filter_prim_paths_expr (Optional[List[str]], Optional): a list of filter expressions which allows for tracking
                                                                        contact forces between the geometry prim and this subset
                                                                        through get_contact_force_matrix().
    """

    def __init__(
        self,
        prim_paths_expr: str,
        name: str = "geometry_prim_view",
        positions: Optional[Union[np.ndarray, torch.Tensor, wp.array]] = None,
        translations: Optional[Union[np.ndarray, torch.Tensor, wp.array]] = None,
        orientations: Optional[Union[np.ndarray, torch.Tensor, wp.array]] = None,
        scales: Optional[Union[np.ndarray, torch.Tensor, wp.array]] = None,
        visibilities: Optional[Union[np.ndarray, torch.Tensor, wp.array]] = None,
        reset_xform_properties: bool = True,
        collisions: Optional[Union[np.ndarray, torch.Tensor, wp.array]] = None,
        track_contact_forces: bool = False,
        prepare_contact_sensors: bool = False,
        disable_stablization: bool = True,
        contact_filter_prim_paths_expr: Optional[List[str]] = [],
    ) -> None:
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
        self._geoms = [None] * self._count
        self._collision_apis = [None] * self._count
        self._mesh_collision_apis = [None] * self._count
        self._physx_collision_apis = [None] * self._count
        for i in range(self.count):
            prim = self._prims[i]
            if prim.IsA(UsdGeom.Cube):
                self._geoms[i] = UsdGeom.Cube(prim)
            elif prim.IsA(UsdGeom.Capsule):
                self._geoms[i] = UsdGeom.Capsule(prim)
            elif prim.IsA(UsdGeom.Cone):
                self._geoms[i] = UsdGeom.Cone(prim)
            elif prim.IsA(UsdGeom.Cylinder):
                self._geoms[i] = UsdGeom.Cylinder(prim)
            elif prim.IsA(UsdGeom.Sphere):
                self._geoms[i] = UsdGeom.Sphere(prim)
            elif prim.IsA(UsdGeom.Mesh):
                self._geoms[i] = UsdGeom.Mesh(prim)
            else:
                self._geoms[i] = UsdGeom.Gprim(prim)

            if collisions is not None:
                collisions = self._backend_utils.to_list(collisions)
                if collisions[i]:
                    self.apply_collision_apis([i])

        self._applied_physics_materials = [None] * self._count
        self._binding_apis = [None] * self._count

        self._track_contact_forces = track_contact_forces or len(contact_filter_prim_paths_expr) != 0
        self._contact_filter_prim_paths_expr = contact_filter_prim_paths_expr
        if self._track_contact_forces:
            self._contact_view = RigidContactView(
                prim_paths_expr=prim_paths_expr,
                filter_paths_expr=contact_filter_prim_paths_expr,
                name=name + "_contact",
                prepare_contact_sensors=prepare_contact_sensors,
                apply_rigid_body_api=False,
                disable_stablization=disable_stablization,
            )
        return

    @property
    def geoms(self) -> List[UsdGeom.Gprim]:
        """
        Returns:
            List[UsdGeom.Gprim]: USD geom objects encapsulated.
        """
        return self._geoms

    def initialize(self, physics_sim_view: omni.physics.tensors.SimulationView = None) -> None:
        if self._track_contact_forces:
            self._contact_view.initialize(physics_sim_view)
        return

    def set_contact_offsets(
        self,
        offsets: Union[np.ndarray, torch.Tensor, wp.array],
        indices: Optional[Union[np.ndarray, list, torch.Tensor, wp.array]] = None,
    ) -> None:
        """Sets contact offsets for prims in the view.

        Args:
            offsets (Union[np.ndarray, torch.Tensor, wp.array]): Contact offsets of the collision shapes. Allowed range [maximum(0, rest_offset), 0].
                                                       Default value is -inf, means default is picked by simulation based on the shape extent.
                                                       Shape (M,).
            indices (Optional[Union[np.ndarray, list, torch.Tensor, wp.array]], optional): indicies to specify which prims
                                                                                 to manipulate. Shape (M,).
                                                                                 Where M <= size of the encapsulated prims in the view.
                                                                                 Defaults to None (i.e: all prims in the view).
        """
        indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
        read_idx = 0
        indices = self._backend_utils.to_list(indices)
        offsets = self._backend_utils.to_list(offsets)
        for i in indices:
            if self._physx_collision_apis[i] is None:
                if self._prims[i].HasAPI(UsdPhysics.PhysxCollisionAPI):
                    collision_api = UsdPhysics.PhysxCollisionAPI(self.prims[i])
                else:
                    collision_api = UsdPhysics.PhysxCollisionAPI.Apply(self._prims[i])
                self._physx_collision_apis[i] = collision_api
            self._physx_collision_apis[i].GetContactOffsetAttr().Set(offsets[i])
            read_idx += 1
        return

    def get_contact_offsets(
        self, indices: Optional[Union[np.ndarray, list, torch.Tensor, wp.array]] = None
    ) -> Union[np.ndarray, torch.Tensor, wp.indexedarray]:
        """Gets contact offsets for prims in the view.

        Args:
            indices (Optional[Union[np.ndarray, list, torch.Tensor, wp.array]], optional): indicies to specify which prims
                                                                                 to query. Shape (M,).
                                                                                 Where M <= size of the encapsulated prims in the view.
                                                                                 Defaults to None (i.e: all prims in the view).

        Returns:
            Union[np.ndarray, torch.Tensor, wp.indexedarray]: Contact offsets of the collision shapes. Shape is (M,).
        """
        indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
        offsets = np.zeros(shape=indices.shape[0], dtype=np.float32)
        write_idx = 0
        indices = self._backend_utils.to_list(indices)
        for i in indices:
            if self._physx_collision_apis[i] is None:
                if self._prims[i].HasAPI(UsdPhysics.PhysxCollisionAPI):
                    collision_api = UsdPhysics.PhysxCollisionAPI(self.prims[i])
                else:
                    collision_api = UsdPhysics.PhysxCollisionAPI.Apply(self._prims[i])
                self._physx_collision_apis[i] = collision_api
            offsets[write_idx] = self._physx_collision_apis[i].GetContactOffsetAttr().Get()
            write_idx += 1
        offsets = self._backend_utils.convert(offsets, dtype="float32", device=self._device, indexed=True)
        return offsets

    def set_rest_offsets(
        self,
        offsets: Union[np.ndarray, torch.Tensor, wp.array],
        indices: Optional[Union[np.ndarray, list, torch.Tensor, wp.array]] = None,
    ) -> None:
        """Sets rest offsets for prims in the view.

        Args:
            offsets (Union[np.ndarray, torch.Tensor, wp.array]): Rest offset of a collision shape. Allowed range [-max_float, contact_offset.
                                                        Default value is -inf, means default is picked by simulatiion.
                                                        For rigid bodies its zero. Shape (M,).
            indices (Optional[Union[np.ndarray, list, torch.Tensor, wp.array]], optional): indicies to specify which prims
                                                                                 to manipulate. Shape (M,).
                                                                                 Where M <= size of the encapsulated prims in the view.
                                                                                 Defaults to None (i.e: all prims in the view).
        """
        indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
        read_idx = 0
        indices = self._backend_utils.to_list(indices)
        offsets = self._backend_utils.to_list(offsets)
        for i in indices:
            if self._physx_collision_apis[i] is None:
                if self._prims[i].HasAPI(UsdPhysics.PhysxCollisionAPI):
                    collision_api = UsdPhysics.PhysxCollisionAPI(self.prims[i])
                else:
                    collision_api = UsdPhysics.PhysxCollisionAPI.Apply(self._prims[i])
                self._physx_collision_apis[i] = collision_api
            self._physx_collision_apis[i].GetRestOffsetAttr().Set(offsets[i])
            read_idx += 1
        return

    def get_rest_offsets(
        self, indices: Optional[Union[np.ndarray, list, torch.Tensor, wp.array]] = None
    ) -> Union[np.ndarray, torch.Tensor, wp.indexedarray]:
        """Gets rest offsets for prims in the view.

        Args:
            indices (Optional[Union[np.ndarray, list, torch.Tensor, wp.array]], optional): indicies to specify which prims
                                                                                 to query. Shape (M,).
                                                                                 Where M <= size of the encapsulated prims in the view.
                                                                                 Defaults to None (i.e: all prims in the view).
        Returns:
            Union[np.ndarray, torch.Tensor, wp.indexedarray]: Rest offsets of the collision shapes. Shape is (M,).
        """
        indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
        offsets = np.zeros(indices.shape[0], dtype=np.float32)
        write_idx = 0
        indices = self._backend_utils.to_list(indices)
        for i in indices:
            if self._physx_collision_apis[i] is None:
                if self._prims[i].HasAPI(UsdPhysics.PhysxCollisionAPI):
                    collision_api = UsdPhysics.PhysxCollisionAPI(self.prims[i])
                else:
                    collision_api = UsdPhysics.PhysxCollisionAPI.Apply(self._prims[i])
                self._physx_collision_apis[i] = collision_api
            offsets[write_idx] = self._physx_collision_apis[i].GetRestOffsetAttr().Get()
            write_idx += 1
        offsets = self._backend_utils.convert(offsets, dtype="float32", device=self._device, indexed=True)
        return offsets

    def set_torsional_patch_radii(
        self,
        radii: Union[np.ndarray, torch.Tensor, wp.array],
        indices: Optional[Union[np.ndarray, list, torch.Tensor, wp.array]] = None,
    ) -> None:
        """Sets torsional patch radii for prims in the view.

        Args:
            radii (Union[np.ndarray, torch.Tensor, wp.array]): radius of the contact patch used to apply torsional friction. Allowed range [0, max_float].
                                                     shape is (M,).
            indices (Optional[Union[np.ndarray, list, torch.Tensor, wp.array]], optional): indicies to specify which prims
                                                                                 to manipulate. Shape (M,).
                                                                                 Where M <= size of the encapsulated prims in the view.
                                                                                 Defaults to None (i.e: all prims in the view).
        """
        indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
        read_idx = 0
        indices = self._backend_utils.to_list(indices)
        radii = self._backend_utils.to_list(radii)
        for i in indices:
            if self._physx_collision_apis[i] is None:
                if self._prims[i].HasAPI(UsdPhysics.PhysxCollisionAPI):
                    collision_api = UsdPhysics.PhysxCollisionAPI(self.prims[i])
                else:
                    collision_api = UsdPhysics.PhysxCollisionAPI.Apply(self._prims[i])
                self._physx_collision_apis[i] = collision_api
            self._physx_collision_apis[i].GetTorsionalPatchRadiusAttr().Set(radii[i])
            read_idx += 1
        return

    def get_torsional_patch_radii(
        self, indices: Optional[Union[np.ndarray, list, torch.Tensor, wp.array]] = None
    ) -> Union[np.ndarray, torch.Tensor, wp.indexedarray]:
        """Gets torsional patch radii for prims in the view.

        Args:
            indices (Optional[Union[np.ndarray, list, torch.Tensor, wp.array]], optional): indicies to specify which prims
                                                                                 to query. Shape (M,).
                                                                                 Where M <= size of the encapsulated prims in the view.
                                                                                 Defaults to None (i.e: all prims in the view).

        Returns:
            Union[np.ndarray, torch.Tensor, wp.indexedarray]: radius of the contact patch used to apply torsional friction. shape is (M,).
        """
        indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
        radii = np.zeros(indices.shape[0], dtype=np.float32)
        write_idx = 0
        indices = self._backend_utils.to_list(indices)
        for i in indices:
            if self._physx_collision_apis[i] is None:
                if self._prims[i].HasAPI(UsdPhysics.PhysxCollisionAPI):
                    collision_api = UsdPhysics.PhysxCollisionAPI(self.prims[i])
                else:
                    collision_api = UsdPhysics.PhysxCollisionAPI.Apply(self._prims[i])
                self._physx_collision_apis[i] = collision_api
            radii[write_idx] = self._physx_collision_apis[i].GetTorsionalPatchRadiusAttr().Get()
            write_idx += 1
        radii = self._backend_utils.convert(radii, dtype="float32", device=self._device, indexed=True)
        return radii

    def set_min_torsional_patch_radii(
        self,
        radii: Union[np.ndarray, torch.Tensor, wp.array],
        indices: Optional[Union[np.ndarray, list, torch.Tensor, wp.array]] = None,
    ) -> None:
        """Sets minimum torsional patch radii for prims in the view.

        Args:
            radii (Union[np.ndarray, torch.Tensor, wp.array]): minimum radius of the contact patch used to apply torsional friction.
                                                     Allowed range [0, max_float]. shape is (M, ).
            indices (Optional[Union[np.ndarray, list, torch.Tensor, wp.array]], optional): indicies to specify which prims
                                                                                 to manipulate. Shape (M,).
                                                                                 Where M <= size of the encapsulated prims in the view.
                                                                                 Defaults to None (i.e: all prims in the view).
        """
        indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
        read_idx = 0
        indices = self._backend_utils.to_list(indices)
        radii = self._backend_utils.to_list(radii)
        for i in indices:
            if self._physx_collision_apis[i] is None:
                if self._prims[i].HasAPI(UsdPhysics.PhysxCollisionAPI):
                    collision_api = UsdPhysics.PhysxCollisionAPI(self.prims[i])
                else:
                    collision_api = UsdPhysics.PhysxCollisionAPI.Apply(self._prims[i])
                self._physx_collision_apis[i] = collision_api
            self._physx_collision_apis[i].GetMinTorsionalPatchRadiusAttr().Set(radii[i])
            read_idx += 1
        return

    def get_min_torsional_patch_radii(
        self, indices: Optional[Union[np.ndarray, list, torch.Tensor]] = None
    ) -> Union[np.ndarray, torch.Tensor]:
        """Gets minimum torsional patch radii for prims in the view.

        Args:
            indices (Optional[Union[np.ndarray, list, torch.Tensor]], optional): indicies to specify which prims
                                                                                 to query. Shape (M,).
                                                                                 Where M <= size of the encapsulated prims in the view.
                                                                                 Defaults to None (i.e: all prims in the view).

        Returns:
            Union[np.ndarray, torch.Tensor]: minimum radius of the contact patch used to apply torsional friction. shape is (M,).
        """
        indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
        radii = self._backend_utils.create_zeros_tensor([indices.shape[0]], dtype="float32", device=self._device)
        write_idx = 0
        for i in indices:
            if self._physx_collision_apis[i.tolist()] is None:
                if self._prims[i.tolist()].HasAPI(UsdPhysics.PhysxCollisionAPI):
                    collision_api = UsdPhysics.PhysxCollisionAPI(self.prims[i])
                else:
                    collision_api = UsdPhysics.PhysxCollisionAPI.Apply(self._prims[i.tolist()])
                self._physx_collision_apis[i.tolist()] = collision_api
            radii[write_idx] = self._backend_utils.create_tensor_from_list(
                self._physx_collision_apis[i.tolist()].GetMinTorsionalPatchRadiusAttr().Get(),
                dtype="float32",
                device=self._device,
            )
            write_idx += 1
        return radii

    def set_collision_approximations(
        self, approximation_types: List[str], indices: Optional[Union[np.ndarray, list, torch.Tensor, wp.array]] = None
    ) -> None:
        """Sets collision approximation types for prims in the view.

        Args:
            approximation_types (List[str]): approximations used for collision,
                                            could be "none", "convexHull" or "convexDecomposition".
                                            List size == M or the size of the view.

            indices (Optional[Union[np.ndarray, list, torch.Tensor, wp.array]], optional): indicies to specify which prims
                                                                                 to manipulate. Shape (M,).
                                                                                 Where M <= size of the encapsulated prims in the view.
                                                                                 Defaults to None (i.e: all prims in the view).
        """
        indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
        read_idx = 0
        indices = self._backend_utils.to_list(indices)
        for i in indices:
            if self._mesh_collision_apis[i] is None:
                if self._prims[i].HasAPI(UsdPhysics.MeshCollisionAPI):
                    collision_api = UsdPhysics.MeshCollisionAPI(self.prims[i])
                else:
                    collision_api = UsdPhysics.MeshCollisionAPI.Apply(self._prims[i])
                self._mesh_collision_apis[i] = collision_api
            self._mesh_collision_apis[i].GetApproximationAttr().Set(approximation_types[i])
            read_idx += 1
        return

    def get_collision_approximations(
        self, indices: Optional[Union[np.ndarray, list, torch.Tensor, wp.array]] = None
    ) -> List[str]:
        """Gets collision approximation types for prims in the view.

        Args:
            indices (Optional[Union[np.ndarray, list, torch.Tensor, wp.array]], optional): indicies to specify which prims
                                                                                 to query. Shape (M,).
                                                                                 Where M <= size of the encapsulated prims in the view.
                                                                                 Defaults to None (i.e: all prims in the view).

        Returns:
            List[str]: approximations used for collision, could be "none", "convexHull" or "convexDecomposition". size == M or size of the view.

        """
        indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
        approximation_types = [None] * indices.shape[0]
        write_idx = 0
        indices = self._backend_utils.to_list(indices)
        for i in indices:
            if self._mesh_collision_apis[i] is None:
                if self._prims[i].HasAPI(UsdPhysics.MeshCollisionAPI):
                    collision_api = UsdPhysics.MeshCollisionAPI(self.prims[i])
                else:
                    collision_api = UsdPhysics.MeshCollisionAPI.Apply(self._prims[i])
                self._mesh_collision_apis[i] = collision_api
            approximation_types[write_idx] = self._mesh_collision_apis[i].GetApproximationAttr().Get()
            write_idx += 1
        return approximation_types

    def enable_collision(self, indices: Optional[Union[np.ndarray, list, torch.Tensor, wp.array]] = None) -> None:
        """Enables collision on prims in the view.

        Args:
            indices (Optional[Union[np.ndarray, list, torch.Tensor, wp.array]], optional): indicies to specify which prims
                                                                                 to manipulate. Shape (M,).
                                                                                 Where M <= size of the encapsulated prims in the view.
                                                                                 Defaults to None (i.e: all prims in the view).
        """
        indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
        indices = self._backend_utils.to_list(indices)
        for i in indices:
            if self._collision_apis[i] is None:
                self.apply_collision_apis([i])
            self._collision_apis[i].GetCollisionEnabledAttr().Set(True)
        return

    def disable_collision(self, indices: Optional[Union[np.ndarray, list, torch.Tensor, wp.array]] = None) -> None:
        """Disables collision on prims in the view.

        Args:
            indices (Optional[Union[np.ndarray, list, torch.Tensor, wp.array]], optional): indicies to specify which prims
                                                                                 to manipulate. Shape (M,).
                                                                                 Where M <= size of the encapsulated prims in the view.
                                                                                 Defaults to None (i.e: all prims in the view).
        """
        indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
        indices = self._backend_utils.to_list(indices)
        for i in indices:
            if self._collision_apis[i] is None:
                continue
            self._collision_apis[i].GetCollisionEnabledAttr().Set(False)
        return

    def is_collision_enabled(
        self, indices: Optional[Union[np.ndarray, list, torch.Tensor, wp.array]] = None
    ) -> Union[np.ndarray, torch.Tensor, wp.indexedarray]:
        """Queries if collision is enabled on prims in the view.

        Args:
            indices (Optional[Union[np.ndarray, list, torch.Tensor, wp.array]], optional): indicies to specify which prims
                                                                                 to query. Shape (M,).
                                                                                 Where M <= size of the encapsulated prims in the view.
                                                                                 Defaults to None (i.e: all prims in the view).

        Returns:
            Union[np.ndarray, torch.Tensor, wp.indexedarray]: True if collision is enabled. Shape is (M,).
        """
        indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
        collisions = np.zeros(shape=indices.shape[0], dtype=np.bool, device=self._device)
        write_idx = 0
        indices = self._backend_utils.to_list(indices)
        for i in indices:
            if self._collision_apis[i] is None:
                collisions[write_idx] = False
            else:
                collisions[write_idx] = self._collision_apis[i].GetCollisionEnabledAttr().Get()
            write_idx += 1
        collisions = self._backend_utils.convert(collisions, dtype="bool", device=self._device, indexed=True)
        return collisions

    def apply_collision_apis(self, indices: Optional[Union[np.ndarray, list, torch.Tensor, wp.array]] = None) -> None:
        """retrieves the collision apis applied to prims already
            or applies collision apis to prims in the view.

        Args:
            indices (Optional[Union[np.ndarray, list, torch.Tensor, wp.array]], optional): indicies to specify which prims
                                                                                 to manipulate. Shape (M,).
                                                                                 Where M <= size of the encapsulated prims in the view.
                                                                                 Defaults to None (i.e: all prims in the view).
        """
        indices = self._backend_utils.to_list(self._backend_utils.resolve_indices(indices, self.count, self._device))
        for i in indices:
            if self.prims[i].HasAPI(UsdPhysics.CollisionAPI):
                self._collision_apis[i] = UsdPhysics.CollisionAPI(self.prims[i])
            else:
                self._collision_apis[i] = UsdPhysics.CollisionAPI.Apply(self.prims[i])
            if self.prims[i].HasAPI(UsdPhysics.MeshCollisionAPI):
                self._mesh_collision_apis[i] = UsdPhysics.MeshCollisionAPI(self.prims[i])
            else:
                self._mesh_collision_apis[i] = UsdPhysics.MeshCollisionAPI.Apply(self.prims[i])
            if self.prims[i].HasAPI(PhysxSchema.PhysxCollisionAPI):
                self._physx_collision_apis[i] = PhysxSchema.PhysxCollisionAPI(self.prims[i])
            else:
                self._physx_collision_apis[i] = PhysxSchema.PhysxCollisionAPI.Apply(self.prims[i])
        return

    def apply_physics_materials(
        self,
        physics_materials: Union[PhysicsMaterial, List[PhysicsMaterial]],
        weaker_than_descendants: Optional[Union[bool, List[bool]]] = None,
        indices: Optional[Union[np.ndarray, list, torch.Tensor, wp.array]] = None,
    ) -> None:
        """Used to apply physics material to prims in the view and optionally its descendants.

        Args:
            physics_materials (Union[PhysicsMaterial, List[PhysicsMaterial]]): physics materials to be applied to prims in the view.
                                                                            Physics material can be used to define friction, restitution..etc.
                                                                            Note: if a physics material is not defined, the defaults will be used
                                                                            from PhysX. If a list is provided then its size has to be equal
                                                                            the view's size or indices size.
                                                                            If one material is provided it will be applied to all prims in the view.
            weaker_than_descendants (Optional[Union[bool, List[bool]]], optional): True if the material shouldn't override the descendants
                                                                                    materials, otherwise False. Defaults to False.
                                                                                    If a list of visual materials is provided then a list
                                                                                    has to be provided with the same size for this arg as well.
            indices (Optional[Union[np.ndarray, list, torch.Tensor, wp.array]], optional): indicies to specify which prims
                                                                                 to manipulate. Shape (M,).
                                                                                 Where M <= size of the encapsulated prims in the view.
                                                                                 Defaults to None (i.e: all prims in the view).

        Raises:
            Exception: length of physics materials != length of prims indexed
            Exception: length of physics materials != length of weaker descendants arg
        """
        indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
        indices = self._backend_utils.to_list(indices)
        if isinstance(physics_materials, list):
            if indices.shape[0] != len(physics_materials):
                raise Exception("length of physics materials != length of prims indexed")
            if weaker_than_descendants is None:
                weaker_than_descendants = [False] * len(physics_materials)
            if len(physics_materials) != len(weaker_than_descendants):
                raise Exception("length of physics materials != length of weaker descendants bools arg")
        if isinstance(physics_materials, list):
            read_idx = 0
            for i in indices:
                if self._binding_apis[i] is None:
                    if self._prims[i].HasAPI(UsdShade.MaterialBindingAPI):
                        self._binding_apis[i] = UsdShade.MaterialBindingAPI(self._prims[i])
                    else:
                        self._binding_apis[i] = UsdShade.MaterialBindingAPI.Apply(self._prims[i])
                if weaker_than_descendants[read_idx]:
                    self._binding_apis[i].Bind(
                        physics_materials[read_idx].material,
                        bindingStrength=UsdShade.Tokens.weakerThanDescendants,
                        materialPurpose="physics",
                    )
                else:
                    self._binding_apis[i].Bind(
                        physics_materials[read_idx].material,
                        bindingStrength=UsdShade.Tokens.strongerThanDescendants,
                        materialPurpose="physics",
                    )
                self._applied_physics_materials[i] = physics_materials[read_idx]
                read_idx += 1
            return
        else:
            if weaker_than_descendants is None:
                weaker_than_descendants = False
            for i in indices:
                if self._binding_apis[i] is None:
                    if self._prims[i].HasAPI(UsdShade.MaterialBindingAPI):
                        self._binding_apis[i] = UsdShade.MaterialBindingAPI(self._prims[i])
                    else:
                        self._binding_apis[i] = UsdShade.MaterialBindingAPI.Apply(self._prims[i])
                if weaker_than_descendants:
                    self._binding_apis[i].Bind(
                        physics_materials.material,
                        bindingStrength=UsdShade.Tokens.weakerThanDescendants,
                        materialPurpose="physics",
                    )
                else:
                    self._binding_apis[i].Bind(
                        physics_materials.material,
                        bindingStrength=UsdShade.Tokens.strongerThanDescendants,
                        materialPurpose="physics",
                    )
                self._applied_physics_materials[i] = physics_materials
        return

    def get_applied_physics_materials(
        self, indices: Optional[Union[np.ndarray, list, torch.Tensor, wp.array]] = None
    ) -> List[PhysicsMaterial]:
        """Gets the applied physics material to prims in the view.

        Args:
            indices (Optional[Union[np.ndarray, list, torch.Tensor, wp.array]], optional): indicies to specify which prims
                                                                                 to query. Shape (M,).
                                                                                 Where M <= size of the encapsulated prims in the view.
                                                                                 Defaults to None (i.e: all prims in the view).

        Returns:
            List[PhysicsMaterial]: the current applied physics materials for prims in the view.
        """
        indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
        result = [None] * indices.shape[0]
        write_idx = 0
        indices = self._backend_utils.to_list(indices)
        for i in indices:
            if self._binding_apis[i] is None:
                if self._prims[i].HasAPI(UsdShade.MaterialBindingAPI):
                    self._binding_apis[i] = UsdShade.MaterialBindingAPI(self._prims[i])
                else:
                    self._binding_apis[i] = UsdShade.MaterialBindingAPI.Apply(self._prims[i])
            if self._applied_physics_materials[i] is not None:
                result[write_idx] = self._applied_visual_materials[i]
                write_idx += 1
            else:
                physics_binding = self._binding_apis[i].GetDirectBinding(materialPurpose="physics")
                material_path = physics_binding.GetMaterialPath()
                if material_path == "":
                    result[write_idx] = None
                else:
                    self._applied_physics_materials[i] = PhysicsMaterial(prim_path=material_path)
                    result[write_idx] = self._applied_physics_materials[i]
                write_idx += 1
        return result

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
                "contact forces cannot be retrieved with this API unless the GeometryPrimView is initialized with track_contact_forces = True or a list of contact filters is provided via contact_filter_prim_paths_expr"
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
                "No filter is specified for get_contact_force_matrix. Initialize the GeometryPrimView with the contact_filter_prim_paths_expr and specify a list of filters."
            )
            return None
