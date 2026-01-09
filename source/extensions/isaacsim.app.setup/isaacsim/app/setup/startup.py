# SPDX-FileCopyrightText: Copyright (c) 2018-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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

"""Startup task utilities for Isaac Sim application.

This module provides async functions for handling application startup tasks
including viewport initialization, ROS bridge enabling, and benchmark recording.
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Callable

import carb
import omni.kit.app
import omni.kit.stage_templates as stage_templates
import omni.usd

if TYPE_CHECKING:
    from carb.settings import ISettings
    from omni.kit.app import IApp, IExtensionManager


async def create_new_stage(update_callback: Callable[[], None]) -> None:
    """Create a new empty stage on startup.

    Args:
        update_callback: Async callback to update the app without signaling ready.
    """
    await update_callback()
    if omni.usd.get_context().can_open_stage():
        stage_templates.new_stage(template=None)
    await update_callback()


async def await_viewport(
    app: IApp,
    ext_manager: IExtensionManager,
    app_title: str,
    update_callback: Callable[[], None],
) -> None:
    """Wait for viewport to be ready and log application startup completion.

    Monitors the viewport for initialization and triggers startup benchmarking
    when the application is ready for use.

    Args:
        app: The Kit application instance.
        ext_manager: Extension manager for checking enabled extensions.
        app_title: Application title for logging.
        update_callback: Async callback to update the app without signaling ready.
    """
    import carb.eventdispatcher
    from omni.kit.viewport.utility import get_active_viewport
    from omni.usd import StageRenderingEventType

    viewport_api = get_active_viewport()

    # Wait for viewport handle if not already available
    if viewport_api.frame_info.get("viewport_handle", None) is None:
        future: asyncio.Future = asyncio.Future()

        def on_frame_event(e: carb.eventdispatcher.Event) -> None:
            vp_handle = viewport_api.frame_info.get("viewport_handle", None)
            if vp_handle is not None and not future.done():
                future.set_result(None)

        usd_context = omni.usd.get_context()
        event_name = usd_context.stage_rendering_event_name(StageRenderingEventType.NEW_FRAME, True)
        sub = carb.eventdispatcher.get_eventdispatcher().observe_event(
            event_name=event_name,
            on_event=on_frame_event,
            observer_name="isaacsim.app.setup.wait_for_viewport",
        )
        while not future.done():
            await update_callback()
        sub = None

    app.print_and_log(f"{app_title} App is loaded.")
    record_startup_benchmark(ext_manager)
    await update_callback()


def record_startup_benchmark(ext_manager: IExtensionManager) -> None:
    """Record startup time as a benchmark metric if benchmarking is enabled.

    Args:
        ext_manager: Extension manager for checking if benchmarking extension is enabled.
    """
    if ext_manager.is_extension_enabled("isaacsim.benchmark.services"):
        from isaacsim.benchmark.services import BaseIsaacBenchmark

        benchmark = BaseIsaacBenchmark(
            benchmark_name="app_startup",
            workflow_metadata={
                "metadata": [
                    {"name": "mode", "data": "async"},
                ]
            },
        )
        benchmark.set_phase("startup", start_recording_frametime=False, start_recording_runtime=False)
        benchmark.store_measurements()
        benchmark.stop()


async def enable_ros_bridge(
    settings: ISettings,
    ext_manager: IExtensionManager,
    update_callback: Callable[[], None],
) -> None:
    """Enable the ROS bridge extension if configured in settings.

    Args:
        settings: Carb settings interface for reading configuration.
        ext_manager: Extension manager for enabling extensions.
        update_callback: Async callback to update the app without signaling ready.
    """
    try:
        ros_bridge_name = settings.get("isaac/startup/ros_bridge_extension")
        if ros_bridge_name:
            await update_callback()
            ext_manager.set_extension_enabled_immediate(ros_bridge_name, True)
            await update_callback()
    except Exception:
        carb.log_warn("isaacsim.app.setup shutdown before ros bridge enabled")


async def enable_ros_sim_control(
    settings: ISettings,
    ext_manager: IExtensionManager,
    update_callback: Callable[[], None],
) -> None:
    """Enable the ROS simulation control extension if configured in settings.

    Args:
        settings: Carb settings interface for reading configuration.
        ext_manager: Extension manager for enabling extensions.
        update_callback: Async callback to update the app without signaling ready.
    """
    try:
        ros_sim_control_enabled = settings.get("isaac/startup/ros_sim_control_extension")
        if ros_sim_control_enabled:
            await update_callback()
            ext_manager.set_extension_enabled_immediate("isaacsim.ros2.sim_control", True)
            await update_callback()
    except Exception:
        carb.log_warn("isaacsim.app.setup shutdown before sim control enabled")
