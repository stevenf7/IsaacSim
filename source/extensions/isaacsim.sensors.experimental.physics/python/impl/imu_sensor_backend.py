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

"""IMU sensor backend -- thin Python wrapper around the C++ IImuSensor plugin.

This module provides API-compatible ImuSensorBackend that delegates all
physics computation to the C++ plugin. The C++ backend uses IPrimDataReader
for velocity data and Pose.h for world transforms, supporting both PhysX
and Newton engines transparently.
"""
from __future__ import annotations

from .common import _PhysicsSensorBase

_INVALID_IMU_READING = None


def _get_invalid_imu_reading() -> object:
    global _INVALID_IMU_READING
    if _INVALID_IMU_READING is None:
        from .. import _physics_sensors

        _INVALID_IMU_READING = _physics_sensors.ImuSensorReading()
    return _INVALID_IMU_READING


class ImuSensorBackend(_PhysicsSensorBase):
    """Backend implementation for IMU sensors, backed by a C++ plugin.

    Delegates all physics-based IMU computation to the C++ IImuSensor
    Carbonite interface. Returns the C++ pybind struct directly for
    minimal per-read overhead.

    Args:
        prim_path: USD path to the IsaacImuSensor prim.

    Example:

    .. code-block:: python

        >>> from isaacsim.sensors.experimental.physics.impl.imu_sensor_backend import ImuSensorBackend

        >>> backend = ImuSensorBackend("/World/ImuSensor")  # doctest: +NO_CHECK
    """

    def _acquire_interface(self) -> object | None:
        from .extension import get_imu_sensor_interface

        return get_imu_sensor_interface()

    def _get_invalid_reading(self) -> object:
        return _get_invalid_imu_reading()

    def get_sensor_reading(self, read_gravity: bool = True) -> object:
        """Get the current IMU sensor reading.

        Args:
            read_gravity: Whether to include gravity in the reading.

        Returns:
            The C++ ImuSensorReading struct directly. Access fields via
            ``reading.linear_acceleration_x``, ``reading.orientation_w``, etc.
            An ``orientation`` property returns ``(w, x, y, z)`` as a tuple.
        """
        return self._get_reading(read_gravity)
