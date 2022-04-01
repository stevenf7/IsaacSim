# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
from pxr import Gf
from typing import Union
import torch
import numpy as np
from scipy.spatial.transform import Rotation
from omni.isaac.core.simulation_context.simulation_context import SimulationContext


def tf_matrix_from_pose(translation: np.ndarray, orientation: np.ndarray) -> np.ndarray:
    """[summary]

    Args:
        pos (np.ndarray): [description]
        rot (np.ndarray): [description]

    Returns:
        [type]: [description]
    """
    mat = Gf.Transform()
    mat.SetRotation(Gf.Rotation(Gf.Quatd(*orientation.tolist())))
    mat.SetTranslation(Gf.Vec3d(*translation.tolist()))
    return np.transpose(mat.GetMatrix())


def tf_matrices_from_poses(
    translations: Union[np.ndarray, torch.Tensor], orientations: Union[np.ndarray, torch.Tensor]
) -> Union[np.ndarray, torch.Tensor]:
    """[summary]

    Args:
        translations (Union[np.ndarray, torch.Tensor]): translations with shape (N, 3).
        orientations (Union[np.ndarray, torch.Tensor]): quaternion representation (scalar first) with shape (N, 4).

    Returns:
        Union[np.ndarray, torch.Tensor]: transformation matrices with shape (N, 4, 4)
    """
    # TODO: add a torch pathway
    backend = "numpy"
    if SimulationContext.instance() is not None:
        backend = SimulationContext.instance().backend
    if backend == "numpy":
        result = np.zeros([orientations.shape[0], 4, 4], dtype=np.float32)
        r = Rotation.from_quat(orientations[:, [1, 2, 3, 0]])
        result[:, :3, :3] = r.as_matrix()
        result[:, :3, 3] = translations
        result[:, 3, 3] = 1
    elif backend == "torch":
        device = None
        if SimulationContext.instance() is not None:
            device = SimulationContext.instance().device
        result = torch.zeros([orientations.shape[0], 4, 4], dtype=torch.float32, device=device)
        r = Rotation.from_quat(orientations[:, [1, 2, 3, 0]].detach().cpu().numpy())
        result[:, :3, :3] = torch.from_numpy(r.as_matrix()).float().to(device)
        result[:, :3, 3] = translations
        result[:, 3, 3] = 1
    return result
