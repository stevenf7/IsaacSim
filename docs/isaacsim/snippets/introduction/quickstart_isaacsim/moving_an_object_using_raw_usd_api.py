# -- Test setup --
import omni.usd
from pxr import Gf, UsdGeom

stage = omni.usd.get_context().get_stage()
UsdGeom.Cube.Define(stage, "/visual_cube_usd")
# -- End test setup --
cube_prim = stage.GetPrimAtPath("/visual_cube_usd")
translate_offset = Gf.Vec3f(1.5, -0.2, 1.0)
rotate_offset = Gf.Vec3f(90, -90, 180)  # note this is in degrees
scale = Gf.Vec3f(1, 1.5, 0.2)
# translation
if not cube_prim.HasAttribute("xformOp:translate"):
    UsdGeom.Xformable(cube_prim).AddTranslateOp().Set(translate_offset)
else:
    cube_prim.GetAttribute("xformOp:translate").Set(translate_offset)
# rotation
if not cube_prim.HasAttribute(
    "xformOp:rotateXYZ"
):  # there are also "xformOp:orient" for quaternion rotation, as well as "xformOp:rotateX", "xformOp:rotateY", "xformOp:rotateZ" for individual axis rotation
    UsdGeom.Xformable(cube_prim).AddRotateXYZOp().Set(rotate_offset)
else:
    cube_prim.GetAttribute("xformOp:rotateXYZ").Set(rotate_offset)
# scale
if not cube_prim.HasAttribute("xformOp:scale"):
    UsdGeom.Xformable(cube_prim).AddScaleOp().Set(scale)
else:
    cube_prim.GetAttribute("xformOp:scale").Set(scale)
