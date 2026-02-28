# SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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

# Example: read and update IRA config using get_config, update_config, add_config_item, delete_config_item.
from isaacsim.replicator.agent.ui import add_config_item, delete_config_item, get_config, update_config

# Example queries
full_config = get_config()
stage_path = get_config("environment.base_stage_asset_path")

# Example updates
update_config("environment.base_stage_asset_path", "Isaac/Environments/Simple_Warehouse/full_warehouse.usd")
update_config("simulation_duration", 120.0)
add_config_item("environment.prop_asset_paths", "Isaac/Props/Conveyors/ConveyorBelt_A08.usd")
delete_config_item("environment.prop_asset_paths", key=0)
