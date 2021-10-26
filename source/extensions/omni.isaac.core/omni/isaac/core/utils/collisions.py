from omni.isaac.dynamic_control import _dynamic_control
from omni.isaac.utils._isaac_utils import math as math_utils
import omni.physx
from pxr import UsdGeom
from omni.isaac.core.utils.stage import get_current_stage


def ray_cast(position, orientation, offset, max_dist=100.0):
    """
    Projects a raycast forward from the end effector, with an offset in end effector space defined by (x_offset, y_offset, z_offset)
    if a hit is found on a distance of 100 centimiters, returns the object usd path and its distance
    """
    tr = _dynamic_control.Transform()
    tr.p = list(position)
    tr.r = [orientation[1], orientation[2], orientation[3], orientation[0]]
    offset_transform = _dynamic_control.Transform()
    offset_transform.p = list(offset)
    raycast_tf = math_utils.mul(tr, offset_transform)
    origin = raycast_tf.p
    rayDir = math_utils.get_basis_vector_x(raycast_tf.r)
    hit = omni.physx.get_physx_scene_query_interface().raycast_closest(origin, rayDir, max_dist)
    if hit["hit"]:
        usdGeom = UsdGeom.Mesh.Get(get_current_stage(), hit["rigidBody"])
        distance = hit["distance"]
        return usdGeom.GetPath().pathString, distance
    return None, 10000.0
