from pxr import Gf

translation = Gf.Vec3d(1, 0, 0)
sphere_xformable = UsdGeom.Xformable(sphere)
move_sphere_op = sphere_xformable.AddTranslateOp(opSuffix="moveSphereOp")
move_sphere_op.Set(translation)
