# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
from pxr import Gf
import numpy as np


def tf_matrix_from_pos_rot(pos: np.ndarray, rot: np.ndarray):
    """[summary]

    Args:
        pos (np.ndarray): [description]
        rot (np.ndarray): [description]

    Returns:
        [type]: [description]
    """
    mat = Gf.Transform()
    mat.SetRotation(Gf.Rotation(Gf.Quatd(rot.tolist())))
    mat.SetTranslation(Gf.Vec3d(pos.tolist()))
    return mat.GetMatrix()
