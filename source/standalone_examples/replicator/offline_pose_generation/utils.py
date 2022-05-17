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
import random
import numpy as np


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

    if not os.path.exists(output_folder):
        os.mkdir(output_folder)

    data_dir = os.path.join(output_folder, "data")
    if not os.path.exists(data_dir):
        os.mkdir(data_dir)

    model_dir = os.path.join(data_dir, "models")
    if not os.path.exists(model_dir):
        os.mkdir(model_dir)

    specific_model_dir = os.path.join(model_dir, specific_model_name_str)
    if not os.path.exists(specific_model_dir):
        os.mkdir(specific_model_dir)

    filename = f"{specific_model_dir}/points.xyz"

    points = get_transformed_points(path, mesh_path)

    np.savetxt(filename, points, fmt="%.6f", delimiter=" ", newline="\n")


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
