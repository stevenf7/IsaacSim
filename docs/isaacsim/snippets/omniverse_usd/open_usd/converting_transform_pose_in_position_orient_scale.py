import omni.usd
from pxr import Gf, Usd, UsdGeom


def convert_ops_from_transform(prim: Usd.Prim):

    # Get the Xformable from prim
    xform = UsdGeom.Xformable(prim)

    # Gets local transform matrix - used to convert the Xform Ops.
    pose = omni.usd.get_local_transform_matrix(prim)

    # Compute Scale
    x_scale = Gf.Vec3d(pose[0][0], pose[0][1], pose[0][2]).GetLength()
    y_scale = Gf.Vec3d(pose[1][0], pose[1][1], pose[1][2]).GetLength()
    z_scale = Gf.Vec3d(pose[2][0], pose[2][1], pose[2][2]).GetLength()

    # Clear Transforms from xform.
    xform.ClearXformOpOrder()

    # Add the Transform, orient, scale set
    xform_op_t = xform.AddXformOp(UsdGeom.XformOp.TypeTranslate, UsdGeom.XformOp.PrecisionDouble, "")
    xform_op_r = xform.AddXformOp(UsdGeom.XformOp.TypeOrient, UsdGeom.XformOp.PrecisionDouble, "")
    xform_op_s = xform.AddXformOp(UsdGeom.XformOp.TypeScale, UsdGeom.XformOp.PrecisionDouble, "")

    xform_op_t.Set(pose.ExtractTranslation())
    xform_op_r.Set(pose.ExtractRotationQuat().GetNormalized())
    xform_op_s.Set(Gf.Vec3d(x_scale, y_scale, z_scale))
