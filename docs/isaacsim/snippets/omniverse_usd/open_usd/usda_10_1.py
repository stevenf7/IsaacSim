# -- Test setup --
import omni.usd
from pxr import Gf, Sdf, UsdShade

stage = omni.usd.get_context().get_stage()

# Create material and shader (from previous snippet context)
material_path = "/hello/material"
stage.DefinePrim(Sdf.Path(material_path), "Material")
shader_prim = stage.DefinePrim(Sdf.Path("{}/Shader".format(material_path)), "Shader")
shader = UsdShade.Shader.Get(stage, shader_prim.GetPath())
shader.CreateInput("diffuse_color_constant", Sdf.ValueTypeNames.Color3f).Set(Gf.Vec3f(1, 0, 0))
# -- End test setup --

new_shader = UsdShade.Shader.Get(stage, "/hello/material/Shader")
new_shader.GetInput("diffuse_color_constant").Set(Gf.Vec3f(0, 0, 1))
