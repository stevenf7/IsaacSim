# Copyright (c) 2023, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

"""Generate augmented synthetic data from annotators
"""

from omni.isaac.kit import SimulationApp

simulation_app = SimulationApp(launch_config={"headless": False})

import argparse
import os
import time

import carb.settings
import numpy as np
import omni.replicator.core as rep
import warp as wp
from omni.isaac.core.utils.nucleus import get_assets_root_path
from omni.isaac.core.utils.stage import open_stage
from PIL import Image

parser = argparse.ArgumentParser()
parser.add_argument("--num_frames", type=int, default=25, help="The number of frames to capture")
parser.add_argument("--use_warp", action="store_true", help="Use warp augmentations instead of numpy")
args, unknown = parser.parse_known_args()

NUM_FRAMES = args.num_frames
USE_WARP = args.use_warp
ENV_URL = "/Isaac/Environments/Grid/default_environment.usd"

# Enable scripts
carb.settings.get_settings().set_bool("/app/omni.graph.scriptnode/opt_in", True)


# Illustrative augmentation switching red and blue channels in rgb data using numpy (CPU) and warp (GPU)
def rgb_to_bgr_np(data_in):
    data_in[:, :, [0, 2]] = data_in[:, :, [2, 0]]
    return data_in


@wp.kernel
def rgb_to_bgr_wp(data_in: wp.array3d(dtype=wp.uint8), data_out: wp.array3d(dtype=wp.uint8)):
    i, j = wp.tid()
    data_out[i, j, 0] = data_in[i, j, 2]
    data_out[i, j, 1] = data_in[i, j, 1]
    data_out[i, j, 2] = data_in[i, j, 0]
    data_out[i, j, 3] = data_in[i, j, 3]


# Gaussian noise augmentation on depth data in numpy (CPU) and warp (GPU)
def gaussian_noise_depth_np(data_in, sigma: float, seed: int):
    np.random.seed(seed)
    return data_in + np.random.randn(*data_in.shape) * sigma


rep.AnnotatorRegistry.register_augmentation(
    "gn_depth_np_sigma_v1", rep.Augmentation.from_function(gaussian_noise_depth_np, sigma=0.01, seed=None)
)

rep.AnnotatorRegistry.register_augmentation(
    "gn_depth_np_sigma_v2", rep.Augmentation.from_function(gaussian_noise_depth_np, sigma=0.25, seed=None)
)

# TODO cannot use wp.float32 (OM-104909)
@wp.kernel
def gaussian_noise_depth_wp(
    data_in: wp.array2d(dtype=wp.uint8), data_out: wp.array2d(dtype=wp.uint8), sigma: float, seed: int
):
    i, j = wp.tid()
    state = wp.rand_init(seed, wp.tid())
    # data_out[i, j] = data_in[i, j] + sigma * wp.randn(state)
    data_out[i, j] = data_in[i, j]


rep.AnnotatorRegistry.register_augmentation(
    "gn_depth_wp_sigma_v1", rep.Augmentation.from_function(gaussian_noise_depth_wp, sigma=0.01, seed=None)
)

rep.AnnotatorRegistry.register_augmentation(
    "gn_depth_wp_sigma_v2", rep.Augmentation.from_function(gaussian_noise_depth_wp, sigma=0.25, seed=None)
)

# Helper functions for writing images from annotator data
def write_rgb(data, path):
    rgb_img = Image.fromarray(data, mode="RGBA")
    rgb_img.save(path + ".png")


def write_depth(data, path):
    # Normalize, handle any nan values, and convert to from float32 to 8-bit int array
    normalized_array = (data - np.min(data)) / (np.max(data) - np.min(data))
    normalized_array = np.nan_to_num(normalized_array)
    integer_array = (normalized_array * 255).astype(np.uint8)
    depth_img = Image.fromarray(integer_array, mode="L")
    depth_img.save(path + ".png")


# Setup the environment and update the app a couple of times to fully load texture/materials
assets_root_path = get_assets_root_path()
open_stage(assets_root_path + ENV_URL)
for _ in range(10):
    simulation_app.update()

# Disable capture on play and async rendering
carb.settings.get_settings().set("/omni/replicator/captureOnPlay", False)
carb.settings.get_settings().set("/omni/replicator/asyncRendering", False)
carb.settings.get_settings().set("/app/asyncRendering", False)

# Create a red cube and a render product from a camera looking at the cube from the top
red_mat = rep.create.material_omnipbr(diffuse=(1, 0, 0))
red_cube = rep.create.cube(position=(0, 0, 0.71), material=red_mat)
cam = rep.create.camera(position=(0, 0, 5), look_at=(0, 0, 0))
rp = rep.create.render_product(cam, (512, 512))

# Get the local augmentations, either from function or from the registry
rgb_to_bgr_augm = None
gn_depth_augm_1 = None
gn_depth_augm_2 = None
if USE_WARP:
    rgb_to_bgr_augm = rep.Augmentation.from_function(rgb_to_bgr_wp)
    gn_depth_augm_1 = rep.AnnotatorRegistry.get_augmentation("gn_depth_wp_sigma_v1")
    gn_depth_augm_2 = rep.AnnotatorRegistry.get_augmentation("gn_depth_wp_sigma_v2")
else:
    rgb_to_bgr_augm = rep.Augmentation.from_function(rgb_to_bgr_np)
    gn_depth_augm_1 = rep.AnnotatorRegistry.get_augmentation("gn_depth_np_sigma_v1")
    gn_depth_augm_2 = rep.AnnotatorRegistry.get_augmentation("gn_depth_np_sigma_v2")


# Output directories
out_dir = os.path.join(os.getcwd(), "_out_augm_annot")
os.makedirs(out_dir, exist_ok=True)

# Register the annotator together with its augmentation
rep.annotators.register(
    name="rgb_to_bgr_augm",
    annotator=rep.annotators.augment(
        source_annotator=rep.AnnotatorRegistry.get_annotator("rgb"),
        augmentation=rgb_to_bgr_augm,
    ),
)

rgb_to_bgr_annot = rep.AnnotatorRegistry.get_annotator("rgb_to_bgr_augm")
depth_annot_1 = rep.AnnotatorRegistry.get_annotator("distance_to_camera")
depth_annot_1.augment(gn_depth_augm_1)
depth_annot_2 = rep.AnnotatorRegistry.get_annotator("distance_to_camera")
depth_annot_2.augment(gn_depth_augm_2)

rgb_to_bgr_annot.attach([rp])
depth_annot_1.attach([rp])
depth_annot_2.attach([rp])


# Generate a replicator graph causing the cube to rotate every frame capture
with rep.trigger.on_frame():
    with red_cube:
        rep.randomizer.rotation()

# Evaluate the graph
rep.orchestrator.preview()

# Measure the duration of capturing the data
start_time = time.time()

# The `step()` function will trigger the randomization graph, feed annotators with new data, and trigger the writers
for i in range(NUM_FRAMES):
    rep.orchestrator.step()
    rgb_data = rgb_to_bgr_annot.get_data()
    depth_data_1 = depth_annot_1.get_data()
    depth_data_2 = depth_annot_2.get_data()
    write_rgb(rgb_data, os.path.join(out_dir, f"annot_rgb_{i}"))
    write_depth(depth_data_1, os.path.join(out_dir, f"annot_depth_{i}_v1"))
    write_depth(depth_data_2, os.path.join(out_dir, f"annot_depth_{i}_v2"))

print(
    f"The duration for capturing {NUM_FRAMES} frames using '{'warp' if USE_WARP else 'numpy'}' was: {time.time() - start_time:.4f} seconds, with an average of {(time.time() - start_time) / NUM_FRAMES:.4f} seconds per frame."
)

simulation_app.close()
