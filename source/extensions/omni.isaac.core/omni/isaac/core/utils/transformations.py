# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

# python
import torch
import numpy as np
from scipy.spatial.transform import Rotation
from typing import Union, Tuple, Sequence

# omniverse
from pxr import Gf

# isaacsim
from omni.isaac.core.utils.rotations import gf_quat_to_np_array
from omni.isaac.core.simulation_context.simulation_context import SimulationContext


def tf_matrix_from_pose(translation: Sequence[float], orientation: Sequence[float]) -> np.ndarray:
    """Compute input pose to transformation matrix.

    Args:
        pos (Sequence[float]): The translation vector.
        rot (Sequence[float]): The orientation quaternion.

    Returns:
        np.ndarray: A 4x4 matrix.
    """
    translation = np.asarray(translation)
    orientation = np.asarray(orientation)
    mat = Gf.Transform()
    mat.SetRotation(Gf.Rotation(Gf.Quatd(*orientation.tolist())))
    mat.SetTranslation(Gf.Vec3d(*translation.tolist()))
    return np.transpose(mat.GetMatrix())


def pose_from_tf_matrix(transformation: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """Gets pose corresponding to input transformation matrix.

    Args:
        transformation (np.ndarray): Column-major transformation matrix. shape is (4, 4).

    Returns:
        Tuple[np.ndarray, np.ndarray]: first index is translation corresponding to transformation. shape is (3, ).
                                       second index is quaternion orientation corresponding to transformation.
                                       quaternion is scalar-first (w, x, y, z). shape is (4, ).
    """
    mat = Gf.Transform()
    mat.SetMatrix(Gf.Matrix4d(np.transpose(transformation)))
    calculated_translation = np.array(mat.GetTranslation())
    calculated_orientation = gf_quat_to_np_array(mat.GetRotation().GetQuat())
    return calculated_translation, calculated_orientation


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
