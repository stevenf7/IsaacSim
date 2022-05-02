# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

from typing import Optional, Sequence

import carb
from omni.isaac.core.materials import PhysicsMaterial
from omni.isaac.core.prims.xform_prim import XFormPrim
from omni.isaac.core.utils.prims import get_prim_at_path
from pxr import PhysxSchema, UsdGeom, UsdPhysics, UsdShade


class GeometryPrim(XFormPrim):
    """Provides high level functions to deal with a Geom prim and its attributes/ properties.
           The prim_path should correspond to type UsdGeom.Cube, UsdGeom.Capsule, UsdGeom.Cone, UsdGeom.Cylinder,
           UsdGeom.Sphere or UsdGeom.Mesh.

        Args:
            prim_path (str): prim path of the Prim to encapsulate or create.
            name (str, optional): shortname to be used as a key by Scene class.
                                    Note: needs to be unique if the object is added to the Scene.
                                    Defaults to "xform_prim".
            position (Optional[Sequence[float]], optional): position in the world frame of the prim. shape is (3, ).
                                                        Defaults to None, which means left unchanged.
            translation (Optional[Sequence[float]], optional): translation in the local frame of the prim
                                                            (with respect to its parent prim). shape is (3, ).
                                                            Defaults to None, which means left unchanged.
            orientation (Optional[Sequence[float]], optional): quaternion orientation in the world/ local frame of the prim
                                                            (depends if translation or position is specified).
                                                            quaternion is scalar-first (w, x, y, z). shape is (4, ).
                                                            Defaults to None, which means left unchanged.
            scale (Optional[Sequence[float]], optional): local scale to be applied to the prim's dimensions. shape is (3, ).
                                                    Defaults to None, which means left unchanged.
            visible (bool, optional): set to false for an invisible prim in the stage while rendering. Defaults to True.
            collision (bool, optional): Set to True if the geometry should have a collider (i.e not only a visual geometry).
                                        Defaults to False.
        """

    def __init__(
        self,
        prim_path: str,
        name: str = "geometry_prim",
        position: Optional[Sequence[float]] = None,
        translation: Optional[Sequence[float]] = None,
        orientation: Optional[Sequence[float]] = None,
        scale: Optional[Sequence[float]] = None,
        visible: bool = True,
        collision: bool = False,
    ) -> None:
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
            carb.log_warn(
                "prim type at path {} passed to the GeometryPrim is not supported at the moment".format(self.prim_path)
            )

        self._apply_collision_api(collision)
        self._applied_physics_material = None

    @property
    def geom(self) -> UsdGeom.Gprim:
        """
        Returns:
            UsdGeom.Gprim: USD geometry object encapsulated.
        """
        return self._geom

    def set_contact_offset(self, offset: float) -> None:
        """
        Args:
            offset (float): Contact offset of a collision shape. Allowed range [maximum(0, rest_offset), 0].
                            Default value is -inf, means default is picked by simulation based on the shape extent.
        """
        if self._physx_collision_api is None:
            raise RuntimeError(f"Physics collision API have not been set for the prim: {self.prim_path}")
        self._physx_collision_api.GetContactOffsetAttr().Set(offset)
        return

    def get_contact_offset(self) -> float:
        """
        Returns:
            float: contact offset of the collision shape.
        """
        if self._physx_collision_api is None:
            raise RuntimeError(f"Physics collision API have not been set for the prim: {self.prim_path}")
        return self._physx_collision_api.GetContactOffsetAttr().Get()

    def set_rest_offset(self, offset: float) -> None:
        """
        Args:
            offset (float): Rest offset of a collision shape. Allowed range [-max_float, contact_offset.
                            Default value is -inf, means default is picked by simulatiion. For rigid bodies its zero.
        """
        if self._physx_collision_api is None:
            raise RuntimeError(f"Physics collision API have not been set for the prim: {self.prim_path}")
        self._physx_collision_api.GetRestOffsetAttr().Set(offset)
        return

    def get_rest_offset(self) -> float:
        """
        Returns:
            float: rest offset of the collision shape.
        """
        if self._physx_collision_api is None:
            raise RuntimeError(f"Physics collision API have not been set for the prim: {self.prim_path}")
        return self._physx_collision_api.GetRestOffsetAttr().Get()

    def set_torsional_patch_radius(self, radius: float) -> None:
        """
        Args:
            radius (float): radius of the contact patch used to apply torsional friction. Allowed range [0, max_float].
        """
        if self._physx_collision_api is None:
            raise RuntimeError(f"Physics collision API have not been set for the prim: {self.prim_path}")
        self._physx_collision_api.GetTorsionalPatchRadiusAttr().Set(radius)
        return

    def get_torsional_patch_radius(self) -> float:
        """
        Returns:
            float: radius of the contact patch used to apply torsional friction. Allowed range [0, max_float].
        """
        if self._physx_collision_api is None:
            raise RuntimeError(f"Physics collision API have not been set for the prim: {self.prim_path}")
        return self._physx_collision_api.GetTorsionalPatchRadiusAttr().Get()

    def set_min_torsional_patch_radius(self, radius: float) -> None:
        """
        Args:
            radius (float): minimum radius of the contact patch used to apply torsional friction. Allowed range [0, max_float].
        """
        if self._physx_collision_api is None:
            raise RuntimeError(f"Physics collision API have not been set for the prim: {self.prim_path}")
        self._physx_collision_api.GetMinTorsionalPatchRadiusAttr().Set(radius)
        return

    def get_min_torsional_patch_radius(self) -> float:
        """
        Returns:
            float: minimum radius of the contact patch used to apply torsional friction. Allowed range [0, max_float].
        """
        if self._physx_collision_api is None:
            raise RuntimeError(f"Physics collision API have not been set for the prim: {self.prim_path}")
        return self._physx_collision_api.GetMinTorsionalPatchRadiusAttr().Get()

    def set_collision_approximation(self, approximation_type: str) -> None:
        """

        Args:
            approximation_type (str): approximation used for collision, could be "none", "convexHull" or "convexDecomposition"
        """
        if self._mesh_collision_api is None:
            raise RuntimeError(f"Mesh collision API have not been set for the prim: {self.prim_path}")
        self._mesh_collision_api.GetApproximationAttr().Set(approximation_type)
        return

    def get_collision_approximation(self) -> str:
        """
        Returns:
            str: approximation used for collision, could be "none", "convexHull" or "convexDecomposition"
        """
        if self._mesh_collision_api is None:
            raise RuntimeError(f"Mesh collision API have not been set for the prim: {self.prim_path}")
        return self._mesh_collision_api.GetApproximationAttr().Get()

    def set_collision_enabled(self, enabled: bool) -> None:
        """

        Args:
        """
        if self._collision_api is None:
            raise RuntimeError(f"Mesh collision API have not been set for the prim: {self.prim_path}")
        self._collision_api.GetCollisionEnabledAttr().Set(enabled)
        return

    def get_collision_enabled(self) -> bool:
        """
        Returns:
        """
        if self._collision_api is None:
            raise RuntimeError(f"Mesh collision API have not been set for the prim: {self.prim_path}")
        return self._collision_api.GetCollisionEnabledAttr().Get()

    def apply_physics_material(self, physics_material: PhysicsMaterial, weaker_than_descendants: bool = False):
        """Used to apply physics material to the held prim and optionally its descendants.

        Args:
            physics_material (PhysicsMaterial): physics material to be applied to the held prim. This where you want to
                                                define friction, restitution..etc. Note: if a physics material is not
                                                defined, the defaults will be used from PhysX.
            weaker_than_descendants (bool, optional): True if the material shouldn't override the descendants
                                                      materials, otherwise False. Defaults to False.
        """
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

    def get_applied_physics_material(self) -> PhysicsMaterial:
        """Returns the current applied physics material in case it was applied using apply_physics_material or not.

        Returns:
            PhysicsMaterial: the current applied physics material.
        """
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

    def _apply_collision_api(self, collision: bool) -> None:
        """Applies collision API to the prim.

        Args:
            collision (bool): Whether to apply the API or not.
        """
        if collision:
            if self.prim.HasAPI(UsdPhysics.CollisionAPI):
                self._collision_api = UsdPhysics.CollisionAPI(self.prim)
            else:
                self._collision_api = UsdPhysics.CollisionAPI.Apply(self.prim)

            if self.prim.HasAPI(UsdPhysics.MeshCollisionAPI):
                self._mesh_collision_api = UsdPhysics.MeshCollisionAPI(self.prim)
            else:
                self._mesh_collision_api = UsdPhysics.MeshCollisionAPI.Apply(self.prim)

            if self.prim.HasAPI(PhysxSchema.PhysxCollisionAPI):
                self._physx_collision_api = PhysxSchema.PhysxCollisionAPI(self.prim)
            else:
                self._physx_collision_api = PhysxSchema.PhysxCollisionAPI.Apply(self.prim)
        else:
            self._collision_api = None
            self._mesh_collision_api = None
            self._physx_collision_api = None
