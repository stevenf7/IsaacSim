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

from .common import (
    _PhysicsSensorBase,
    _SensorStepManager,
)


def _get_raycast_interface() -> object | None:
    from .extension import get_raycast_sensor_interface

    return get_raycast_sensor_interface()


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

    def __init__(self, prim_path: str):
        self._prim_path = prim_path
        self._sensor_created: bool = False
        self._iface = None
        _SensorStepManager.instance().register(self)

    def _ensure_sensor(self) -> bool:
        """Ensure the raycast sensor is created and initialized.

        Returns:
            True if the sensor is created and initialized, False otherwise.
        """
        if self._iface is None:
            self._iface = _get_raycast_interface()
        if self._iface is None:
            return False
        if self._sensor_created:
            return True
        self._sensor_created = self._iface.create_sensor(self._prim_path)
        return self._sensor_created

    def get_sensor_reading(self) -> object:
        """Get the current raycast sensor reading.

        Returns:
            The C++ RaycastSensorReading struct. Access fields via
            ``reading.depths``, ``reading.hit_positions``, etc.
        """
        if not self._sensor_created and not self._ensure_sensor():
            return _get_invalid_raycast_reading()

        reading = self._iface.get_sensor_reading(self._prim_path)
        if not reading.is_valid:
            self._sensor_created = False
            if not self._ensure_sensor():
                return _get_invalid_raycast_reading()
            reading = self._iface.get_sensor_reading(self._prim_path)
        return reading

    def on_physics_step(self, step_dt: float):
        """Handle physics step events.

        Args:
            step_dt: Physics step duration in seconds.
        """

    def on_timeline_stop(self):
        """Handle timeline stop events."""
        self._sensor_created = False
        self._iface = None

    def reset(self):
        """Reset the raycast sensor.

        Removes the sensor from the simulation and resets state.
        """
        if self._iface is not None and self._sensor_created:
            self._iface.remove_sensor(self._prim_path)
        self._sensor_created = False
