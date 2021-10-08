# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
from typing import Optional
import omni.kit.app
import carb
from pxr import UsdShade, UsdPhysics


class PhysicsMaterial(object):
    def __init__(
        self,
        prim_path,
        name="physics_material",
        static_friction: Optional[float] = None,
        dynamic_friction: Optional[float] = None,
        restitution: Optional[float] = None,
    ) -> None:
        self._name = name
        self._prim_path = prim_path

        stage = omni.usd.get_context().get_stage()
        if stage.GetPrimAtPath(prim_path).IsValid():
            carb.log_warn("Physics Material Prim already defined at path: {}".format(prim_path))
            self._material = UsdShade.Material(stage.GetPrimAtPath(prim_path))
        else:
            self._material = UsdShade.Material.Define(stage, prim_path)
        self._prim = stage.GetPrimAtPath(prim_path)
        if self._prim.HasAPI(UsdPhysics.MaterialAPI):
            self._material_api = UsdPhysics.MaterialAPI(self._prim)
        else:
            self._material_api = UsdPhysics.MaterialAPI.Apply(self._prim)
        if static_friction is not None:
            self._material_api.CreateStaticFrictionAttr().Set(static_friction)
        if dynamic_friction is not None:
            self._material_api.CreateDynamicFrictionAttr().Set(dynamic_friction)
        if restitution is not None:
            self._material_api.CreateRestitutionAttr().Set(restitution)
        return

    @property
    def prim_path(self):
        return self._prim_path

    @property
    def prim(self):
        return self._prim

    @property
    def name(self):
        return self._name

    @property
    def material(self):
        return self._material

    def set_dynamic_friction(self, friction):
        if self._material_api.GetDynamicFrictionAttr().Get() is None:
            self._material_api.CreateDynamicFrictionAttr().Set(friction)
        else:
            self._material_api.GetDynamicFrictionAttr().Set(friction)
        return

    def get_dynamic_friction(self):
        if self._material_api.GetDynamicFrictionAttr().Get() is None:
            carb.log_warn("A dynamic friction attribute is not set yet")
            return None
        else:
            return self._material_api.GetDynamicFrictionAttr().Get()

    def set_static_friction(self, friction):
        if self._material_api.GetStaticFrictionAttr().Get() is None:
            self._material_api.CreateStaticFrictionAttr().Set(friction)
        else:
            self._material_api.GetStaticFrictionAttr().Set(friction)
        return

    def get_static_friction(self):
        if self._material_api.GetStaticFrictionAttr().Get() is None:
            carb.log_warn("A static friction attribute is not set yet")
            return None
        else:
            return self._material_api.GetStaticFrictionAttr().Get()

    def set_restitution(self, restitution):
        if self._material_api.GetRestitutionAttr().Get() is None:
            self._material_api.CreateRestitutionAttr().Set(restitution)
        else:
            self._material_api.GetRestitutionAttr().Set(restitution)
        return

    def get_restitution(self):
        if self._material_api.GetRestitutionAttr().Get() is None:
            carb.log_warn("A restitution attribute is not set yet")
            return None
        else:
            return self._material_api.GetRestitutionAttr().Get()
