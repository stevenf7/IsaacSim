# SPDX-FileCopyrightText: Copyright (c) 2021-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: LicenseRef-NvidiaProprietary
#
# NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
# property and proprietary rights in and to this material, related
# documentation and any modifications thereto. Any use, reproduction,
# disclosure or distribution of this material and related documentation
# without an express license agreement from NVIDIA CORPORATION or
# its affiliates is strictly prohibited.

from isaacsim import SimulationApp

simulation_app = SimulationApp({"headless": False})

from isaacsim.core.api import SimulationContext
from isaacsim.core.utils.prims import create_prim
from isaacsim.core.utils.stage import add_reference_to_stage, is_stage_loading
from isaacsim.storage.native import get_assets_root_path

assets_root_path = get_assets_root_path()
asset_path = assets_root_path + "/Isaac/Robots/FrankaRobotics/FrankaPanda/franka.usd"
robot = add_reference_to_stage(usd_path=asset_path, prim_path="/World/Franka")
robot.GetVariantSet("Gripper").SetVariantSelection("AlternateFinger")
robot.GetVariantSet("Mesh").SetVariantSelection("Quality")
simulation_context = SimulationContext()
create_prim("/DistantLight", "DistantLight")
# wait for things to load
simulation_app.update()
while is_stage_loading():
    simulation_app.update()

# need to initialize physics getting any articulation..etc
simulation_context.initialize_physics()
simulation_context.play()

for i in range(1000):
    simulation_context.step(render=True)

simulation_context.stop()
simulation_app.close()
