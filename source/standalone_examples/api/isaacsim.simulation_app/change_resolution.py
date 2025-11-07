# SPDX-FileCopyrightText: Copyright (c) 2020-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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

import random

from isaacsim import SimulationApp

# Simple example showing how to change resolution
kit = SimulationApp({"headless": False})

from isaacsim.core.utils.stage import is_stage_loading, open_stage
from isaacsim.storage.native import get_assets_root_path

# Load the warehouse environment to demonstrate the changing resolution
assets_root_path = get_assets_root_path()
if assets_root_path is None:
    carb.log_error("Could not find Isaac Sim assets folder")
    kit.close()

usd_path = assets_root_path + "/Isaac/Environments/Simple_Warehouse/warehouse.usd"
open_stage(usd_path)
while is_stage_loading():
    kit.update()
print("Loading Complete")

from omni.kit.viewport.utility import get_active_viewport

viewport_api = get_active_viewport()

while kit.is_running():
    for i in range(10):
        width = random.randint(128, 1980)
        height = random.randint(128, 1980)
        viewport_api.set_texture_resolution((width, height))
        print(f"Resolution set to: {width}, {height} using viewport API.")
        for j in range(100):
            kit.update()

# cleanup
kit.close()
