# Copyright (c) 2020, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.


"""Instance Segmentation Training Demonstration

Use a PyTorch dataloader together with OmniKit to generate scenes and groundtruth to
train a [Mask-RCNN](https://arxiv.org/abs/1703.06870) model.
"""


import omni
import torch
from torch.utils.data import DataLoader
import torchvision
import matplotlib.pyplot as plt
import numpy as np
from omni.isaac.synthetic_utils import visualization as vis

from . import dataset


class Trainer:
    def __init__(self, folder_path, iterations, visualize=True, network="mask_rcnn"):
        self.cur_iter = 0
        self.folder_path = folder_path
        self.iterations = iterations
        self.visualize = visualize
        self.network = network

    async def train(self):
        device = "cuda"

        # Setup data
        self.train_set = dataset.RandomObjects(self.folder_path)
        self.train_set.load_data()
        train_loader = DataLoader(self.train_set, batch_size=2, collate_fn=lambda x: tuple(zip(*x)))

        from omni.isaac.synthetic_utils import visualization as vis

        # Setup Model
        model = None
        if self.network == "mask_rcnn" or self.network == "faster_rcnn":
            # Workaround to avoid SSL Handshake error while downloading models
            # https://github.com/pytorch/pytorch/issues/2271
            from torchvision.models.resnet import model_urls

            model_urls["resnet50"] = model_urls["resnet50"].replace("https://", "http://")
        if self.network == "mask_rcnn":
            model = torchvision.models.detection.maskrcnn_resnet50_fpn(pretrained=False, num_classes=3)
        elif self.network == "faster_rcnn":
            model = torchvision.models.detection.fasterrcnn_resnet50_fpn(pretrained=False, num_classes=3)
        model = model.to(device)
        optimizer = torch.optim.Adam(model.parameters(), lr=0.0001)

        if self.visualize:
            plt.ion()
            self.fig, self.axes = plt.subplots(1, 2, figsize=(14, 7))

        for i, train_batch in enumerate(train_loader):
            self.cur_iter = i
            if i > self.iterations:
                print("Exiting ...")
                break

            model.train()
            images, targets = train_batch
            images = [i.to(device) for i in images]
            targets = [{k: v.to(device) for k, v in t.items()} for t in targets]
            loss_dict = model(images, targets)
            loss = sum(loss for loss in loss_dict.values())

            print(f"ITER {i} | {loss:.6f}")

            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

            if i % 10 == 0:
                model.eval()
                with torch.no_grad():
                    predictions = model(images[:1])

                if self.visualize:
                    if self.network == "mask_rcnn":
                        self.visualize_maskrcnn(predictions, images)
                    elif self.network == "faster_rcnn":
                        self.visualize_fasterrcnn(predictions, images)

            await omni.kit.app.get_app_interface().next_update_async()

    def visualize_maskrcnn(self, predictions, images):
        idx = 0
        score_thresh = 0.5
        mask_thresh = 0.5

        pred = predictions[idx]

        np_image = images[idx].permute(1, 2, 0).cpu().numpy()
        for ax in self.axes:
            self.fig.suptitle(f"Iteration {self.cur_iter:05}", fontsize=14)
            ax.cla()
            ax.axis("off")
            ax.imshow(np_image)
        self.axes[0].set_title("Input")
        self.axes[1].set_title("Input + Predictions")

        score_filter = [i for i in range(len(pred["scores"])) if pred["scores"][i] > score_thresh]
        num_instances = len(score_filter)
        colours = vis.random_colours(num_instances, enable_random=False)

        overlay = np.zeros_like(np_image)
        for mask, colour in zip(pred["masks"], colours):
            overlay[mask.squeeze().cpu().numpy() > mask_thresh, :3] = colour

        self.axes[1].imshow(overlay, alpha=0.5)
        mapping = {i + 1: cat for i, cat in enumerate(self.train_set.categories)}
        labels = [mapping[label.item()] for label in pred["labels"]]
        vis.plot_boxes(self.axes[1], pred["boxes"], labels=labels, colours=colours)

        plt.draw()
        plt.savefig(self.train_set.folder_path + "/train.png")

    def visualize_fasterrcnn(self, predictions, images):
        idx = 0
        score_thresh = 0.5

        pred = predictions[idx]

        np_image = images[idx].permute(1, 2, 0).cpu().numpy()
        for ax in self.axes:
            self.fig.suptitle(f"Iteration {self.cur_iter:05}", fontsize=14)
            ax.cla()
            ax.axis("off")
            ax.imshow(np_image)
        self.axes[0].set_title("Input")
        self.axes[1].set_title("Input + Predictions")

        score_filter = [i for i in range(len(pred["scores"])) if pred["scores"][i] > score_thresh]
        num_instances = len(score_filter)
        colours = vis.random_colours(num_instances, enable_random=False)

        mapping = {i + 1: cat for i, cat in enumerate(self.train_set.categories)}
        labels = [mapping[label.item()] for label in pred["labels"]]
        vis.plot_boxes(self.axes[1], pred["boxes"], labels=labels, colours=colours)

        plt.draw()
        plt.savefig(self.train_set.folder_path + "/train.png")
