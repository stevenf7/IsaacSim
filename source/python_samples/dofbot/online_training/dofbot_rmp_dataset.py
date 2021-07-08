# Copyright (c) 2020, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.


"""Cube Dataset with online randomized scene generation for Bounding Box Detection training.

Use OmniKit to generate a simple scene. At each iteration, the scene is populated by
creating a cube that rests on a plane. The cube pose, colours and textures are randomized. 
The camera position is also randomized using RMP, where a specified gripper position acts as the RMP target 
The groundtruth is then captured, consisting of an RGB rendered image, and Tight 2D Bounding Boxes 
"""

from math import floor
import os
import torch
import random
import numpy as np
import signal

import carb
from omni.isaac.python_app import OmniKitHelper

# Default rendering parameters
RENDER_CONFIG = {
    "renderer": "PathTracing",
    "samples_per_pixel_per_frame": 12,
    "experience": f'{os.environ["EXP_PATH"]}/omni.isaac.sim.python.kit',
    "headless": False,
    "width": 640,
    "height": 480,
}


class RandomObjects(torch.utils.data.IterableDataset):
    """Dataset of cube + distractor objects - domain randomize position/colour/texture/lighting/camera angle
    The RGB image and BoundingBox are captured by moving a camera aimed at the centre of the scene
    which is positioned at random but at a fixed distance from the centre. 
    """

    def __init__(self):
        self.kit = OmniKitHelper(config=RENDER_CONFIG)
        import omni
        from omni.isaac.samples.scripts.dofbot_rmp_sample.sample import RMPSample

        self.stage = self.kit.get_stage()

        # Instantiate RMPSample
        self.sample = RMPSample()

        # Equivalent to _on_window()
        self.sample.create_robot()
        self.sample.setup_world()
        self.viewport = omni.kit.viewport.get_default_viewport_window()
        self.viewport.set_camera_position("/OmniverseKit_Persp", 142, -127, 56, True)
        self.viewport.set_camera_target("/OmniverseKit_Persp", -180, 234, -27, True)

        # Start the timeline, subscribe physics step
        self.kit.play()
        handle = omni.physx.acquire_physx_interface().subscribe_physics_step_events(self._on_simulation_step)
        print(handle)
        while self.kit.is_loading():
            self.kit.update()
        print("Timeline started---------------------------")

        # Load for a bit
        frame = 0
        while frame < 60 or self.kit.is_loading():
            self.kit.update()
            frame = frame + 1

        # Training Variables
        self.iter_counter = 0
        self.curr_image = None
        self.curr_target = None
        self.device = "cuda"
        self.categories = ["None", "Cube", "Sphere", "Cone"]
        self.counter = 0

    def _on_simulation_step(self, step):
        self.sample.step(1)

    def process_groundtruth(self, gt):
        import torch

        # RGB
        image = gt["rgb"][..., :3]  # Drop alpha channel
        if isinstance(gt["rgb"], np.ndarray):
            image = torch.tensor(image, dtype=torch.float, device="cuda")  # Cast to tensor if numpy array
        image = image.float() / 255.0  # Normalize between 0. and 1. and change order to channel-first.
        image = image.permute(2, 0, 1)

        # 2D Bounding Boxes
        gt_bbox = gt["boundingBox2DTight"]
        categories = ["None", "Cube", "Sphere", "Cone"]
        mapping = {cat: i + 1 for i, cat in enumerate(categories)}
        bboxes = torch.tensor(gt_bbox[["x_min", "y_min", "x_max", "y_max"]].tolist())
        labels = torch.LongTensor([mapping[bb["semanticLabel"]] for bb in gt_bbox])

        # If no objects present in view
        if bboxes.nelement() == 0:
            target = {
                "boxes": torch.zeros((0, 4), dtype=torch.float32),
                "labels": torch.tensor([1], dtype=torch.int64),
                "image_id": torch.LongTensor([self.iter_counter]),
                "area": torch.tensor(0, dtype=torch.float32),
                "iscrowd": torch.zeros((0,), dtype=torch.int64),
            }

        else:
            # Calculate bounding box area for each area
            areas = (bboxes[:, 2] - bboxes[:, 0]) * (bboxes[:, 3] - bboxes[:, 1])
            # Identify invalid bounding boxes to filter final output
            valid_areas = (areas > 0.0) * (areas < (image.shape[1] * image.shape[2]))
            target = {
                "boxes": bboxes[valid_areas],
                "labels": labels[valid_areas],
                "image_id": torch.LongTensor([self.iter_counter]),
                "area": areas[valid_areas],
                "iscrowd": torch.BoolTensor([False] * len(bboxes[valid_areas])),  # Assume no crowds
            }
        return image, target

    # ITERATION----------------------------------------------
    def __iter__(self):
        return self

    def __next__(self):
        print("next!------------------------------")
        # Update for 20 steps before collecting groundtruth
        self.sample.populate_scene()
        while self.counter % 20 != 0 or self.kit.is_loading():
            self.counter += 1
            self.kit.update()
        self.iter_counter += 1
        curr_gt = self.sample.collect_groundtruth()
        self.curr_image, self.curr_target = self.process_groundtruth(curr_gt)

        return self.curr_image, self.curr_target


if __name__ == "__main__":
    "Typical usage"
    import matplotlib.pyplot as plt

    dataset = RandomObjects()

    from omni.isaac.synthetic_utils import visualization as vis

    _, axes = plt.subplots(1, 2, figsize=(10, 5))
    plt.tight_layout()
    count = 0

    for image, target in dataset:
        np_image = image.permute(1, 2, 0).cpu().numpy()
        for ax in axes:
            ax.clear()
            ax.axis("off")
            ax.imshow(np_image)

        num_instances = len(target["boxes"])
        colours = vis.random_colours(num_instances, enable_random=False)

        categories = ["None", "Cube", "Sphere", "Cone"]
        mapping = {i + 1: cat for i, cat in enumerate(categories)}
        labels = [mapping[label.item()] for label in target["labels"]]
        vis.plot_boxes(ax, target["boxes"].tolist(), labels=labels, colours=colours)

        plt.draw()
        plt.savefig("dataset.png")

    # cleanup
    dataset.kit.stop()
    dataset.kit.shutdown()
