import lula
from omni.isaac.core.prims.xform_prim import XFormPrim
from omni.isaac.core.utils.numpy.rotations import quats_to_rot_matrices


def get_prim_pose_in_meters(prim: XFormPrim, meters_per_unit: float):
    pos, quat_rot = prim.get_world_pose()
    rot = quats_to_rot_matrices(quat_rot)
    pos *= meters_per_unit
    return pos, rot


def get_prim_pose_in_meters_rel_robot_base(prim, meters_per_unit, robot_pos, robot_rot):
    # returns the position of a prim relative to the position of the robot
    trans, rot = get_prim_pose_in_meters(prim, meters_per_unit)
    return get_pose_rel_robot_base(trans, rot, robot_pos, robot_rot)


def get_pose_rel_robot_base(trans, rot, robot_pos, robot_rot):
    inv_rob_rot = robot_rot.T

    if trans is not None:
        trans_rel = inv_rob_rot @ (trans - robot_pos)
    else:
        trans_rel = None

    if rot is not None:
        rot_rel = inv_rob_rot @ rot
    else:
        rot_rel = None

    return trans_rel, rot_rel


def get_pose3(trans=None, rot=None):
    if trans is None and rot is None:
        return lula.Pose3()

    if trans is None:
        return lula.Pose3.from_rotation(lula.Rotation3(rot))

    if rot is None:
        return lula.Pose3.from_translation(trans)

    return lula.Pose3(lula.Rotation3(rot), trans)
