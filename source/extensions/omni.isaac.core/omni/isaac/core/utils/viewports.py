import carb
import omni
from pxr import UsdGeom, Usd, Gf
from omni.isaac.core.utils.stage import get_current_stage
import numpy as np
import omni.kit.app
import omni.kit.viewport
import typing


def set_camera_view(eye: np.array = None, target: np.array = None, vel: float = 0.05) -> None:
    """[summary]

    Args:
        eye (list, optional): [description]. Defaults to [1.5, 1.5, 1.5].
        target (list, optional): [description]. Defaults to [0.01, 0.01, 0.01].
        vel (float, optional): [description]. Defaults to 0.05.
    """
    # TODO: to be removed after propagation of stage units
    meters_per_unit = UsdGeom.GetStageMetersPerUnit(get_current_stage())
    if eye is None:
        eye = np.array([1.5, 1.5, 1.5]) / meters_per_unit
    if target is None:
        target = np.array([0.01, 0.01, 0.01]) / meters_per_unit
    vel = vel / meters_per_unit
    viewport = omni.kit.viewport.get_default_viewport_window()
    viewport.set_camera_position("/OmniverseKit_Persp", eye[0], eye[1], eye[2], True)
    viewport.set_camera_target("/OmniverseKit_Persp", target[0], target[1], target[2], True)
    viewport.set_camera_move_velocity(vel)
    return


def get_intrinsics_matrix(viewport: omni.kit.viewport.IViewportWindow):
    """
    Returns the intrisics matrix associated with the specified viewport

    The following image convention is assumed:

    +x should point to the right in the image
    +y should point down in the image
    """

    stage = omni.usd.get_context().get_stage()
    prim = stage.GetPrimAtPath(viewport.get_active_camera())
    focal_length = prim.GetAttribute("focalLength").Get()
    horiz_aperture = prim.GetAttribute("horizontalAperture").Get()
    width, height = viewport.get_texture_resolution()
    vert_aperture = height / width * horiz_aperture
    fx = width * focal_length / horiz_aperture
    fy = height * focal_length / vert_aperture
    cx = width * 0.5
    cy = height * 0.5
    return np.array([[fx, 0.0, cx], [0.0, fy, cy], [0.0, 0.0, 1.0]])


def backproject_depth(
    depth_image: np.array, viewport: omni.kit.viewport.IViewportWindow, max_clip_depth: float
) -> np.array:
    """
    Backproject depth image to image space
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
    """
    Project depth image to world space
    """

    stage = omni.usd.get_context().get_stage()
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
