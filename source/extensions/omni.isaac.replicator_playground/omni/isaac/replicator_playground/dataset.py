# Copyright (c) 2020, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.


import omni
import os
import torch
import matplotlib.pyplot as plt
import numpy as np
import signal
from PIL import Image
from omni.isaac.synthetic_utils import visualization as vis


class RandomObjects(torch.utils.data.IterableDataset):
    def __init__(self, folder_path, split=0.7, train=True):
        self.stage = omni.usd.get_context().get_stage()

        self.categories = []
        self.gt_all = []
        self.cur_idx = 0
        self.exiting = False
        self.folder_path = folder_path

        signal.signal(signal.SIGINT, self._handle_exit)

    def _handle_exit(self, *args, **kwargs):
        print("exiting dataset generation...")
        self.exiting = True

    def __iter__(self):
        return self

    def load_data(self, dataset_size=None):
        categories = []
        rgb_path = self.folder_path + "/Viewport/rgb"
        instance_path = self.folder_path + "/Viewport/instance"
        bbox2d_path = self.folder_path + "/Viewport/bbox_2d_tight"

        if dataset_size is None:
            dataset_size = len(next(os.walk(rgb_path))[2])

        for i in range(0, dataset_size):
            gt = {}
            rgb_file_path = rgb_path + "/" + str(i) + ".png"
            instance_file_path = instance_path + "/" + str(i) + ".npy"
            bbox2d_file_path = bbox2d_path + "/" + str(i) + ".npy"
            rgb = np.asarray(Image.open(rgb_file_path))
            instance = np.load(instance_file_path, allow_pickle=True)
            bbox2d = np.load(bbox2d_file_path, allow_pickle=True)
            gt["rgb"] = rgb
            gt["boundingBox2DTight"] = bbox2d
            gt["instanceSegmentation"] = instance
            self.gt_all.append(gt)
            for label in bbox2d["semanticLabel"]:
                if label not in categories:
                    categories.append(label)
        self.categories = categories

    def __next__(self):
        # Collect Groundtruth
        gt = self.gt_all[self.cur_idx % len(self.gt_all)]

        # RGB
        # Drop alpha channel
        image = gt["rgb"][..., :3]
        # Cast to tensor if numpy array
        if isinstance(gt["rgb"], np.ndarray):
            image = torch.tensor(image, dtype=torch.float, device="cuda")
        # Normalize between 0. and 1. and change order to channel-first.
        image = image.float() / 255.0
        image = image.permute(2, 0, 1)

        # Bounding Box
        gt_bbox = gt["boundingBox2DTight"]

        # Create mapping from categories to index
        mapping = {cat: i + 1 for i, cat in enumerate(self.categories)}
        bboxes = torch.tensor(gt_bbox[["x_min", "y_min", "x_max", "y_max"]].tolist())
        # For each bounding box, map semantic label to label index
        labels = torch.LongTensor([mapping[bb["semanticLabel"]] for bb in gt_bbox])

        # Calculate bounding box area for each area
        areas = (bboxes[:, 2] - bboxes[:, 0]) * (bboxes[:, 3] - bboxes[:, 1])
        # Idenfiy invalid bounding boxes to filter final output
        valid_areas = (areas > 0.0) * (areas < (image.shape[1] * image.shape[2]))

        # Instance Segmentation
        instance_data = gt["instanceSegmentation"]
        instance_list = [im[0] for im in gt_bbox]
        masks = np.zeros((len(instance_list), *instance_data.shape), dtype=np.bool)
        for i, instances in enumerate(instance_list):
            masks[i] = np.isin(instance_data, instances)
        if isinstance(masks, np.ndarray):
            masks = torch.tensor(masks, device="cuda")

        target = {
            "boxes": bboxes[valid_areas],
            "labels": labels[valid_areas],
            "masks": masks[valid_areas],
            "image_id": torch.LongTensor([self.cur_idx]),
            "area": areas[valid_areas],
            "iscrowd": torch.BoolTensor([False] * len(bboxes[valid_areas])),  # Assume no crowds
        }

        self.cur_idx += 1
        return image, target


async def visualize_data(train_data, train_data_idx=None):
    if train_data_idx is not None:
        train_data.cur_idx = train_data_idx
    plt.ion()
    _, axes = plt.subplots(1, 2, figsize=(10, 5))
    plt.tight_layout()
    # for image, target in self.train_data:
    image, target = train_data.__next__()
    for ax in axes:
        ax.clear()
        ax.axis("off")

    np_image = image.permute(1, 2, 0).cpu().numpy()
    axes[0].imshow(np_image)

    num_instances = len(target["boxes"])
    colours = vis.random_colours(num_instances, enable_random=False)
    overlay = np.zeros_like(np_image)
    for mask, colour in zip(target["masks"].cpu().numpy(), colours):
        overlay[mask, :3] = colour

    axes[1].imshow(overlay)
    mapping = {i + 1: cat for i, cat in enumerate(train_data.categories)}
    labels = [mapping[label.item()] for label in target["labels"]]
    vis.plot_boxes(ax, target["boxes"].tolist(), labels=labels, colours=colours)

    plt.draw()
    plt.savefig(train_data.folder_path + "/dataset.png")
    await omni.kit.app.get_app_interface().next_update_async()
