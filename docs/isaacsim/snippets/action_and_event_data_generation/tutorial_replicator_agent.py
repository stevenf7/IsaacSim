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

"""
Minimal IRA example: SimulationApp setup, load config, setup simulation, generate data.
"""

import os
import tempfile

from isaacsim import SimulationApp

# Start the application
simulation_app = SimulationApp({"headless": True})

# Get the utility to enable extensions
from isaacsim.core.utils.extensions import enable_extension

# Enable the IRA extension
enable_extension("isaacsim.replicator.agent.core")
simulation_app.update()

# Default config (no version); version is injected at write time from current IRA support.
DEFAULT_CONFIG = {
    "isaacsim.replicator.agent": {
        "environment": {
            "base_stage_asset_path": "Isaac/Environments/Simple_Warehouse/full_warehouse.usd",
        },
    },
}


def _get_ira_config_version() -> str:
    """Return the minimum supported IRA config version (injected before serialization)."""
    try:
        from omni.metropolis.utils.versioning_util import get_extension_version

        return get_extension_version("isaacsim.replicator.agent.core")
    except Exception:
        return "1.2.0"


def _get_config_path() -> str:
    """Return config path; create a temp default config file with current IRA version."""
    import copy

    import yaml

    config = copy.deepcopy(DEFAULT_CONFIG)
    config["isaacsim.replicator.agent"]["version"] = _get_ira_config_version()
    content = yaml.dump(config, default_flow_style=False, sort_keys=False)
    fd, path = tempfile.mkstemp(suffix=".yaml", prefix="ira_default_config_")
    try:
        with os.fdopen(fd, "w") as f:
            f.write(content)
        return path
    except Exception:
        os.close(fd)
        raise


async def run_ira_data_generation(run_data_generation: bool = False):
    from isaacsim.replicator.agent.core import api as IRA

    # IRA: load config. Specify the config file path.
    config_path = _get_config_path()
    result = IRA.load_config_file(config_path)
    if not result:
        raise RuntimeError(f"Failed to load IRA config: {config_path}")

    # IRA: get config, you can modify the config here
    config = IRA.get_config_file()
    IRA.set_config(config)

    # IRA: setup simulation
    await IRA.setup_simulation()

    # Allow a few frames for scene to settle
    import omni.kit.app

    app = omni.kit.app.get_app()
    for _ in range(10):
        await app.next_update_async()

    # IRA: generate data (only when run_data_generation is True)
    if run_data_generation:
        await IRA.start_data_generation_async(will_wait_until_complete=True)


from omni.kit.async_engine import run_coroutine

task = run_coroutine(run_ira_data_generation(run_data_generation=False))
while not task.done():
    simulation_app.update()
