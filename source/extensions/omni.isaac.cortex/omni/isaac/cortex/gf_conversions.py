# Copyright (c) 2020-2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

""" A collection of conversion tools for converting to and from Graphics Foundation (GF) data
structures.
"""

from __future__ import print_function

import numpy as np
import tf.transformations
from pxr import Gf


def usd_euler_angles_from_matrix(R):
    """ Convert a rotation matrix R to a Gf.Vec3d containing Euler angles in degrees.
    """
    T = np.eye(4, 4)
    T[:3, :3] = R
    x, y, z = tf.transformations.euler_from_matrix(T)
    s = 180.0 / np.pi
    rot_euler_usd = Gf.Vec3d(s * x, s * y, s * z)
    return rot_euler_usd


def set_prim_transform(prim, T):
    """ Set the prim's Euler angle transform attributes to the information in the provided
    homogeneous transform matrix T.

    Sets xformOp:translate and xformOp:rotateXYZ. The latter Euler angle rotation information is
    represented in degrees.
    """

    translate = T[:3, 3]
    gf_translate = 100.0 * Gf.Vec3d(translate[0], translate[1], translate[2])

    translate_handle = prim.GetAttribute("xformOp:translate")
    rotate_xyz_handle = prim.GetAttribute("xformOp:rotateXYZ")

    translate_handle.Set(gf_translate)
    rotate_xyz_handle.Set(usd_euler_angles_from_matrix(T[:3, :3]))
