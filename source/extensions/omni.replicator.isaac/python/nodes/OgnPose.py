"""
This is the implementation of the OGN node defined in OgnPose.ogn
"""

# Array or tuple values are accessed as numpy arrays so you probably need this import
import json

import numpy as np
import omni.graph.core as og
from omni.isaac.core.utils.transformations import tf_matrix_from_pose
from omni.isaac.core.utils.rotations import euler_angles_to_quat


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

        prims_to_world_row_major = prims_to_world_row_major

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

        instance_to_semantic = instance_semantic_map - min_semantic_idx

        id_to_parents = {}
        # Mapping from a semantic itself to its parents.
        for i in range(0, len(instance_to_semantic), max_semantic_hierarchy_depth):
            curr_semantic_id = instance_to_semantic[i]
            id_to_parents[curr_semantic_id] = []
            for j in range(1, max_semantic_hierarchy_depth):
                parent_semantic_id = instance_to_semantic[i + j]
                if parent_semantic_id != 65535:  # Avoid invalid data
                    id_to_parents[curr_semantic_id].append(parent_semantic_id)

        # Mapping from index to semantic labels of each prim
        index_to_labels = {}

        # Iterate through all semantic tokens, and choose those who required by the semantic types.
        valid_semantic_entity_count = 0
        prim_paths = []

        for i in range(num_semantics):
            # TODO Is there a validity check that needs to be performed here?
            is_valid = True
            if is_valid:
                index_to_labels[valid_semantic_entity_count] = {}

                # Find labels of itself and parent labels
                self_labels = semantic_token_map[i * num_semantic_tokens : (i + 1) * num_semantic_tokens]
                parent_labels = []

                if i in id_to_parents.keys():
                    for parent_semantic_id in id_to_parents[i]:
                        parent_labels.extend(
                            semantic_token_map[
                                parent_semantic_id
                                * num_semantic_tokens : (parent_semantic_id + 1)
                                * num_semantic_tokens
                            ]
                        )

                all_labels = self_labels + parent_labels

                prim_paths.append(all_labels[0])
                for label_string in all_labels:
                    for label in label_string.split(" "):
                        if ":" not in label:
                            continue
                        semantic_type, semantic_data = label.split(":")
                        if semantic_type in required_semantic_types:
                            index_to_labels[valid_semantic_entity_count].setdefault(semantic_type, set()).add(
                                semantic_data
                            )
                # TODO I don't remember why I put this todo here :(   Maybe the bouding box node this code is taken from would provide a clue? Maybe it has to do with semantic filtering?
                valid_semantic_entity_count += 1

        semantic_ids = []
        labels_to_id = {}
        id_to_labels = {}
        id_count = 0

        for index, labels in index_to_labels.items():
            labels_str = str(labels)
            if labels_str not in labels_to_id:
                labels_to_id[labels_str] = id_count
                id_to_labels[id_count] = {}

                for label in labels:
                    id_to_labels[id_count] = {k: ",".join(sorted(v)) for k, v in labels.items()}

                semantic_ids.append(id_count)
                id_count += 1
            else:
                semantic_ids.append(labels_to_id[labels_str])

        serialized_index_to_labels = json.dumps(id_to_labels)

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

            homo = np.pad(prim_translations, ((0, 0), (0, 1)), constant_values=1.0)
            tf_points = np.dot(homo, view_proj_matrix)
            tf_points = tf_points / (tf_points[..., -1:])
            tf_points[..., :2] = 0.5 * (tf_points[..., :2] + 1)
            image_space_points = tf_points[..., :3]

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
