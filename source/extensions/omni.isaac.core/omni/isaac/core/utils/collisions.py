# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

from pxr import UsdShade, UsdPhysics, Usd
from typing import Optional


def add_physics_material(
    stage: Usd.Stage,
    prim: Usd.Prim,
    static_friction: float,
    dynamic_friction: float,
    restitution: float,
    density: Optional(float) = None,
) -> UsdShade.Material:
    """adds a physics material to the prim passed in as an argument with the specified material properties.

    Args:
        stage (Usd.Stage): current usd stage used.
        prim (Usd.Prim): prim object to encapsulate.
        static_friction (float): static friction to be applied on the physics material.
        dynamic_friction (float): dynamic friction to be applied on the physics material.
        restitution (float): restitution to be applied on the physics material.
        density (float, optional): density to be applied in kg. Defaults to None.

    Returns:
        UsdShade.Material: the material prim that was applied to the prim passed in as an argument.
    """
    path = f"{prim.GetPath()}/PhysicsMaterial"
    materialPrim = UsdShade.Material.Define(stage, path)
    material = UsdPhysics.MaterialAPI.Apply(stage.GetPrimAtPath(path))
    if density is not None:
        material.CreateDensityAttr().Set(density)
    material.CreateStaticFrictionAttr().Set(static_friction)
    material.CreateDynamicFrictionAttr().Set(dynamic_friction)
    material.CreateRestitutionAttr().Set(restitution)
    bindingAPI = UsdShade.MaterialBindingAPI.Apply(prim)
    bindingAPI.Bind(materialPrim, UsdShade.Tokens.weakerThanDescendants, "physics")
    return materialPrim
