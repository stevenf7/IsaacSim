import atexit
import colorsys
import queue
import os
import threading
import numpy as np
from PIL import Image, ImageDraw
import json
import csv


class KittiWriter:
    def __init__(self, data_dir="kitti_data", num_worker_threads=4, max_queue_size=500, train_size=10, classes=[]):
        atexit.register(self.stop_threads)
        # Threading for multiple scenes
        self.num_worker_threads = num_worker_threads
        # Initialize queue with a specified size
        self.q = queue.Queue(max_queue_size)
        self.threads = []
        self.data_dir = data_dir
        self.make_output_folders()
        self.train_size = train_size
        self.classes = classes

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
            data = self.q.get()
            if data is None:
                break
            else:
                self.save_image(data)
                if int(data["METADATA"]["image_id"]) < self.train_size:
                    self.save_label(data)
            self.q.task_done()

    def save_label(self, data):
        """Saves the labels for the 2d bounding boxes in Kitti format."""
        label_set = []
        viewport_width = data["METADATA"]["BBOX2DLOOSE"]["WIDTH"]
        viewport_height = data["METADATA"]["BBOX2DLOOSE"]["HEIGHT"]

        for box in data["DATA"]["BBOX2DLOOSE"]:
            label = []

            # 2D bounding box points
            x_min, y_min, x_max, y_max = int(box[6]), int(box[7]), int(box[8]), int(box[9])

            # Check if bounding boxes are in the viewport
            if (
                x_min < 0
                or y_min < 0
                or x_max > viewport_width
                or y_max > viewport_height
                or x_min > viewport_width
                or y_min > viewport_height
                or y_max < 0
                or x_max < 0
            ):
                continue

            semantic_label = str(box[2])

            # Skip label if not in class list
            if self.classes != [] and semantic_label not in self.classes:
                continue

            # Adding Kitting Data,  NOTE: Only class and 2d bbox coordinates are filled in
            label.append(semantic_label)
            label.append(f"{0.00:.2f}")
            label.append(3)
            label.append(f"{0.00:.2f}")
            label.append(x_min)
            label.append(y_min)
            label.append(x_max)
            label.append(y_max)
            for _ in range(7):
                label.append(f"{0.00:.2f}")

            label_set.append(label)

        with open(os.path.join(self.train_label_dir, f"{data['METADATA']['image_id']}.txt"), "w") as annotation_file:
            writer = csv.writer(annotation_file, delimiter=" ")
            writer.writerows(label_set)

    def save_image(self, data):
        """Saves the RGB image in the correct directory for kitti"""
        if int(data["METADATA"]["image_id"]) < self.train_size:
            rgb_img = Image.fromarray(data["DATA"]["RGB"], "RGBA").convert("RGB")
            rgb_img.save(f"{self.train_folder}/image_2/{data['METADATA']['image_id']}{'.png'}")
        else:
            rgb_img = Image.fromarray(data["DATA"]["RGB"], "RGBA").convert("RGB")
            rgb_img.save(f"{self.test_folder}/image_2/{data['METADATA']['image_id']}{'.png'}")

    def make_output_folders(self):
        """Checks if the output folders are created. If not, it creates them."""
        if not os.path.exists(self.data_dir):
            os.mkdir(self.data_dir)

        self.train_folder = os.path.join(self.data_dir, "training")
        self.test_folder = os.path.join(self.data_dir, "testing")

        if not os.path.exists(self.train_folder):
            os.mkdir(self.train_folder)

        if not os.path.exists(self.test_folder):
            os.mkdir(self.test_folder)

        self.train_img_dir = os.path.join(self.train_folder, "image_2")
        if not os.path.exists(self.train_img_dir):
            os.mkdir(self.train_img_dir)

        self.train_label_dir = os.path.join(self.train_folder, "label_2")
        if not os.path.exists(self.train_label_dir):
            os.mkdir(self.train_label_dir)

        if not os.path.exists(os.path.join(self.test_folder, "image_2")):
            os.mkdir(os.path.join(self.test_folder, "image_2"))
