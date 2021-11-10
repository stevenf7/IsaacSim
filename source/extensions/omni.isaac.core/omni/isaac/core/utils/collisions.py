# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

import omni.physx
from pxr import UsdGeom, Gf
from omni.isaac.core.utils.stage import get_current_stage
import numpy as np
import typing


def ray_cast(
    position: np.array, orientation: np.array, offset: np.array, max_dist: float = 100.0
) -> typing.Tuple[str, float]:
    """Projects a raycast forward along x axis with specified offset
    if a hit is found on a distance of 100 centimiters, returns the object usd path and its distance
    
    Args:
        position (np.array): position for ray cast
        orientation (np.array): orientation for ray cast
        offset (np.array): Offset for ray cast
        max_dist (float, optional): Maximum distance to test for collisions in stage units,  Defaults to 100.0.
    
    Returns:
        typing.Tuple[str, float]: path to geometry that was hit and hit distance, returns None, 10000 if no hit occurred
    """

    input_tr = Gf.Matrix4f()
    input_tr.SetTranslate(Gf.Vec3f(*position))
    input_tr.SetRotateOnly(Gf.Quatf(*orientation.tolist()))
    offset_transform = Gf.Matrix4f()
    offset_transform.SetTranslate(Gf.Vec3f(*offset))
    raycast_tf = offset_transform * input_tr
    trans = raycast_tf.ExtractTranslation()
    direction = raycast_tf.ExtractRotation().TransformDir((1, 0, 0))
    origin = (trans[0], trans[1], trans[2])
    ray_dir = (direction[0], direction[1], direction[2])

    hit = omni.physx.get_physx_scene_query_interface().raycast_closest(origin, ray_dir, max_dist)
    if hit["hit"]:
        usdGeom = UsdGeom.Mesh.Get(get_current_stage(), hit["rigidBody"])
        distance = hit["distance"]
        return usdGeom.GetPath().pathString, distance
    return None, 10000.0
