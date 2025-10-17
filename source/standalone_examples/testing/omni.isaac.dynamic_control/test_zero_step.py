# SPDX-FileCopyrightText: Copyright (c) 2021-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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

from isaacsim import SimulationApp

simulation_app = SimulationApp({"headless": False})
import carb
import omni
import omni.physics.core
from isaacsim.core.api import SimulationContext
from isaacsim.storage.native import get_assets_root_path
from omni.isaac.dynamic_control import _dynamic_control
from pxr import UsdUtils

stage = simulation_app.context.get_stage()
stage_id = UsdUtils.StageCache.Get().GetId(stage).ToLongInt()
sim_context = SimulationContext(stage_units_in_meters=1.0)

physics_stage_update_interface = omni.physics.core.get_physics_stage_update_interface()
physics_sim_interface = omni.physics.core.get_physics_simulation_interface()
physics_sim_interface.attach_stage(stage_id)
assets_root_path = get_assets_root_path()
if assets_root_path is None:
    carb.log_error("Could not find Isaac Sim assets folder")
asset_path = assets_root_path + "/Isaac/Robots/FrankaRobotics/FrankaPanda/franka.usd"

prim = stage.DefinePrim("/panda", "Xform")
prim.GetReferences().AddReference(asset_path)
physics_stage_update_interface.force_load_physics_from_usd()
sim_context._timeline.play()
physics_sim_interface.simulate(elapsed_time=0, current_time=0)
physics_sim_interface.fetch_results()
dc = _dynamic_control.acquire_dynamic_control_interface()
# Get the handle to force it to refresh, this should not crash.
art = dc.get_articulation("/panda")
sim_context._timeline.stop()
sim_context._timeline.play()
simulation_app.update()
simulation_app.close()
