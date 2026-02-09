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
"""Omniverse extension entry point for physics-based sensors.

This module provides the extension lifecycle management for the
isaacsim.sensors.experimental.physics extension, initializing the sensor step
manager when the extension loads.
"""
from __future__ import annotations

import omni

from .common import _SensorStepManager

EXTENSION_NAME = "Isaac Sensor"


class Extension(omni.ext.IExt):
    """Omniverse extension class for physics-based sensors.

    Manages the lifecycle of the sensor step manager singleton which
    coordinates sensor updates with physics simulation events.
    """

    def on_startup(self, ext_id: str) -> None:
        """Initialize the extension when it is loaded.

        Creates the _SensorStepManager singleton to register physics
        and timeline callbacks for sensor coordination.

        Args:
            ext_id: Extension identifier provided by the extension manager.
        """
        # Initialize sensor manager to set up physics callbacks
        _SensorStepManager.instance()

    def on_shutdown(self) -> None:
        """Clean up resources when the extension is unloaded.

        Currently no cleanup is required as the sensor manager
        singleton handles its own callback lifecycle.
        """
