import omni
from pxr import Gf, Sdf, UsdShade

mtl_created_list = []
# Create a new material using OmniGlass.mdl
omni.kit.commands.execute(
    "CreateAndBindMdlMaterialFromLibrary",
    mdl_name="OmniGlass.mdl",
    mtl_name="OmniGlass",
    mtl_created_list=mtl_created_list,
)
# Get reference to created material
stage = omni.usd.get_context().get_stage()
mtl_prim = stage.GetPrimAtPath(mtl_created_list[0])
# Set material inputs, these can be determined by looking at the .mdl file
# or by selecting the Shader attached to the Material in the stage window and looking at the details panel
omni.usd.create_material_input(mtl_prim, "glass_color", Gf.Vec3f(0, 1, 0), Sdf.ValueTypeNames.Color3f)
omni.usd.create_material_input(mtl_prim, "glass_ior", 1.0, Sdf.ValueTypeNames.Float)
# Create a prim to apply the material to
result, path = omni.kit.commands.execute("CreateMeshPrimCommand", prim_type="Cube")
# Get the path to the prim
cube_prim = stage.GetPrimAtPath(path)
# Bind the material to the prim
cube_mat_shade = UsdShade.Material(mtl_prim)
UsdShade.MaterialBindingAPI(cube_prim).Bind(cube_mat_shade, UsdShade.Tokens.strongerThanDescendants)
