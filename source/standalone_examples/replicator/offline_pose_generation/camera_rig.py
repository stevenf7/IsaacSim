# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
from typing import Optional
import numpy as np
from omni.isaac.core import World
from omni.isaac.core.prims.xform_prim import XFormPrim
from pxr import UsdGeom
import math
import carb
import omni
from omni.isaac.core.utils.rotations import euler_angles_to_quat
from standalone_examples.replicator.offline_pose_generation.utils import (
    get_random_values_in_range,
    get_world_pose_from_relative,
    get_translation_from_target,
)
import random


class CameraRig(XFormPrim):
    """Creates and manages both a xform representing a camera rig, and a camera prim. Additionally, this class provides
       an API to find a random pose that is in view of the camera. 

    Args:
        prim_path (str): prim path of the Prim to encapsulate or create, representing a camera rig.
        name (str): shortname to be used as a key by Scene class for the camera rig. Note: needs to be unique if the 
                    object is added to the Scene.
        camera_prim_path_suffix (str): suffix (basename) of the prim path at which a camera prim will be created. 
        width (int): width of the camera prim's viewport in pixels.
        height (int): height of the camera prim's viewport in pixels.
        f_x (float): focal length of the camera in the x-direction in pixels.
        f_y (float): focal length of the camera in the y-direction in pixels.
        c_x (float): principal point x-coordinate.
        c_y (float): principal point y-coordinate.
        camera_rotation (np.ndarray, optional): rotation of the camera with respect to the camera rig. rotation is given
                                                in degrees as XYZ Euler angles. Shape is (3, ). Defaults to 
                                                np.array([180, 0, 0]), which corresponds to a camera with +z out, 
                                                +x right, and +y down.
        position (Optional[np.ndarray], optional): position of the camera rig in the world frame. Shape is (3, ).
                                                   Defaults to None, which means left unchanged.
        translation (Optional[np.ndarray], optional): translation of the camera rig in the local frame. The local 
                                                      coordinate frame is considered to be the frame of the camera rig's 
                                                      parent prim. Shape is (3, ). Defaults to None, which means left 
                                                      unchanged.
        orientation (Optional[np.ndarray], optional): quaternion orientation of the camera rig in the world/local frame 
                                                      (depends if translation or position is specified). Quaternion is 
                                                      scalar-first (w, x, y, z). Shape is (4, ). Defaults to None, which 
                                                      means left unchanged.
    """

    def __init__(
        self,
        prim_path: str,
        name: str,
        camera_prim_path_suffix: str,
        width: int,
        height: int,
        f_x: float,
        f_y: float,
        c_x: float,
        c_y: float,
        camera_rotation: np.ndarray = np.array([180, 0, 0]),
        position: Optional[np.ndarray] = None,
        translation: Optional[np.ndarray] = None,
        orientation: Optional[np.ndarray] = None,
    ) -> None:

        self.world = World.instance()

        XFormPrim.__init__(
            self, prim_path=prim_path, name=name, position=position, translation=translation, orientation=orientation
        )

        self.camera_path = f"{prim_path}/{camera_prim_path_suffix}"
        self._setup_camera(self.camera_path, width, height, f_x, f_y, c_x, c_y, camera_rotation)
        self._setup_viewport(self.camera_path, width, height)

    def _setup_camera(self, camera_prim_path, width, height, f_x, f_y, c_x, c_y, camera_rotation):
        """Create camera and set intrinsics.

        Args:
            camera_prim_path (str): prim path at which a camera prim will be created. 
            width (int): width of the camera prim's viewport in pixels.
            height (int): height of the camera prim's viewport in pixels.
            f_x (float): focal length of the camera in the x-direction in pixels.
            f_y (float): focal length of the camera in the y-direction in pixels.
            c_x (float): principal point x-coordinate.
            c_y (float): principal point y-coordinate.
            camera_rotation (np.ndarray): rotation of the camera with respect to the camera rig. rotation is given in 
                                          degrees as XYZ Euler angles. Shape is (3, ).
        """

        self.camera_prim = self.world.stage.DefinePrim(camera_prim_path, "Camera")
        camera_xform_prim = XFormPrim(self.camera_path, name="camera_xform_prim")
        camera_xform_prim.set_local_pose(orientation=euler_angles_to_quat(camera_rotation, degrees=True))

        self.width = width
        self.height = height

        self.f_x = f_x
        self.f_y = f_y
        self.c_x = c_x
        self.c_y = c_y

        self.fov_x = 2 * math.atan(self.width / (2 * f_x))
        self.fov_y = 2 * math.atan(self.height / (2 * f_y))

        self._camera = UsdGeom.Camera(self.camera_prim)
        self.horizontal_aperture = self._camera.GetHorizontalApertureAttr().Get()
        self.focal_length = self.horizontal_aperture * f_x / self.width
        self.vertical_aperture = self.focal_length * self.height / f_y
        self._camera.GetFocalLengthAttr().Set(self.focal_length)
        self._camera.GetVerticalApertureAttr().Set(self.vertical_aperture)
        self._camera.GetClippingRangeAttr().Set((0.01, 10000))

    def _setup_viewport(self, camera_prim_path, width, height):
        """Set viewport resolution and active camera.

        Args:
            camera_prim_path (str): prim path of the camera prim to set as the viewport's active camera.
            width (int): width of the camera prim's viewport in pixels.
            height (int): height of the camera prim's viewport in pixels.
        """

        carb.settings.acquire_settings_interface().set_int("/app/renderer/resolution/width", -1)
        carb.settings.acquire_settings_interface().set_int("/app/renderer/resolution/height", -1)

        # Get existing viewport
        self.viewport = omni.kit.viewport_legacy.get_viewport_interface()
        viewport_handle = self.viewport.get_instance("Viewport")
        self.viewport_window = self.viewport.get_viewport_window(viewport_handle)

        self.viewport_window.set_texture_resolution(width, height)
        self.viewport_window.set_active_camera(camera_prim_path)

    def get_camera_intrinsic_matrix(self):
        """Get camera intrinsic matrix.

        Returns:
            np.ndarray: intrinsic matrix of the camera. Shape is (3, 3).
        """

        intrinsic_matrix = np.array([[self.f_x, 0, self.c_x], [0, self.f_y, self.c_y], [0, 0, 1]])

        return intrinsic_matrix

    def get_random_translation_from_camera(self, min_distance, max_distance, fraction_to_screen_edge):
        """Get a random translation from the camera, in the camera's frame, that's in view of the camera.

        Args:
            min_distance (float): minimum distance away from the camera (along the optical axis) of the random 
                                  translation.
            max_distance (float): maximum distance away from the camera (along the optical axis) of the random 
                                  translation.
            fraction_to_screen_edge (float): maximum allowed fraction to the edge of the screen the translated point may 
                                             appear when viewed from the camera. A value of 0 corresponds to the 
                                             translated point being centered in the camera's view (on the optical axis), 
                                             whereas a value of 1 corresponds to the translated point being on the edge 
                                             of the screen in the camera's view.

        Returns:
            np.ndarray: random translation from the camera, in the camera's frame, that's in view of the camera. Shape 
                        is (3, ).
        """

        # Randomly select distance away from camera (along the optical axis)
        random_z_distance = random.uniform(min_distance, max_distance)

        # Use distance away to determine allowable range of horizontal/vertical motion that is in view of camera
        theta_x = self.fov_x / 2.0
        theta_y = self.fov_y / 2.0

        max_x = random_z_distance * math.tan(fraction_to_screen_edge * theta_x)
        max_y = random_z_distance * math.tan(fraction_to_screen_edge * theta_y)

        # Translation relative to camera in the z direction is negative due to cameras in Isaac Sim having coordinates
        # of -z out, +y up, and +x right.
        random_x = random.uniform(-max_x, max_x)
        random_y = random.uniform(-max_y, max_y)
        random_z = -random_z_distance

        return np.array([random_x, random_y, random_z])

    def get_random_world_pose_in_view(
        self, min_distance, max_distance, fraction_to_screen_edge, prim_path, min_rotation_range, max_rotation_range
    ):
        """Get a pose defined in the world frame that's in view of the camera. 

        Args:
            min_distance (float): minimum distance away from the camera (along the optical axis) of the random 
                                  translation.
            max_distance (float): maximum distance away from the camera (along the optical axis) of the random 
                                  translation.
            fraction_to_screen_edge (float): maximum allowed fraction to the edge of the screen the translated point may 
                                             appear when viewed from the camera. A value of 0 corresponds to the 
                                             translated point being centered in the camera's view (on the optical axis), 
                                             whereas a value of 1 corresponds to the translated point being on the edge 
                                             of the screen in the camera's view.
            prim_path (str): path of the prim whose frame the orientation is defined with respect to.
            min_rotation_range (np.ndarray): minimum XYZ Euler angles of the random pose, defined with respect to the 
                                             frame of the prim at prim_path. Shape is (3, ).
            max_rotation_range (np.ndarray): maximum XYZ Euler angles of the random pose, defined with respect to the 
                                             frame of the prim at prim_path.

        Returns:
            Tuple[np.ndarray, np.ndarray]: first index is position in the world frame. Shape is (3, ). Second index is 
                                           quaternion orientation in the world frame. Quaternion is scalar-first 
                                           (w, x, y, z). Shape is (4, ).
        """

        random_translation_from_camera = self.get_random_translation_from_camera(
            min_distance, max_distance, fraction_to_screen_edge
        )
        random_translation_from_prim = get_translation_from_target(
            random_translation_from_camera, self.camera_path, prim_path
        )

        # Rotation ranges are expressed as Euler XYZ angles with respect to the frame of the prim at prim_path
        random_rotation_from_prim = get_random_values_in_range(min_rotation_range, max_rotation_range)
        random_orientation_from_prim = euler_angles_to_quat(random_rotation_from_prim, degrees=True)

        translation, orientation = get_world_pose_from_relative(
            prim_path, random_translation_from_prim, random_orientation_from_prim
        )

        return translation, orientation
