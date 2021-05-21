import omni
import asyncio
import carb


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
