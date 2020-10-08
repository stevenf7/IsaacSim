#!/usr/bin/env python
# Copyright (c) 2020, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.


import math
import numpy as np


def get_view_proj_mat(camera_tf_matrix, fov, aspect_ratio, z_near, z_far):
    view_matrix = np.linalg.inv(camera_tf_matrix)
    projection_mat = get_projection_matrix(fov, aspect_ratio, z_near, z_far)
    return np.dot(view_matrix, projection_mat)


def get_projection_matrix(fov, aspect_ratio, z_near, z_far):
    """Calculate the camera projection matrix.
    """
    a = -1.0 / math.tan(fov / 2)
    b = -a * aspect_ratio
    c = z_far / (z_far - z_near)
    d = z_near * z_far / (z_far - z_near)
    return np.array([[a, 0.0, 0.0, 0.0], [0.0, b, 0.0, 0.0], [0.0, 0.0, c, 1.0], [0.0, 0.0, d, 0.0]])


def project_points(view_projection_matrix, points):
    """Project points onto a 2D plane.
    """
    points_homo = np.pad(points, ((0, 0), (0, 1)), mode="constant", constant_values=1.0)
    tf_points = np.dot(points_homo, view_projection_matrix)
    tf_points = tf_points / (tf_points[..., -1:])
    tf_points[..., :2] = 0.5 * (tf_points[..., :2] + 1)
    return tf_points
