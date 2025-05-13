# SPDX-FileCopyrightText: Copyright (c) 2024-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: LicenseRef-NvidiaProprietary
#
# NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
# property and proprietary rights in and to this material, related
# documentation and any modifications thereto. Any use, reproduction,
# disclosure or distribution of this material and related documentation
# without an express license agreement from NVIDIA CORPORATION or
# its affiliates is strictly prohibited.

from isaacsim import SimulationApp

simulation_app = SimulationApp(launch_config={"headless": False})

import asyncio
import os
import random

import omni.kit.app
import omni.replicator.core as rep
import omni.timeline
import omni.usd
from pxr import Gf, Sdf, Usd, UsdGeom, UsdPhysics

# Make sure the simready explorer extension is enabled
ext_manager = omni.kit.app.get_app().get_extension_manager()
if not ext_manager.is_extension_enabled("omni.simready.explorer"):
    ext_manager.set_extension_enabled_immediate("omni.simready.explorer", True)
import omni.simready.explorer as sre


def enable_simready_explorer():
    if sre.get_instance().browser_model is None:
        import omni.kit.actions.core as actions

        actions.execute_action("omni.simready.explorer", "toggle_window")


async def search_assets_async():
    print(f"\tSearching for simready assets...")
    tables = await sre.find_assets(["table", "furniture"])
    plates = await sre.find_assets(["plate"])
    bowls = await sre.find_assets(["bowl"])
    dishes = plates + bowls
    fruits = await sre.find_assets(["fruit"])
    vegetables = await sre.find_assets(["vegetable"])
    items = fruits + vegetables
    return tables, dishes, items


def run_simready_randomization(scenario_id):
    print(f"Creating new stage for scenario {scenario_id}...")
    omni.usd.get_context().new_stage()
    stage = omni.usd.get_context().get_stage()

    random.seed(12)
    rep.set_global_seed(12)

    dome_light = stage.DefinePrim("/World/DomeLight", "DomeLight")
    dome_light.CreateAttribute("inputs:intensity", Sdf.ValueTypeNames.Float).Set(500.0)

    distant_light = stage.DefinePrim("/World/DistantLight", "DistantLight")
    if not distant_light.GetAttribute("xformOp:rotateXYZ"):
        UsdGeom.Xformable(distant_light).AddRotateXYZOp()
    distant_light.GetAttribute("xformOp:rotateXYZ").Set((-75, 0, 0))
    distant_light.CreateAttribute("inputs:intensity", Sdf.ValueTypeNames.Float).Set(2500)

    # Simready explorer window needs to be created for the search to work
    enable_simready_explorer()

    # Search for the simready assets and wait until the task is complete
    search_task = asyncio.ensure_future(search_assets_async())
    while not search_task.done():
        simulation_app.update()
    tables, dishes, items = search_task.result()
    print(f"\tFound {len(tables)} tables, {len(dishes)} dishes, {len(items)} items")

    # Load the simready assets with rigid body properties
    variants = {"PhysicsVariant": "RigidBody"}

    # Choose a random table from the list of tables and add it to the stage with physics
    table_asset = random.choice(tables)
    _, table_prim_path = sre.add_asset_to_stage(table_asset.main_url, variants=variants, payload=True)
    print(f"\tAdded '{table_asset.name}'")

    print(f"\tDisabling rigid body properties and keeping only colliders...")
    # Disable the rigid body properties and keep only the colliders
    table_prim = stage.GetPrimAtPath(table_prim_path)
    if not table_prim.HasAPI(UsdPhysics.RigidBodyAPI):
        rigid_body_api = UsdPhysics.RigidBodyAPI.Apply(table_prim)
    else:
        rigid_body_api = UsdPhysics.RigidBodyAPI(table_prim)
    rigid_body_api.CreateRigidBodyEnabledAttr(False)

    # Compute the height of the table from its bounding box
    bbox_cache = UsdGeom.BBoxCache(Usd.TimeCode.Default(), includedPurposes=[UsdGeom.Tokens.default_])
    table_bbox = bbox_cache.ComputeWorldBound(table_prim)
    table_size = table_bbox.GetRange().GetSize()

    # Choose one random plate from the list of plates
    dish_asset = random.choice(dishes)
    _, dish_prim_path = sre.add_asset_to_stage(dish_asset.main_url, variants=variants, payload=True)
    print(f"\tAdded '{dish_asset.name}'")

    # Compute the height of the plate from its bounding box
    dish_prim = stage.GetPrimAtPath(dish_prim_path)
    dish_bbox = bbox_cache.ComputeWorldBound(dish_prim)
    dish_size = dish_bbox.GetRange().GetSize()

    # Get a random position for the plate on the table using the two sizes
    dish_x = random.uniform(-table_size[0] / 2 + dish_size[0] / 2, table_size[0] / 2 - dish_size[0] / 2)
    dish_y = random.uniform(-table_size[1] / 2 + dish_size[1] / 2, table_size[1] / 2 - dish_size[1] / 2)
    dish_z = table_size[2] + dish_size[2] / 2

    # Move the plate to the random position on the table
    dish_prim.GetAttribute("xformOp:translate").Set(Gf.Vec3f(dish_x, dish_y, dish_z))

    # Spawn a random number of items
    num_items = random.randint(3, 6)
    item_prims = []
    for _ in range(num_items):
        item_asset = random.choice(items)
        _, item_prim_path = sre.add_asset_to_stage(item_asset.main_url, variants=variants, payload=True)
        item_prims.append(stage.GetPrimAtPath(item_prim_path))
    print(f"\tAdded {[item.GetName() for item in item_prims]}")

    # Move the items on top of each other above the plate
    current_z = dish_z
    xy_offset = dish_size[0] / 4
    for item_prim in item_prims:
        item_bbox = bbox_cache.ComputeWorldBound(item_prim)
        item_size = item_bbox.GetRange().GetSize()
        item_x = dish_x + random.uniform(-xy_offset, xy_offset)
        item_y = dish_y + random.uniform(-xy_offset, xy_offset)
        item_z = current_z + item_size[2] / 2
        item_prim.GetAttribute("xformOp:translate").Set(Gf.Vec3f(item_x, item_y, item_z))
        current_z += item_size[2]

    # Run the simulation for several frames
    timeline = omni.timeline.get_timeline_interface()
    timeline.play()
    for _ in range(35):
        simulation_app.update()
    timeline.pause()

    # Capture the scene using a basicwriter
    rep.orchestrator.set_capture_on_play(False)
    cam = rep.create.camera(position=(0, 0, 2), look_at=(dish_x, dish_y, dish_z))
    rp = rep.create.render_product(cam, (512, 512))
    output_dir = os.path.join(os.getcwd(), f"_out_simready_assets_{scenario_id}")
    print(f"\tWriting to {output_dir}...")
    writer = rep.writers.get("BasicWriter")
    writer.initialize(output_dir=output_dir, rgb=True)
    writer.attach(rp)

    rep.orchestrator.preview()
    rep.orchestrator.step(delta_time=0.0, rt_subframes=16)
    rep.orchestrator.wait_until_complete()

    writer.detach()
    rp.destroy()


def run_simready_randomizations(num_scenarios):
    for i in range(num_scenarios):
        print(f"Running simready randomization scenario {i}..")
        run_simready_randomization(scenario_id=i)


run_simready_randomizations(2)

simulation_app.close()
