#!/usr/bin/env python
# Copyright (c) 2020, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.


"""Helper class for writing groundtruth data offline.
"""

import atexit
import colorsys
import queue
import os
import threading
import numpy as np
from PIL import Image, ImageDraw


class DataWriter:
    def __init__(self, data_dir, num_worker_threads, max_queue_size=500):
        atexit.register(self.stop_threads)
        self.data_dir = data_dir

        # Threading for multiple scenes
        self.num_worker_threads = num_worker_threads
        # Initialize queue with a specified size
        self.q = queue.Queue(max_queue_size)
        self.threads = []

        self.check_for_output_folder()

    def start_threads(self):
        """Start worker threads."""
        for _ in range(self.num_worker_threads):
            t = threading.Thread(target=self.worker, daemon=True)
            t.start()
            self.threads.append(t)

    def stop_threads(self):
        """Waits for all tasks to be completed before stopping worker threads."""
        print(f"Finish writing data...")

        # Block until all tasks are done
        self.q.join()

        # Stop workers
        for _ in range(self.num_worker_threads):
            self.q.put(None)
        for t in self.threads:
            t.join()

        print(f"Done.")

    def worker(self):
        """Processes task from queue. Each tasks contains groundtruth data and metadata which is used to transform the output and write it to disk."""
        while True:
            groundtruth = self.q.get()
            if groundtruth is None:
                break
            filename = groundtruth["METADATA"]["image_id"]
            for gt_type, data in groundtruth["DATA"].items():
                if gt_type == "RGB":
                    self.save_image(gt_type, data, filename)
                elif gt_type == "DEPTH":
                    if groundtruth["METADATA"]["DEPTH"]["NPY"]:
                        np.save(self.depth_folder + filename + ".npy", data)
                    if groundtruth["METADATA"]["DEPTH"]["COLORIZE"]:
                        self.save_image(gt_type, data, filename)
                elif gt_type == "INSTANCE":
                    self.save_segmentation(
                        gt_type,
                        data,
                        filename,
                        groundtruth["METADATA"]["INSTANCE"]["WIDTH"],
                        groundtruth["METADATA"]["INSTANCE"]["HEIGHT"],
                        groundtruth["METADATA"]["INSTANCE"]["COLORIZE"],
                        groundtruth["METADATA"]["INSTANCE"]["NPY"],
                    )
                elif gt_type == "SEMANTIC":
                    self.save_segmentation(
                        gt_type,
                        data,
                        filename,
                        groundtruth["METADATA"]["SEMANTIC"]["WIDTH"],
                        groundtruth["METADATA"]["SEMANTIC"]["HEIGHT"],
                        groundtruth["METADATA"]["SEMANTIC"]["COLORIZE"],
                        groundtruth["METADATA"]["SEMANTIC"]["NPY"],
                    )
                elif gt_type in ["BBOX2DTIGHT", "BBOX2DLOOSE"]:
                    self.save_bbox(
                        gt_type,
                        data,
                        filename,
                        groundtruth["METADATA"][gt_type]["COLORIZE"],
                        groundtruth["DATA"]["RGB"],
                        groundtruth["METADATA"][gt_type]["NPY"],
                    )
                else:
                    raise NotImplementedError
            self.q.task_done()

    def random_colours(self, N):
        start = 0
        hues = [(start + i / N) % 1.0 for i in range(N)]
        colours = [list(colorsys.hsv_to_rgb(h, 0.9, 1.0)) for i, h in enumerate(hues)]
        return colours

    def colorize_segmentation(self, segmentation_image, width=1280, height=720, num_colors=None):
        segmentation_mappings = segmentation_image[:, :, 0]
        segmentation_list = np.unique(segmentation_mappings)
        if num_colors is None:
            num_colors = np.max(segmentation_list) + 1
        color_pixels = self.random_colours(num_colors)
        color_pixels = [
            [color_pixel[0] * 255, color_pixel[1] * 255, color_pixel[2] * 255] for color_pixel in color_pixels
        ]
        segmentation_masks = np.zeros((len(segmentation_list), *segmentation_mappings.shape), dtype=np.bool)
        index_list = []
        for index, segmentation_id in enumerate(segmentation_list):
            segmentation_masks[index] = segmentation_mappings == segmentation_id
            index_list.append(segmentation_id)
        color_image = np.zeros((height, width, 3), dtype=np.uint8)
        for index, mask, colour in zip(index_list, segmentation_masks, color_pixels):
            color_image[mask] = color_pixels[index]
        color_image_list = color_image
        return np.array(color_image_list)

    def colorize_bboxes(self, bboxes_2d_data, bboxes_2d_rgb):
        semantic_id_list = []
        bbox_2d_list = []
        rgb_img = Image.fromarray(bboxes_2d_rgb)
        rgb_img_draw = ImageDraw.Draw(rgb_img)
        for bbox_2d in bboxes_2d_data:
            if bbox_2d[1] > 0:
                semantic_id_list.append(bbox_2d[1])
                bbox_2d_list.append(bbox_2d)
        semantic_id_list_np = np.unique(np.array(semantic_id_list))
        color_list = self.random_colours(len(semantic_id_list_np.tolist()))
        for bbox_2d in bbox_2d_list:
            index = np.where(semantic_id_list_np == bbox_2d[1])[0][0]
            bbox_color = color_list[index]
            rgb_img_draw.rectangle(
                [(bbox_2d[2], bbox_2d[3]), (bbox_2d[4], bbox_2d[5])],
                outline=(int(255 * bbox_color[0]), int(255 * bbox_color[1]), int(255 * bbox_color[2])),
                width=2,
            )
        bboxes_2d_rgb = np.array(rgb_img)
        # bboxes_2d_rgb = bboxes_2d_rgb.reshape(bboxes_2d_rgb.size)
        return bboxes_2d_rgb

    def save_segmentation(self, data_type, data, filename, width=1280, height=720, display_rgb=True, save_npy=True):
        # Save ground truth data locally as npy
        if data_type == "INSTANCE" and save_npy:
            np.save(self.instance_folder + filename + ".npy", data)
        if data_type == "SEMANTIC" and save_npy:
            np.save(self.semantic_folder + filename + ".npy", data)
        if display_rgb:
            image_data = np.frombuffer(data, dtype=np.uint8).reshape(*data.shape, -1)
            num_colors = 20 if data_type == "SEMANTIC" else None
            color_image = self.colorize_segmentation(image_data, width, height, num_colors)
            color_image_rgb = Image.fromarray(color_image, "RGB")
            if data_type == "INSTANCE":
                color_image_rgb.save(f"{self.instance_folder}/{filename}.png")
            if data_type == "SEMANTIC":
                color_image_rgb.save(f"{self.semantic_folder}/{filename}.png")

    def save_image(self, img_type, image_data, filename):
        if img_type == "RGB":
            # Save ground truth data locally as png
            rgb_img = Image.fromarray(image_data, "RGBA")
            rgb_img.save(f"{self.rgb_folder}/{filename}.png")
        elif img_type == "DEPTH":
            # Convert linear depth to inverse depth for better visualization
            image_data = image_data * 100
            image_data = np.reciprocal(image_data)
            # Save ground truth data locally as png
            image_data[image_data == 0.0] = 1e-5
            image_data = np.clip(image_data, 0, 255)
            image_data -= np.min(image_data)
            image_data /= np.max(image_data)
            depth_img = Image.fromarray((image_data * 255.0).astype(np.uint8))
            depth_img.save(f"{self.depth_folder}/{filename}.png")

    def save_bbox(self, data_type, data, filename, display_rgb=True, rgb_data=None, save_npy=True):
        # Save ground truth data locally as npy
        if data_type == "BBOX2DTIGHT" and save_npy:
            np.save(self.bbox_2d_tight_folder + filename + ".npy", data)
        if data_type == "BBOX2DLOOSE" and save_npy:
            np.save(self.bbox_2d_loose_folder + filename + ".npy", data)
        if display_rgb and rgb_data is not None:
            color_image = self.colorize_bboxes(data, rgb_data)
            color_image_rgb = Image.fromarray(color_image, "RGBA")
            if data_type == "BBOX2DTIGHT":
                color_image_rgb.save(f"{self.bbox_2d_tight_folder}/{filename}.png")
            if data_type == "BBOX2DLOOSE":
                color_image_rgb.save(f"{self.bbox_2d_loose_folder}/{filename}.png")

    def check_for_output_folder(self):
        """Checks if the output folders are created. If not, it creates them."""
        if not os.path.exists(self.data_dir):
            os.mkdir(self.data_dir)
        self.rgb_folder = self.data_dir + "/rgb/"
        if not os.path.exists(self.rgb_folder):
            os.mkdir(self.rgb_folder)
        self.depth_folder = self.data_dir + "/depth/"
        if not os.path.exists(self.depth_folder):
            os.mkdir(self.depth_folder)
        self.instance_folder = self.data_dir + "/instance_segmentation/"
        if not os.path.exists(self.instance_folder):
            os.mkdir(self.instance_folder)
        self.semantic_folder = self.data_dir + "/semantic_segmentation/"
        if not os.path.exists(self.semantic_folder):
            os.mkdir(self.semantic_folder)
        self.bbox_2d_tight_folder = self.data_dir + "/bbox_2d_tight/"
        if not os.path.exists(self.bbox_2d_tight_folder):
            os.mkdir(self.bbox_2d_tight_folder)
        self.bbox_2d_loose_folder = self.data_dir + "/bbox_2d_loose/"
        if not os.path.exists(self.bbox_2d_loose_folder):
            os.mkdir(self.bbox_2d_loose_folder)
