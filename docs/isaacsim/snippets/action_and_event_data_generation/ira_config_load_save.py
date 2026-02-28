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

# Example: load, inspect, and save IRA config using the Configuration Editor API.
import os
import tempfile

from isaacsim.replicator.agent.ui import get_config_file_path, load_config_file, save_config_file

config_path = get_config_file_path()
if config_path:
    from pathlib import Path

    target_config_path = Path(config_path).parent / "warehouse.yaml"
else:
    target_config_path = None

if target_config_path and load_config_file(target_config_path, set_config=True):
    print("Config loaded; current file:", get_config_file_path())

# ... do some config modifications using update_config and add_config_item

fd, temp_save_path = tempfile.mkstemp(suffix=".yaml")
os.close(fd)
save_config_file(temp_save_path)
