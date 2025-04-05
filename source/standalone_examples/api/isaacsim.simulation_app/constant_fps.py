# SPDX-FileCopyrightText: Copyright (c) 2024-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: LicenseRef-NvidiaProprietary
#
# NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
# property and proprietary rights in and to this material, related
# documentation and any modifications thereto. Any use, reproduction,
# disclosure or distribution of this material and related documentation
# without an express license agreement from NVIDIA CORPORATION or
# its affiliates is strictly prohibited.

import time

from isaacsim import SimulationApp

# Simple example showing how to fix frame rate to (roughly) a constant value (with respect to wall-clock)
# Note frame rate cannot be set artificially higher than what the sim will run at on the current hardware,
# but it can be kept artificially lower for (eg.) synchronization with an external service.

DESIRED_FRAME_RATE = 10.0  # frames per second
frame_period_s = 1.0 / DESIRED_FRAME_RATE

simulation_app = SimulationApp({"headless": True})

import carb
import omni

# Callback to measure app update time as precisely as possible
last_frametime_timestamp_ns = 0.0
app_update_time_s = 0.0


def update_event_callback(event: carb.events.IEvent):
    timestamp_ns = time.perf_counter_ns()
    app_update_time_s = round((timestamp_ns - last_frametime_timestamp_ns) / 1e9, 9)
    last_frametime_timestamp_ns = timestamp_ns


carb.eventdispatcher.get_eventdispatcher().observe_event(
    event_name=omni.kit.app.GLOBAL_EVENT_UPDATE,
    on_event=update_event_callback,
    observer_name="constant_fps.update_event_callback",
)

while simulation_app.is_running():
    # Measure duration of single app update
    simulation_app.update()
    # Sleep for the duration of the fixed frame
    sleep_duration_s = frame_period_s - app_update_time_s
    if sleep_duration_s <= 0.0:
        carb.log_warn(f"simulation_app.update() took {app_update_time_s} s >= fixed period {frame_period_s} s.")
    else:
        time.sleep(sleep_duration_s)
    instantaneous_fps = 1.0 / max(frame_period_s, app_update_time_s)
    carb.log_warn(f"FPS is {instantaneous_fps}")

simulation_app.close()
