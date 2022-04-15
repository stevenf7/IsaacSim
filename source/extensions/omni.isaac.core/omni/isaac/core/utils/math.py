# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

import numpy as np


def radians_to_degrees(rad_angles: np.ndarray) -> np.ndarray:
    """[summary]

    Args:
        rad_angles (np.ndarray): [description]

    Returns:
        np.ndarray: [description]
    """
    return rad_angles * (180.0 / np.pi)


def cross(a, b):
    """[summary]    
    Args:
        a (np.ndarray, list): [description]
        b (np.ndarray, list): [description]

    Returns:
        np.ndarray: [description]
    """
    return [a[1] * b[2] - a[2] * b[1], a[0] * b[2] - a[2] * b[0], a[0] * b[1] - a[1] * b[0]]
