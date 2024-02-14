# Copyright (c) 2024, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

import argparse

parser = argparse.ArgumentParser()
parser.add_argument("-n", "--num-cameras", type=int, default=1, help="Number of cameras")
parser.add_argument(
    "--resolution", nargs=2, type=int, default=[1280, 720], help="Camera resolution as [width, height] px"
)
parser.add_argument("--num-gpus", type=int, default=1, help="Number of GPUs on machine.")
args, unknown = parser.parse_known_args()

n_camera = args.num_cameras
resolution = args.resolution
n_gpu = args.num_gpus

import numpy as np
from isaac_sim import SimulationApp

simulation_app = SimulationApp({"headless": True})

TEST_NUM_APP_UPDATES = 60 * 10

import omni
from omni.isaac.core.utils.extensions import enable_extension
from omni.isaac.core.utils.rotations import euler_angles_to_quat
from omni.isaac.core.utils.stage import is_stage_loading
from omni.isaac.sensor import Camera
from omni.kit.viewport.utility import get_active_viewport

enable_extension("omni.isaac.benchmark.services")
from omni.isaac.benchmark.services import base_isaac_benchmark

# Create the benchmark
benchmark = base_isaac_benchmark.BaseIsaacBenchmark(
    benchmark_name=f"cameras_{n_camera}_resolution_{resolution[0]}_{resolution[1]}_gpu_{n_gpu}"
)
benchmark.set_phase("loading")
benchmark.start_runtime()

scene_path = "/Isaac/Environments/Simple_Warehouse/full_warehouse.usd"
benchmark.fully_load_stage(benchmark.assets_root_path + scene_path)

timeline = omni.timeline.get_timeline_interface()
timeline.play()
cameras = []

for i in range(n_camera):
    render_product_path = None
    if i == 0:
        viewport_api = get_active_viewport()
        render_product_path = viewport_api.get_render_product_path()
    cameras.append(
        Camera(
            prim_path="/Cameras/Camera_" + str(i),
            position=np.array([-8, 13, 2.0]),
            resolution=resolution,
            orientation=euler_angles_to_quat([90, 0, 90 + i * 360 / n_camera], degrees=True),
            render_product_path=render_product_path,
        )
    )

    omni.kit.app.get_app().update()
    cameras[i].initialize()

# make sure scene is loaded in all viewports
while is_stage_loading():
    print("asset still loading, waiting to finish")
    omni.kit.app.get_app().update()
omni.kit.app.get_app().update()

benchmark.stop_runtime()
benchmark.store_measurements()

# perform benchmark
benchmark.set_phase("benchmark")
benchmark.start_collecting_frametime()

for _ in range(1 if benchmark.test_mode else TEST_NUM_APP_UPDATES):
    omni.kit.app.get_app().update()

benchmark.stop_collecting_frametime()
benchmark.store_measurements()
benchmark.stop()

timeline.stop()
cameras = None
