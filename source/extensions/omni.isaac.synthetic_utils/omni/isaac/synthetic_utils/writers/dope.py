# Copyright (c) 2020-2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.


"""Helper class for writing groundtruth data offline in a format compatible with the DOPE model.
"""

import os
import io
import numpy as np
from PIL import Image
from .base import BaseWriter
from omni.syntheticdata.scripts.helpers import world_to_image
from omni.isaac.core.utils.transformations import pose_from_tf_matrix

import boto3
import json


class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return json.JSONEncoder.default(self, obj)


class DOPEWriter(BaseWriter):
    def __init__(
        self,
        data_dir,
        num_worker_threads,
        num_frames,
        max_queue_size=500,
        use_s3=False,
        endpoint_url="",
        bucket_name="data_2",
    ):
        BaseWriter.__init__(self, data_dir, num_worker_threads, max_queue_size)

        self.num_frames = num_frames

        self.data_dir = data_dir
        self.use_s3 = use_s3

        if self.use_s3:
            if len(bucket_name) < 3 or len(bucket_name) > 63:
                raise Exception(
                    "Name of s3 bucket must be between 3 and 63 characters long. Please pass in a new bucket name to --output_folder."
                )
            self.session = boto3.Session()
            self.s3 = self.session.resource("s3", endpoint_url=endpoint_url)
            try:
                self.bucket = self.s3.create_bucket(Bucket=bucket_name)
            except:
                self.bucket = self.s3.Bucket(bucket_name)
        else:
            self.create_output_folders()

    def worker(self):
        """Processes task from queue. Each task contains groundtruth data and metadata which is used to transform the output and write it to disk."""
        while True:
            groundtruth = self.q.get()
            if groundtruth is None:
                break

            image_id = groundtruth["IMAGEID"]

            # RGB
            self.save_rgb(groundtruth["RGB"], image_id)

            # 3D
            self.save_bbox_3d(
                groundtruth["BBOX3D"],
                image_id,
                groundtruth["POSE"]["VIEWPARAMS"],
                groundtruth["OCCLUSION"],
                groundtruth["POSE"]["INDEXTOCLASSNAME"],
                groundtruth["POSE"]["DESIREDCAMERATOWORLD"],
            )

            self.q.task_done()

    def save_rgb(self, data, image_id):
        """Saves a RGB image

        Args:
            data (np.ndarray): Image data in RGBA order. Shape is (Height, Width, 4).
            image_id (str): ID of the image being saved. 
        """

        # Save ground truth data locally as png
        if self.use_s3:
            rgb_img = Image.fromarray(data, "RGBA")
            mem_img = io.BytesIO()
            rgb_img.save(mem_img, format="PNG")

            self.bucket.put_object(Body=mem_img.getvalue(), Key=f"{image_id.zfill(6)}.png")
        else:
            rgb_img = Image.fromarray(data, "RGBA")
            rgb_img.save(f"{self.vid_dir}/{image_id.zfill(6)}.png")

    def save_bbox_3d(self, data, image_id, view_params, occlusion_values, index_to_name, camera_to_world):
        """
        Args:
            data (numpy.ndarray): A structured array with the fields: `[('instanceId', '<u4'), ('semanticId', '<u4'),
            ("metadata", "O"), ('x_min', '<f4'), ('y_min', '<f4'), ('z_min', '<f4'), ('x_max', '<f4'), ('y_max', '<f4'),
            ('z_max', '<f4'), ('transform', '<f4', (4, 4)), ('corners', '<f4', (8, 3))]`.
            
            image_id (str): String containing the image id
            
            view_params (dict): Dictionary containing view parameters.

            occlusion_values (numpy.ndarray): A structured numpy array with the fields: [('instanceId', '<u4'), ('semanticId', '<u4'),
            ('occlusionRatio', '<f4')], where occlusion ranges from 0 (not occluded) to 1 (fully occluded).
            If `parsed` is True, the additional fields [('name', 'O'), ('semanticLabel', 'O'), ("metadata", "O")]
            are returned.

            index_to_name (dict): Dictionary mapping semanticId to class name.

        """
        objects = []
        world_to_camera = np.linalg.inv(camera_to_world)

        for object in data:
            # See sensors.get_bounding_box_3d() to find information on the array returned
            semanticId, instanceId, corners = object[0], object[4][0], object[-1]

            world_transform = object[-2].astype("float")

            _, rotation = pose_from_tf_matrix(world_to_camera @ world_transform)

            center = corners.mean(axis=0)

            all_points = np.concatenate((corners, center.reshape(1, 3)))  # Append center as 9th corner

            # Convert center to be in the camera frame
            location = np.concatenate((center, [1])) @ world_to_camera
            location = location[:3]

            # Convert points from world frame to image frame
            image_space_points = world_to_image(all_points, None, view_params)
            resolution = np.array([[view_params["width"], view_params["height"], 1.0]])
            pixel_coordinates = image_space_points * resolution

            projected_cuboid_points = [
                [pixel_coordinate[0], pixel_coordinate[1]] for pixel_coordinate in pixel_coordinates
            ]

            # points returned as: [RUB, LUB, RDB, LDB, RUF, LUF, RDF, LDF]
            # but DOPE expects  : [LUF, RUF, RDF, LDF, LUB, RUB, RDB, LDB]
            projected_cuboid = [
                projected_cuboid_points[5],
                projected_cuboid_points[4],
                projected_cuboid_points[6],
                projected_cuboid_points[7],
                projected_cuboid_points[1],
                projected_cuboid_points[0],
                projected_cuboid_points[2],
                projected_cuboid_points[3],
                projected_cuboid_points[8],  # center
            ]

            # occlusion_values = list(filter(lambda x: x[0] == instanceId, occlusion_values))
            occlusion_values = list(filter(lambda x: x[1] == semanticId, occlusion_values))

            occlusion = occlusion_values[0][2] if len(occlusion_values) > 0 else 0
            visibility = float(1.0 - occlusion)  # Visibility is 1 - occlusion

            # DOPE only filters out visibility values of 0 but should ignore image if visibility falls below 0.5
            visibility = 0 if visibility < 0.05 else visibility

            groundtruth = {
                "class": index_to_name[semanticId],
                "visibility": visibility,
                "location": location * 100,  # Convert m to cm
                "quaternion_xyzw": rotation,
                "projected_cuboid": projected_cuboid,
            }

            objects.append(groundtruth)

        output = {"camera_data": {}, "objects": objects}  # TO-DO: Add camera_data. This is not used for training script

        if self.use_s3:
            self.bucket.put_object(Body=json.dumps(output, indent=2, cls=NumpyEncoder), Key=f"{image_id.zfill(6)}.json")
        else:
            with open(f"{self.vid_dir}/{image_id.zfill(6)}.json", "w") as f:
                json.dump(output, f, indent=2, cls=NumpyEncoder)

    def create_output_folders(self):
        if not os.path.exists(self.data_dir):
            os.mkdir(self.data_dir)

        self.vid_dir = os.path.join(self.data_dir, "DOPE")
        if not os.path.exists(self.vid_dir):
            os.mkdir(self.vid_dir)
