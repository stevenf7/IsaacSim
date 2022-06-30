# Copyright (c) 2018-2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

import omni
import asyncio
import carb
from omni.isaac.core.utils.stage import open_stage_async
from omni.isaac.core.utils.nucleus import get_assets_root_path


def set_translate(prim, new_loc):
    from pxr import Gf, UsdGeom

    properties = prim.GetPropertyNames()
    if "xformOp:translate" in properties:
        translate_attr = prim.GetAttribute("xformOp:translate")

        translate_attr.Set(new_loc)
    elif "xformOp:translation" in properties:
        translation_attr = prim.GetAttribute("xformOp:translate")
        translation_attr.Set(new_loc)
    elif "xformOp:transform" in properties:
        transform_attr = prim.GetAttribute("xformOp:transform")
        matrix = prim.GetAttribute("xformOp:transform").Get()
        matrix.SetTranslateOnly(new_loc)
        transform_attr.Set(matrix)
    else:
        xform = UsdGeom.Xformable(prim)
        xform_op = xform.AddXformOp(UsdGeom.XformOp.TypeTransform, UsdGeom.XformOp.PrecisionDouble, "")
        xform_op.Set(Gf.Matrix4d().SetTranslate(new_loc))


def set_rotate(prim, rot_mat):
    from pxr import Gf, UsdGeom

    properties = prim.GetPropertyNames()
    if "xformOp:rotate" in properties:
        rotate_attr = prim.GetAttribute("xformOp:rotate")
        rotate_attr.Set(rot_mat)
    elif "xformOp:transform" in properties:
        transform_attr = prim.GetAttribute("xformOp:transform")
        matrix = prim.GetAttribute("xformOp:transform").Get()
        matrix.SetRotateOnly(rot_mat.ExtractRotation())
        transform_attr.Set(matrix)
    else:
        xform = UsdGeom.Xformable(prim)
        xform_op = xform.AddXformOp(UsdGeom.XformOp.TypeTransform, UsdGeom.XformOp.PrecisionDouble, "")
        xform_op.Set(Gf.Matrix4d().SetRotate(rot_mat))


async def add_cube(path, size, offset):
    from pxr import UsdPhysics, UsdGeom

    stage = omni.usd.get_context().get_stage()
    cubeGeom = UsdGeom.Cube.Define(stage, path)
    cubePrim = stage.GetPrimAtPath(path)

    cubeGeom.CreateSizeAttr(size)
    cubeGeom.AddTranslateOp().Set(offset)
    await omni.kit.app.get_app().next_update_async()  # Need this to avoid flatcache errors
    rigid_api = UsdPhysics.RigidBodyAPI.Apply(cubePrim)
    rigid_api.CreateRigidBodyEnabledAttr(True)
    UsdPhysics.CollisionAPI.Apply(cubePrim)

    return cubeGeom


async def add_carter():
    from pxr import Gf, PhysicsSchemaTools

    assets_root_path = get_assets_root_path()
    if assets_root_path is None:
        carb.log_error("Could not find Isaac Sim assets folder")
        return
    (result, error) = await open_stage_async(assets_root_path + "/Isaac/Robots/Carter/carter_v1.usd")
    stage = omni.usd.get_context().get_stage()

    PhysicsSchemaTools.addGroundPlane(stage, "/World/groundPlane", "Z", 1500, Gf.Vec3f(0, 0, -0.25), Gf.Vec3f(0.5))


async def add_carter_ros():
    from pxr import Gf, PhysicsSchemaTools

    assets_root_path = get_assets_root_path()
    if assets_root_path is None:
        carb.log_error("Could not find Isaac Sim assets folder")
        return
    (result, error) = await open_stage_async(assets_root_path + "/Isaac/Samples/ROS2/Robots/Carter_ROS.usd")

    # Disabling cameras by default
    import omni.graph.core as og

    ros_cameras_graph_path = "/Carter/ROS_Cameras"
    og.Controller.set(og.Controller.attribute(ros_cameras_graph_path + "/enable_camera_left.inputs:condition"), False)
    og.Controller.set(og.Controller.attribute(ros_cameras_graph_path + "/enable_camera_right.inputs:condition"), False)

    stage = omni.usd.get_context().get_stage()

    PhysicsSchemaTools.addGroundPlane(stage, "/World/groundPlane", "Z", 1500, Gf.Vec3f(0, 0, -0.25), Gf.Vec3f(0.5))


async def add_franka():
    assets_root_path = get_assets_root_path()
    if assets_root_path is None:
        carb.log_error("Could not find Isaac Sim assets folder")
        return
    (result, error) = await open_stage_async(assets_root_path + "/Isaac/Robots/Franka/franka.usd")
