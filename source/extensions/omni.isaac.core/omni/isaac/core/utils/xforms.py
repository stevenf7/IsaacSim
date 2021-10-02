# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
import numpy as np
from omni.isaac.core.utils.rotations import quat_to_euler_angles
from pxr import Gf, Usd, UsdGeom
import carb


def reset_xform_ops(prim: Usd.Prim):
    """
    Remove all xform ops
    """
    xformable = UsdGeom.Xformable(prim)
    xformable.ClearXformOpOrder()
    # Remove any authored transform properties
    authored_prop_names = prim.GetAuthoredPropertyNames()
    for prop_name in authored_prop_names:
        if prop_name.startswith("xformOp:"):
            prim.RemoveProperty(prop_name)


def set_xform_position(prim: Usd.Prim, position: np.ndarray) -> None:
    """Sets the position of the prim in stage. The method does this through the USD API.

        Args:
            position (np.ndarray): position of the prim to set in stage. shape (3,).
        """
    if not isinstance(position, list):
        position = position.tolist()

    position = Gf.Vec3d(*position)

    properties = prim.GetPropertyNames()
    if "xformOp:translate" in properties:
        translate_attr = prim.GetAttribute("xformOp:translate")
        translate_attr.Set(position)
    elif "xformOp:translation" in properties:
        translation_attr = prim.GetAttribute("xformOp:translate")
        translation_attr.Set(position)
    elif "xformOp:transform" in properties:
        transform_attr = prim.GetAttribute("xformOp:transform")
        matrix = prim.GetAttribute("xformOp:transform").Get()
        matrix.SetTranslateOnly(position)
        transform_attr.Set(matrix)
    else:
        xform = UsdGeom.Xformable(prim)
        xform_op = xform.AddXformOp(UsdGeom.XformOp.TypeTransform, UsdGeom.XformOp.PrecisionDouble, "")
        xform_op.Set(Gf.Matrix4d().SetTranslate(position))
    return


def set_xform_orientation(prim: Usd.Prim, quat: np.ndarray) -> None:
    """Sets the orientation of the prim in stage. The method does this through the USD API.

        Args:
            quat (np.ndarray): orientation represented as a quaternion. quaternion is scalar-first (w, x, y, z).
                               shape (4,).
        """
    if not isinstance(quat, list):
        quat = quat.tolist()
    rotation_properties = [
        "xformOp:orient",
        "xformOp:rotateX",
        "xformOp:rotateXYZ",  #
        "xformOp:rotateXZY",  #
        "xformOp:rotateY",
        "xformOp:rotateYXZ",  #
        "xformOp:rotateYZX",  #
        "xformOp:rotateZ",
        "xformOp:rotateZYX",  #
        "xformOp:rotateZXY",  #
    ]
    properties = prim.GetPropertyNames()
    for rotation_property in rotation_properties:
        if rotation_property in properties:
            if rotation_property == "xformOp:orient":
                rotq = Gf.Quatf(*quat)
                rotation_attr = prim.GetAttribute(rotation_property)
                rotation_attr.Set(rotq)
            elif rotation_property == "xformOp:rotateXYZ":
                roll, pitch, yaw = quat_to_euler_angles(np.array(quat), degrees=True)
                rotation_attr = prim.GetAttribute(rotation_property)
                rotation_attr.Set(Gf.Vec3f(roll, pitch, yaw))
            elif rotation_property == "xformOp:rotateZYX":
                roll, pitch, yaw = quat_to_euler_angles(np.array(quat), degrees=True)
                rotation_attr = prim.GetAttribute(rotation_property)
                rotation_attr.Set(Gf.Vec3f(yaw, pitch, roll))
            elif rotation_property == "xformOp:rotateZXY":
                roll, pitch, yaw = quat_to_euler_angles(np.array(quat), degrees=True)
                rotation_attr = prim.GetAttribute(rotation_property)
                rotation_attr.Set(Gf.Vec3f(yaw, roll, pitch))
            elif rotation_property == "xformOp:rotateYZX":
                roll, pitch, yaw = quat_to_euler_angles(np.array(quat), degrees=True)
                rotation_attr = prim.GetAttribute(rotation_property)
                rotation_attr.Set(Gf.Vec3f(pitch, yaw, roll))
            elif rotation_property == "xformOp:rotateYXZ":
                roll, pitch, yaw = quat_to_euler_angles(np.array(quat), degrees=True)
                rotation_attr = prim.GetAttribute(rotation_property)
                rotation_attr.Set(Gf.Vec3f(pitch, roll, yaw))
            elif rotation_property == "xformOp:rotateXZY":
                roll, pitch, yaw = quat_to_euler_angles(np.array(quat), degrees=True)
                rotation_attr = prim.GetAttribute(rotation_property)
                rotation_attr.Set(Gf.Vec3f(roll, yaw, pitch))
            elif rotation_property == "xformOp:rotateY":
                # TODO: double check with Hammad
                roll, pitch, yaw = quat_to_euler_angles(np.array(quat), degrees=True)
                rotation_attr = prim.GetAttribute(rotation_property)
                rotation_attr.Set(pitch)
            elif rotation_property == "xformOp:rotateX":
                # TODO: double check with Hammad
                roll, pitch, yaw = quat_to_euler_angles(np.array(quat), degrees=True)
                rotation_attr = prim.GetAttribute(rotation_property)
                rotation_attr.Set(roll)
            elif rotation_property == "xformOp:rotateZ":
                # TODO: double check with Hammad
                roll, pitch, yaw = quat_to_euler_angles(np.array(quat), degrees=True)
                rotation_attr = prim.GetAttribute(rotation_property)
                rotation_attr.Set(yaw)
            else:
                carb.log_error(f"rotation property {rotation_property} is not defined in the list.")
            return
    rotm = Gf.Matrix3d(Gf.Quatd(*quat))
    if "xformOp:transform" in properties:
        transform_attr = prim.GetAttribute("xformOp:transform")
        matrix = prim.GetAttribute("xformOp:transform").Get()
        matrix.SetRotateOnly(rotm)
        transform_attr.Set(matrix)
    else:
        xform = UsdGeom.Xformable(prim)
        xform_op = xform.AddXformOp(UsdGeom.XformOp.TypeTransform, UsdGeom.XformOp.PrecisionDouble, "")
        xform_op.Set(Gf.Matrix4d().SetRotateOnly(rotm))
    return


def set_xform_scale(prim: Usd.Prim, scale: np.ndarray) -> None:
    """
     Sets the scale of the prim in stage. The method does this through the USD API.

    Args:
        scale (np.ndarray): scale of the prim to set in stage. shape (3,).
    """
    if not isinstance(scale, list):
        scale = scale.tolist()
    scale = Gf.Vec3d(*scale)
    properties = prim.GetPropertyNames()
    if "xformOp:scale" in properties:
        translate_attr = prim.GetAttribute("xformOp:scale")
        translate_attr.Set(scale)
    elif "xformOp:transform" in properties:
        transform_attr = prim.GetAttribute("xformOp:transform")
        matrix = prim.GetAttribute("xformOp:transform").Get().RemoveScaleShear()
        # because we cannto set the scale directly we multiply it to the existing matrix with its scale removed
        transform_attr.Set(Gf.Matrix4d().SetScale(scale) * matrix)
    else:
        xform = UsdGeom.Xformable(prim)
        xform_op = xform.AddXformOp(UsdGeom.XformOp.TypeTransform, UsdGeom.XformOp.PrecisionDouble, "")
        xform_op.Set(Gf.Matrix4d().SetScale(scale))
    return
