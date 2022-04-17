# Copyright (c) 2020-2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.


"""Helper class for writing groundtruth data offline in a similar format to the YCB Video Dataset.
"""

from scipy.io import savemat
import os
import numpy as np
from PIL import Image
from .base import BaseWriter
from omni.syntheticdata.scripts.helpers import world_to_image
from omni.isaac.core.utils.stage import get_stage_units


class YCBVideoWriter(BaseWriter):
    def __init__(self, data_dir, num_worker_threads, num_frames, max_queue_size=500):
        BaseWriter.__init__(self, data_dir, num_worker_threads, max_queue_size)
        from omni.isaac.synthetic_utils import visualization

        self.visualization = visualization
        self.num_frames = num_frames
        self.create_output_folders()
        self.create_train_text_file()

    def worker(self):
        """Processes task from queue. Each task contains groundtruth data and metadata which is used to transform the output and write it to disk."""
        while True:
            groundtruth = self.q.get()
            if groundtruth is None:
                break

            image_id = groundtruth["IMAGEID"]

            # RGB
            self.save_rgb(groundtruth["RGB"], image_id)

            # Depth
            self.save_depth(groundtruth["DEPTH"], image_id)

            # Semantic Segmentation
            self.save_segmentation(groundtruth["SEMANTIC"], image_id)

            # 2D BBox
            self.save_bbox(groundtruth["BBOX2DTIGHT"], image_id)

            # Meta.mat file
            self.save_meta(
                groundtruth["POSE"]["PRIMSTOWORLD"],
                groundtruth["POSE"]["DESIREDCAMERATOWORLD"],
                groundtruth["POSE"]["VIEWPARAMS"],
                groundtruth["POSE"]["CAMERAINTRINSICS"],
                groundtruth["POSE"]["CLASSNAMETOINDEX"],
                groundtruth["BBOX2DTIGHT"],
                image_id,
            )

            self.q.task_done()

    def save_rgb(self, data, image_id):
        """Saves a RGB image for the YCB Video Dataset.

        Args:
            data (np.ndarray): Image data in RGBA order. Shape is (Height, Width, 4).
            image_id (str): ID of the image being saved. 
        """

        # Save ground truth data locally as png
        rgb_img = Image.fromarray(data, "RGBA")
        rgb_img.save(f"{self.vid_dir}/{image_id}-color.png")

    def save_depth(self, data, image_id):
        """Saves a depth image for the YCB Video Dataset. Note: Depth images are only for visualization and testing, and
           would need to be adapted to conform to the exact format used in the YCB Video Dataset. 

        Args:
            data (np.ndarray): Depth data. Shape is (Height, Width).
            image_id (str): ID of the image being saved. 
        """

        # Convert linear depth to inverse depth for better visualization
        data = data * 100
        if np.max(data) > 0:
            data = np.reciprocal(data)

        # Save ground truth data locally as png
        data[data == 0.0] = 1e-5
        data = np.clip(data, 0, 255)
        data -= np.min(data)
        if np.max(data) > 0:
            data /= np.max(data)
        depth_img = Image.fromarray((data * 255.0).astype(np.uint8))
        depth_img.save(f"{self.vid_dir}/{image_id}-depth.png")

    def save_segmentation(self, data, image_id):
        """Saves a segmentation label image file for the YCB Video Dataset. Segmentation label is saved as a grayscale 
           image.

        Args:
            data (np.ndarray): Segmentation label data. Shape is (Height, Width).
            image_id (str): ID of the image being saved. 
        """

        # Save ground truth data locally as png
        img = Image.fromarray(np.uint8(data), "L")
        img.save(f"{self.vid_dir}/{image_id}-label.png")

    def save_bbox(self, tight_bboxes, image_id):
        """Saves a text file describing bounding boxes of semantically-labeled objects in view for the YCB Video 
           Dataset. Note: Lines of the bounding box text file consist of a class name and the position of the bounding 
           box. The positions of the bounding boxes are represented by the upper-left coordinate, followed by the 
           bottom-right coordinate. Coordinates are expressed in pixels, where the origin of the image is the top-left 
           corner, with +x to the right and +y down.

        Args:
            tight_bboxes (np.ndarray): Tight bounding box data. See get_bounding_box_2d_tight() in 
                                       omni.syntheticdata.scripts.sensors for more details.
            image_id (str): ID of the image being saved. 
        """

        fname = f"{self.vid_dir}/{image_id}-box.txt"
        f = open(fname, "w")

        for bbox in tight_bboxes:

            bbox_str = f"{bbox[2]} {bbox[6]} {bbox[7]} {bbox[8]} {bbox[9]}\n"  # "class_name x1 y1 x2 y2"

            f.write(bbox_str)

        f.close()

    def save_meta(
        self,
        prims_to_world,
        desired_camera_to_world,
        view_params,
        intrinsic_matrix,
        class_name_to_index,
        tight_bboxes,
        image_id,
    ):
        """Saves a metadata ".mat" file for the YCB Video Dataset, containing:
           - Class indexes (from a pre-defined mapping) corresponding to each semantically-labeled object in view.
           - A depth image scaling factor.
           - The intrinsic matrix of the camera.
           - Poses from the frame of each semantically-labeled object in view to the world frame, represented as a 
             rotation matrix and a translation.
           - The center (in pixel coordinates) of each semantically-labeled object in view. Pixel coordinates are 
             expressed relative to the top-left corner of the image, with +x to the right and +y down.

        Args:
            prims_to_world (np.ndarray): Column-major transformation matrices from the frame of each 
                                         semantically-labeled prim in view to the world frame. Shape is 
                                         (num_prims, 4, 4).
            desired_camera_to_world (np.ndarray): Column-major transformation matrix from the frame of the desired 
                                                  camera to the world frame. Shape is (4, 4). Note: This transformation 
                                                  matrix does not need to be gathered directly from a camera prim, and 
                                                  if a non-default camera coordinate system is used (as in the YCB Video 
                                                  Dataset), then this transformation matrix needs to be calculated 
                                                  either from a prim having the coordinate system of the "desired 
                                                  camera", or by performing a transformation on the camera prim's (i.e. 
                                                  default camera's) transformation matrix.
            view_params (dict): Dictionary containing view parameters. See get_view_params() in 
                                omni.syntheticdata.scripts.helpers for more details.
            intrinsic_matrix (np.ndarray): Matrix representing camera intrinsics. Shape is (3, 3).
            class_name_to_index (dict): Mapping from class name to corresponding pre-defined class index.
            tight_bboxes (np.ndarray): Tight bounding box data. See get_bounding_box_2d_tight() in 
                                       omni.syntheticdata.scripts.sensors for more details.
            image_id (str): ID of the image being saved. 
        """

        world_to_desired_camera = np.linalg.inv(desired_camera_to_world)

        n = len(tight_bboxes)

        if n > 0:
            # Class indexes
            cls_indexes = [[class_name_to_index[tight_bbox[2]]] for tight_bbox in tight_bboxes]

            # Poses
            prims_to_desired_camera = world_to_desired_camera @ prims_to_world

            # Convert translations from stage units to meters
            meters_per_stage_unit = get_stage_units()
            prims_to_desired_camera[:, :-1, -1] = prims_to_desired_camera[:, :-1, -1] * meters_per_stage_unit

            # Make poses have a shape of (3, 4, n)
            poses = np.moveaxis(prims_to_desired_camera[:, :-1, :], 0, -1)

            # Centers
            prim_translations = prims_to_world[:, :-1, -1]
            image_space_points = world_to_image(prim_translations, None, view_params)
            resolution = np.array([[view_params["width"], view_params["height"], 1.0]])
            pixel_coordinates = image_space_points * resolution
            centers = [[pixel_coordinate[0], pixel_coordinate[1]] for pixel_coordinate in pixel_coordinates]

        else:
            cls_indexes = []

            poses = np.array([[[]]], dtype=np.float64)

            centers = []

        cls_indexes = np.asarray(cls_indexes, dtype=np.uint8)
        meta_dict = {
            "cls_indexes": cls_indexes,
            "factor_depth": np.array([10000], dtype=np.uint16),
            "intrinsic_matrix": intrinsic_matrix,
            "poses": poses,
            "center": centers,
        }

        savemat(f"{self.vid_dir}/{image_id}-meta.mat", meta_dict)

    def create_output_folders(self):
        """Creates an output directory structure (if necessary), similar to that used in the YCB Video Dataset. Note: A 
           single video directory is used to hold all the generated synthetic data, rather than several directories
           (each representing a separate video file, as in the YCB Video Dataset).
        """

        if not os.path.exists(self.data_dir):
            os.mkdir(self.data_dir)

        data_dir = os.path.join(self.data_dir, "data")
        if not os.path.exists(data_dir):
            os.mkdir(data_dir)

        self.ycb_video_dir = os.path.join(data_dir, "YCB_Video")
        if not os.path.exists(self.ycb_video_dir):
            os.mkdir(self.ycb_video_dir)

        ycb_video_data_dir = os.path.join(self.ycb_video_dir, "data")
        if not os.path.exists(ycb_video_data_dir):
            os.mkdir(ycb_video_data_dir)

        self.vid_dir = os.path.join(ycb_video_data_dir, "0000")
        if not os.path.exists(self.vid_dir):
            os.mkdir(self.vid_dir)

    def create_train_text_file(self):
        """Creates a text file to specify the set of YCB Video Dataset samples to be used during training of a model. 
           Lines include the video basename corresponding to the video that the sample is from, and the image ID of the
           sample. Training samples are written as if a single video is being used (see the note in 
           create_output_folders()). Additionally, it is assumed data is generated only for model training (rather than 
           for testing or validation).
        """

        train_filename = os.path.join(self.ycb_video_dir, "train.txt")
        f = open(train_filename, "w")

        vid_dir_basename = os.path.basename(os.path.normpath(self.vid_dir))

        for i in range(self.num_frames):

            train_file_str = f"{vid_dir_basename}/{i:06d}\n"
            f.write(train_file_str)

        f.close()
