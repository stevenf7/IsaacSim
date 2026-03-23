# -- Test setup --
import omni.kit.commands
import omni.usd
from pxr import UsdGeom, UsdShade

stage = omni.usd.get_context().get_stage()

# Create a sphere to bind material to
UsdGeom.Sphere.Define(stage, "/hello/world")
sphere = stage.GetPrimAtPath("/hello/world")
# -- End test setup --

omni.kit.commands.execute(
    "CreateAndBindMdlMaterialFromLibrary",
    mdl_name="OmniSurface.mdl",
    mtl_name="OmniSurface",
    mtl_created_list=["/Looks/OmniSurface"],
)

new_material = UsdShade.Material.Get(stage, "/Looks/OmniSurface")

binding_api = UsdShade.MaterialBindingAPI.Apply(sphere)
binding_api.Bind(new_material)
