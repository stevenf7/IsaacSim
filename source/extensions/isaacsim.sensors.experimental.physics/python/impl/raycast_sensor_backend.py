# SPDX-FileCopyrightText: Copyright (c) 2025-2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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

"""Raycast sensor backend -- thin Python wrapper around the C++ IRaycastSensor plugin."""
from __future__ import annotations

from .common import _PhysicsSensorBase

_INVALID_RAYCAST_READING = None


def _get_invalid_raycast_reading() -> object:
    global _INVALID_RAYCAST_READING
    if _INVALID_RAYCAST_READING is None:
        from .. import _physics_sensors

        _INVALID_RAYCAST_READING = _physics_sensors.RaycastSensorReading()
    return _INVALID_RAYCAST_READING


class RaycastSensorBackend(_PhysicsSensorBase):
    """Backend implementation for raycast sensors, backed by a C++ plugin.

    Args:
        prim_path: USD path to the IsaacRaycastSensor prim.
    """

    def _acquire_interface(self) -> object | None:
        from .extension import get_raycast_sensor_interface

        return get_raycast_sensor_interface()

    def _get_invalid_reading(self) -> object:
        return _get_invalid_raycast_reading()

    def get_sensor_reading(self) -> object:
        """Get the current raycast sensor reading.

        Returns:
            The C++ RaycastSensorReading struct. Access fields via
            ``reading.depths``, ``reading.hit_positions``, etc.
        """
        return self._get_reading()
