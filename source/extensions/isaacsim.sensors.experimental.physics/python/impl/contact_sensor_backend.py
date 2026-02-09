# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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
"""Contact sensor backend implementation.

This module provides the core physics-based contact sensor logic that:
- Processes raw PhysX contact events
- Applies radius and threshold filtering
- Computes contact forces from impulses
"""
from __future__ import annotations

from typing import cast

import numpy as np
import omni.isaac.IsaacSensorSchema as IsaacSensorSchema
from isaacsim.core.experimental.utils import prim as prim_utils
from isaacsim.core.experimental.utils import stage as stage_utils
from isaacsim.core.experimental.utils import xform as xform_utils
from isaacsim.core.simulation_manager import SimulationManager
from pxr import PhysicsSchemaTools

from .common import (
    ContactSensorReading,
    _ContactReportManager,
    _find_rigid_body_parent_path,
    _PhysicsSensorBase,
    _SensorStepManager,
    _to_numpy,
)


class ContactSensorBackend(_PhysicsSensorBase):
    """Backend implementation for contact sensors.

    Processes raw PhysX contact data to produce filtered sensor readings.
    Supports radius filtering and force thresholds.

    Args:
        prim_path: USD path to the IsaacContactSensor prim.

    Example:

    .. code-block:: python

        >>> from isaacsim.sensors.experimental.physics.impl.contact_sensor_backend import ContactSensorBackend

        >>> backend = ContactSensorBackend("/World/ContactSensor")  # doctest: +NO_CHECK
    """

    def __init__(self, prim_path: str) -> None:
        self._prim_path = prim_path

        # Validate prim type before attempting to resolve parent
        self._is_valid_sensor = self._check_sensor_prim_type()
        self._parent_prim_path, _ = _find_rigid_body_parent_path(prim_path) if self._is_valid_sensor else (None, False)
        self._parent_token = PhysicsSchemaTools.sdfPathToInt(self._parent_prim_path) if self._parent_prim_path else None

        # Latest reading (updated each physics step)
        self._latest_reading = ContactSensorReading()

        # Timing state
        self._time_seconds = 0.0  # Current simulation time
        self._time_delta = 0.0  # Physics timestep

        # Sensor configuration (read from USD attributes)
        self._radius = -1.0  # Negative means no radius filtering
        self._min_threshold = 0.0
        self._max_threshold = 100000.0

        self._enabled = True
        self._previous_enabled = True

        # Step tracking for on-demand updates
        self._last_step_time = -1.0
        self._last_physics_step = -1
        self._initialized = False

        # Get contact manager singleton for raw contact data
        self._contact_manager = _ContactReportManager.instance()

        # Register with step manager for physics callbacks
        _SensorStepManager.instance().register(self)

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

    def _refresh_from_prim(self) -> None:
        """Update sensor configuration from USD prim attributes.

        Reads enabled, threshold, and radius attributes from the IsaacContactSensor prim.
        """
        stage = stage_utils.get_current_stage(backend="usd")
        prim = stage.GetPrimAtPath(self._prim_path)
        if not prim.IsValid():
            self._is_valid_sensor = False
            return

        # Re-validate prim type in case it changed
        self._is_valid_sensor = prim.GetTypeName() == "IsaacContactSensor"
        if not self._is_valid_sensor:
            return

        # Resolve parent rigid body if not yet done
        if self._parent_token is None:
            self._parent_prim_path, _ = _find_rigid_body_parent_path(self._prim_path)
            self._parent_token = (
                PhysicsSchemaTools.sdfPathToInt(self._parent_prim_path) if self._parent_prim_path else None
            )

        typed_prim = IsaacSensorSchema.IsaacContactSensor(prim)

        # Read enabled state
        enabled_attr = typed_prim.GetEnabledAttr()
        if enabled_attr.IsValid():
            enabled_value = enabled_attr.Get()
            self._enabled = enabled_value if enabled_value is not None else True
        else:
            self._enabled = True

        # Read force thresholds
        threshold_attr = typed_prim.GetThresholdAttr()
        if threshold_attr.IsValid():
            threshold = threshold_attr.Get()
            if threshold:
                self._min_threshold = float(threshold[0])
                self._max_threshold = float(threshold[1])

        # Read contact radius
        radius_attr = typed_prim.GetRadiusAttr()
        if radius_attr.IsValid():
            radius = radius_attr.Get()
            if radius is not None:
                self._radius = float(radius)

    def on_physics_step(self, step_dt: float) -> None:
        """Process contact data for the current physics step.

        Called by _SensorStepManager after each physics step.
        Updates the sensor reading based on raw contact events.

        Args:
            step_dt: Duration of the physics step in seconds.
        """
        self._refresh_from_prim()
        self._time_delta = float(step_dt)
        self._time_seconds = float(SimulationManager.get_simulation_time())
        self._last_step_time = self._time_seconds
        self._last_physics_step = SimulationManager.get_num_physics_steps()

        if not self._is_valid_sensor:
            return

        # Handle enabled state changes
        if self._previous_enabled != self._enabled:
            if not self._enabled:
                self._latest_reading = ContactSensorReading()
                self._initialized = False
            self._previous_enabled = self._enabled

        if not self._enabled or self._parent_token is None:
            return

        # Get raw contacts for parent body and process them
        raw_contacts = self._contact_manager.get_raw_contacts_for_body(self._parent_token)
        self._latest_reading = self._process_raw_contacts(raw_contacts)
        self._initialized = True

    def on_timeline_stop(self) -> None:
        """Reset sensor state when timeline stops.

        Clears all readings and timing state to prepare for next simulation.
        """
        self._latest_reading = ContactSensorReading()
        self._time_seconds = 0.0
        self._time_delta = 0.0
        self._last_step_time = -1.0
        self._last_physics_step = -1
        self._initialized = False

    def _process_raw_contacts(self, raw_contacts: list[dict[str, object]]) -> ContactSensorReading:
        """Convert raw contact events into a sensor reading.

        Filters contacts by radius, accumulates impulses, converts to force,
        and applies threshold filtering.

        Args:
            raw_contacts: Contact dictionaries from the contact report manager.

        Returns:
            Reading with computed force value and contact state.
        """
        reading = ContactSensorReading(time=self._time_seconds)
        if not raw_contacts:
            return reading

        # Get sensor world position for radius filtering
        sensor_position, _ = xform_utils.get_world_pose(self._prim_path)
        sensor_position = _to_numpy(sensor_position)

        # Accumulate impulses from all qualifying contacts
        total_impulse = np.zeros(3, dtype=np.float64)
        for entry in raw_contacts:
            position_dict = cast(dict[str, float], entry["position"])
            position = np.array([position_dict["x"], position_dict["y"], position_dict["z"]], dtype=np.float64)

            # Radius filtering: skip contacts outside sensor radius
            distance = np.linalg.norm(sensor_position - position)
            if self._radius > 0.0 and distance >= self._radius:
                continue

            impulse_dict = cast(dict[str, float], entry["impulse"])
            impulse = np.array([impulse_dict["x"], impulse_dict["y"], impulse_dict["z"]], dtype=np.float64)

            # Invert impulse if parent is body1 (impulse direction is from body0 to body1)
            should_invert = cast(int, entry["body1"]) == self._parent_token
            if should_invert:
                impulse = -impulse
            total_impulse += impulse

        # No valid contacts after filtering
        if np.linalg.norm(total_impulse) <= 0.0:
            return reading

        # Convert impulse to force: F = impulse / dt
        dt_value = cast(float | int, raw_contacts[0].get("dt", self._time_delta)) if raw_contacts else self._time_delta
        dt = float(dt_value)
        if dt <= 0.0:
            dt = self._time_delta if self._time_delta > 0 else 1.0 / 60.0

        force_value = float(np.linalg.norm(total_impulse) / dt)

        # Apply threshold filtering
        force_value = min(force_value, self._max_threshold)
        if force_value < self._min_threshold:
            reading.value = 0.0
            reading.in_contact = False
            return reading

        reading.value = force_value
        reading.in_contact = True
        return reading

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
        # Validate prim still exists
        if not prim_utils.get_prim_at_path(self._prim_path).IsValid():
            return ContactSensorReading(is_valid=False, time=0.0)

        # Check sensor type is valid
        if not self._is_valid_sensor:
            return ContactSensorReading(is_valid=False, time=0.0)

        # Ensure we have current data if simulation is running
        if SimulationManager.is_simulating():
            current_step = SimulationManager.get_num_physics_steps()
            if current_step != self._last_physics_step:
                self.on_physics_step(SimulationManager.get_physics_dt())

        # Return invalid if sensor is disabled
        if not self._enabled:
            return ContactSensorReading(is_valid=False, time=0.0)

        reading = self._latest_reading
        reading.is_valid = True
        return reading

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
        if self._parent_token is None or not self._is_valid_sensor:
            return []
        return self._contact_manager.get_raw_contacts_for_body(self._parent_token)

    @property
    def parent_token(self) -> int | None:
        """Get the physics token of the parent rigid body.

        Returns:
            Integer token identifying the parent rigid body, or None if
            no parent was found.
        """
        return self._parent_token
