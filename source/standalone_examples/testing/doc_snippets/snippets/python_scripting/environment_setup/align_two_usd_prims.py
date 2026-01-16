import omni
from pxr import Gf, UsdGeom

stage = omni.usd.get_context().get_stage()
# Create a cube
result, path_a = omni.kit.commands.execute("CreateMeshPrimCommand", prim_type="Cube")
prim_a = stage.GetPrimAtPath(path_a)
# change the cube pose
xform = UsdGeom.Xformable(prim_a)
transform = xform.AddTransformOp()
mat = Gf.Matrix4d()
mat.SetTranslateOnly(Gf.Vec3d(0.10, 1, 1.5))
mat.SetRotateOnly(Gf.Rotation(Gf.Vec3d(0, 1, 0), 290))
transform.Set(mat)
# Create a second cube
result, path_b = omni.kit.commands.execute("CreateMeshPrimCommand", prim_type="Cube")
prim_b = stage.GetPrimAtPath(path_b)
# Get the transform of the first cube
pose = omni.usd.utils.get_world_transform_matrix(prim_a)
# Clear the transform on the second cube
xform = UsdGeom.Xformable(prim_b)
xform.ClearXformOpOrder()
# Set the pose of prim_b to that of prim_b
xform_op = xform.AddXformOp(UsdGeom.XformOp.TypeTransform, UsdGeom.XformOp.PrecisionDouble, "")
xform_op.Set(pose)
