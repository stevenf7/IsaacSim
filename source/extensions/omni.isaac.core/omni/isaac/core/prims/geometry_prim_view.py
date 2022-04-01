# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

from typing import Optional, Union, List
import numpy as np
from omni.isaac.core.prims.xform_prim_view import XFormPrimView
from pxr import UsdGeom, UsdPhysics, PhysxSchema, UsdShade
import torch
from omni.isaac.core.materials import PhysicsMaterial
from omni.isaac.core.simulation_context.simulation_context import SimulationContext


class GeometryPrimView(XFormPrimView):
    """Provides high level functions to deal with a Geom prim and its attributes/ properties.
           The prim_path should correspond to type UsdGeom.Cube, UsdGeom.Capsule, UsdGeom.Cone, UsdGeom.Cylinder, 
           UsdGeom.Sphere or UsdGeom.Mesh.

        Args:
            prim_path (str): prim path of the Prim to encapsulate or create.
            name (str, optional): shortname to be used as a key by Scene class. 
                                    Note: needs to be unique if the object is added to the Scene.
                                    Defaults to "xform_prim".
            position (Optional[np.ndarray], optional): position in the world frame of the prim. shape is (3, ).
                                                        Defaults to None, which means left unchanged.
            translation (Optional[np.ndarray], optional): translation in the local frame of the prim
                                                            (with respect to its parent prim). shape is (3, ).
                                                            Defaults to None, which means left unchanged.
            orientation (Optional[np.ndarray], optional): quaternion orientation in the world/ local frame of the prim
                                                            (depends if translation or position is specified).
                                                            quaternion is scalar-first (w, x, y, z). shape is (4, ).
                                                            Defaults to None, which means left unchanged.
            scale (Optional[np.ndarray], optional): local scale to be applied to the prim's dimensions. shape is (3, ).
                                                    Defaults to None, which means left unchanged.
            visible (bool, optional): set to false for an invisible prim in the stage while rendering. Defaults to True.
            collision (bool, optional): Set to True if the geometry should have a collider (i.e not only a visual geometry). 
                                        Defaults to False.
        """

    def __init__(
        self,
        prim_paths_expr: str,
        name: str = "geometry_prim_view",
        positions: Optional[Union[np.ndarray, torch.Tensor]] = None,
        translations: Optional[Union[np.ndarray, torch.Tensor]] = None,
        orientations: Optional[Union[np.ndarray, torch.Tensor]] = None,
        scales: Optional[Union[np.ndarray, torch.Tensor]] = None,
        visibilities: Optional[Union[np.ndarray, torch.Tensor]] = None,
        collisions: Optional[Union[np.ndarray, torch.Tensor]] = None,
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
                if collisions[i] and prim.HasAPI(UsdPhysics.CollisionAPI):
                    self._collision_apis[i] = UsdPhysics.CollisionAPI(prim)
                elif collisions[i]:
                    self._collision_apis[i] = UsdPhysics.CollisionAPI.Apply(prim)
                if collisions[i] and prim.HasAPI(UsdPhysics.MeshCollisionAPI):
                    self._mesh_collision_apis[i] = UsdPhysics.MeshCollisionAPI(prim)
                elif collisions[i]:
                    self._mesh_collision_apis[i] = UsdPhysics.MeshCollisionAPI.Apply(prim)
                if collisions[i] and prim.HasAPI(PhysxSchema.PhysxCollisionAPI):
                    self._physx_collision_apis[i] = PhysxSchema.PhysxCollisionAPI(prim)
                elif collisions[i]:
                    self._physx_collision_apis[i] = PhysxSchema.PhysxCollisionAPI.Apply(prim)

        if SimulationContext.instance() is not None:
            self._backend = SimulationContext.instance().backend
            self._device = SimulationContext.instance().device
            self._backend_utils = SimulationContext.instance().backend_utils
        self._applied_physics_materials = [None] * self._count
        self._binding_apis = [None] * self._count
        return

    @property
    def geoms(self) -> UsdGeom.Gprim:
        """
        Returns:
            UsdGeom.Gprim: USD geometry object encapsulated.
        """
        return self._geoms

    def set_contact_offsets(
        self, offsets: Union[np.ndarray, torch.Tensor], indices: Optional[Union[np.ndarray, list, torch.Tensor]] = None
    ) -> None:
        """
        Args:
            offset (float): Contact offset of a collision shape. Allowed range [maximum(0, rest_offset), 0]. 
                            Default value is -inf, means default is picked by simulation based on the shape extent.
        """
        indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
        read_idx = 0
        for i in indices:
            self._physx_collision_apis[i.tolist()].GetContactOffsetAttr().Set(offsets[i].tolist())
            read_idx += 1
        return

    def get_contact_offset(
        self, indices: Optional[Union[np.ndarray, list, torch.Tensor]] = None
    ) -> Union[np.ndarray, list, torch.Tensor]:
        """
        Returns:
            float: contact offset of the collision shape.
        """
        indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
        offsets = self._backend_utils.create_zeros_tensor([indices.shape[0]], dtype="float32", device=self._device)
        write_idx = 0
        for i in indices:
            offsets[write_idx] = self._backend_utils.create_tensor_from_list(
                self._physx_collision_apis[i.tolist()].GetContactOffsetAttr().Get(),
                dtype="float32",
                device=self._device,
            )
            write_idx += 1
        return offsets

    def set_rest_offset(
        self, offsets: Union[np.ndarray, torch.Tensor], indices: Optional[Union[np.ndarray, list, torch.Tensor]] = None
    ) -> None:
        """
        Args:
            offset (float): Rest offset of a collision shape. Allowed range [-max_float, contact_offset. 
                            Default value is -inf, means default is picked by simulatiion. For rigid bodies its zero.
        """
        indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
        read_idx = 0
        for i in indices:
            self._physx_collision_apis[i.tolist()].GetRestOffsetAttr().Set(offsets[i].tolist())
            read_idx += 1
        return

    def get_rest_offset(
        self, indices: Optional[Union[np.ndarray, list, torch.Tensor]] = None
    ) -> Union[np.ndarray, list, torch.Tensor]:
        """
        Returns:
            float: rest offset of the collision shape.
        """
        indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
        offsets = self._backend_utils.create_zeros_tensor([indices.shape[0]], dtype="float32", device=self._device)
        write_idx = 0
        for i in indices:
            offsets[write_idx] = self._backend_utils.create_tensor_from_list(
                self._physx_collision_apis[i.tolist()].GetRestOffsetAttr().Get(), dtype="float32", device=self._device
            )
            write_idx += 1
        return offsets

    def set_torsional_patch_radii(
        self, radii: Union[np.ndarray, torch.Tensor], indices: Optional[Union[np.ndarray, list, torch.Tensor]] = None
    ) -> None:
        """
        Args:
            radius (float): radius of the contact patch used to apply torsional friction. Allowed range [0, max_float].
        """
        indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
        read_idx = 0
        for i in indices:
            self._physx_collision_apis[i.tolist()].GetTorsionalPatchRadiusAttr().Set(radii[i].tolist())
            read_idx += 1
        return

    def get_torsional_patch_radius(
        self, indices: Optional[Union[np.ndarray, list, torch.Tensor]] = None
    ) -> Union[np.ndarray, list, torch.Tensor]:
        """
        Returns:
            float: radius of the contact patch used to apply torsional friction. Allowed range [0, max_float].
        """
        indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
        radii = self._backend_utils.create_zeros_tensor([indices.shape[0]], dtype="float32", device=self._device)
        write_idx = 0
        for i in indices:
            radii[write_idx] = self._backend_utils.create_tensor_from_list(
                self._physx_collision_apis[i.tolist()].GetTorsionalPatchRadiusAttr().Get(),
                dtype="float32",
                device=self._device,
            )
            write_idx += 1
        return radii

    def set_min_torsional_patch_radii(
        self, radii: Union[np.ndarray, torch.Tensor], indices: Optional[Union[np.ndarray, list, torch.Tensor]] = None
    ) -> None:
        """
        Args:
            radius (float): minimum radius of the contact patch used to apply torsional friction. Allowed range [0, max_float].
        """
        indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
        read_idx = 0
        for i in indices:
            self._physx_collision_apis[i.tolist()].GetMinTorsionalPatchRadiusAttr().Set(radii[i.tolist()])
            read_idx += 1
        return

    def get_min_torsional_patch_radius(
        self, indices: Optional[Union[np.ndarray, list, torch.Tensor]] = None
    ) -> Union[np.ndarray, list, torch.Tensor]:
        """
        Returns:
            float: minimum radius of the contact patch used to apply torsional friction. Allowed range [0, max_float].
        """
        indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
        radii = self._backend_utils.create_zeros_tensor([indices.shape[0]], dtype="float32", device=self._device)
        write_idx = 0
        for i in indices:
            radii[write_idx] = self._backend_utils.create_tensor_from_list(
                self._physx_collision_apis[i.tolist()].GetMinTorsionalPatchRadiusAttr().Get(),
                dtype="float32",
                device=self._device,
            )
            write_idx += 1
        return radii

    def set_collision_approximations(
        self, approximation_types: List[str], indices: Optional[Union[np.ndarray, list, torch.Tensor]] = None
    ) -> None:
        """

        Args:
            approximation_type (str): approximation used for collision, could be "none", "convexHull" or "convexDecomposition"
        """
        indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
        read_idx = 0
        for i in indices:
            self._mesh_collision_apis[i.tolist()].GetApproximationAttr().Set(approximation_types[i])
            read_idx += 1
        return

    def get_collision_approximation(self, indices: Optional[Union[np.ndarray, list, torch.Tensor]] = None) -> List[str]:
        """
        Returns:
            str: approximation used for collision, could be "none", "convexHull" or "convexDecomposition"
        """
        indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
        approximation_types = [None] * indices.shape[0]
        write_idx = 0
        for i in indices:
            approximation_types[write_idx] = self._mesh_collision_apis[i.tolist()].GetApproximationAttr().Get()
            write_idx += 1
        return approximation_types

    def apply_physics_materials(
        self,
        physics_materials: Union[PhysicsMaterial, List[PhysicsMaterial]],
        weaker_than_descendants: Optional[Union[bool, List[bool]]] = None,
        indices: Optional[Union[np.ndarray, list, torch.Tensor]] = None,
    ):
        """Used to apply physics material to the held prim and optionally its descendants.

        Args:
            physics_material (PhysicsMaterial): physics material to be applied to the held prim. This where you want to
                                                define friction, restitution..etc. Note: if a physics material is not
                                                defined, the defaults will be used from PhysX.
            weaker_than_descendants (bool, optional): True if the material shouldn't override the descendants
                                                      materials, otherwise False. Defaults to False.
        """
        indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
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
                if self._binding_apis[i.tolist()] is None:
                    if self._prims[i].HasAPI(UsdShade.MaterialBindingAPI):
                        self._binding_apis[i.tolist()] = UsdShade.MaterialBindingAPI(self._prims[i.tolist()])
                    else:
                        self._binding_apis[i.tolist()] = UsdShade.MaterialBindingAPI.Apply(self._prims[i.tolist()])
                if weaker_than_descendants[read_idx]:
                    self._binding_apis[i.tolist()].Bind(
                        physics_materials[read_idx].material,
                        bindingStrength=UsdShade.Tokens.weakerThanDescendants,
                        materialPurpose="physics",
                    )
                else:
                    self._binding_apis[i.tolist()].Bind(
                        physics_materials[read_idx].material,
                        bindingStrength=UsdShade.Tokens.strongerThanDescendants,
                        materialPurpose="physics",
                    )
                self._applied_physics_materials[i.tolist()] = physics_materials[read_idx]
                read_idx += 1
            return
        else:
            if weaker_than_descendants is None:
                weaker_than_descendants = False
            for i in indices:
                if self._binding_apis[i.tolist()] is None:
                    if self._prims[i.tolist()].HasAPI(UsdShade.MaterialBindingAPI):
                        self._binding_apis[i.tolist()] = UsdShade.MaterialBindingAPI(self._prims[i.tolist()])
                    else:
                        self._binding_apis[i.tolist()] = UsdShade.MaterialBindingAPI.Apply(self._prims[i.tolist()])
                if weaker_than_descendants:
                    self._binding_apis[i].Bind(
                        physics_materials.material,
                        bindingStrength=UsdShade.Tokens.weakerThanDescendants,
                        materialPurpose="physics",
                    )
                else:
                    self._binding_apis[i.tolist()].Bind(
                        physics_materials.material,
                        bindingStrength=UsdShade.Tokens.strongerThanDescendants,
                        materialPurpose="physics",
                    )
                self._applied_physics_materials[i.tolist()] = physics_materials
        return

    def get_applied_physics_materials(
        self, indices: Optional[Union[np.ndarray, list, torch.Tensor]] = None
    ) -> List[PhysicsMaterial]:
        """Returns the current applied physics material in case it was applied using apply_physics_material or not.

        Returns:
            PhysicsMaterial: the current applied physics material.
        """
        indices = self._backend_utils.resolve_indices(indices, self.count, self._device)
        result = [None] * indices.shape[0]
        write_idx = 0
        for i in indices:
            if self._binding_apis[i.tolist()] is None:
                if self._prims[i].HasAPI(UsdShade.MaterialBindingAPI):
                    self._binding_apis[i.tolist()] = UsdShade.MaterialBindingAPI(self._prims[i.tolist()])
                else:
                    self._binding_apis[i.tolist()] = UsdShade.MaterialBindingAPI.Apply(self._prims[i.tolist()])
            if self._applied_physics_materials[i.tolist()] is not None:
                result[write_idx] = self._applied_visual_materials[i.tolist()]
                write_idx += 1
            else:
                physics_binding = self._binding_apis[i.tolist()].GetDirectBinding(materialPurpose="physics")
                material_path = physics_binding.GetMaterialPath()
                if material_path == "":
                    result[write_idx] = None
                else:
                    self._applied_physics_materials[i.tolist()] = PhysicsMaterial(prim_path=material_path)
                    result[write_idx] = self._applied_physics_materials[i.tolist()]
                write_idx += 1
        return result
