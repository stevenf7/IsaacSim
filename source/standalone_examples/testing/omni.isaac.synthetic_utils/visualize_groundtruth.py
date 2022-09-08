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

import copy
import os
import omni
import random
import numpy as np
import matplotlib.pyplot as plt
from omni.isaac.kit import SimulationApp

TRANSLATION_RANGE = 3.0  # meters
NUM_PLOTS = 5

ENABLE_PHYSICS = True
GLASS_MATERIAL = True

simulation_app = SimulationApp({"renderer": "RayTracedLighting", "headless": True})

from omni.isaac.core.objects import DynamicCuboid, DynamicSphere
from omni.isaac.core.materials import OmniGlass, PreviewSurface
from omni.isaac.core.utils.viewports import set_camera_view
from omni.isaac.core.utils.semantics import add_update_semantics
from omni.isaac.core.utils.stage import is_stage_loading
from omni.isaac.core import World

from omni.isaac.synthetic_utils import SyntheticDataHelper
from omni.syntheticdata import visualize, helpers
from omni.kit.viewport.utility import get_active_viewport

from pxr import Sdf, UsdLux

the_world = World()
the_world.reset()

set_camera_view(eye=np.array([7, 7, 2]), target=np.array([0, 0, 0.5]))

# Add a distant light
light_prim = UsdLux.DistantLight.Define(the_world.scene.stage, Sdf.Path("/DistantLight"))
light_prim.CreateIntensityAttr(500)

if ENABLE_PHYSICS:
    # Create a ground plane
    the_world.scene.add_ground_plane(size=1000, color=np.array([1, 1, 1]))

# Create 10 randomly positioned coloured spheres and cubes
# We will assign each a semantic label based on their shape (sphere/cube)
prims = []
path_root = "/World/"
name_prefix = "prim"
for i in range(10):
    prim_type = random.choice(["Cube", "Sphere"])
    name = name_prefix + str(i)
    path = path_root + name
    core_prim = DynamicCuboid(path, name) if prim_type == "Cube" else DynamicSphere(path, name)
    prims.append(core_prim)

    translation = np.random.rand(3) * TRANSLATION_RANGE
    color = np.random.rand(3)

    if GLASS_MATERIAL:
        material = OmniGlass(
            path + "/" + name + "_glass", name=name + "_glass", ior=1.25, depth=0.001, thin_walled=False, color=color
        )
    else:
        material = PreviewSurface(path + "/" + name + "_mat", name=name + "_mat", color=color)

    core_prim.set_world_pose(translation)
    core_prim.apply_visual_material(material)

    add_update_semantics(core_prim.prim, prim_type)

    the_world.scene.add(core_prim)

print("Waiting until all materials are loaded")
while is_stage_loading():
    simulation_app.app.update()

viewport_api = get_active_viewport()

sd_helper = SyntheticDataHelper()
sensor_names = [
    "rgb",
    "depth",
    "boundingBox2DTight",
    "boundingBox2DLoose",
    "instanceSegmentation",
    "semanticSegmentation",
    "boundingBox3D",
    "camera",
    "pose",
]

# # initialize sensors first as it can take several frames before they are ready
sd_helper.initialize(sensor_names, viewport_api)


def make_plots(gt, name_suffix=""):
    # GROUNDTRUTH VISUALIZATION
    # Setup a figure
    _, axes = plt.subplots(2, 4, figsize=(20, 7))
    axes = axes.flat
    for ax in axes:
        ax.axis("off")

    # RGB
    axes[0].set_title("RGB")
    for ax in axes[:-1]:
        ax.imshow(gt["rgb"])

    # DEPTH
    axes[1].set_title("Depth")
    depth_data = np.clip(gt["depth"], 0, 255)
    axes[1].imshow(visualize.colorize_distance(depth_data.squeeze()))

    # BBOX2D TIGHT
    axes[2].set_title("BBox 2D Tight")
    rgb_data = copy.deepcopy(gt["rgb"])
    axes[2].imshow(visualize.colorize_bboxes(gt["boundingBox2DTight"], rgb_data))

    # BBOX2D LOOSE
    axes[3].set_title("BBox 2D Loose")
    rgb_data = copy.deepcopy(gt["rgb"])
    axes[3].imshow(visualize.colorize_bboxes(gt["boundingBox2DLoose"], rgb_data))

    # INSTANCE SEGMENTATION
    axes[4].set_title("Instance Segmentation")
    instance_seg = gt["instanceSegmentation"][0]
    instance_rgb = visualize.colorize_segmentation(instance_seg)
    axes[4].imshow(instance_rgb, alpha=1.0)

    # SEMANTIC SEGMENTATION
    axes[5].set_title("Semantic Segmentation")
    semantic_seg = gt["semanticSegmentation"]
    semantic_rgb = visualize.colorize_segmentation(semantic_seg)
    axes[5].imshow(semantic_rgb, alpha=1.0)

    # BBOX 3D
    axes[6].set_title("BBox 3D")
    bbox_3d_data = gt["boundingBox3D"]
    bboxes_3d_corners = bbox_3d_data["corners"]
    projected_corners = helpers.world_to_image(bboxes_3d_corners.reshape(-1, 3), viewport_api)
    projected_corners = projected_corners.reshape(-1, 8, 3)
    rgb_data = copy.deepcopy(gt["rgb"])
    bboxes3D_rgb = visualize.colorize_bboxes_3d(projected_corners, rgb_data)
    axes[6].imshow(bboxes3D_rgb)

    # Save figure
    print("saving figure to: ", os.getcwd() + "/visualize_groundtruth" + name_suffix + ".png")
    plt.savefig("visualize_groundtruth" + name_suffix + ".png")

    # Display camera parameters
    print("Camera Parameters")
    print("==================")
    print(gt["camera"])
    # Display poses of semantically labelled assets
    print("Object Pose")
    print("============")
    print(gt["pose"])


for i in range(NUM_PLOTS):
    if ENABLE_PHYSICS:
        # start simulation
        the_world.play()

        # Step simulation so that objects fall to rest
        print("simulating physics...")
        for frame in range(60):
            the_world.step(render=False)
        print("done")
        # the_world.pause()

    the_world.render()
    gt = sd_helper.get_groundtruth(sensor_names, viewport_api, verify_sensor_init=False)
    make_plots(gt, name_suffix=str(i))

    for core_prim in prims:
        translation = np.random.rand(3) * TRANSLATION_RANGE
        color = np.random.rand(3)

        core_prim.set_world_pose(translation)
        core_prim.get_applied_visual_material().set_color(color)

# cleanup
the_world.stop()
simulation_app.close()
