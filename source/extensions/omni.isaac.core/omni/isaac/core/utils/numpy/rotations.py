import typing
import numpy as np
from pxr import Gf
from scipy.spatial.transform import Rotation


def gf_quat_to_tensor(orientation: typing.Union[Gf.Quatd, Gf.Quatf, Gf.Quaternion], device=None) -> np.ndarray:
    """Converts a pxr Quaternion type to a numpy array following [w, x, y, z] convention.

    Args:
        orientation (typing.Union[Gf.Quatd, Gf.Quatf, Gf.Quaternion]): [description]

    Returns:
        np.ndarray: [description]
    """
    quat = np.zeros(4)
    quat[1:] = orientation.GetImaginary()
    quat[0] = orientation.GetReal()
    return quat


def euler_angles_to_quats(euler_angles: np.ndarray, degrees: bool = False, device=None) -> np.ndarray:
    """Vectorized version of converting euler angles to quaternion (scalar first)

    Args:
        euler_angles (typing.Union[np.ndarray, torch.Tensor]): euler angles with shape (N, 3) representation XYZ
        degrees (bool, optional): True if degrees, False if radians. Defaults to False.

    Returns:
        typing.Union[np.ndarray, torch.Tensor]: quaternions representation of the angles (N, 4) - scalar first.
    """
    rot = Rotation.from_euler("xyz", euler_angles, degrees=degrees)
    result = rot.as_quat()[:, [3, 0, 1, 2]]
    return result
