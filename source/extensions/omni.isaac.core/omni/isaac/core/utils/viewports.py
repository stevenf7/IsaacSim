from pxr import UsdGeom
from omni.isaac.core.utils.stage import get_current_stage
import numpy as np
import omni.kit.app


def set_camera_view(eye=None, target=None, vel=0.05):
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
