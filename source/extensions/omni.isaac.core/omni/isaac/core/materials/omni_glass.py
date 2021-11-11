# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

from omni.isaac.core.materials import VisualMaterial
import omni.kit.app
import carb
from pxr import Gf, UsdShade, Sdf
from typing import Optional
import numpy as np
from omni.isaac.core.utils.prims import move_prim, get_prim_at_path, is_prim_path_valid
from omni.kit.material.library import CreateAndBindMdlMaterialFromLibrary


class OmniGlass(VisualMaterial):
    def __init__(
        self,
        prim_path,
        name="omni_glass",
        shader=None,
        color: Optional[np.ndarray] = None,
        ior: float = None,
        depth: float = None,
        thin_walled: bool = None,
    ):
        # Check if material exists
        stage = omni.usd.get_context().get_stage()
        if is_prim_path_valid(prim_path=prim_path):
            material = UsdShade.Material(get_prim_at_path(prim_path))
        else:
            mtl_created_list = []
            CreateAndBindMdlMaterialFromLibrary(
                mdl_name="OmniGlass.mdl", mtl_name="OmniGlass", mtl_created_list=mtl_created_list
            ).do()
            move_prim(path_from=mtl_created_list[0], path_to=prim_path)
            material = UsdShade.Material(get_prim_at_path(prim_path))
        # omni.usd.create_material_input just calls the USD shader CreateInput(...) and adds a min / max rang,
        # display name, etc...  We don't need that here, so we can just call the USD shader api directly
        if shader is None:
            if stage.GetPrimAtPath(f"{prim_path}/shader").IsValid():
                carb.log_info("Shader Prim already defined at path: {}".format(f"{prim_path}/shader"))
                shader = UsdShade.Shader(stage.GetPrimAtPath(f"{prim_path}/shader"))
            elif stage.GetPrimAtPath(f"{prim_path}/Shader").IsValid():
                carb.log_info("Shader Prim already defined at path: {}".format(f"{prim_path}/shader"))
                shader = UsdShade.Shader(stage.GetPrimAtPath(f"{prim_path}/Shader"))
            else:
                raise Exception("omni glass shader is not defined")
        VisualMaterial.__init__(
            self,
            prim_path=prim_path,
            prim=stage.GetPrimAtPath(prim_path),
            shaders_list=[shader],
            material=material,
            name=name,
        )
        shader.CreateIdAttr("OmniGlass")
        if color is not None:
            shader.CreateInput("glass_color", Sdf.ValueTypeNames.Color3f).Set(Gf.Vec3f(*color.tolist()))
        if ior is not None:
            shader.CreateInput("glass_ior", Sdf.ValueTypeNames.Float).Set(ior)
        if depth is not None:
            shader.CreateInput("depth", Sdf.ValueTypeNames.Float).Set(depth)
        if thin_walled is not None:
            shader.CreateInput("thin_walled", Sdf.ValueTypeNames.Bool).Set(thin_walled)
        material.CreateSurfaceOutput().ConnectToSource(shader, "surface")

        return

    def set_color(self, color: np.ndarray):
        if self.shaders_list[0].GetInput("glass_color").Get() is None:
            self.shaders_list[0].CreateInput("glass_color", Sdf.ValueTypeNames.Color3f).Set(Gf.Vec3f(*color.tolist()))
        else:
            self.shaders_list[0].GetInput("glass_color").Set(Gf.Vec3f(*color.tolist()))
        return

    def get_color(self):
        if self.shaders_list[0].GetInput("glass_color").Get() is None:
            carb.log_warn("A color attribute is not set yet")
            return None
        else:
            return np.array(self.shaders_list[0].GetInput("glass_color").Get())

    def set_ior(self, ior):
        if self.shaders_list[0].GetInput("glass_ior").Get() is None:
            self.shaders_list[0].CreateInput("glass_ior", Sdf.ValueTypeNames.Float).Set(ior)
        else:
            self.shaders_list[0].GetInput("glass_ior").Set(ior)
        return

    def get_ior(self):
        if self.shaders_list[0].GetInput("glass_ior").Get() is None:
            carb.log_warn("A glass_ior attribute is not set yet")
            return None
        else:
            return self.shaders_list[0].GetInput("glass_ior").Get()

    def set_depth(self, depth):
        if self.shaders_list[0].GetInput("depth").Get() is None:
            self.shaders_list[0].CreateInput("depth", Sdf.ValueTypeNames.Float).Set(depth)
        else:
            self.shaders_list[0].GetInput("depth").Set(depth)
        return

    def get_depth(self):
        if self.shaders_list[0].GetInput("depth").Get() is None:
            carb.log_warn("A depth attribute is not set yet")
            return None
        else:
            return self.shaders_list[0].GetInput("depth").Get()

    def set_thin_walled(self, thin_walled):
        if self.shaders_list[0].GetInput("thin_walled").Get() is None:
            self.shaders_list[0].CreateInput("thin_walled", Sdf.ValueTypeNames.Float).Set(thin_walled)
        else:
            self.shaders_list[0].GetInput("thin_walled").Set(thin_walled)
        return

    def get_thin_walled(self):
        if self.shaders_list[0].GetInput("thin_walled").Get() is None:
            carb.log_warn("A thin_walled attribute is not set yet")
            return None
        else:
            return self.shaders_list[0].GetInput("thin_walled").Get()
