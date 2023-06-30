# Copyright (c) 2018-2023, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#


import os
import random
import time
from itertools import cycle

import carb
import omni.kit.test
from omni.isaac.core.utils.nucleus import get_assets_root_path
from omni.isaac.core.utils.stage import add_reference_to_stage, create_new_stage_async, open_stage_async
from pxr import UsdGeom, UsdLux

from ..utils.base_isaac_benchmark import BaseIsaacBenchmark

ASSETS_PATH = "/Isaac/Environments/Simple_Warehouse/Props"
RANDOM_SEED = 132
TEST_NUM_ASSETS = [100, 1000]
TEST_NUM_LIGHTS = [8, 16]

# Helper function to get the test from the arguments
def get_test_name_from_args(num_assets, location, prim_type, api, num_lights=0):
    test_name = "scene_generation_"

    # Test name if the assets are spawned at the origin
    if location.lower() == "origin":
        test_name += "origin_"
        if prim_type.lower() == "xform":
            test_name += "xform_"
        elif prim_type.lower() == "mesh":
            test_name += "mesh_"
            if api.lower() == "usd":
                test_name += "usd_"
            elif api.lower() == "isaac":
                test_name += "isaac_"
        return f"{test_name}{num_assets}_assets"

    # Test name if the assets are randomized (can only be meshes w/wo lights)
    elif location.lower() == "random":
        return f"{test_name}random_{num_lights}_lights_{num_assets}_assets"


# Get a list of assets as a cycle iterator
def get_usd_assets_from_path_as_cycle(assets_path):
    assets_root_path = get_assets_root_path()
    path = assets_root_path + assets_path
    assets = []
    result, entries = omni.client.list(path)
    if result != omni.client.Result.OK:
        carb.log_error(f"Could not list assets in path: {path}")
        return
    for entry in entries:
        _, ext = os.path.splitext(entry.relative_path)
        if ext == ".usd":
            assets.append(f"{path}/{entry.relative_path}")
    return cycle(assets)


# Calculate an spawning area extent from the number of assets
def get_extent_from_num_assets(num_assets):
    return (num_assets ** (1 / 3), num_assets ** (1 / 3), num_assets ** (1 / 4))


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


# Spawn all assets in a new stage (caching)
async def load_all_assets_in_new_stage_async(assets_path):
    assets_root_path = get_assets_root_path()
    path = assets_root_path + assets_path
    assets = []
    result, entries = omni.client.list(path)
    if result != omni.client.Result.OK:
        carb.log_error(f"Could not list assets in path: {path}")
        return
    for entry in entries:
        _, ext = os.path.splitext(entry.relative_path)
        if ext == ".usd":
            assets.append(f"{path}/{entry.relative_path}")

    # Create a new stage and load all assets in its origin
    await create_new_stage_async()
    stage = omni.usd.get_context().get_stage()
    print(f"Loading {len(assets)} assets in stage from {assets_path}...")
    start = time.time()
    for i, asset_path in enumerate(assets):
        asset_name = os.path.splitext(os.path.basename(asset_path))[0]

        prim = stage.DefinePrim(f"/World/Assets/{asset_name}_{i}", "Xform")
        prim.GetReferences().AddReference(asset_path)

    # Wait (update the app) until the stage is fully loaded (materials/textures)
    await wait_until_stage_is_fully_loaded_async()
    print(f"Done loading assets in stage in {time.time() - start} seconds.")


# Spawn the assets in the origin using various parameters
def spawn_assets_at_origin(stage, num_assets, prim_type, api, assets_path=None):
    # Spawn only Xforms
    if prim_type.lower() == "xform":
        for i in range(num_assets):
            stage.DefinePrim(f"/World/Assets/Xform_{i}", "Xform")

    # Spawn meshes using USD API or Isaac Sim helpers
    elif prim_type.lower() == "mesh":
        # Get a list of assets and cycle through them
        assets_cycle = get_usd_assets_from_path_as_cycle(assets_path)

        # Spawn assets using the USD API directly
        if api.lower() == "usd":
            for i in range(num_assets):
                asset_path = next(assets_cycle)
                asset_name = os.path.splitext(os.path.basename(asset_path))[0]
                prim = stage.DefinePrim(f"/World/Assets/{asset_name}_{i}", "Xform")
                prim.GetReferences().AddReference(asset_path)

        # Spawn assets using Isaac Sim helpers
        elif api.lower() == "isaac":
            for i in range(num_assets):
                asset_path = next(assets_cycle)
                asset_name = os.path.splitext(os.path.basename(asset_path))[0]
                add_reference_to_stage(asset_path, f"/World/Assets/{asset_name}_{i}")


# Spawn assets (w/wo lights) in random poses in the scene
def spawn_assets_randomized(stage, num_assets, num_lights, assets_path):
    # Set the random seed to get the same random locations every time
    random.seed(RANDOM_SEED)

    # Get a list of assets and cycle through them
    assets_cycle = get_usd_assets_from_path_as_cycle(assets_path)

    # Get the spawning area depending on the number of assets
    ext = get_extent_from_num_assets(num_assets)

    # Spawn a ground below the spawning area to drop shadows and reflect lights
    _, plane_path = omni.kit.commands.execute("CreateMeshPrim", prim_type="Plane")
    plane_prim = stage.GetPrimAtPath(plane_path)
    if not plane_prim.GetAttribute("xformOp:translate"):
        UsdGeom.Xformable(plane_prim).AddTranslateOp()
    plane_prim.GetAttribute("xformOp:translate").Set((0, 0, -2))

    if not plane_prim.GetAttribute("xformOp:scale"):
        UsdGeom.Xformable(plane_prim).AddScaleOp()
    plane_prim.GetAttribute("xformOp:scale").Set((ext[0] * 2, ext[1] * 2, 1))

    # Spawn the assets
    for i in range(num_assets):
        asset_path = next(assets_cycle)
        asset_name = os.path.splitext(os.path.basename(asset_path))[0]

        prim = stage.DefinePrim(f"/World/Assets/{asset_name}_{i}", "Xform")
        prim.GetReferences().AddReference(asset_path)

        location = (random.uniform(-ext[0], ext[0]), random.uniform(-ext[1], ext[1]), random.uniform(0, ext[2]))
        if not prim.GetAttribute("xformOp:translate"):
            UsdGeom.Xformable(prim).AddTranslateOp()
        prim.GetAttribute("xformOp:translate").Set(location)

        rotation = (random.uniform(0, 360), random.uniform(0, 360), random.uniform(0, 360))
        if not prim.GetAttribute("xformOp:rotateXYZ"):
            UsdGeom.Xformable(prim).AddRotateXYZOp()
        prim.GetAttribute("xformOp:rotateXYZ").Set(rotation)

    # Include random lights between the assets
    for i in range(num_lights):
        light_location = (random.uniform(-ext[0], ext[0]), random.uniform(-ext[1], ext[1]), random.uniform(0, ext[2]))
        light = UsdLux.SphereLight.Define(stage, f"/World/Lights/SphereLight_{i}")
        light.CreateRadiusAttr(ext[2])
        light.CreateIntensityAttr(500)
        light_prim = light.GetPrim()
        if not light_prim.GetAttribute("xformOp:translate"):
            UsdGeom.Xformable(light_prim).AddTranslateOp()
        light_prim.GetAttribute("xformOp:translate").Set(light_location)


class TestBenchmarkSceneGeneration(BaseIsaacBenchmark):
    async def setUp(self):
        await super().setUp()
        pass

    async def tearDown(self):
        await super().tearDown()
        pass

    # ----------------------------------------------------------------------
    async def benchmark_scene_generation(
        self, num_assets, location="origin", prim_type="xform", api="usd", num_lights=0
    ):
        # Set the test name
        self.test_run.test_name = get_test_name_from_args(num_assets, location, prim_type, api, num_lights)

        await create_new_stage_async()
        await omni.kit.app.get_app().next_update_async()
        stage = omni.usd.get_context().get_stage()

        # <----------------------------
        # Perform the loading benchmark
        self.set_phase("spawn")
        self.start_runtime()
        await omni.kit.app.get_app().next_update_async()

        # spawn the assest (xform or meshes) in the origin, (usd/isaac api) or at random poses (meshes, lights)
        if location.lower() == "origin":
            spawn_assets_at_origin(stage, num_assets, prim_type, api, ASSETS_PATH)
        elif location.lower() == "random":
            spawn_assets_randomized(stage, num_assets, num_lights, ASSETS_PATH)

        # Wait (update the app) until the stage is fully loaded (materials/textures)
        await wait_until_stage_is_fully_loaded_async()

        await omni.kit.app.get_app().next_update_async()
        self.stop_runtime()
        await self.store_measurements()
        # ---------------------------->

        timeline = omni.timeline.get_timeline_interface()
        timeline.play()
        await omni.kit.app.get_app().next_update_async()

        # <----------------------------
        # Perform application play benchmark
        self.set_phase("play")
        self.start_collecting_frametime()

        for _ in range(250):
            await omni.kit.app.get_app().next_update_async()

        self.stop_collecting_frametime()
        await self.store_measurements()
        # ---------------------------->

        # Stop the running timeline
        timeline.stop()
        await omni.kit.app.get_app().next_update_async()

        # Export the stage to file
        stage.GetRootLayer().Export(f"{self.test_run.test_name}.usda")
        await omni.kit.app.get_app().next_update_async()

        # Create a fresh stage
        await create_new_stage_async()
        await omni.kit.app.get_app().next_update_async()

        # <----------------------------
        # Perform load saved stage benchmark
        self.set_phase("load")
        self.start_runtime()
        await omni.kit.app.get_app().next_update_async()

        await open_stage_async(f"{self.test_run.test_name}.usda")
        await wait_until_stage_is_fully_loaded_async()

        await omni.kit.app.get_app().next_update_async()
        self.stop_runtime()
        await self.store_measurements()
        # ---------------------------->

        # Delete the exported file
        os.remove(f"{self.test_run.test_name}.usda")

    # Not a benchmark: load all meshes in scene once for the first time to run any existing caches
    async def test_benchmark_0_scene_generation(self):
        await load_all_assets_in_new_stage_async(ASSETS_PATH)

    # Benchmark: xfoms in origin (usd api by default)
    async def test_benchmark_1_scene_generation(self):
        for num in TEST_NUM_ASSETS:
            await self.benchmark_scene_generation(num_assets=num, location="origin", prim_type="xform", api="usd")

    # Benchmark: meshes in origin, usd api
    async def test_benchmark_2_scene_generation(self):
        for num in TEST_NUM_ASSETS:
            await self.benchmark_scene_generation(num_assets=num, location="origin", prim_type="mesh", api="usd")

    # Benchmark: meshes in origin, isaac api
    async def test_benchmark_3_scene_generation(self):
        for num in TEST_NUM_ASSETS:
            await self.benchmark_scene_generation(num_assets=num, location="origin", prim_type="mesh", api="isaac")

    # Benchmark: randomized, meshed (usd api by default)
    async def test_benchmark_4_scene_generation(self):
        for num in TEST_NUM_ASSETS:
            await self.benchmark_scene_generation(num_assets=num, location="random")

    # Benchmark: randomized, meshed, lights (usd api by default)
    async def test_benchmark_5_scene_generation(self):
        for num_a in TEST_NUM_ASSETS:
            for num_l in TEST_NUM_LIGHTS:
                await self.benchmark_scene_generation(num_assets=num_a, location="random", num_lights=num_l)
