# Copyright (c) 2020-2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

# TODO: rename to gf_tools

from __future__ import print_function

import numpy as np
import tf.transformations
from pxr import Gf


def usd_euler_angles_from_matrix(R):
    T = np.eye(4, 4)
    T[:3, :3] = R
    x, y, z = tf.transformations.euler_from_matrix(T)
    s = 180.0 / np.pi
    rot_euler_usd = Gf.Vec3d(s * x, s * y, s * z)
    return rot_euler_usd


def set_prim_transform(prim, T):
    translate = T[:3, 3]
    gf_translate = 100.0 * Gf.Vec3d(translate[0], translate[1], translate[2])

    translate_handle = prim.GetAttribute("xformOp:translate")
    rotate_xyz_handle = prim.GetAttribute("xformOp:rotateXYZ")

    translate_handle.Set(gf_translate)
    rotate_xyz_handle.Set(usd_euler_angles_from_matrix(T[:3, :3]))
