#!/usr/bin/env python
# Copyright (c) 2020, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.


"""Demonstration of using OmniKit to generate a scene, collect groundtruth and visualize
the results.
"""

import os
import random
import numpy as np
from pxr import UsdGeom, Semantics
from omni.isaac.synthetic_utils import OmniKitHelper
from omni.isaac.synthetic_utils import visualization as vis
from omni.isaac.synthetic_utils import camera
from omni.isaac.synthetic_utils import SyntheticDataHelper
from omni.isaac.synthetic_utils import utils as ut
import matplotlib.pyplot as plt


TRANSLATION_RANGE = 300.0
SCALE = 50.0


def main():
    kit = OmniKitHelper(
        {"renderer": "RayTracedLighting", "experience": f'{os.environ["EXP_PATH"]}/isaac-sim-python.json'}
    )
    sd_helper = SyntheticDataHelper()

    # SCENE SETUP
    # Get the current stage
    stage = kit.get_stage()

    # Add a distant light
    stage.DefinePrim("/World/Light", "DistantLight")

    # Create 10 randomly positioned and coloured spheres and cube
    # We will assign each a semantic label based on their shape (sphere/cube)
    for i in range(10):
        prim_type = random.choice(["Cube", "Sphere"])
        prim = stage.DefinePrim(f"/World/cube{i}", prim_type)
        translation = np.random.rand(3) * TRANSLATION_RANGE
        UsdGeom.XformCommonAPI(prim).SetTranslate(translation.tolist())
        UsdGeom.XformCommonAPI(prim).SetScale((SCALE, SCALE, SCALE))
        prim.GetAttribute("primvars:displayColor").Set([np.random.rand(3).tolist()])

        # Add semantic label based on prim type
        sem = Semantics.SemanticsAPI.Apply(prim, "Semantics")
        sem.CreateSemanticTypeAttr()
        sem.CreateSemanticDataAttr()
        sem.GetSemanticTypeAttr().Set("class")
        sem.GetSemanticDataAttr().Set(prim_type)

    # Get groundtruth
    gt = sd_helper.get_groundtruth(
        [
            "rgb",
            "depth",
            "boundingBox2DTight",
            "boundingBox2DLoose",
            "instanceSegmentation",
            "semanticSegmentation",
            "boundingBox3D",
            "camera",
        ]
    )

    # GROUNDTRUTH VISUALIZATION

    # Setup a figure
    _, axes = plt.subplots(2, 4, figsize=(20, 7))
    axes = axes.flat
    for ax in axes:
        ax.axis("off")

    # RGB
    axes[0].set_title("RGB")
    for ax in axes[:-1]:
        ax.imshow(ut.to_numpy(gt["rgb"]))

    # DEPTH
    axes[1].set_title("Depth")
    axes[1].imshow(ut.to_numpy(gt["depth"]))

    # BBOX2D TIGHT
    random.seed(1)
    axes[2].set_title("BBox 2D Tight")
    bboxes = gt["boundingBox2DTight"][["x_min", "y_min", "x_max", "y_max"]]
    labels = gt["boundingBox2DTight"]["semanticLabel"]
    label_ids = gt["boundingBox2DTight"]["semanticId"]
    label_colours = vis.random_colours(max(label_ids) + 1)
    colours = [label_colours[label_id] for label_id in label_ids]
    vis.plot_boxes(axes[2], bboxes, labels=labels, colours=colours)

    # BBOX2D LOOSE
    random.seed(1)
    axes[3].set_title("BBox 2D Loose")
    bboxes = gt["boundingBox2DLoose"][["x_min", "y_min", "x_max", "y_max"]]
    labels = gt["boundingBox2DLoose"]["semanticLabel"]
    label_ids = gt["boundingBox2DLoose"]["semanticId"]
    label_colours = vis.random_colours(max(label_ids) + 1)
    colours = [label_colours[label_id] for label_id in label_ids]
    vis.plot_boxes(axes[3], bboxes, labels=labels, colours=colours)

    # INSTANCE SEGMENTATION
    random.seed(1)
    axes[4].set_title("Instance Segmentation")
    _, instance_seg = gt["instanceSegmentation"]
    instance_rgb = vis.instance_segmentation_to_rgb(ut.to_numpy(instance_seg))
    axes[4].imshow(instance_rgb, alpha=0.7)

    # SEMANTIC SEGMENTATION
    random.seed(1)
    axes[5].set_title("Semantic Segmentation")
    _, semantic_seg = gt["semanticSegmentation"]
    semantic_rgb = vis.semantic_segmentation_to_rgb(ut.to_numpy(semantic_seg))
    axes[5].imshow(semantic_rgb, alpha=0.7)

    # BBOX 3D
    axes[6].set_title("BBox 3D")

    width = gt["camera"]["resolution"]["width"]
    height = gt["camera"]["resolution"]["height"]
    view_proj_mat = gt["camera"]["view_projection_matrix"]
    points = gt["boundingBox3D"].reshape(-1, 3)
    projected = camera.project_points(view_proj_mat, points)[..., :2] * np.array([[width, height]])

    face_idx_list = [[0, 1, 3, 2], [4, 5, 7, 6], [2, 3, 7, 6], [0, 1, 5, 4], [0, 2, 6, 4], [1, 3, 7, 5]]
    colours = vis.random_colours(len(face_idx_list))
    for p in projected.reshape(-1, 8, 2):
        for face_idxs, colour in zip(face_idx_list, colours):
            face = plt.Polygon(p[face_idxs], alpha=0.3, color=colour)
            axes[6].add_patch(face)

    # Display figure
    plt.tight_layout()
    plt.show()
    plt.savefig("out.png")


if __name__ == "__main__":
    main()
