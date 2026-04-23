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

"""Joint state sensor backend -- thin Python wrapper around the C++ IJointStateSensor plugin.

Delegates all physics computation to the C++ plugin, which uses IArticulationDataView
for engine-agnostic articulation DOF data access. The C++ JointStateSensorReading
carries the complete reading (dof_count, dof_names, positions, velocities, efforts).
"""
from __future__ import annotations

from .common import _PhysicsSensorBase

_INVALID_JOINT_STATE_READING = None


def _get_invalid_reading() -> object:
    global _INVALID_JOINT_STATE_READING
    if _INVALID_JOINT_STATE_READING is None:
        from .. import _physics_sensors

        _INVALID_JOINT_STATE_READING = _physics_sensors.JointStateSensorReading()
    return _INVALID_JOINT_STATE_READING


class JointStateSensorBackend(_PhysicsSensorBase):
    """Backend implementation for joint state sensors, backed by a C++ plugin.

    Returns the C++ JointStateSensorReading struct directly from get_sensor_reading().
    The reading carries the complete state: dof_count, dof_names, positions,
    velocities, and efforts — all accessible as properties on the returned object.

    Args:
        articulation_prim_path: USD path to the articulation root prim.
    """

    def __init__(self, articulation_prim_path: str) -> None:
        super().__init__(articulation_prim_path)

    def _acquire_interface(self) -> object | None:
        from .extension import get_joint_state_sensor_interface

        return get_joint_state_sensor_interface()

    def _get_invalid_reading(self) -> object:
        return _get_invalid_reading()

    def get_sensor_reading(self) -> object:
        """Get the complete joint state reading.

        Returns:
            The C++ JointStateSensorReading struct with dof_count, dof_names,
            positions, velocities, and efforts populated when is_valid is True.
        """
        return self._get_reading()
