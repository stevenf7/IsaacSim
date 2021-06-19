# Copyright (c) 2020-2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

import numpy as np
from numpy.linalg import norm
import copy
import traceback
import carb
import math

from pxr import Gf


def normalize(v):
    if norm(v) == 0:
        traceback.print_stack()
    v /= norm(v)
    return v


def normalized(v):
    if v is None:
        return None
    return normalize(copy.deepcopy(v))


def proj_orth(v1, v2, normalize_res=False, eps=1e-5):
    v2_norm = norm(v2)
    if v2_norm < eps:
        return v1

    v2n = v2 / v2_norm
    v1 = v1 - np.dot(v1, v2n) * v2n
    if normalize_res:
        return normalized(v1)
    else:
        return v1


def axes2mat(axis_x, axis_z, dominant_axis="z"):
    if dominant_axis == "z":
        axis_x = proj_orth(axis_x, axis_z)
    elif dominant_axis == "x":
        axis_z = proj_orth(axis_z, axis_x)
    elif dominant_axis is None:
        pass
    else:
        raise RuntimeError("Unrecognized dominant_axis: %s" % dominant_axis)

    axis_x = axis_x / norm(axis_x)
    axis_z = axis_z / norm(axis_z)
    axis_y = np.cross(axis_z, axis_x)

    R = np.zeros((3, 3))
    R[0:3, 0] = axis_x
    R[0:3, 1] = axis_y
    R[0:3, 2] = axis_z

    return R


# Projects T to align with the provided direction vector v.
def proj_to_align(R, v):
    max_entry = max(enumerate([np.abs(np.dot(R[0:3, i], v)) for i in range(3)]), key=lambda entry: entry[1])
    return axes2mat(R[0:3, (max_entry[0] + 1) % 3], v)


def as_np_matrix_t(input):
    result = np.identity(4)
    result[:3, 3] = Gf.Vec3f(input.p.x, input.p.y, input.p.z)
    result[:3, :3] = Gf.Matrix3f(Gf.Quatf(input.r.w, Gf.Vec3f(input.r.x, input.r.y, input.r.z))).GetTranspose()
    return result


def lookAt(camera, target, up):

    F = (target - camera).GetNormalized()
    R = Gf.Cross(up, F).GetNormalized()
    U = Gf.Cross(F, R)

    q = Gf.Quatf()
    trace = R[0] + U[1] + F[2]
    if trace > 0.0:
        s = 0.5 / math.sqrt(trace + 1.0)
        q = Gf.Quatf(0.25 / s, Gf.Vec3f((U[2] - F[1]) * s, (F[0] - R[2]) * s, (R[1] - U[0]) * s))
    else:
        if R[0] > U[1] and R[0] > F[2]:
            s = 2.0 * math.sqrt(1.0 + R[0] - U[1] - F[2])
            q = Gf.Quatf((U[2] - F[1]) / s, Gf.Vec3f(0.25 * s, (U[0] + R[1]) / s, (F[0] + R[2]) / s))
        elif U[1] > F[2]:
            s = 2.0 * math.sqrt(1.0 + U[1] - R[0] - F[2])
            q = Gf.Quatf((F[0] - R[2]) / s, Gf.Vec3f((U[0] + R[1]) / s, 0.25 * s, (F[1] + U[2]) / s))
        else:
            s = 2.0 * math.sqrt(1.0 + F[2] - R[0] - U[1])
            q = Gf.Quatf((R[1] - U[0]) / s, Gf.Vec3f((F[0] + R[2]) / s, (F[1] + U[2]) / s, 0.25 * s))
    return q


def quaternionToEulerAngles(q):
    q_img = q.GetImaginary()
    q_real = q.GetReal()
    # roll (x-axis rotation)
    sinr_cosp = 2 * (q_real * q_img[0] + q_img[1] * q_img[2])
    cosr_cosp = 1 - 2 * (q_img[0] * q_img[0] + q_img[1] * q_img[1])
    roll = math.atan2(sinr_cosp, cosr_cosp)

    # pitch (y-axis rotation)
    sinp = 2 * (q_real * q_img[1] - q_img[2] * q_img[0])
    if abs(sinp) >= 1:
        pitch = math.copysign(M_PI / 2, sinp)  # use 90 degrees if out of range
    else:
        pitch = math.asin(sinp)

    # yaw (z-axis rotation)
    siny_cosp = 2 * (q_real * q_img[2] + q_img[0] * q_img[1])
    cosy_cosp = 1 - 2 * (q_img[1] * q_img[1] + q_img[2] * q_img[2])
    yaw = math.atan2(siny_cosp, cosy_cosp)

    return roll, pitch, yaw
