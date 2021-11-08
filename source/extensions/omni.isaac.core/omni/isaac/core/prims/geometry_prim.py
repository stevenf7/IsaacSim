# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

from typing import Optional
import numpy as np
from omni.isaac.core.prims.xform_prim import XFormPrim
from pxr import UsdGeom, UsdPhysics, PhysxSchema, UsdShade
from omni.isaac.core.utils.prims import get_prim_at_path

import carb
from omni.isaac.core.materials import PhysicsMaterial


class GeometryPrim(XFormPrim):
    def __init__(
        self,
        prim_path: str,
        name: Optional[str] = "geometry_prim",
        position: Optional[np.ndarray] = None,
        translation: Optional[np.ndarray] = None,
        orientation: Optional[np.ndarray] = None,
        scale: Optional[np.ndarray] = None,
        visible: bool = True,
        collision: bool = False,
    ) -> None:
        """Provides common functionalities to geometry prims such as cube, sphere..etc.

        Args:
            prim (Usd.Prim): USD prim object to encapsulate.
            geom (UsdGeom.Gprim): USD geometry object to encapsulate. You can retrive it using UsdGeom.Gprim(prim).
            name (str, optional): name given to the prim, this can be different than the prim path. Defaults to None.
            position (np.ndarray, optional): position in the world frame to set the prim. shape is (3, ) Defaults to None.
            orientation (np.ndarray, optional): quaternion orientation in the world frame to set the prim. 
                                              quaternion is scalar-first (w, x, y, z). shape is (4, ). Defaults to None.
            color (np.ndarray, optional): color to be applied to the geometric prim (R, G, B) 0-1. shape (3,). Defaults to None.
            visible (bool, optional): set to false for an invisible prim in the stage while rendering. Defaults to True.
        """
        prim = get_prim_at_path(prim_path)
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
        if prim.IsA(UsdGeom.Cube):
            self._geom = UsdGeom.Cube(prim)
        elif prim.IsA(UsdGeom.Capsule):
            self._geom = UsdGeom.Capsule(prim)
        elif prim.IsA(UsdGeom.Cone):
            self._geom = UsdGeom.Cone(prim)
        elif prim.IsA(UsdGeom.Cylinder):
            self._geom = UsdGeom.Cylinder(prim)
        elif prim.IsA(UsdGeom.Sphere):
            self._geom = UsdGeom.Sphere(prim)
        elif prim.IsA(UsdGeom.Mesh):
            self._geom = UsdGeom.Mesh(prim)
        else:
            self._geom = UsdGeom.Gprim(prim)
            carb.log_info(
                "prim type at path {} passed to the GeometryPrim is not supported at the moment".format(self.prim_path)
            )

        if collision and prim.HasAPI(UsdPhysics.CollisionAPI):
            self._collision_api = UsdPhysics.CollisionAPI(prim)
        elif collision:
            self._collision_api = UsdPhysics.CollisionAPI.Apply(prim)

        if collision and prim.HasAPI(UsdPhysics.MeshCollisionAPI):
            self._mesh_collision_api = UsdPhysics.MeshCollisionAPI(prim)
        elif collision:
            self._mesh_collision_api = UsdPhysics.MeshCollisionAPI.Apply(prim)

        if collision and prim.HasAPI(PhysxSchema.PhysxCollisionAPI):
            self._physx_collision_api = PhysxSchema.PhysxCollisionAPI(prim)
        elif collision:
            self._physx_collision_api = PhysxSchema.PhysxCollisionAPI.Apply(prim)
        self._applied_physics_material = None
        return

    @property
    def geom(self) -> UsdGeom.Gprim:
        """
        Returns:
            UsdGeom.Gprim: USD geometry object encapsulated.
        """
        return self._geom

    def set_contact_offset(self, offset):
        self._physx_collision_api.GetContactOffsetAttr().Set(offset)
        return

    def get_contact_offset(self):
        return self._physx_collision_api.GetContactOffsetAttr().Get()

    def set_rest_offset(self, offset):
        self._physx_collision_api.GetRestOffsetAttr().Set(offset)
        return

    def get_rest_offset(self):
        return self._physx_collision_api.GetRestOffsetAttr().Get()

    def set_torsional_patch_radius(self, radius):
        self._physx_collision_api.GetTorsionalPatchRadiusAttr().Set(radius)
        return

    def get_torsional_patch_radius(self):
        return self._physx_collision_api.GetTorsionalPatchRadiusAttr().Get()

    def set_min_torsional_patch_radius(self, radius):
        self._physx_collision_api.GetMinTorsionalPatchRadiusAttr().Set(radius)
        return

    def get_min_torsional_patch_radius(self):
        return self._physx_collision_api.GetMinTorsionalPatchRadiusAttr().Get()

    def set_collision_approximation(self, approximation_type):
        # approximation_type = ["none", "convexHull", "convexDecomposition"]
        self._mesh_collision_api.GetApproximationAttr().Get().Set(approximation_type)
        return

    def get_collision_approximation(self):
        return self._mesh_collision_api.GetApproximationAttr().Get()

    def apply_physics_material(self, physics_material, weaker_than_descendants=False):
        if self._binding_api is None:
            if self._prim.HasAPI(UsdShade.MaterialBindingAPI):
                self._binding_api = UsdShade.MaterialBindingAPI(self.prim)
            else:
                self._binding_api = UsdShade.MaterialBindingAPI.Apply(self.prim)
        if weaker_than_descendants:
            self._binding_api.Bind(
                physics_material.material,
                bindingStrength=UsdShade.Tokens.weakerThanDescendants,
                materialPurpose="physics",
            )
        else:
            self._binding_api.Bind(
                physics_material.material,
                bindingStrength=UsdShade.Tokens.strongerThanDescendants,
                materialPurpose="physics",
            )
        self._applied_physics_material = physics_material
        return

    def get_applied_physics_material(self):
        if self._binding_api is None:
            if self._prim.HasAPI(UsdShade.MaterialBindingAPI):
                self._binding_api = UsdShade.MaterialBindingAPI(self.prim)
            else:
                self._binding_api = UsdShade.MaterialBindingAPI.Apply(self.prim)
        if self._applied_physics_material is not None:
            return self._applied_physics_material
        else:
            physics_binding = self._binding_api.GetDirectBinding(materialPurpose="physics")
            path = physics_binding.GetMaterialPath()
            if path == "":
                return None
            else:
                self._applied_physics_material = PhysicsMaterial(prim_path=path)
                return self._applied_physics_material
