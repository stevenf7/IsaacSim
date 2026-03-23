# -- Test setup --
import omni
from pxr import Gf, UsdGeom

# Create a cube mesh in the stage
stage = omni.usd.get_context().get_stage()
result, path = omni.kit.commands.execute("CreateMeshPrimCommand", prim_type="Cube")
# -- End test setup --
# Get the prim and set its transform matrix
cube_prim = stage.GetPrimAtPath(path)
xform = UsdGeom.Xformable(cube_prim)
transform = xform.AddTransformOp()
mat = Gf.Matrix4d()
mat.SetTranslateOnly(Gf.Vec3d(0.10, 1, 1.5))
mat.SetRotateOnly(Gf.Rotation(Gf.Vec3d(0, 1, 0), 290))
transform.Set(mat)
