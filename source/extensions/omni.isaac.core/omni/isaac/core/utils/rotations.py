# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

import math

import numpy as np
from pxr import Gf
from scipy.spatial.transform import Rotation as R


def quat_to_rot_matrix(quat: np.ndarray) -> np.ndarray:
    # might need to be normalized
    rotm = Gf.Matrix3f(Gf.Quatf(*quat.tolist())).GetTranspose()
    return np.array(rotm)


def quat_to_euler_angles(quat: np.ndarray, degrees: bool = False) -> np.ndarray:
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

    if degrees:
        roll = math.degrees(roll)
        pitch = math.degrees(pitch)
        yaw = math.degrees(yaw)

    return roll, pitch, yaw


def euler_angles_to_quat(euler_angles: np.ndarray, degrees: bool = False) -> np.ndarray:
    roll, pitch, yaw = euler_angles
    if degrees:
        roll = math.radians(roll)
        pitch = math.radians(pitch)
        yaw = math.radians(yaw)
    cr = np.cos(roll / 2.0)
    sr = np.sin(roll / 2.0)
    cy = np.cos(yaw / 2.0)
    sy = np.sin(yaw / 2.0)
    cp = np.cos(pitch / 2.0)
    sp = np.sin(pitch / 2.0)
    w = (cr * cp * cy) + (sr * sp * sy)
    x = (sr * cp * cy) - (cr * sp * sy)
    y = (cr * sp * cy) + (sr * cp * sy)
    z = (cr * cp * sy) - (sr * sp * cy)
    return np.array([w, x, y, z])


def gf_quatd_to_np_array(orientation: Gf.Quatd) -> np.ndarray:
    quat = np.zeros(4)
    quat[1:] = orientation.GetImaginary()
    quat[0] = orientation.GetReal()
    return quat


def gf_quatf_to_np_array(orientation: Gf.Quatf) -> np.ndarray:
    quat = np.zeros(4)
    quat[1:] = orientation.GetImaginary()
    quat[0] = orientation.GetReal()
    return quat


def gf_rotation_to_np_array(orientation: Gf.Quatf) -> np.ndarray:
    return gf_quatd_to_np_array(orientation.GetQuat())
