# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

import carb
import omni
from pxr import UsdGeom, Usd, Gf
from omni.isaac.core.utils.stage import get_current_stage, get_stage_units
import numpy as np
import omni.kit.app
import omni.kit.viewport
import typing


def set_camera_view(
    eye: typing.Optional[np.ndarray] = None,
    target: typing.Optional[np.ndarray] = None,
    vel: float = 0.05,
    camera_prim_path: str = "/OmniverseKit_Persp",
) -> None:
    """Set the location and target for a camera prim in the stage given its path

    Args:
        eye (typing.Optional[np.ndarray], optional): Location of camera. Defaults to None.
        target (typing.Optional[np.ndarray], optional): Location of camera target. Defaults to None.
        vel (float, optional): Velocity of the camera when controlling with keyboard. Defaults to 0.05.
        camera_prim_path (str, optional): Path to camera prim being set. Defaults to "/OmniverseKit_Persp".
    """
    meters_per_unit = get_stage_units()
    if eye is None:
        eye = np.array([1.5, 1.5, 1.5]) / meters_per_unit
    if target is None:
        target = np.array([0.01, 0.01, 0.01]) / meters_per_unit
    vel = vel / meters_per_unit
    viewport = omni.kit.viewport.get_default_viewport_window()
    viewport.set_camera_position(camera_prim_path, eye[0], eye[1], eye[2], True)
    viewport.set_camera_target(camera_prim_path, target[0], target[1], target[2], True)
    viewport.set_camera_move_velocity(vel)
    return


def get_intrinsics_matrix(viewport: omni.kit.viewport.IViewportWindow) -> np.ndarray:
    """Get intrinsics Matrix for the camera attached to a specific viewport

    Args:
        viewport (omni.kit.viewport.IViewportWindow): Handle to viewport window

    Returns:
        np.ndarray: the intrinsics matrix associated with the specified viewport
                    The following image convention is assumed:
                    +x should point to the right in the image
                    +y should point down in the image
    """
    stage = get_current_stage()
    prim = stage.GetPrimAtPath(viewport.get_active_camera())
    focal_length = prim.GetAttribute("focalLength").Get()
    horizontal_aperture = prim.GetAttribute("horizontalAperture").Get()
    vertical_aperture = prim.GetAttribute("verticalAperture").Get()
    width, height = viewport.get_texture_resolution()
    fx = width * focal_length / horizontal_aperture
    fy = height * focal_length / vertical_aperture
    cx = width * 0.5
    cy = height * 0.5
    return np.array([[fx, 0.0, cx], [0.0, fy, cy], [0.0, 0.0, 1.0]])


def set_intrinsics_matrix(
    viewport: omni.kit.viewport.IViewportWindow, intrinsics_matrix: np.ndarray, focal_length: float = 1.0
) -> None:
    """Set intrinsics Matrix for the camera attached to a specific viewport

    Note:
        We assume cx and cy are centered in the camera
        horizontal_aperture_offset and vertical_aperture_offset are computed and set on the camera prim but are not used

    Args:
        viewport (omni.kit.viewport.IViewportWindow): Handle to viewport window
        intrinsics_matrix (np.ndarray): 3x3 intrinsics matrix
        focal_length (float, optional): default focal length to use when computing aperture values. Defaults to 1.0.

    Raises:
        ValueError: If intrinsics matrix is not 3x3
        ValueError:  camera prim is not valid
    """

    if intrinsics_matrix.shape != (3, 3):
        raise ValueError("intrinsics_matrix must be 3x3")

    fx = intrinsics_matrix[0, 0]
    fy = intrinsics_matrix[1, 1]
    cx = intrinsics_matrix[0, 2]
    cy = intrinsics_matrix[1, 2]

    stage = get_current_stage()
    prim = UsdGeom.Camera(stage.GetPrimAtPath(viewport.get_active_camera()))
    print(prim)
    if prim is None:
        raise ValueError("Viewport does not have a valid camera prim")

    width, height = viewport.get_texture_resolution()

    horizontal_aperture = width * focal_length / fx
    vertical_aperture = height * focal_length / fy
    # TODO: this should be set_attr_val
    # We have to do it this way because the camera might be on a differen layer (default cameras are on session layer),
    # and this is the simplest way to set the property on the right layer.
    omni.usd.utils.set_prop_val(prim.GetFocalLengthAttr(), focal_length)
    omni.usd.utils.set_prop_val(prim.GetHorizontalApertureAttr(), horizontal_aperture)
    omni.usd.utils.set_prop_val(prim.GetVerticalApertureAttr(), vertical_aperture)
    omni.usd.utils.set_prop_val(prim.GetHorizontalApertureOffsetAttr(), (cx - width / 2) / fx)
    omni.usd.utils.set_prop_val(prim.GetVerticalApertureOffsetAttr(), (cy - height / 2) / fy)


def backproject_depth(
    depth_image: np.array, viewport: omni.kit.viewport.IViewportWindow, max_clip_depth: float
) -> np.array:
    """Backproject depth image to image space

    Args:
        depth_image (np.array): [description]
        viewport (omni.kit.viewport.IViewportWindow): [description]
        max_clip_depth (float): [description]

    Returns:
        np.array: [description]
    """

    intrinsics_matrix = get_intrinsics_matrix(viewport)
    fx = intrinsics_matrix[0][0]
    fy = intrinsics_matrix[1][1]
    cx = intrinsics_matrix[0][2]
    cy = intrinsics_matrix[1][2]
    height = depth_image.shape[0]
    width = depth_image.shape[1]
    input_x = np.arange(width)
    input_y = np.arange(height)
    input_x, input_y = np.meshgrid(input_x, input_y)
    input_x = input_x.flatten()
    input_y = input_y.flatten()
    input_z = depth_image.flatten()
    input_z[input_z > max_clip_depth] = 0
    output_x = (input_x * input_z - cx * input_z) / fx
    output_y = (input_y * input_z - cy * input_z) / fy
    raw_pc = np.stack([output_x, output_y, input_z], -1).reshape([height * width, 3])
    return raw_pc


def project_depth_to_worldspace(
    depth_image: np.array, viewport: omni.kit.viewport.IViewportWindow, max_clip_depth: float
) -> typing.List[carb.Float3]:
    """Project depth image to world space

    Args:
        depth_image (np.array): [description]
        viewport (omni.kit.viewport.IViewportWindow): [description]
        max_clip_depth (float): [description]

    Returns:
        typing.List[carb.Float3]: [description]
    """
    stage = get_current_stage()
    prim = stage.GetPrimAtPath(viewport.get_active_camera())
    prim_tf = UsdGeom.Xformable(prim).ComputeLocalToWorldTransform(Usd.TimeCode())
    units_per_meter = 1.0 / UsdGeom.GetStageMetersPerUnit(stage)

    depth_data = depth_image * units_per_meter
    depth_data = -np.clip(depth_data, 0, max_clip_depth)

    pc = backproject_depth(depth_data, viewport, max_clip_depth)
    points = []
    for pts in pc:
        p = prim_tf.Transform(Gf.Vec3d(-pts[0], pts[1], pts[2]))
        points.append(carb.Float3(p[0], p[1], p[2]))

    return points
