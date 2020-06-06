#!/usr/bin/env python
# Copyright (c) 2020, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.


import random
import colorsys
import numpy as np
import matplotlib.pyplot as plt


def random_colours(N):
    """
    Generate random colors.
    Generate visually distinct colours by linearly spacing the hue 
    channel in HSV space and then convert to RGB space.
    """
    start = random.random()
    hues = [(start + i / N) % 1.0 for i in range(N)]
    colours = [colorsys.hsv_to_rgb(h, 0.9, 1.0) for i, h in enumerate(hues)]
    random.shuffle(colours)
    return colours


def plot_boxes(ax, bboxes, labels, label_size=0):
    colours = random_colours(len(set(labels)))
    colour_mapping = {label: colours[i] for i, label in enumerate(set(labels))}
    for bb, label in zip(bboxes, labels):
        x = bb[0]
        y = bb[1]
        w = bb[2] - x
        h = bb[3] - y
        box = plt.Rectangle((x, y), w, h, fill=False, edgecolor=colour_mapping[label])
        ax.add_patch(box)
        if label_size > 0:
            font = {"family": "sans-serif", "color": colour_mapping[label], "size": 10}
            ax.text(bb[0], bb[1], label, font_dict=font)


def instance_segmentation_to_rgb(instance_segmentation):
    num_instance, height, width = instance_segmentation.shape
    colours = random_colours(num_instance)

    instance_rgb = np.zeros((height, width, 3))
    for mask, colour in zip(instance_segmentation, colours):
        instance_rgb[mask] = colour
    return instance_rgb


def semantic_segmentation_to_rgb(semantic_segmentation):
    num_labels, height, width = semantic_segmentation.shape
    colours = random_colours(num_labels)
    semantic_rgb = np.zeros((height, width, 3))
    for mask, colour in zip(semantic_segmentation, colours):
        semantic_rgb[mask] = colour
    return semantic_rgb
