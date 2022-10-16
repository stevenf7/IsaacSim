# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

# python
import numpy as np
import random
import math
from typing import Tuple

# omniverse
from pxr import Usd, UsdGeom

# isaacsim
from omni.isaac.core.utils.stage import get_stage_units
from omni.isaac.core.utils.transformations import tf_matrix_from_pose, pose_from_tf_matrix
from omni.isaac.core.utils.rotations import euler_angles_to_quat


def get_relative_transform(source_prim: Usd.Prim, target_prim: Usd.Prim) -> np.ndarray:
    """Get the relative transformation matrix from the source prim to the target prim.

    Args:
        source_prim (Usd.Prim): source prim from which frame to compute the relative transform.
        target_prim (Usd.Prim): target prim to which frame to compute the relative transform.
    
    Returns:
        np.ndarray: Column-major transformation matrix with shape (4, 4).
    """

    # Row-major transformation matrix
    source_to_world_row_major_tf = UsdGeom.Xformable(source_prim).ComputeLocalToWorldTransform(Usd.TimeCode.Default())
    target_to_world_row_major_tf = UsdGeom.Xformable(target_prim).ComputeLocalToWorldTransform(Usd.TimeCode.Default())

    # Convert to column-major transformation matrix
    source_to_world_column_major_tf = np.transpose(source_to_world_row_major_tf)
    target_to_world_column_major_tf = np.transpose(target_to_world_row_major_tf)

    world_to_target_column_major_tf = np.linalg.inv(target_to_world_column_major_tf)
    source_to_target_column_major_tf = source_to_world_column_major_tf @ world_to_target_column_major_tf

    return source_to_target_column_major_tf


def get_mesh_vertices_relative_to(mesh_prim: UsdGeom.Mesh, coord_prim: Usd.Prim) -> np.ndarray:
    """Get vertices of the mesh prim in the coordinate system of the given prim.

    Args:
        mesh_prim (UsdGeom.Mesh): mesh prim to get the vertice points.
        coord_prim (Usd.Prim): prim used as relative coordinate.

    Returns:
        np.ndarray: vertices of the mesh in the coordinate system of the given prim. Shape is (N, 3).
    """

    # Vertices of the mesh in the mesh's coordinate system
    vertices_vec3f = UsdGeom.Mesh(mesh_prim).GetPointsAttr().Get()
    vertices = np.array(vertices_vec3f)
    vertices_tf_row_major = np.pad(vertices, ((0, 0), (0, 1)), constant_values=1.0)

    # Transformation matrix from the coordinate system of the mesh to the coordinate system of the prim
    relative_tf_column_major = get_relative_transform(mesh_prim, coord_prim)
    relative_tf_row_major = np.transpose(relative_tf_column_major)

    # Transform points so they are in the coordinate system of the top-level ancestral xform prim
    points_in_relative_coord = vertices_tf_row_major @ relative_tf_row_major

    points_in_meters = points_in_relative_coord[:, :-1] * get_stage_units()

    return points_in_meters


def get_translation_from_target(
    translation_from_source: np.ndarray, source_prim: Usd.Prim, target_prim: Usd.Prim
) -> np.ndarray:
    """Get a translation with respect to the target's frame, from a translation in the source's frame.

    Args:
        translation_from_source (np.ndarray): translation from the frame of the prim at source_path. Shape is (3, ).
        source_prim (Usd.Prim): prim path of the prim whose frame the original/untransformed translation
                           (translation_from_source) is defined with respect to.
        target_prim (Usd.Prim): prim path of the prim whose frame corresponds to the target frame that the returned
                           translation will be defined with respect to.

    Returns:
        np.ndarray: translation with respect to the target's frame. Shape is (3, ).
    """

    translation_from_source_homogenous = np.pad(translation_from_source, ((0, 1)), constant_values=1.0)

    source_to_target = get_relative_transform(source_prim, target_prim)

    translation_from_target_homogenous = translation_from_source_homogenous @ np.transpose(source_to_target)
    translation_from_target = translation_from_target_homogenous[:-1]

    return translation_from_target


def get_random_values_in_range(min_range: np.ndarray, max_range: np.ndarray) -> np.ndarray:
    """Get an array of random values where each element is between the corresponding min_range and max_range element.

    Args:
        min_range (np.ndarray): minimum values for each corresponding element of the array of random values. Shape is
                                (num_values, ).
        max_range (np.ndarray): maximum values for each corresponding element of the array of random values. Shape is
                                (num_values, ).

    Returns:
        np.ndarray: array of random values. Shape is (num_values, ).
    """

    return np.array([random.uniform(min_val, max_val) for min_val, max_val in zip(min_range, max_range)])


def get_world_pose_from_relative(
    coord_prim: Usd.Prim, relative_translation: np.ndarray, relative_orientation: np.ndarray
) -> Tuple[np.ndarray, np.ndarray]:
    """Get a pose defined in the world frame from a pose defined relative to the frame of the coord_prim.

    Args:
        coord_prim (Usd.Prim): path of the prim whose frame the relative pose is defined with respect to.
        relative_translation (np.ndarray): translation relative to the frame of the prim at prim_path. Shape is (3, ).
        relative_orientation (np.ndarray): quaternion orientation relative to the frame of the prim at prim_path.
                                           Quaternion is scalar-first (w, x, y, z). Shape is (4, ).

    Returns:
        Tuple[np.ndarray, np.ndarray]: first index is position in the world frame. Shape is (3, ). Second index is
                                       quaternion orientation in the world frame. Quaternion is scalar-first
                                       (w, x, y, z). Shape is (4, ).
    """

    # Row-major transformation matrix from the prim's coordinate system to the world coordinate system
    prim_transform_matrix = UsdGeom.Xformable(coord_prim).ComputeLocalToWorldTransform(Usd.TimeCode.Default())

    # Convert transformation matrix to column-major
    prim_to_world = np.transpose(prim_transform_matrix)

    # Column-major transformation matrix from the pose to the frame the pose is defined with respect to
    relative_pose_to_prim = tf_matrix_from_pose(relative_translation, relative_orientation)

    # Chain the transformations
    relative_pose_to_world = prim_to_world @ relative_pose_to_prim

    # Translation and quaternion with respect to the world frame of the relatively defined pose
    world_position, world_orientation = pose_from_tf_matrix(relative_pose_to_world)

    return world_position, world_orientation


def get_random_translation_from_camera(
    min_distance: float, max_distance: float, fov_x: float, fov_y: float, fraction_to_screen_edge: float
) -> np.ndarray:
    """Get a random translation from the camera, in the camera's frame, that's in view of the camera.

    Args:
        min_distance (float): minimum distance away from the camera (along the optical axis) of the random
                                translation.
        max_distance (float): maximum distance away from the camera (along the optical axis) of the random
                                translation.
        fov_x (float): field of view of the camera in the x-direction in radians.
        fov_y (float): field of view of the camera in the y-direction in radians.
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
    theta_x = fov_x / 2.0
    theta_y = fov_y / 2.0

    max_x = random_z_distance * math.tan(fraction_to_screen_edge * theta_x)
    max_y = random_z_distance * math.tan(fraction_to_screen_edge * theta_y)

    # Translation relative to camera in the z direction is negative due to cameras in Isaac Sim having coordinates
    # of -z out, +y up, and +x right.
    random_x = random.uniform(-max_x, max_x)
    random_y = random.uniform(-max_y, max_y)
    random_z = -random_z_distance

    return np.array([random_x, random_y, random_z])


def get_random_world_pose_in_view(
    camera_prim: Usd.Prim,
    min_distance: float,
    max_distance: float,
    fov_x: float,
    fov_y: float,
    fraction_to_screen_edge: float,
    coord_prim: Usd.Prim,
    min_rotation_range: np.ndarray,
    max_rotation_range: np.ndarray,
) -> Tuple[np.ndarray, np.ndarray]:
    """Get a pose defined in the world frame that's in view of the camera.

    Args:
        camera_prim (Usd.Prim): prim path of the camera.
        min_distance (float): minimum distance away from the camera (along the optical axis) of the random
                                translation.
        max_distance (float): maximum distance away from the camera (along the optical axis) of the random
                                translation.
        fov_x (float): field of view of the camera in the x-direction in radians.
        fov_y (float): field of view of the camera in the y-direction in radians.
        fraction_to_screen_edge (float): maximum allowed fraction to the edge of the screen the translated point may
                                            appear when viewed from the camera. A value of 0 corresponds to the
                                            translated point being centered in the camera's view (on the optical axis),
                                            whereas a value of 1 corresponds to the translated point being on the edge
                                            of the screen in the camera's view.
        coord_prim (Usd.Prim): prim whose frame the orientation is defined with respect to.
        min_rotation_range (np.ndarray): minimum XYZ Euler angles of the random pose, defined with respect to the
                                            frame of the prim at prim_path. Shape is (3, ).
        max_rotation_range (np.ndarray): maximum XYZ Euler angles of the random pose, defined with respect to the
                                            frame of the prim at prim_path.

    Returns:
        Tuple[np.ndarray, np.ndarray]: first index is position in the world frame. Shape is (3, ). Second index is
                                        quaternion orientation in the world frame. Quaternion is scalar-first
                                        (w, x, y, z). Shape is (4, ).
    """

    random_translation_from_camera = get_random_translation_from_camera(
        min_distance, max_distance, fov_x, fov_y, fraction_to_screen_edge
    )
    random_translation_from_prim = get_translation_from_target(random_translation_from_camera, camera_prim, coord_prim)

    # Rotation ranges are expressed as Euler XYZ angles with respect to the frame of the prim at prim_path
    random_rotation_from_prim = get_random_values_in_range(min_rotation_range, max_rotation_range)
    random_orientation_from_prim = euler_angles_to_quat(random_rotation_from_prim, degrees=True)

    translation, orientation = get_world_pose_from_relative(
        coord_prim, random_translation_from_prim, random_orientation_from_prim
    )

    return translation, orientation
