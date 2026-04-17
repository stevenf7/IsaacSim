# SPDX-FileCopyrightText: Copyright (c) 2025-2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os

from isaacsim import SimulationApp

simulation_app = SimulationApp(launch_config={"headless": False})

import omni.kit.app
import omni.kit.commands
import omni.timeline
import omni.usd
from isaacsim.core.utils.stage import add_reference_to_stage
from isaacsim.storage.native import get_assets_root_path
from pxr import PhysxSchema, UsdGeom, UsdPhysics

# User path of the HF NuRec dataset
USER_PATH = "/home/user/PhysicalAI-Robotics-NuRec"

# Paths for loading and placing the Nova Carter navigation asset and its target.
NOVA_CARTER_NAV_URL = "/Isaac/Samples/Replicator/OmniGraph/nova_carter_nav_only.usd"
NOVA_CARTER_NAV_USD_PATH = "/World/NovaCarterNav"
NOVA_CARTER_NAV_TARGET_PATH = f"{NOVA_CARTER_NAV_USD_PATH}/targetXform"
# Scenarios for testing navigation in the environments
EXAMPLE_CONFIGS = [
    {
        "name": "Andoria",
        "stage_url": f"{USER_PATH}/hand_hold-endeavor-andoria/stage_particle.usdz",
        "nav_start_loc": (0.0, 0.5, 0.0),
        "nav_relative_target_loc": (0.0, 6.0, 0.0),
        "create_collision_ground_plane": False,
        "num_simulation_steps": 500,
    },
    {
        "name": "Wormhole",
        "stage_url": f"{USER_PATH}/hand_hold-endeavor-wormhole/stage_particle.usdz",
        "nav_start_loc": (5, 0, 0),
        "nav_relative_target_loc": (0, -4, 0),
        "create_collision_ground_plane": False,
        "num_simulation_steps": 500,
    },
    {
        "name": "Cafe",
        "stage_url": f"{USER_PATH}/nova_carter-cafe/stage_particle.usdz",
        "nav_start_loc": (0, 0, 0),
        "nav_relative_target_loc": (-3, -1.5, 0),
        "create_collision_ground_plane": False,
        "num_simulation_steps": 500,
    },
    {
        "name": "Galileo",
        "stage_url": f"{USER_PATH}/nova_carter-galileo/stage_particle.usdz",
        "nav_start_loc": (-2.5, 2.5, 0),
        "nav_relative_target_loc": (4, 0, 0),
        "create_collision_ground_plane": False,
        "num_simulation_steps": 500,
    },
]


def run_example(example_config):
    example_name = f"{example_config.get('name')} - {example_config.get('num_simulation_steps')}"
    print(f"Running example: '{example_name}'")

    # Open the stage
    stage_url = example_config.get("stage_url")
    if not stage_url:
        print("Stage URL not provided, exiting")
        return
    if not os.path.exists(stage_url):
        print(f"Stage URL does not exist: '{stage_url}', exiting")
        return

    print(f"Opening stage: '{stage_url}'")
    omni.usd.get_context().open_stage(stage_url)
    stage = omni.usd.get_context().get_stage()
    if stage is None:
        print(f"Failed to open stage: '{stage_url}', exiting")
        return

    # Make sure the physics scene is set to synchronous for the navigation to work
    for prim in stage.Traverse():
        if prim.IsA(UsdPhysics.Scene):
            physx_scene = PhysxSchema.PhysxSceneAPI.Apply(prim)
            physx_scene.GetUpdateTypeAttr().Set("Synchronous")
            break

    # Load the carter navigation asset
    assets_root_path = get_assets_root_path()
    carter_nav_path = assets_root_path + NOVA_CARTER_NAV_URL
    print(f"Loading carter nova asset: '{carter_nav_path}'")
    carter_nav_prim = add_reference_to_stage(usd_path=carter_nav_path, prim_path=NOVA_CARTER_NAV_USD_PATH)

    # Set the carter navigation start location
    nav_start_loc = example_config.get("nav_start_loc")
    if not nav_start_loc:
        print(f"Navigation start location not provided, exiting")
        return
    print(f"Setting carter navigation start location to: {nav_start_loc}")
    if not carter_nav_prim.GetAttribute("xformOp:translate"):
        UsdGeom.Xformable(carter_nav_prim).AddTranslateOp()
    carter_nav_prim.GetAttribute("xformOp:translate").Set(nav_start_loc)

    # Check if a collision ground plane needs to be created at the spawn location
    if example_config.get("create_collision_ground_plane"):
        plane_path = "/World/CollisionPlane"
        print(f"Creating collision ground plane {plane_path} at {nav_start_loc}")
        omni.kit.commands.execute("CreateMeshPrimWithDefaultXform", prim_path=plane_path, prim_type="Plane")
        plane_prim = stage.GetPrimAtPath(plane_path)
        plane_prim.GetAttribute("xformOp:scale").Set((10, 10, 1))
        plane_prim.GetAttribute("xformOp:translate").Set(nav_start_loc)
        if not plane_prim.HasAPI(UsdPhysics.CollisionAPI):
            collision_api = UsdPhysics.CollisionAPI.Apply(plane_prim)
        else:
            collision_api = UsdPhysics.CollisionAPI(plane_prim)
        collision_api.CreateCollisionEnabledAttr(True)
        plane_prim.GetAttribute("visibility").Set("invisible")

    # Set the carter navigation target prim location
    nav_relative_target_loc = example_config.get("nav_relative_target_loc")
    if not nav_relative_target_loc:
        print(f"Navigation relative target location not provided, exiting")
        return
    print(f"Setting carter navigation target location to: {nav_relative_target_loc}")
    carter_navigation_target_prim = stage.GetPrimAtPath(NOVA_CARTER_NAV_TARGET_PATH)
    if not carter_navigation_target_prim.IsValid():
        print(f"Carter navigation target prim not found at path: '{NOVA_CARTER_NAV_TARGET_PATH}', exiting")
        return
    if not carter_navigation_target_prim.GetAttribute("xformOp:translate"):
        UsdGeom.Xformable(carter_navigation_target_prim).AddTranslateOp()
    carter_navigation_target_prim.GetAttribute("xformOp:translate").Set(nav_relative_target_loc)

    # Run the simulation for the given number of steps
    num_simulation_steps = example_config.get("num_simulation_steps")
    if not num_simulation_steps:
        print(f"Number of simulation steps not provided, exiting")
        return
    print(f"Running {num_simulation_steps} simulation steps")
    timeline = omni.timeline.get_timeline_interface()
    timeline.play()
    for i in range(num_simulation_steps):
        if i % 10 == 0:
            print(f"Step {i}, time: {timeline.get_current_time():.4f}")
        simulation_app.update()

    print(f"Simulation complete, pausing timeline")
    timeline.pause()


def run_examples():
    for example_config in EXAMPLE_CONFIGS:
        run_example(example_config)


run_examples()

simulation_app.close()
