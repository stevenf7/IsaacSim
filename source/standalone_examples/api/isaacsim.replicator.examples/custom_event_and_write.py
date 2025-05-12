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

import os

import carb
import omni.replicator.core as rep
import omni.usd
import usdrt


def is_fsd_enabled():
    return carb.settings.get_settings().get_as_bool("/app/useFabricSceneDelegate")


omni.usd.get_context().new_stage()
distance_light = rep.create.light(rotation=(315, 0, 0), intensity=4000, light_type="distant")

large_cube = rep.create.cube(scale=1.25, position=(1, 1, 0))
small_cube = rep.create.cube(scale=0.75, position=(-1, -1, 0))
large_cube_prim_path = large_cube.get_output("prims")[0]
small_cube_prim_path = small_cube.get_output("prims")[0]

if is_fsd_enabled():
    usdrt_stage = usdrt.Usd.Stage.Attach(omni.usd.get_context().get_stage_id())
    large_cube_prim = usdrt_stage.GetPrimAtPath(str(large_cube_prim_path), False)
    small_cube_prim = usdrt_stage.GetPrimAtPath(str(small_cube_prim_path), False)
else:
    usd_stage = omni.usd.get_context().get_stage()
    large_cube_prim = usd_stage.GetPrimAtPath(str(large_cube_prim_path))
    small_cube_prim = usd_stage.GetPrimAtPath(str(small_cube_prim_path))

rp = rep.create.render_product("/OmniverseKit_Persp", (512, 512))
writer = rep.WriterRegistry.get("BasicWriter")
out_dir = os.path.join(os.getcwd(), "_out_custom_event")
print(f"Writing data to {out_dir}")
writer.initialize(output_dir=out_dir, rgb=True)
writer.attach(rp)

with rep.trigger.on_custom_event(event_name="randomize_large_cube"):
    with large_cube:
        rep.randomizer.rotation()

with rep.trigger.on_custom_event(event_name="randomize_small_cube"):
    with small_cube:
        rep.randomizer.rotation()


def run_example():
    print(f"Randomizing small cube")
    rep.utils.send_og_event(event_name="randomize_small_cube")
    print("Capturing frame")
    rep.orchestrator.step(rt_subframes=8)

    print("Moving small cube")
    small_cube_prim.GetAttribute("xformOp:translate").Set((-2, -2, 0))
    print("Capturing frame")
    rep.orchestrator.step(rt_subframes=8)

    print(f"Randomizing large cube")
    rep.utils.send_og_event(event_name="randomize_large_cube")
    print("Capturing frame")
    rep.orchestrator.step(rt_subframes=8)

    print("Moving large cube")
    large_cube_prim.GetAttribute("xformOp:translate").Set((2, 2, 0))
    print("Capturing frame")
    rep.orchestrator.step(rt_subframes=8)

    # Wait until all the data is saved to disk
    rep.orchestrator.wait_until_complete()


run_example()

simulation_app.close()
