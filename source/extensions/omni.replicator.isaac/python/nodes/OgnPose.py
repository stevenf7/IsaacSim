"""
This is the implementation of the OGN node defined in OgnPose.ogn
"""

# Array or tuple values are accessed as numpy arrays so you probably need this import
import json

import numpy as np
import omni.graph.core as og
from omni.isaac.core.utils.transformations import tf_matrix_from_pose
from omni.isaac.core.utils.rotations import euler_angles_to_quat

from omni.replicator.isaac.scripts.utils import get_image_space_points, get_semantics


class OgnPose:
    """
         gets poses of assets with semantic labels
    """

    @staticmethod
    def compute(db) -> bool:
        """Compute the outputs from the current input"""

        return_data_list = [("semanticId", "<u4"), ("prims_to_desired_camera", "<f4", (4, 4))]

        get_centers = db.inputs.getCenters

        if get_centers:
            center_type = ("center_coords_image_space", "<f4", (2,))
            return_data_list.append(center_type)

        return_data_dtype = np.dtype(return_data_list)

        num_semantics = db.inputs.sdIMNumSemantics

        prims_to_world_row_major = db.inputs.sdIMSemanticWorldTransform.view(np.float32).reshape((num_semantics, 4, 4))
        prims_to_world_row_major[:, :-1, :-1] = prims_to_world_row_major[:, :-1, :-1] * 100.0

        if num_semantics == 0:
            db.outputs.data = np.frombuffer(np.empty(0, dtype=return_data_dtype).tobytes(), dtype=np.uint8)
            db.outputs.exec = og.ExecutionAttributeState.ENABLED
            db.outputs.swhFrameNumber = db.inputs.swhFrameNumber
            db.outputs.bufferSize = 0
            db.outputs.height = 0
            db.outputs.width = 0
            db.outputs.idToLabels = "{}"
            return True

        num_semantic_tokens = db.inputs.sdIMNumSemanticTokens

        instance_semantic_map = db.inputs.sdIMInstanceSemanticMap.view(np.uint16)
        min_semantic_idx = db.inputs.sdIMMinSemanticIndex
        max_semantic_hierarchy_depth = db.inputs.sdIMMaxSemanticHierarchyDepth
        semantic_token_map = db.inputs.sdIMSemanticTokenMap

        required_semantic_types = db.inputs.semanticTypes

        # If list of semantics is empty, return False
        if len(required_semantic_types) == 0:
            return False

        serialized_index_to_labels, semantic_ids, valid_semantic_entity_count, prim_paths = get_semantics(
            num_semantics,
            num_semantic_tokens,
            instance_semantic_map,
            min_semantic_idx,
            max_semantic_hierarchy_depth,
            semantic_token_map,
            required_semantic_types,
        )

        # Poses
        cameraRotation = db.inputs.cameraRotation
        width = db.inputs.width
        height = db.inputs.height
        cameraViewTransform = db.inputs.cameraViewTransform
        cameraProjection = db.inputs.cameraProjection

        default_camera_to_desired_camera = tf_matrix_from_pose(
            translation=(0.0, 0.0, 0.0), orientation=euler_angles_to_quat(cameraRotation, degrees=True)
        )

        world_to_default_camera_row_major = np.asarray(cameraViewTransform).reshape((4, 4))
        world_to_default_camera = np.transpose(world_to_default_camera_row_major)

        prims_to_world = np.transpose(prims_to_world_row_major, axes=(0, 2, 1))

        prims_to_desired_camera = default_camera_to_desired_camera @ world_to_default_camera @ prims_to_world

        # Centers
        if get_centers:
            prim_translations = prims_to_world[:, :-1, -1]

            default_camera_to_image_row_major = np.asarray(cameraProjection).reshape((4, 4))

            # Default view projection matrix, transforming points from world frame to image space of default camera
            world_to_default_image = world_to_default_camera_row_major @ default_camera_to_image_row_major
            default_camera_to_desired_camera_row_major = np.transpose(default_camera_to_desired_camera)

            # Desired view projection matrix, transforming points from world frame to image space of desired camera
            view_proj_matrix = world_to_default_image @ default_camera_to_desired_camera_row_major

            image_space_points = get_image_space_points(prim_translations, view_proj_matrix)

            resolution_homogenous = np.array([[width, height, 1.0]])
            pixel_coordinates = image_space_points * resolution_homogenous
            centers = [[pixel_coordinate[0], pixel_coordinate[1]] for pixel_coordinate in pixel_coordinates]

        data = np.zeros(valid_semantic_entity_count, dtype=return_data_dtype)

        data["semanticId"] = np.array(semantic_ids)
        data["prims_to_desired_camera"] = prims_to_desired_camera

        if get_centers:
            data["center_coords_image_space"] = pixel_coordinates[:, :-1]

        db.outputs.data = np.frombuffer(data.tobytes(), dtype=np.uint8)
        db.outputs.idToLabels = serialized_index_to_labels
        db.outputs.primPaths = prim_paths
        db.outputs.exec = og.ExecutionAttributeState.ENABLED
        db.outputs.swhFrameNumber = db.inputs.swhFrameNumber
        db.outputs.bufferSize = 0
        db.outputs.height = 0
        db.outputs.width = 0

        return True
