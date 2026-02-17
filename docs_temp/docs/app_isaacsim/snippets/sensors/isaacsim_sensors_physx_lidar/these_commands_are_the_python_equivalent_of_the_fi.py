from isaacsim.core.utils.stage import get_current_stage
from pxr import Gf, UsdGeom, UsdPhysics

stage = get_current_stage()
CubePath = "/World/CubeName"  # Create a Cube
cubeGeom = UsdGeom.Cube.Define(stage, CubePath)
cubePrim = stage.GetPrimAtPath(CubePath)
cubeGeom.AddTranslateOp().Set(Gf.Vec3f(2.0, 0.0, 0.0))  # Move it away from the LIDAR
cubeGeom.CreateSizeAttr(1)  # Scale it appropriately
collisionAPI = UsdPhysics.CollisionAPI.Apply(cubePrim)  # Add a Physics Collider to it
