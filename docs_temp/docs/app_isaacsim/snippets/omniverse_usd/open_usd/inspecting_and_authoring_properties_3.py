translation = Gf.Vec3d(0, 0, 1)
xform_xformable = UsdGeom.Xformable(xform)
move_parent_op = xform_xformable.AddTranslateOp(opSuffix="moveParentOp")
move_parent_op.Set(translation)
