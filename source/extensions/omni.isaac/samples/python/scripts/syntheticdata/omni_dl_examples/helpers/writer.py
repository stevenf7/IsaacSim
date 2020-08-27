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
import queue
import os
import threading
import numpy as np
from PIL import Image


class DataWriter:
    def __init__(self, data_dir):
        atexit.register(self.stop_threads)
        self.data_dir = data_dir

        # Threading for multiple scenes
        self.num_worker_threads = 4
        self.q = queue.Queue()
        self.threads = []

        self.check_for_output_folder()

    def start_threads(self):
        # Start worker threads
        for _ in range(self.num_worker_threads):
            t = threading.Thread(target=self.worker, daemon=True)
            t.start()
            self.threads.append(t)

    def stop_threads(self):
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
        while True:
            groundtruth = self.q.get()
            if groundtruth is None:
                break
            filename = groundtruth["metadata"]["image_id"]
            for gt_type, data in groundtruth["data"].items():
                if gt_type in ["depth", "rgb"]:
                    self.save_image(gt_type, data, filename)
                elif gt_type == "instanceSegmentation":
                    self.save_numpy(data, filename)
                else:
                    raise NotImplementedError
            self.q.task_done()

    def save_numpy(self, data, filename):
        if data is None:
            return
        # Save ground truth data locally as npy
        np.save(self.instance_folder + filename + ".npy", data)

    def save_image(self, img_type, image_data, filename):
        if image_data is None:
            return
        if img_type == "rgb":
            # Save ground truth rgb data locally as png
            rgb_img = Image.fromarray(image_data, "RGBA")
            rgb_img.save(f"{self.rgb_folder}/{filename}.png")
        elif img_type == "depth":
            # Save ground truth depth data locally as png
            image_data[image_data == 0.0] = 1e-5
            image_data = np.clip(image_data, 0, 255)
            image_data -= np.min(image_data)
            image_data /= np.max(image_data)
            depth_img = Image.fromarray((image_data * 255.0).astype(np.uint8))
            depth_img.save(f"{self.depth_folder}/{filename}.png")

    def check_for_output_folder(self):
        if not os.path.exists(self.data_dir):
            os.mkdir(self.data_dir)
        self.rgb_folder = self.data_dir + "/rgb/"
        if not os.path.exists(self.rgb_folder):
            os.mkdir(self.rgb_folder)
        self.depth_folder = self.data_dir + "/depth/"
        if not os.path.exists(self.depth_folder):
            os.mkdir(self.depth_folder)
        self.instance_folder = self.data_dir + "/instanceSegmentation/"
        if not os.path.exists(self.instance_folder):
            os.mkdir(self.instance_folder)
