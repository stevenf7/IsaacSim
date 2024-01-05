# Copyright (c) 2018-2023, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

import os
import shutil

import carb
import omni.kit.test
import omni.replicator.core as rep
from omni.isaac.benchmark.services.base_isaac_benchmark import BaseIsaacBenchmark
from omni.isaac.benchmark.services.utils import wait_until_stage_is_fully_loaded_async
from omni.isaac.core.utils.nucleus import get_assets_root_path
from omni.isaac.core.utils.stage import create_new_stage_async, open_stage

STAGE = "/Isaac/Samples/Replicator/Benchmark/full_warehouse_worker_benchmark_sdg.usd"
LOOK_AT_PRIM_PATH = "/Root/SM_CardBoxA_3"
DEFAULT_RESOLUTION = (1280, 720)
TEST_NUM_APP_UPDATES = 100
SDG_NUM_FRAMES = 100
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


# Count the number of SDG frames written to disk
def check_number_of_written_sdg_frames(output_directory, num_frames_expected, verbose=False):
    # Count the written frames by counting the 'rgb_*.png' files in the output directory,
    # or in case of multiple cameras the '/rgb' folder of the first subdirectory
    folders = [f for f in os.listdir(output_directory) if os.path.isdir(os.path.join(output_directory, f))]
    num_written_frames = 0
    if len(folders) > 0:
        first_subdir_path = os.path.join(output_directory, folders[0], "rgb")
        rgb_files = [f for f in os.listdir(first_subdir_path) if f.startswith("rgb_")]
        num_written_frames = len(rgb_files)
        if verbose:
            print(
                f"Found {len(folders)} folders in {output_directory}, counted {num_written_frames} rgb_*.png files in {first_subdir_path}"
            )
    else:
        rgb_files = [f for f in os.listdir(output_directory) if f.startswith("rgb_")]
        num_written_frames = len(rgb_files)
        if verbose:
            print(f"No subdirectories found, counted {num_written_frames} rgb_*.png files in {output_directory}")
    return num_written_frames == num_frames_expected


class TestBenchmarkSDGGeneration(BaseIsaacBenchmark):
    async def setUp(self):
        await super().setUp()
        pass

    async def tearDown(self):
        await super().tearDown()
        # set capture on play back to true
        carb_settings = carb.settings.get_settings()
        carb_settings.set_bool("/omni/replicator/captureOnPlay", True)
        pass

    # ----------------------------------------------------------------------
    async def benchmark_sdg_generation(self, num_render_products, resolution, num_frames, annotators="rgb"):
        # Set the test name
        self.test_run.test_name = f"sdg_generation_cameras_{num_render_products}_resolution_{resolution[0]}_{resolution[1]}_frames_{num_frames}_{annotators}_annotators"
        print(f" ** [sdg_benchmark] Running test: {self.test_run.test_name}")

        # Create a fresh stage
        await create_new_stage_async()
        await wait_until_stage_is_fully_loaded_async()
        assets_root_path = get_assets_root_path()

        # <---------------------------- loading phase -----------------------------
        # Perform the loading phase: check for the duration for loading the stage,
        # where the first frames take longer in order to load all the prims followed by the materials/textures
        self.set_phase("loading")
        # self.start_collecting_frametime()
        self.start_runtime()
        await omni.kit.app.get_app().next_update_async()

        # Async version seems to cause running extra frames when collecting frametimes
        # await open_stage_async(assets_root_path + STAGE)
        open_stage(assets_root_path + STAGE)
        await wait_until_stage_is_fully_loaded_async()

        await omni.kit.app.get_app().next_update_async()
        self.stop_runtime()
        # self.stop_collecting_frametime()
        await self.store_measurements()
        # ----------------------------- loading phase ----------------------------->

        # <---------------------------- baseline phase -----------------------------
        # Perform the baseline phase: check the performance with the cleanly loaded stage
        self.set_phase("baseline")
        self.start_collecting_frametime()

        # Run for a few frames to check the clean stage stats
        for _ in range(1 if self.test_mode else TEST_NUM_APP_UPDATES):
            await omni.kit.app.get_app().next_update_async()

        self.stop_collecting_frametime()
        await self.store_measurements()
        # ---------------------------- baseline phase ------------------------------->

        # Setup the SDG parts for the benchmark (render products, writer, etc.)
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
        # Evaluate og graph
        await rep.orchestrator.preview_async()

        # <---------------------------- baseline_sdg phase -----------------------------
        # Check the performance with the SDG parts loaded
        self.set_phase("baseline_sdg")
        self.start_collecting_frametime()

        # Run for a few frames to check the stage stats with the render products
        for _ in range(1 if self.test_mode else TEST_NUM_APP_UPDATES):
            await omni.kit.app.get_app().next_update_async()

        self.stop_collecting_frametime()
        await self.store_measurements()
        # ---------------------------- baseline_sdg phase ------------------------------->

        # Make sure capture on play is not on
        carb_settings = carb.settings.get_settings()
        carb_settings.set_bool("/omni/replicator/captureOnPlay", False)

        # <---------------------------- benchmark phase -----------------------------
        # Check the performance while writing SDG data
        self.set_phase("benchmark")
        self.start_collecting_frametime()
        self.start_runtime()

        await rep.orchestrator.run_until_complete_async(num_frames=(1 if self.test_mode else num_frames))
        # await rep.orchestrator.run_async(num_frames=num_frames)
        # for _ in range(num_frames):
        #     await rep.orchestrator.step_async()
        # await rep.orchestrator.wait_until_complete_async()

        self.stop_runtime()
        self.stop_collecting_frametime()
        await self.store_measurements()
        # ---------------------------- benchmark phase ------------------------------->

        # Cleanup writer, render products, and replicator graphs
        writer.detach()
        writer = None
        for rp in render_products:
            rp.destroy()
        render_products.clear()
        stage = omni.usd.get_context().get_stage()
        if stage.GetPrimAtPath("/Replicator"):
            omni.kit.commands.execute("DeletePrimsCommand", paths=["/Replicator"])
        await omni.kit.app.get_app().next_update_async()

        # Check that all the SDG frames were written to disk
        all_frames_written = check_number_of_written_sdg_frames(
            output_directory, (1 if self.test_mode else num_frames), verbose=True
        )
        # Remove the written data from disk
        shutil.rmtree(output_directory)
        # Check results if all the frames were written
        self.assertTrue(all_frames_written)

        # <---------------------------- baseline_cleanup phase -----------------------------
        # Check performance after running the SDG benchmark and cleaning up replicator functionalities
        self.set_phase("baseline_cleanup")
        self.start_collecting_frametime()

        # Run for a few frames to check the stage stats after detaching the writer and destroying the render products
        for _ in range(1 if self.test_mode else TEST_NUM_APP_UPDATES):
            await omni.kit.app.get_app().next_update_async()

        self.stop_collecting_frametime()
        await self.store_measurements()
        # ---------------------------- baseline_cleanup phase ------------------------------->

    # ----------------------------------------------------------------------
    # Render products with rgb
    async def test_benchmark_sdg_1_camera_rgb_annotator(self):
        await self.benchmark_sdg_generation(
            num_render_products=1, resolution=DEFAULT_RESOLUTION, num_frames=SDG_NUM_FRAMES, annotators="rgb"
        )

    async def test_benchmark_sdg_2_camera_rgb_annotator(self):
        await self.benchmark_sdg_generation(
            num_render_products=2, resolution=DEFAULT_RESOLUTION, num_frames=SDG_NUM_FRAMES, annotators="rgb"
        )

    async def test_benchmark_sdg_4_camera_rgb_annotator(self):
        await self.benchmark_sdg_generation(
            num_render_products=4, resolution=DEFAULT_RESOLUTION, num_frames=SDG_NUM_FRAMES, annotators="rgb"
        )

    # ----------------------------------------------------------------------
    # Render products with all annotators
    async def test_benchmark_sdg_1_camera_all_annotator(self):
        await self.benchmark_sdg_generation(
            num_render_products=1, resolution=DEFAULT_RESOLUTION, num_frames=SDG_NUM_FRAMES, annotators="all"
        )

    async def test_benchmark_sdg_2_camera_all_annotator(self):
        await self.benchmark_sdg_generation(
            num_render_products=2, resolution=DEFAULT_RESOLUTION, num_frames=SDG_NUM_FRAMES, annotators="all"
        )

    async def test_benchmark_sdg_4_camera_all_annotator(self):
        await self.benchmark_sdg_generation(
            num_render_products=4, resolution=DEFAULT_RESOLUTION, num_frames=SDG_NUM_FRAMES, annotators="all"
        )

    # ----------------------------------------------------------------------
    # Benchmark resolution with rgb
    async def test_benchmark_sdg_128_128_resolution_rgb_annotator(self):
        await self.benchmark_sdg_generation(
            num_render_products=1, resolution=(128, 128), num_frames=SDG_NUM_FRAMES, annotators="rgb"
        )

    async def test_benchmark_sdg_256_256_resolution_rgb_annotator(self):
        await self.benchmark_sdg_generation(
            num_render_products=1, resolution=(256, 256), num_frames=SDG_NUM_FRAMES, annotators="rgb"
        )

    async def test_benchmark_sdg_512_512_resolution_rgb_annotator(self):
        await self.benchmark_sdg_generation(
            num_render_products=1, resolution=(512, 512), num_frames=SDG_NUM_FRAMES, annotators="rgb"
        )

    # ----------------------------------------------------------------------
    # Benchmark resolution with all annotators
    async def test_benchmark_sdg_128_128_resolution_all_annotator(self):
        await self.benchmark_sdg_generation(
            num_render_products=1, resolution=(128, 128), num_frames=SDG_NUM_FRAMES, annotators="all"
        )

    async def test_benchmark_sdg_256_256_resolution_all_annotator(self):
        await self.benchmark_sdg_generation(
            num_render_products=1, resolution=(256, 256), num_frames=SDG_NUM_FRAMES, annotators="all"
        )

    async def test_benchmark_sdg_512_512_resolution_all_annotator(self):
        await self.benchmark_sdg_generation(
            num_render_products=1, resolution=(512, 512), num_frames=SDG_NUM_FRAMES, annotators="all"
        )
