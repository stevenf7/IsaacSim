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
parser.add_argument("-n", "--n-sensor", type=int, default=1, help="Number of sensors")
parser.add_argument("--num-gpus", type=int, default=1, help="Number of GPUs on machine.")
args, unknown = parser.parse_known_args()

n_sensor = args.n_sensor
n_gpu = args.num_gpus

from isaacsim import SimulationApp

simulation_app = SimulationApp({"headless": True})

TEST_NUM_APP_UPDATES = 60 * 10

import omni
import omni.replicator.core as rep
from omni.isaac.core.utils.extensions import enable_extension
from omni.isaac.core.utils.prims import delete_prim
from pxr import Gf

enable_extension("omni.isaac.benchmark.services")
from omni.isaac.benchmark.services import base_isaac_benchmark

# Create the benchmark
benchmark = base_isaac_benchmark.BaseIsaacBenchmark(
    benchmark_name="benchmark_rtx_lidar",
    workflow_metadata={
        "metadata": [
            {"name": "num_3d_lidars", "data": n_sensor},
            {"name": "num_gpus", "data": n_gpu},
        ]
    },
)
benchmark.set_phase("loading")

scene_path = "/Isaac/Environments/Simple_Warehouse/full_warehouse.usd"
benchmark.fully_load_stage(benchmark.assets_root_path + scene_path)
timeline = omni.timeline.get_timeline_interface()
hydra_textures = []
writers = []
sensors = []
for i in range(n_sensor):
    lidar_type = "Rotary"
    if i % 2:
        lidar_type = "Solid_State"
    lidar_path = "/World/Rtx" + lidar_type + "Lidar_" + str(i)
    sensor_translation = Gf.Vec3f([-8, 13 + i * 2.0, 2.0])  # these positions are used for full_warehouse.usd
    # make sure to test rotary and solid state together.
    lidar_config = "Example_" + lidar_type

    _, sensor = omni.kit.commands.execute(
        "IsaacSensorCreateRtxLidar",
        path=lidar_path,
        parent=None,
        config=lidar_config,
        translation=sensor_translation,
        orientation=Gf.Quatd(1.0, 0.0, 0.0, 0.0),  # Gf.Quatd is w,i,j,k
    )
    sensors.append(sensor)
    hydra_texture = rep.create.render_product(sensor.GetPath(), [1, 1], name="Isaac")
    hydra_textures.append(hydra_texture)
    # Create the post process graph that publishes the render var
    writer = rep.writers.get("Writer" + "IsaacPrintRTXLidarInfo")
    writer.initialize(testMode=True)
    writer.attach([hydra_texture])
    writers.append(writer)

    omni.kit.app.get_app().update()

benchmark.store_measurements()

benchmark.set_phase("benchmark")
timeline.play()

for _ in range(1 if benchmark.test_mode else TEST_NUM_APP_UPDATES):
    omni.kit.app.get_app().update()

benchmark.store_measurements()
benchmark.stop()

timeline.stop()

for writer in writers:
    writer.detach()
omni.kit.app.get_app().update()

for sensor in sensors:
    delete_prim(sensor.GetPath())
omni.kit.app.get_app().update()

for texture in hydra_textures:
    texture = None
omni.kit.app.get_app().update()
