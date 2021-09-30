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
from omni.isaac.utils.scripts.test_utils import load_test_file
from omni.isaac.utils.scripts.nucleus_utils import find_nucleus_server


def create_joint_state(name, position, velocity=[], effort=[]):
    import rospy
    from sensor_msgs.msg import JointState
    from std_msgs.msg import Header

    js = JointState()
    js.header = Header()
    js.header.stamp = rospy.Time.now()
    js.name = name
    js.position = position
    js.velocity = velocity
    js.effort = effort
    return js


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


async def simulate(seconds, steps_per_sec=60):
    for frame in range(int(steps_per_sec * seconds)):
        await omni.kit.app.get_app().next_update_async()


async def wait_for_rosmaster():
    carb.log_info("Waiting for rosmaster to start")
    import rosgraph

    tries = 0
    while True:
        if tries > 10:
            carb.log_info(f"ROS master was not found after {tries} tries")
            return

        try:
            tries = tries + 1
            rosgraph.Master("/rostopic").getPid()
        except:
            carb.log_info("ROS master is not running yet...")
            await asyncio.sleep(1.0)
            continue
        else:
            carb.log_info("ROS master is running, continuing")
            break


async def bridge_rosmaster_connect(_rosbridge):

    tries = 0
    while True:
        if tries > 100:
            carb.log_info(f"ROS master was not found after {tries} tries")
            return
        if _rosbridge.ros_master_check():
            carb.log_info(f"ROS master was found after {tries} tries")
            return
        else:
            await omni.kit.app.get_app().next_update_async()
            tries = tries + 1


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

    result, nucleus_server = find_nucleus_server()
    if result is False:
        carb.log_error("Could not find nucleus server with /Isaac folder")
        return
    nucleus_path = nucleus_server + "/Isaac"
    (result, error) = await load_test_file(nucleus_path + "/Robots/Carter/carter_v1.usd")
    stage = omni.usd.get_context().get_stage()

    PhysicsSchemaTools.addGroundPlane(stage, "/World/groundPlane", "Z", 1500, Gf.Vec3f(0, 0, -25), Gf.Vec3f(0.5))


async def add_carter_ros():
    from pxr import Gf, PhysicsSchemaTools

    result, nucleus_server = find_nucleus_server()
    if result is False:
        carb.log_error("Could not find nucleus server with /Isaac folder")
        return
    nucleus_path = nucleus_server + "/Isaac"
    (result, error) = await load_test_file(nucleus_path + "/Samples/ROS/Robots/Carter_ROS.usd")
    stage = omni.usd.get_context().get_stage()

    PhysicsSchemaTools.addGroundPlane(stage, "/World/groundPlane", "Z", 1500, Gf.Vec3f(0, 0, -25), Gf.Vec3f(0.5))


async def add_franka():
    result, nucleus_server = find_nucleus_server()
    if result is False:
        carb.log_error("Could not find nucleus server with /Isaac folder")
        return
    nucleus_path = nucleus_server + "/Isaac"
    (result, error) = await load_test_file(nucleus_path + "/Robots/Franka/franka.usd")
    stage = omni.usd.get_context().get_stage()
