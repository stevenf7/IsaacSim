# SPDX-FileCopyrightText: Copyright (c) 2024-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

# [snippet-start]
import omni.kit.actions.core
import omni.timeline
import omni.usd
from isaacsim.core.simulation_manager import SimulationManager
from isaacsim.core.simulation_manager.impl.mjc_scene import NewtonMjcScene
from isaacsim.core.utils.stage import add_reference_to_stage
from isaacsim.storage.native import get_assets_root_path
from pxr import Sdf, UsdLux

omni.usd.get_context().new_stage()
SimulationManager.switch_physics_engine("newton")
stage = omni.usd.get_context().get_stage()

action_registry = omni.kit.actions.core.get_action_registry()
action_registry.get_action("omni.kit.viewport.menubar.lighting", "set_lighting_mode_camera").execute()
UsdLux.DistantLight.Define(stage, Sdf.Path("/DistantLight")).CreateIntensityAttr(500)

mjc_scene = NewtonMjcScene("/World/PhysicsScene")
mjc_scene.set_dt(0.002)
mjc_scene.set_integrator("implicit")
mjc_scene.set_gravity((0.0, 0.0, -9.81))

asset_path = get_assets_root_path() + "/Isaac/Robots/FrankaRobotics/FrankaPanda/franka.usd"
add_reference_to_stage(usd_path=asset_path, prim_path="/World/Franka")

timeline = omni.timeline.get_timeline_interface()
timeline.play()
