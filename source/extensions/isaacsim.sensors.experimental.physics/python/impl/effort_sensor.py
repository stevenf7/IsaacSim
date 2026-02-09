# SPDX-FileCopyrightText: Copyright (c) 2021-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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
"""Effort sensor for measuring joint torques.

This module provides the EffortSensor class for reading joint effort
(torque/force) values from articulated physics bodies.
"""
from __future__ import annotations

from typing import Any

import carb
import carb.eventdispatcher
import numpy as np
import omni.kit.utils
import omni.physics.core
import omni.timeline
import omni.usd
from isaacsim.core.experimental.prims import Articulation
from isaacsim.core.experimental.utils import prim as prim_utils
from isaacsim.core.simulation_manager import SimulationManager
from pxr import UsdPhysics


class EffortSensorReading:
    """Effort sensor reading data.

    Args:
        is_valid: Whether this reading contains valid data.
        time: Simulation time when the reading was taken.
        value: Effort (torque/force) value at the joint.
    """

    def __init__(self, is_valid: bool = False, time: float = 0, value: float = 0) -> None:
        self.is_valid = is_valid
        self.time = time
        self.value = value


class EffortSensor(Articulation):
    """Sensor for measuring joint effort (torque/force).

    Reads effort values from an articulated body's joint using the physics
    tensor API.

    Args:
        prim_path: USD path to the joint, formatted as articulation_path/joint_name.
        enabled: Whether the sensor is initially enabled.

    Raises:
        RuntimeError: If no articulation root is found in the prim hierarchy.

    Example:

        .. code-block:: python

            from isaacsim.sensors.experimental.physics import EffortSensor

            # Create sensor for a robot joint
            sensor = EffortSensor("/World/Robot/joint_1")

            # Read joint effort
            reading = sensor.get_sensor_reading()
            if reading.is_valid:
                print(f"Joint torque: {reading.value}")
    """

    def __init__(self, prim_path: str, enabled: bool = True) -> None:
        # Initialize callback list early for safe cleanup if init fails
        self._callback_ids: list[Any] = []
        self.current_time = 0.0
        self.enabled = enabled

        # Circular buffer for sensor readings
        self.data_buffer_size = 10
        self.sensor_reading_buffer = [EffortSensorReading() for i in range(self.data_buffer_size)]

        self.physics_num_steps = 0.0
        self.is_initialized = False
        self.dof: Any = None
        self.dof_indices: Any = None

        # Parse path to get articulation body and joint name
        self.body_prim_path = "/".join(prim_path.split("/")[:-1])
        self.dof_name = prim_path.split("/")[-1]

        # Find articulation root in hierarchy
        articulation_root = prim_utils.get_first_matching_parent_prim(
            self.body_prim_path,
            predicate=lambda prim, _: prim_utils.has_api(prim, UsdPhysics.ArticulationRootAPI),
            include_self=True,
        )
        if articulation_root is None:
            raise RuntimeError(f"Unable to find articulation root for path: {self.body_prim_path}")

        super().__init__(paths=prim_utils.get_prim_path(articulation_root))
        self.initialize_callbacks()
        return

    def initialize_callbacks(self) -> None:
        """Register physics and timeline event callbacks."""
        self._acquisition_callback = (
            omni.physics.core.get_physics_simulation_interface().subscribe_physics_on_step_events(
                pre_step=False, order=0, on_update=self._data_acquisition_callback
            )
        )

        self._stage_open_callback = carb.eventdispatcher.get_eventdispatcher().observe_event(
            event_name=omni.usd.get_context().stage_event_name(omni.usd.StageEventType.OPENED),
            on_event=self._stage_open_callback_fn,
            observer_name="isaacsim.sensors.experimental.physics.EffortSensor.initialize._stage_open_callback",
        )

        timeline = omni.timeline.get_timeline_interface()
        self._timer_reset_callback_stop = carb.eventdispatcher.get_eventdispatcher().observe_event(
            event_name=omni.timeline.GLOBAL_EVENT_STOP,
            on_event=self._timeline_stop_callback_fn,
            observer_name="isaacsim.sensors.experimental.physics.EffortSensor.initialize._timeline_stop_callback",
        )
        self._timer_reset_callback_play = carb.eventdispatcher.get_eventdispatcher().observe_event(
            event_name=omni.timeline.GLOBAL_EVENT_PLAY,
            on_event=self._timeline_play_callback_fn,
            observer_name="isaacsim.sensors.experimental.physics.EffortSensor.initialize._timeline_play_callback",
        )

    def _stage_open_callback_fn(self, event: Any = None) -> None:
        self._acquisition_callback = None
        self._timer_reset_callback_stop = None
        self._timer_reset_callback_play = None
        self._stage_open_callback = None
        return

    def _timeline_stop_callback_fn(self, event: Any) -> None:
        self.current_time = 0
        self.sensor_reading_buffer = [EffortSensorReading() for i in range(self.data_buffer_size)]
        self.physics_num_steps = 0
        return

    def _timeline_play_callback_fn(self, event: Any) -> None:
        self.is_initialized = False
        return

    def _data_acquisition_callback(self, step_size: float, context: Any) -> None:
        self.current_time = float(SimulationManager.get_simulation_time())
        self.physics_num_steps = float(SimulationManager.get_num_physics_steps())

        # Wait for physics to stabilize (2 steps)
        if self.physics_num_steps <= 2:
            return

        # Initialize DOF indices on first valid step
        elif not self.is_initialized:
            if not self.is_physics_tensor_entity_initialized():
                return
            try:
                self.dof_indices = self.get_dof_indices(self.dof_name)
            except AssertionError:
                self.dof_indices = None
            self.is_initialized = True

        # Handle invalid DOF
        if self.dof_indices is None:
            self.sensor_reading_buffer.insert(0, EffortSensorReading())
            self.sensor_reading_buffer.pop()
            self.sensor_reading_buffer[0].time = 0.0
            self.sensor_reading_buffer[0].value = 0.0
            self.sensor_reading_buffer[0].is_valid = False
            return

        if self.enabled:
            # Read effort from physics tensor API
            efforts = self.get_dof_projected_joint_forces(dof_indices=self.dof_indices)
            self.sensor_reading_buffer.insert(0, EffortSensorReading())
            self.sensor_reading_buffer.pop()

            self.sensor_reading_buffer[0].time = self.current_time

            effort_value = self._extract_effort_value(efforts)
            if effort_value is None:
                self.sensor_reading_buffer[0].value = 0.0
                self.sensor_reading_buffer[0].is_valid = False
                carb.log_warn(
                    f"Effort sensor error, none or multiple efforts found for path:  {self.prim_path} with joint {self.dof_name}"
                )
            else:
                self.sensor_reading_buffer[0].value = effort_value
                self.sensor_reading_buffer[0].is_valid = True

    def get_sensor_reading(self) -> EffortSensorReading:
        """Get the current effort sensor reading.

        Returns:
            Reading with effort value and validity state.

        Example:

        .. code-block:: python

            >>> reading = sensor.get_sensor_reading()  # doctest: +NO_CHECK
            >>> reading.is_valid  # doctest: +NO_CHECK
            False
        """
        if not self.enabled:
            return EffortSensorReading()
        latest = self.sensor_reading_buffer[0]
        if not latest.is_valid:
            return EffortSensorReading()
        return EffortSensorReading(is_valid=True, time=latest.time, value=latest.value)

    def update_dof_name(self, dof_name: str) -> None:
        """Update the DOF (degree of freedom) name being measured.

        Args:
            dof_name: Name of the joint DOF to monitor.

        Example:

        .. code-block:: python

            >>> sensor.update_dof_name("joint_1")
        """
        if self.physics_num_steps <= 2:
            carb.log_warn("unable to update path, please call again after 3 physics steps")
            return

        self.dof_name = dof_name
        try:
            self.dof_indices = self.get_dof_indices(self.dof_name)
        except AssertionError:
            carb.log_warn("unable to find joint corresponding to the dof name, disabling sensor")
            self.dof_indices = None

        if self.dof_indices is None:
            self.is_initialized = False

    def change_buffer_size(self, new_buffer_size: int) -> None:
        """Change the size of the sensor reading buffer.

        Args:
            new_buffer_size: New buffer size (number of readings to store).

        Example:

        .. code-block:: python

            >>> sensor.change_buffer_size(4)
        """
        self.sensor_reading_buffer = np.resize(np.array(self.sensor_reading_buffer), new_buffer_size).tolist()
        self.data_buffer_size = new_buffer_size

    def _extract_effort_value(self, efforts: Any) -> float | None:
        if efforts is None:
            return None

        if hasattr(efforts, "numpy"):
            efforts = efforts.numpy()

        efforts = np.array(efforts)
        if efforts.size < 1:
            return None

        return float(efforts.reshape(-1)[0])
