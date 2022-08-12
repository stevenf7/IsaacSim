# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
import os
from pxr import Usd, UsdGeom
from omni.isaac.core.utils.stage import get_current_stage, get_stage_units
from omni.isaac.core.utils.transformations import tf_matrix_from_pose, pose_from_tf_matrix
from omni.isaac.core.utils.rotations import euler_angles_to_quat
from omni.syntheticdata.scripts.helpers import get_bbox_3d_corners
import random
import math
import numpy as np
from pathlib import Path
import carb


def get_source_to_target_transform(source_path, target_path):
    """Get the transformation matrix from the frame of the prim at source path to the frame of the prim at target path.

    Args:
        source_path (str): prim path of the prim whose frame corresponds to the original/untransformed source frame.
        target_path (str): prim path of the prim whose frame corresponds to the transformed target frame.

    Returns:
        np.ndarray: Column-major transformation matrix from the frame of the prim at source path to the frame of the
                    prim at target path. Shape is (4, 4).
    """

    stage = get_current_stage()

    source_prim = stage.GetPrimAtPath(source_path)
    target_prim = stage.GetPrimAtPath(target_path)

    source_transform_matrix = UsdGeom.Xformable(source_prim).ComputeLocalToWorldTransform(Usd.TimeCode.Default())
    target_transform_matrix = UsdGeom.Xformable(target_prim).ComputeLocalToWorldTransform(Usd.TimeCode.Default())

    source_to_world = np.transpose(source_transform_matrix)
    target_to_world = np.transpose(target_transform_matrix)

    world_to_target = np.linalg.inv(target_to_world)

    source_to_target = world_to_target @ source_to_world

    return source_to_target


def get_transformed_points(path, mesh_path):
    """Get vertices of the mesh at mesh_path in the coordinate system of the prim at path.

    Args:
        path (str): prim path of the prim having the frame for which to define the vertices with respect to.
        mesh_path (str): prim path of the mesh for which to get the vertices of.

    Returns:
        np.ndarray: vertices of the mesh at mesh_path in the coordinate system of the prim at path. Shape is
                    (num_vertices, 3)
    """

    stage = get_current_stage()

    mesh_prim = stage.GetPrimAtPath(mesh_path)

    # Vertices of the mesh in the mesh's coordinate system
    points_in_mesh_coords_vec3f = UsdGeom.Mesh(mesh_prim).GetPointsAttr().Get()
    points_in_mesh_coords = np.array(points_in_mesh_coords_vec3f)
    points_in_mesh_coords_homogeneous = np.pad(points_in_mesh_coords, ((0, 0), (0, 1)), constant_values=1.0)

    # Transformation matrix from the coordinate system of the mesh to the coordinate system of the prim
    mesh_to_prim = get_source_to_target_transform(mesh_path, path)

    # Transform points so they are in the coordinate system of the top-level ancestral xform prim
    points = points_in_mesh_coords_homogeneous @ np.transpose(mesh_to_prim)

    points_in_meters = points[:, :-1] * get_stage_units()

    return points_in_meters


def save_points_xyz(path, mesh_path, specific_model_name_str, output_folder):
    """Create points.xyz file representing vertices of the mesh, defined in the frame of the prim at path. The
       points.xyz file will be saved in the output_folder/data/models/specific_model_name_str/ directory.

    Args:
        path (str): prim path of the prim having the frame for which to define the vertices with respect to.
        mesh_path (str): prim path of the mesh for which to get the vertices of.
        specific_model_name_str (str): name of the part to get the vertices of. Note: This corresponds to the name used
                                       for the part in the YCB Video Dataset, and is unrelated to the name of the part
                                       in the scene.
        output_folder (str): path of the base output directory.
    """

    file_path = os.path.join(output_folder, "data", "models", specific_model_name_str, "points.xyz")
    dirname = os.path.dirname(file_path)
    os.makedirs(dirname, exist_ok=True)

    points = get_transformed_points(path, mesh_path)
    np.savetxt(file_path, points, fmt="%.6f", delimiter=" ", newline="\n")


def get_translation_from_target(translation_from_source, source_path, target_path):
    """Get a translation with respect to the target's frame, from a translation in the source's frame.

    Args:
        translation_from_source (np.ndarray): translation from the frame of the prim at source_path. Shape is (3, ).
        source_path (str): prim path of the prim whose frame the original/untransformed translation
                           (translation_from_source) is defined with respect to.
        target_path (str): prim path of the prim whose frame corresponds to the target frame that the returned
                           translation will be defined with respect to.

    Returns:
        np.ndarray: translation with respect to the target's frame. Shape is (3, ).
    """

    translation_from_source_homogenous = np.pad(translation_from_source, ((0, 1)), constant_values=1.0)

    source_to_target = get_source_to_target_transform(source_path, target_path)

    translation_from_target_homogenous = translation_from_source_homogenous @ np.transpose(source_to_target)
    translation_from_target = translation_from_target_homogenous[:-1]

    return translation_from_target


def get_random_values_in_range(min_range, max_range):
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


def get_world_pose_from_relative(prim_path, relative_translation, relative_orientation):
    """Get a pose defined in the world frame from a pose defined relative to the frame of the prim at prim_path.

    Args:
        prim_path (str): path of the prim whose frame the relative pose is defined with respect to.
        relative_translation (np.ndarray): translation relative to the frame of the prim at prim_path. Shape is (3, ).
        relative_orientation (np.ndarray): quaternion orientation relative to the frame of the prim at prim_path.
                                           Quaternion is scalar-first (w, x, y, z). Shape is (4, ).

    Returns:
        Tuple[np.ndarray, np.ndarray]: first index is position in the world frame. Shape is (3, ). Second index is
                                       quaternion orientation in the world frame. Quaternion is scalar-first
                                       (w, x, y, z). Shape is (4, ).
    """

    stage = get_current_stage()

    prim = stage.GetPrimAtPath(prim_path)

    # Row-major transformation matrix from the prim's coordinate system to the world coordinate system
    prim_transform_matrix = UsdGeom.Xformable(prim).ComputeLocalToWorldTransform(Usd.TimeCode.Default())

    # Convert transformation matrix to column-major
    prim_to_world = np.transpose(prim_transform_matrix)

    # Column-major transformation matrix from the pose to the frame the pose is defined with respect to
    relative_pose_to_prim = tf_matrix_from_pose(relative_translation, relative_orientation)

    # Chain the transformations
    relative_pose_to_world = prim_to_world @ relative_pose_to_prim

    # Translation and quaternion with respect to the world frame of the relatively defined pose
    world_position, world_orientation = pose_from_tf_matrix(relative_pose_to_world)

    return world_position, world_orientation


def get_random_translation_from_camera(min_distance, max_distance, fov_x, fov_y, fraction_to_screen_edge):
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
    camera_path,
    min_distance,
    max_distance,
    fov_x,
    fov_y,
    fraction_to_screen_edge,
    prim_path,
    min_rotation_range,
    max_rotation_range,
):
    """Get a pose defined in the world frame that's in view of the camera.

    Args:
        camera_path (str): prim path of the camera.
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

    random_translation_from_camera = get_random_translation_from_camera(
        min_distance, max_distance, fov_x, fov_y, fraction_to_screen_edge
    )
    random_translation_from_prim = get_translation_from_target(random_translation_from_camera, camera_path, prim_path)

    # Rotation ranges are expressed as Euler XYZ angles with respect to the frame of the prim at prim_path
    random_rotation_from_prim = get_random_values_in_range(min_rotation_range, max_rotation_range)
    random_orientation_from_prim = euler_angles_to_quat(random_rotation_from_prim, degrees=True)

    translation, orientation = get_world_pose_from_relative(
        prim_path, random_translation_from_prim, random_orientation_from_prim
    )

    return translation, orientation


def get_as_sdh_bb_3d_format(bb_3d_repl):
    """Get the OV Replicator BBox 3d Annotator's data as SyntheticDataHelper format:
        see get_bounding_box_3d in omni.isaac.synthetic_utils/omni/isaac/synthetic_utils/syntheticdata.py
    """

    sdh_bb_3d = []
    corners = get_bbox_3d_corners(bb_3d_repl["data"])

    for i, bb_3d_data in enumerate(bb_3d_repl["data"]):
        sdh_bb_3d.append(
            (
                bb_3d_data["semanticId"] + 1,
                bb_3d_repl["info"]["primPaths"][i],
                bb_3d_repl["info"]["idToLabels"][str(i)]["class"],
                "",
                [-1],  # TODO dummy instanceId value
                bb_3d_data["semanticId"] + 1,
                bb_3d_data["x_min"],
                bb_3d_data["y_min"],
                bb_3d_data["z_min"],
                bb_3d_data["x_max"],
                bb_3d_data["y_max"],
                bb_3d_data["z_max"],
                bb_3d_data["transform"],
                corners[i],
            )
        )
    return sdh_bb_3d
