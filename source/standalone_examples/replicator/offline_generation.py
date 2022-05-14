# Copyright (c) 2022, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.


"""Generate offline synthetic dataset
"""
from omni.isaac.kit import SimulationApp

# Set rendering parameters and create an instance of kit
CONFIG = {"renderer": "RayTracedLighting", "headless": True, "width": 1024, "height": 1024, "num_frames": 10}
STAGE = "/Samples/Synthetic_Data/Stage/warehouse_with_sensors.usd"
print("Creating Kit")
kit = SimulationApp(launch_config=CONFIG)


import carb
from omni.isaac.core.utils.nucleus import get_assets_root_path

# Find the Isaac asset server
def prefix_with_isaac_asset_server(relative_path):
    assets_root_path = get_assets_root_path()
    if assets_root_path is None:
        carb.log_error("Could not find Isaac Sim assets folder")
        return
    return assets_root_path + relative_path


# we will be using the replicator library
import omni.replicator.core as rep

# This allows us to run replicator, which will update the random
# parameters and save out the data for as many frames as listed
def run_orchestrator():
    rep.orchestrator.run()

    # Wait until started
    while not rep.orchestrator.get_is_started():
        kit.update()

    # Wait until stopped
    while rep.orchestrator.get_is_started():
        kit.update()

    rep.BackendDispatch.wait_until_done()


with rep.new_layer():
    print("Loading Stage")
    env = rep.create.from_usd(prefix_with_isaac_asset_server(STAGE))

    # In the original scene, we want to use /World/Camera/RandomCamera
    # When we pull in with replicator we get /Replicator/Ref/Camera/RandomCamera
    # Searching for just the camera name will give us the one we want.
    # box_to_look_at = rep.get.prims(path_pattern="SmallKLT_Visual_150")
    camera = rep.create.camera(
        position=(0.360693, 3.8932, 2.63715), look_at="/Replicator/Ref/warehouse/KLT_Bins/SmallKLT_Visual_150"
    )
    render_product = rep.create.render_product(camera, (CONFIG["width"], CONFIG["height"]))

    with rep.trigger.on_frame(num_frames=CONFIG["num_frames"]):
        with camera:
            rep.modify.pose(position=rep.distribution.uniform((-4.00, -11.60, 1.00), (6.00, 15.40, 5.00)))

    # Initialize and attach writer
    writer = rep.WriterRegistry.get("BasicWriter")

    writer.initialize(
        output_dir="_output_headles",
        rgb=True,
        bounding_box_2d_tight=True,
        bounding_box_2d_loose=True,
        semantic_segmentation=True,
        instance_segmentation=True,
        distance_to_camera=True,
        distance_to_image_plane=True,
        bounding_box_3d=True,
        occlusion=True,
        normals=True,
        motion_vectors=True,
    )

    writer.attach([render_product])
    run_orchestrator()

print("closing kit")
kit.close()
print("done")
