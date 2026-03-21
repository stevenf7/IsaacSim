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

"""Effort sensor backend -- thin Python wrapper around the C++ IEffortSensor plugin.

This module provides an API-compatible EffortSensorBackend that delegates all
physics computation to the C++ plugin. The C++ backend uses IPrimDataReader
for articulation DOF effort data, supporting both PhysX and Newton engines
transparently.
"""
from __future__ import annotations


def _get_effort_interface() -> object | None:
    from .extension import get_effort_sensor_interface

    return get_effort_sensor_interface()


_INVALID_EFFORT_READING = None


def _get_invalid_effort_reading() -> object:
    global _INVALID_EFFORT_READING
    if _INVALID_EFFORT_READING is None:
        from .. import _physics_sensors

        _INVALID_EFFORT_READING = _physics_sensors.EffortSensorReading()
    return _INVALID_EFFORT_READING


class EffortSensorBackend:
    """Backend implementation for effort sensors, backed by a C++ plugin.

    Returns the C++ EffortSensorReading struct directly for minimal
    per-read overhead.

    Args:
        joint_prim_path: USD path to the joint prim.
    """

    def __init__(self, joint_prim_path: str) -> None:
        self._joint_prim_path = joint_prim_path
        self._sensor_created: bool = False
        self._iface = None

    def _ensure_sensor(self) -> bool:
        if self._iface is None:
            self._iface = _get_effort_interface()
        if self._iface is None:
            return False
        if self._sensor_created:
            return True
        self._sensor_created = self._iface.create_sensor(self._joint_prim_path)
        return self._sensor_created

    def get_sensor_reading(self) -> object:
        """Get the current effort sensor reading.

        Returns the C++ EffortSensorReading struct directly.
        """
        if not self._sensor_created and not self._ensure_sensor():
            return _get_invalid_effort_reading()

        reading = self._iface.get_sensor_reading(self._joint_prim_path)
        if not reading.is_valid:
            self._sensor_created = False
            if not self._ensure_sensor():
                return _get_invalid_effort_reading()
            reading = self._iface.get_sensor_reading(self._joint_prim_path)
        return reading

    def on_timeline_stop(self) -> None:
        self._sensor_created = False
        self._iface = None

    def reset(self) -> None:
        if self._iface is not None and self._sensor_created:
            self._iface.remove_sensor(self._joint_prim_path)
        self._sensor_created = False
