# Copyright (c) 2018-2022, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#


import omni.kit.test
import os
import time
import shutil
from omni.isaac.core.utils.stage import create_new_stage_async
from omni.isaac.core.utils.stage import open_stage_async
from omni.isaac.core.utils.nucleus import get_assets_root_path

import omni.replicator.core as rep

from ..utils.base_isaac_benchmark import BaseIsaacBenchmark

STAGE = "/Isaac/Samples/Replicator/Stage/full_warehouse_worker_and_anim_cameras.usd"
LOOK_AT_PRIM_PATH = "/Root/SM_CardBoxA_3"
TEST_NUM_RENDER_PRODUCTS = [1, 2]
TEST_RESOLUTIONS = [(32, 32), (128, 128)]
TEST_NUM_FRAMES = 10
TEST_RESOLUTION = (128, 128)
TEST_NUM_APP_UPDATES = 60 * 10
ALL_ANNOTATORS = {
    "rgb": True,
    "bounding_box_2d_tight": True,
    "bounding_box_2d_loose": True,
    "semantic_segmentation": True,
    "colorize_semantic_segmentation": True,
    "instance_id_segmentation": True,
    "colorize_instance_id_segmentation": True,
    "instance_segmentation": True,
    "colorize_instance_segmentation": True,
    "distance_to_camera": True,
    "distance_to_image_plane": True,
    "bounding_box_3d": True,
    "occlusion": True,
    "normals": True,
    "motion_vectors": True,
    "camera_params": True,
    "pointcloud": True,
    "pointcloud_include_unlabelled": True,
    "skeleton_data": True,
}


# Update the app until the materials and textures are fully loaded (stop once the frame update times become small)
async def wait_until_stage_is_fully_loaded_async():
    # 4/5 frames are usually needed to load materials/textures
    frame_start = time.time()
    for i in range(10):
        await omni.kit.app.get_app().next_update_async()
        curr_time = time.time()
        if curr_time - frame_start < 0.1:
            print(f"\tStage fully loaded at frame {i} (last frame duration: {curr_time - frame_start} seconds)..")
            break
        frame_start = curr_time


class TestBenchmarkSDGGeneration(BaseIsaacBenchmark):
    async def setUp(self):
        await super().setUp()
        pass

    async def tearDown(self):
        await super().tearDown()
        pass

    # ----------------------------------------------------------------------
    async def benchmark_sdg_generation(self, num_render_products, resolution, num_frames, annotators="rgb"):
        # Set the test name
        self.test_run.test_name = f"sdg_generation_{num_render_products}_{resolution[0]}x{resolution[1]}_rps_{num_frames}_frames_{annotators}_annot"

        # Create a fresh stage
        await create_new_stage_async()
        await omni.kit.app.get_app().next_update_async()

        # <----------------------------
        # Perform the loading benchmark
        self.set_phase("load stage")
        self.start_collecting_frametime()
        await omni.kit.app.get_app().next_update_async()

        assets_root_path = get_assets_root_path()
        await open_stage_async(assets_root_path + STAGE)
        await wait_until_stage_is_fully_loaded_async()

        await omni.kit.app.get_app().next_update_async()
        self.stop_collecting_frametime()
        await self.store_measurements()
        # ---------------------------->

        # <----------------------------
        # Perform clean stage benchmark
        self.set_phase("run clean stage")
        self.start_collecting_frametime()

        # Run for a few frames to check the clean stage stats
        for _ in range(TEST_NUM_APP_UPDATES):
            await omni.kit.app.get_app().next_update_async()

        self.stop_collecting_frametime()
        await self.store_measurements()
        # ---------------------------->

        # <----------------------------
        # Perform application play benchmark
        self.set_phase("setup sdg")
        self.start_collecting_frametime()

        render_products = []
        for i in range(num_render_products):
            z_offset = i * 0.005
            cam = rep.create.camera(position=(-6, -1, 4 + z_offset), look_at=LOOK_AT_PRIM_PATH, name=f"cam_{i}")
            render_products.append(rep.create.render_product(cam, resolution))

        writer = rep.WriterRegistry.get("BasicWriter")
        output_directory = os.getcwd() + "/" + self.test_run.test_name
        if annotators == "rgb":
            writer.initialize(output_dir=output_directory, rgb=True)
        elif annotators == "all":
            writer.initialize(output_dir=output_directory, **ALL_ANNOTATORS)

        await writer.attach_async(render_products)
        await omni.kit.app.get_app().next_update_async()

        # Run for a few frames to check the stage stats with the render products
        for _ in range(TEST_NUM_APP_UPDATES):
            await omni.kit.app.get_app().next_update_async()

        self.stop_collecting_frametime()
        await self.store_measurements()
        # ---------------------------->

        # <----------------------------
        # Perform load saved stage benchmark
        self.set_phase("run sdg")
        self.start_collecting_frametime()

        await rep.orchestrator.run_until_complete_async(num_frames=num_frames)

        self.stop_collecting_frametime()
        await self.store_measurements()
        # ---------------------------->

        # <----------------------------
        # Perform load saved stage benchmark
        self.set_phase("detach sdg")
        self.start_collecting_frametime()

        writer.detach()

        # Run for a few frames to check the stage stats after detaching the writer
        for _ in range(TEST_NUM_APP_UPDATES):
            await omni.kit.app.get_app().next_update_async()

        self.stop_collecting_frametime()
        await self.store_measurements()
        # ---------------------------->

        # Remove generated data
        shutil.rmtree(output_directory)

    # Benchmark render products with rgb
    async def test_benchmark_1_sdg_generation(self):
        for num_rp in TEST_NUM_RENDER_PRODUCTS:
            await self.benchmark_sdg_generation(
                num_render_products=num_rp, resolution=TEST_RESOLUTION, num_frames=TEST_NUM_FRAMES, annotators="rgb"
            )

    # Benchmark render products with all annotators
    async def test_benchmark_2_sdg_generation(self):
        for num_rp in TEST_NUM_RENDER_PRODUCTS:
            await self.benchmark_sdg_generation(
                num_render_products=num_rp, resolution=TEST_RESOLUTION, num_frames=TEST_NUM_FRAMES, annotators="all"
            )

    # Benchmark resolution with rgb
    async def test_benchmark_3_sdg_generation(self):
        for res in TEST_RESOLUTIONS:
            await self.benchmark_sdg_generation(
                num_render_products=1, resolution=res, num_frames=TEST_NUM_FRAMES, annotators="rgb"
            )

    # Benchmark resolution with all annotators
    async def test_benchmark_4_sdg_generation(self):
        for res in TEST_RESOLUTIONS:
            await self.benchmark_sdg_generation(
                num_render_products=1, resolution=res, num_frames=TEST_NUM_FRAMES, annotators="all"
            )
