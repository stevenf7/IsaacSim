# -- Test setup --
import omni.usd
from pxr import Sdf, UsdGeom, UsdShade

stage = omni.usd.get_context().get_stage()

# Create sphere and material
UsdGeom.Sphere.Define(stage, "/hello/world")
sphere = stage.GetPrimAtPath("/hello/world")
mat_prim = stage.DefinePrim(Sdf.Path("/hello/material"), "Material")
material_prim = UsdShade.Material.Get(stage, mat_prim.GetPath())
# -- End test setup --

# bind the material
material = UsdShade.Material(material_prim)
binding_api = UsdShade.MaterialBindingAPI.Apply(sphere)
binding_api.Bind(material)
