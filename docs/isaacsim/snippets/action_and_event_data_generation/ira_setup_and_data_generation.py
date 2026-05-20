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

# Example: Setup and data generation with event observers.
import tempfile
from pathlib import Path

import carb
from isaacsim.replicator.agent.core.events import IRAEvents
from isaacsim.replicator.agent.ui import (
    get_config_file_path,
    load_config_file,
    setup_simulation,
    start_data_generation,
    update_config,
)

# Skipping actual simulation setup and data generation by default for brevity
RUN_SETUP = False


def on_setup_done(event):
    """Callback for when simulation setup is done."""
    carb.log_info("Simulation setup done")
    start_data_generation()
    handle_setup.reset()


def on_data_done(event):
    """Callback for when data generation is done."""
    carb.log_info("Data generation done")
    handle_data.reset()


# Set up callbacks for setup simulation and data generation
dispatcher = carb.eventdispatcher.get_eventdispatcher()
handle_setup = dispatcher.observe_event(
    event_name=IRAEvents.SET_UP_SIMULATION_DONE_EVENT,
    on_event=on_setup_done,
    observer_name="setup_done_observer",
)
handle_data = dispatcher.observe_event(
    event_name=IRAEvents.DATA_GENERATION_DONE_EVENT,
    on_event=on_data_done,
    observer_name="data_done_observer",
)

config_path = get_config_file_path()
if config_path:
    target_config_path = Path(config_path).parent / "full_pipeline.yaml"
else:
    print("No config file path found")
    target_config_path = None

if target_config_path and load_config_file(target_config_path):
    temp_path = Path(tempfile.mkdtemp(prefix="IRA_Output_"))
    update_config("simulation_duration", 2.0)
    update_config("replicator.writers.IRABasicWriter.output_dir", str(temp_path))

    if RUN_SETUP:
        setup_simulation()
        print(f"Generating data to: {temp_path}")
        # When setup is done, SET_UP_SIMULATION_DONE_EVENT will fire
        # calling our local on_setup_done(), which in turn calls start_data_generation()

# If setup_simulation() was not run, the event callbacks never fire; unsubscribe here.
# When RUN_SETUP is True, on_setup_done/on_data_done reset the handles when events fire.
if not RUN_SETUP:
    handle_setup.reset()
    handle_data.reset()
