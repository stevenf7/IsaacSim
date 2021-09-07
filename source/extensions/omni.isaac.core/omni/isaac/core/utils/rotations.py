# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

import numpy as np
from pxr import Gf
import math


def rot_matrix_from_quat(quat: np.ndarray) -> np.ndarray:
    # might need to be normalized
    rotm = Gf.Matrix3f(Gf.Quatf(*quat.tolist())).GetTranspose()
    return np.array(rotm)


def quat_to_euler_angles(quat: np.ndarray) -> np.ndarray:
    quat_img = quat[1:]
    quat_real = quat[0]
    # roll (x-axis rotation)
    sinr_cosp = 2 * (quat_real * quat_img[0] + quat_img[1] * quat_img[2])
    cosr_cosp = 1 - 2 * (quat_img[0] * quat_img[0] + quat_img[1] * quat_img[1])
    roll = math.atan2(sinr_cosp, cosr_cosp)

    # pitch (y-axis rotation)
    sinp = 2 * (quat_real * quat_img[1] - quat_img[2] * quat_img[0])
    if abs(sinp) >= 1:
        pitch = math.copysign(math.pi / 2, sinp)  # use 90 degrees if out of range
    else:
        pitch = math.asin(sinp)

    # yaw (z-axis rotation)
    siny_cosp = 2 * (quat_real * quat_img[2] + quat_img[0] * quat_img[1])
    cosy_cosp = 1 - 2 * (quat_img[1] * quat_img[1] + quat_img[2] * quat_img[2])
    yaw = math.atan2(siny_cosp, cosy_cosp)

    return roll, pitch, yaw


def euler_angles_to_quat(euler_angles: np.ndarray) -> np.ndarray:
    roll, pitch, yaw = euler_angles
    c1 = np.cos(yaw / 2.0)
    s1 = np.sin(yaw / 2.0)
    c2 = np.cos(pitch / 2.0)
    s2 = np.sin(pitch / 2.0)
    c3 = np.cos(roll / 2.0)
    s3 = np.sin(roll / 2.0)
    c1c2 = c1 * c2
    s1s2 = s1 * s2
    w = c1c2 * c3 - s1s2 * s3
    x = c1c2 * s3 + s1s2 * c3
    y = s1 * c2 * c3 + c1 * s2 * s3
    z = c1 * s2 * c3 - s1 * c2 * s3
    return np.array([w, x, y, z])
