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

from isaacsim import SimulationApp

# Start the application
simulation_app = SimulationApp({"headless": True})

# Get the utility to enable extensions
from isaacsim.core.utils.extensions import enable_extension

# Enable the IRA extension
enable_extension("isaacsim.replicator.agent.core")
simulation_app.update()


def _get_config_path() -> str:
    """Return path to the minimal IRA config bundled with the extension."""
    import omni.kit.app

    core_ext_path = (
        omni.kit.app.get_app().get_extension_manager().get_extension_path_by_module("isaacsim.replicator.agent.core")
    )
    default_config_file_path = os.path.join(core_ext_path, "data", "sample_configs", "minimal.yaml")
    if not os.path.isfile(default_config_file_path):
        raise FileNotFoundError(f"IRA config not found: {default_config_file_path}")
    return default_config_file_path


async def run_ira_data_generation(setup_simulation: bool = False, run_data_generation: bool = False):
    from isaacsim.replicator.agent.core import api as IRA

    # IRA: load config. Specify the config file path.
    config_path = _get_config_path()
    result = IRA.load_config_file(config_path)
    if not result:
        raise RuntimeError(f"Failed to load IRA config: {config_path}")

    # IRA: get config, you can modify the config here
    config = IRA.get_config_file()
    IRA.set_config(config)

    # IRA: setup simulation (only when setup_simulation is True)
    if setup_simulation:
        await IRA.setup_simulation()

        # Allow a few frames for scene to settle
        import omni.kit.app

        app = omni.kit.app.get_app()
        for _ in range(10):
            await app.next_update_async()

        # IRA: generate data (only when run_data_generation is True)
        if run_data_generation:
            await IRA.start_data_generation_async(will_wait_until_complete=True)


simulation_app.run_coroutine(run_ira_data_generation(setup_simulation=False, run_data_generation=False))

simulation_app.close()
