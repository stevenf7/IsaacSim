import omni
from pxr import Gf, PhysicsSchemaTools, PhysxSchema, UsdGeom, UsdPhysics

# USD api for getting the stage
stage = omni.usd.get_context().get_stage()

# Adding a Cube
path = "/visual_cube_usd"
cubeGeom = UsdGeom.Cube.Define(stage, path)
cubePrim = stage.GetPrimAtPath(path)
size = 0.5
offset = Gf.Vec3f(1.5, -0.2, 1.0)
cubeGeom.CreateSizeAttr(size)
if not cubePrim.HasAttribute("xformOp:translate"):
    UsdGeom.Xformable(cubePrim).AddTranslateOp().Set(offset)
else:
    cubePrim.GetAttribute("xformOp:translate").Set(offset)
