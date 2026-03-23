# -- Test setup --
import omni.usd
from pxr import Gf, Sdf, UsdShade

stage = omni.usd.get_context().get_stage()
# -- End test setup --

# create the material and shader
material_path = "/hello/material"
mat_prim = stage.DefinePrim(Sdf.Path(material_path), "Material")
material_prim = UsdShade.Material.Get(stage, mat_prim.GetPath())

shader_path = stage.DefinePrim(Sdf.Path("{}/Shader".format(material_path)), "Shader")
shader_prim = UsdShade.Shader.Get(stage, shader_path.GetPath())

with Sdf.ChangeBlock():
    # connect up the shader graph
    shader_out = shader_prim.CreateOutput("out", Sdf.ValueTypeNames.Token)
    material_prim.CreateSurfaceOutput("mdl").ConnectToSource(shader_out)
    material_prim.CreateVolumeOutput("mdl").ConnectToSource(shader_out)
    material_prim.CreateDisplacementOutput("mdl").ConnectToSource(shader_out)
    shader_prim.GetImplementationSourceAttr().Set(UsdShade.Tokens.sourceAsset)
    shader_prim.SetSourceAsset(Sdf.AssetPath("OmniPBR.mdl"), "mdl")
    shader_prim.SetSourceAssetSubIdentifier("OmniPBR", "mdl")

    omni.usd.create_material_input(
        mat_prim,
        "diffuse_color_constant",
        Gf.Vec3f(1, 0, 0),
        Sdf.ValueTypeNames.Color3f,
    )
    omni.usd.create_material_input(
        mat_prim,
        "emissive_color",
        Gf.Vec3f(1, 0, 0),
        Sdf.ValueTypeNames.Color3f,
    )
