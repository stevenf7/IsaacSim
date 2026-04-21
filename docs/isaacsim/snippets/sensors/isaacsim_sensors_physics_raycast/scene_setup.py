import omni.usd
from pxr import Gf, Sdf, UsdGeom, UsdPhysics

stage = omni.usd.get_context().get_stage()

UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
UsdGeom.SetStageMetersPerUnit(stage, 1.0)

UsdPhysics.Scene.Define(stage, Sdf.Path("/World/PhysicsScene"))

ground = UsdGeom.Cube.Define(stage, "/World/GroundPlane")
ground.GetSizeAttr().Set(1.0)
ground.AddTranslateOp().Set(Gf.Vec3d(0, 0, -0.05))
ground.AddScaleOp().Set(Gf.Vec3f(50, 50, 0.1))
UsdPhysics.CollisionAPI.Apply(ground.GetPrim())

wall = UsdGeom.Cube.Define(stage, "/World/Obstacles/Wall")
wall.GetSizeAttr().Set(1.0)
wall.AddTranslateOp().Set(Gf.Vec3d(5, 0, 1.5))
wall.AddScaleOp().Set(Gf.Vec3f(0.2, 8, 3))
UsdPhysics.CollisionAPI.Apply(wall.GetPrim())

UsdGeom.Xform.Define(stage, "/World/Sensors")
