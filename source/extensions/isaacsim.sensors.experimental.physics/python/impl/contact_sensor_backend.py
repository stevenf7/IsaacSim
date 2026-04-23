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

"""Contact sensor backend -- thin Python wrapper around the C++ IContactSensor plugin.

This module provides an API-compatible ContactSensorBackend that delegates all
physics computation to the C++ plugin. The C++ backend uses PhysX
getFullContactReport() for contact data, supporting both readings and raw
contact retrieval without any Python callback relay.
"""
from __future__ import annotations

from isaacsim.core.experimental.utils import prim as prim_utils
from isaacsim.core.experimental.utils import stage as stage_utils
from isaacsim.core.simulation_manager import SimulationManager

from .common import (
    ContactSensorReading,
    _PhysicsSensorBase,
)


class ContactSensorBackend(_PhysicsSensorBase):
    """Backend implementation for contact sensors, backed by a C++ plugin.

    Delegates all physics-based contact processing to the C++ IContactSensor
    Carbonite interface. Provides a Python API for reading contact values
    and raw contact data.

    Sensor creation is deferred until the first call that needs it, to handle
    the case where the backend is instantiated before the simulation starts.

    Args:
        prim_path: USD path to the IsaacContactSensor prim.

    Example:

    .. code-block:: python

        >>> from isaacsim.sensors.experimental.physics.impl.contact_sensor_backend import ContactSensorBackend

        >>> backend = ContactSensorBackend("/World/ContactSensor")  # doctest: +NO_CHECK
    """

    def __init__(self, prim_path: str) -> None:
        super().__init__(prim_path)
        self._is_valid_sensor = self._check_sensor_prim_type()
        self._latest_reading = ContactSensorReading()
        self._last_physics_step = -1

    def _acquire_interface(self) -> object | None:
        from .extension import get_contact_sensor_interface

        return get_contact_sensor_interface()

    def _get_invalid_reading(self) -> object:
        return ContactSensorReading()

    def _check_sensor_prim_type(self) -> bool:
        """Verify that the prim is an IsaacContactSensor type.

        Returns:
            True if the prim exists and is an IsaacContactSensor, False otherwise.
        """
        stage = stage_utils.get_current_stage(backend="usd")
        prim = stage.GetPrimAtPath(self._prim_path)
        if not prim.IsValid():
            return False
        return prim.GetTypeName() == "IsaacContactSensor"

    def on_physics_step(self, step_dt: float) -> None:
        """Called by _SensorStepManager after each physics step.

        Reads the latest C++ sensor reading and caches it locally.

        Args:
            step_dt: Duration of the physics step in seconds.
        """
        self._last_physics_step = SimulationManager.get_num_physics_steps()

        if not self._is_valid_sensor:
            return

        if not self._ensure_sensor():
            return

        cpp_reading = self._iface.get_sensor_reading(self._prim_path)
        if not cpp_reading.is_valid and self._sensor_created:
            self._sensor_created = False
            if self._ensure_sensor():
                cpp_reading = self._iface.get_sensor_reading(self._prim_path)

        self._latest_reading = cpp_reading

    def on_timeline_stop(self) -> None:
        """Reset sensor state when timeline stops."""
        super().on_timeline_stop()
        self._latest_reading = ContactSensorReading()
        self._last_physics_step = -1

    def get_sensor_reading(self) -> ContactSensorReading:
        """Get the current contact sensor reading.

        Returns:
            Reading with contact state and force value. Returns invalid reading
            if sensor is disabled or prim is invalid.

        Example:

        .. code-block:: python

            >>> reading = backend.get_sensor_reading()  # doctest: +NO_CHECK
            >>> reading.is_valid  # doctest: +NO_CHECK
            False
        """
        if not prim_utils.get_prim_at_path(self._prim_path).IsValid():
            return ContactSensorReading(is_valid=False, time=0.0)

        if not self._is_valid_sensor:
            return ContactSensorReading(is_valid=False, time=0.0)

        if not self._ensure_sensor():
            return ContactSensorReading(is_valid=False, time=0.0)

        if SimulationManager.is_simulating():
            current_step = SimulationManager.get_num_physics_steps()
            if current_step != self._last_physics_step:
                self.on_physics_step(SimulationManager.get_physics_dt())

        return self._latest_reading

    def get_raw_data(self) -> list[dict[str, object]]:
        """Get raw contact data for the sensor's parent body.

        Returns:
            Raw contact dictionaries containing body0, body1, position, normal,
            impulse, time, and dt fields. Empty when sensor is invalid.

        Example:

        .. code-block:: python

            >>> raw = backend.get_raw_data()  # doctest: +NO_CHECK
            >>> len(raw)  # doctest: +NO_CHECK
            0
        """
        if not self._is_valid_sensor:
            return []

        if not self._ensure_sensor():
            return []

        return self._iface.get_raw_contacts(self._prim_path)

    @property
    def parent_token(self) -> int | None:
        """Get the physics token of the parent rigid body.

        Returns:
            Integer token identifying the parent rigid body, or None if
            no parent was found.
        """
        return None
