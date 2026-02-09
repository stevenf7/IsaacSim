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
"""IMU sensor backend implementation.

This module provides the core physics-based IMU sensor logic that:
- Captures linear velocity and angular velocity from the physics simulation
- Computes linear acceleration from velocity differences between steps
- Applies rolling average filters to smooth acceleration, velocity, and orientation
- Transforms measurements from world frame to sensor local frame
"""
from __future__ import annotations

import numpy as np
import omni.isaac.IsaacSensorSchema as IsaacSensorSchema
from isaacsim.core.experimental.prims import RigidPrim
from isaacsim.core.experimental.utils import stage as stage_utils
from isaacsim.core.experimental.utils import transform as transform_utils
from isaacsim.core.experimental.utils import xform as xform_utils
from isaacsim.core.simulation_manager import SimulationManager
from pxr import UsdGeom, UsdPhysics

from .common import (
    IMURawData,
    IMUSensorReading,
    Quaternion,
    _clone_imu_reading,
    _find_rigid_body_parent_path,
    _normalize_quaternion,
    _PhysicsSensorBase,
    _quat_multiply,
    _sanitize_vector,
    _SensorStepManager,
    _to_numpy,
)


class ImuSensorBackend(_PhysicsSensorBase):
    """Backend implementation for IMU (Inertial Measurement Unit) sensors.

    Processes rigid body physics data to produce filtered IMU readings including
    linear acceleration, angular velocity, and orientation. Supports configurable
    filter widths for noise reduction.

    The sensor operates in the following coordinate frame:
    - Measurements are transformed from world frame to sensor local frame
    - Gravity can optionally be included in acceleration readings
    - Orientation is reported in world frame

    Args:
        prim_path: USD path to the IsaacImuSensor prim.

    Example:

    .. code-block:: python

        >>> from isaacsim.sensors.experimental.physics.impl.imu_sensor_backend import ImuSensorBackend

        >>> backend = ImuSensorBackend("/World/ImuSensor")  # doctest: +NO_CHECK
    """

    def __init__(self, prim_path: str) -> None:
        self._prim_path = prim_path

        # Find parent rigid body for velocity data
        self._parent_prim_path, self._is_articulation_link = _find_rigid_body_parent_path(prim_path)
        self._rigid_prim = RigidPrim(self._parent_prim_path) if self._parent_prim_path else None

        # Sensor configuration from USD attributes
        self._linear_acceleration_filter = 1  # Rolling average window for acceleration
        self._angular_velocity_filter = 1  # Rolling average window for angular velocity
        self._orientation_filter = 1  # Rolling average window for orientation

        # Raw data buffer for velocity history (used to compute acceleration)
        self._raw_buffer_size = 20
        self._raw_buffer = [IMURawData() for _ in range(self._raw_buffer_size)]

        # Processed sensor readings
        self._sensor_readings = [IMUSensorReading() for _ in range(self._raw_buffer_size)]

        # Timing state
        self._time_seconds = 0.0  # Current simulation time
        self._time_delta = 0.0  # Physics timestep

        # Gravity vectors (world and sensor frame)
        self._gravity = np.array([0.0, 0.0, 0.0], dtype=np.float64)
        self._gravity_sensor_frame = np.array([0.0, 0.0, 0.0], dtype=np.float64)

        # Enabled state tracking
        self._enabled = True
        self._previous_enabled = True

        # Step tracking for on-demand updates
        self._last_step_time = -1.0
        self._last_physics_step = -1

        # Local transform from parent to sensor
        self._sensor_local_translation = np.zeros(3, dtype=np.float64)
        self._sensor_local_orientation = np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float64)

        # Fallback gravity computation when physics hasn't started
        self._gravity_no_physics_delay_s = 1.0
        self._gravity_no_physics_ready = False

        # Register with step manager for physics callbacks
        _SensorStepManager.instance().register(self)

    def _refresh_from_prim(self) -> None:
        """Update sensor configuration from USD prim attributes.

        Reads enabled, filter widths, local transform, and gravity configuration
        from the stage. Resizes buffers if filter widths change.
        """
        stage = stage_utils.get_current_stage(backend="usd")
        prim = stage.GetPrimAtPath(self._prim_path)
        if not prim.IsValid():
            return

        # Initialize parent prim if not yet resolved
        if self._parent_prim_path is None:
            self._parent_prim_path, self._is_articulation_link = _find_rigid_body_parent_path(self._prim_path)
            self._rigid_prim = RigidPrim(self._parent_prim_path) if self._parent_prim_path else None

        # Read sensor local transform relative to parent
        local_translation, local_orientation = xform_utils.get_local_pose(self._prim_path)
        self._sensor_local_translation = _sanitize_vector(np.array(_to_numpy(local_translation), dtype=np.float64))
        self._sensor_local_orientation = _normalize_quaternion(_to_numpy(local_orientation))

        typed_prim = IsaacSensorSchema.IsaacImuSensor(prim)

        # Read enabled state
        enabled_attr = typed_prim.GetEnabledAttr()
        if enabled_attr.IsValid():
            enabled_value = enabled_attr.Get()
            self._enabled = enabled_value if enabled_value is not None else True
        else:
            self._enabled = True

        # Read filter widths (minimum 1)
        linear_width_attr = typed_prim.GetLinearAccelerationFilterWidthAttr()
        if linear_width_attr.IsValid():
            linear_width = linear_width_attr.Get()
            if linear_width is not None:
                self._linear_acceleration_filter = max(int(linear_width), 1)

        angular_width_attr = typed_prim.GetAngularVelocityFilterWidthAttr()
        if angular_width_attr.IsValid():
            angular_width = angular_width_attr.Get()
            if angular_width is not None:
                self._angular_velocity_filter = max(int(angular_width), 1)

        orientation_width_attr = typed_prim.GetOrientationFilterWidthAttr()
        if orientation_width_attr.IsValid():
            orientation_width = orientation_width_attr.Get()
            if orientation_width is not None:
                self._orientation_filter = max(int(orientation_width), 1)

        # Resize buffers to accommodate filter windows (need 2x for acceleration diff)
        max_rolling = max(self._linear_acceleration_filter, self._angular_velocity_filter, self._orientation_filter)
        desired_size = max(2 * max_rolling, 20)
        if desired_size != self._raw_buffer_size:
            self._raw_buffer_size = desired_size
            self._raw_buffer = [IMURawData() for _ in range(self._raw_buffer_size)]
            self._sensor_readings = [IMUSensorReading() for _ in range(self._raw_buffer_size)]

        # Read gravity from physics scene
        unit_scale = UsdGeom.GetStageMetersPerUnit(stage)
        if not np.isfinite(unit_scale) or unit_scale <= 0.0:
            unit_scale = 1.0

        # Default gravity values (Earth gravity in -Z direction)
        gravity_direction = np.array([0.0, 0.0, -1.0], dtype=np.float64)
        gravity_magnitude = 9.80665

        # Find physics scene and read gravity configuration
        for prim_it in stage.Traverse():
            if prim_it.IsA(UsdPhysics.Scene):
                scene = UsdPhysics.Scene(prim_it)
                gravity_magnitude_attr = scene.GetGravityMagnitudeAttr()
                if gravity_magnitude_attr.HasAuthoredValueOpinion():
                    gravity_magnitude = gravity_magnitude_attr.Get() or gravity_magnitude
                gravity_direction_attr = scene.GetGravityDirectionAttr()
                if gravity_direction_attr.HasAuthoredValueOpinion():
                    gravity_direction_value = gravity_direction_attr.Get()
                    if gravity_direction_value is not None:
                        gravity_direction = np.array(
                            [gravity_direction_value[0], gravity_direction_value[1], gravity_direction_value[2]],
                            dtype=np.float64,
                        )
                break

        # Compute gravity vector in world frame (accounts for stage units)
        # Negative direction because gravity acts opposite to the defined direction
        gravity_direction = _sanitize_vector(gravity_direction)
        if not np.isfinite(gravity_magnitude):
            gravity_magnitude = 9.80665
        self._gravity = gravity_magnitude / unit_scale * -gravity_direction

    def _get_world_orientation(self) -> np.ndarray:
        """Get the world orientation of the sensor prim.

        Uses RigidPrim if available for physics-accurate orientation,
        falls back to USD transform if not.

        Returns:
            Normalized quaternion [w, x, y, z] representing world orientation.
        """
        if self._rigid_prim is not None:
            try:
                _, parent_orientations = self._rigid_prim.get_world_poses(indices=[0])
                parent_orientation = _normalize_quaternion(_to_numpy(parent_orientations[0]))
                # Combine parent orientation with local sensor offset
                return _normalize_quaternion(_quat_multiply(parent_orientation, self._sensor_local_orientation))
            except Exception:
                pass

        # Fallback to USD xform
        _, orientation = xform_utils.get_world_pose(self._prim_path)
        return _normalize_quaternion(_to_numpy(orientation))

    def _update_gravity_sensor_frame_no_physics(self, sim_time: float) -> None:
        """Update gravity in sensor frame when physics hasn't run yet.

        Used during timeline play before the first physics step to provide
        valid gravity readings. Waits a short delay to ensure stage is ready.

        Args:
            sim_time: Current simulation time in seconds.
        """
        if self._gravity_no_physics_ready or sim_time < self._gravity_no_physics_delay_s:
            return

        # Transform gravity from world to sensor frame
        orientation = self._get_world_orientation()
        rotation_matrix = transform_utils.quaternion_to_rotation_matrix(orientation).numpy()
        rotation_world_to_body = rotation_matrix.T  # World-to-body rotation
        self._gravity_sensor_frame = _sanitize_vector(rotation_world_to_body @ self._gravity)
        self._gravity_no_physics_ready = True

    def on_physics_step(self, step_dt: float) -> None:
        """Process physics data for the current step.

        Called by _SensorStepManager after each physics step. Captures
        velocity data, computes acceleration, applies filters, and
        updates sensor readings.

        Args:
            step_dt: Duration of the physics step in seconds.
        """
        self._refresh_from_prim()
        self._time_delta = float(step_dt)
        self._time_seconds = float(SimulationManager.get_simulation_time())
        self._last_step_time = self._time_seconds
        self._last_physics_step = SimulationManager.get_num_physics_steps()

        # Handle enabled state transitions
        if self._previous_enabled != self._enabled:
            if self._enabled:
                self._raw_buffer = [IMURawData() for _ in range(self._raw_buffer_size)]
                self._sensor_readings = [IMUSensorReading() for _ in range(self._raw_buffer_size)]
            else:
                # Sensor just disabled - clear all data
                self.reset()
            self._previous_enabled = self._enabled

        if not self._enabled:
            return

        # Ensure RigidPrim is available for velocity queries
        if self._parent_prim_path is not None and self._rigid_prim is None:
            try:
                self._rigid_prim = RigidPrim(self._parent_prim_path)
            except Exception:
                self._rigid_prim = None

        # Get current sensor orientation and compute world-to-body rotation
        orientation = self._get_world_orientation()
        rotation_matrix = transform_utils.quaternion_to_rotation_matrix(orientation).numpy()
        rotation_world_to_body = rotation_matrix.T  # World-to-body (sensor frame) rotation

        # Transform gravity to sensor frame
        self._gravity_sensor_frame = _sanitize_vector(rotation_world_to_body @ self._gravity)

        # Get velocities from physics and transform to sensor frame
        linear_velocity_body = np.zeros(3, dtype=np.float64)
        angular_velocity_body = np.zeros(3, dtype=np.float64)
        if self._rigid_prim is not None:
            try:
                linear_vel, angular_vel = self._rigid_prim.get_velocities()
                linear_velocity_world = _sanitize_vector(np.array(_to_numpy(linear_vel[0]), dtype=np.float64))
                angular_velocity_world = _sanitize_vector(np.array(_to_numpy(angular_vel[0]), dtype=np.float64))
                linear_velocity_body = _sanitize_vector(rotation_world_to_body @ linear_velocity_world)
                angular_velocity_body = _sanitize_vector(rotation_world_to_body @ angular_velocity_world)
            except Exception:
                pass

        # Store raw data in circular buffer
        if self._raw_buffer:
            self._raw_buffer.pop()
        self._raw_buffer.insert(
            0,
            IMURawData(
                time=self._time_seconds,
                dt=self._time_delta,
                linear_velocity_x=linear_velocity_body[0],
                linear_velocity_y=linear_velocity_body[1],
                linear_velocity_z=linear_velocity_body[2],
                angular_velocity_x=angular_velocity_body[0],
                angular_velocity_y=angular_velocity_body[1],
                angular_velocity_z=angular_velocity_body[2],
                orientation_w=float(orientation[0]),
                orientation_x=float(orientation[1]),
                orientation_y=float(orientation[2]),
                orientation_z=float(orientation[3]),
            ),
        )

        # Create new sensor reading
        if self._sensor_readings:
            self._sensor_readings.pop()
        self._sensor_readings.insert(0, IMUSensorReading(time=self._time_seconds))

        # Apply rolling average filter to angular velocity
        self._sensor_readings[0].angular_velocity_x = float(
            np.mean([self._raw_buffer[i].angular_velocity_x for i in range(self._angular_velocity_filter)])
        )
        self._sensor_readings[0].angular_velocity_y = float(
            np.mean([self._raw_buffer[i].angular_velocity_y for i in range(self._angular_velocity_filter)])
        )
        self._sensor_readings[0].angular_velocity_z = float(
            np.mean([self._raw_buffer[i].angular_velocity_z for i in range(self._angular_velocity_filter)])
        )

        # Sanitize angular velocity
        angular_velocity = np.array(
            [
                self._sensor_readings[0].angular_velocity_x,
                self._sensor_readings[0].angular_velocity_y,
                self._sensor_readings[0].angular_velocity_z,
            ],
            dtype=np.float64,
        )
        angular_velocity = _sanitize_vector(angular_velocity)
        self._sensor_readings[0].angular_velocity_x = float(angular_velocity[0])
        self._sensor_readings[0].angular_velocity_y = float(angular_velocity[1])
        self._sensor_readings[0].angular_velocity_z = float(angular_velocity[2])

        # Compute linear acceleration from velocity differences
        # Uses pairs of samples separated by filter width for noise reduction
        acceleration_sum = np.zeros(3, dtype=np.float64)
        for i in range(self._linear_acceleration_filter):
            dt = self._raw_buffer[i].time - self._raw_buffer[i + self._linear_acceleration_filter].time
            if dt > 1e-10:
                acceleration_sum[0] += (
                    self._raw_buffer[i].linear_velocity_x
                    - self._raw_buffer[i + self._linear_acceleration_filter].linear_velocity_x
                ) / dt
                acceleration_sum[1] += (
                    self._raw_buffer[i].linear_velocity_y
                    - self._raw_buffer[i + self._linear_acceleration_filter].linear_velocity_y
                ) / dt
                acceleration_sum[2] += (
                    self._raw_buffer[i].linear_velocity_z
                    - self._raw_buffer[i + self._linear_acceleration_filter].linear_velocity_z
                ) / dt
        acceleration_sum /= float(self._linear_acceleration_filter)
        acceleration_sum = _sanitize_vector(acceleration_sum)
        self._sensor_readings[0].linear_acceleration_x = float(acceleration_sum[0])
        self._sensor_readings[0].linear_acceleration_y = float(acceleration_sum[1])
        self._sensor_readings[0].linear_acceleration_z = float(acceleration_sum[2])

        # Apply rolling average filter to orientation
        orientation_average = np.mean(
            [
                [
                    self._raw_buffer[i].orientation_w,
                    self._raw_buffer[i].orientation_x,
                    self._raw_buffer[i].orientation_y,
                    self._raw_buffer[i].orientation_z,
                ]
                for i in range(self._orientation_filter)
            ],
            axis=0,
        )
        if np.any(~np.isfinite(orientation_average)):
            orientation_average = orientation
        orientation_average = _normalize_quaternion(orientation_average)
        self._sensor_readings[0].orientation = Quaternion(
            float(orientation_average[0]),
            float(orientation_average[1]),
            float(orientation_average[2]),
            float(orientation_average[3]),
        )

    def on_timeline_stop(self) -> None:
        """Reset sensor state when timeline stops.

        Clears all readings, timing state, and RigidPrim reference.
        """
        self.reset()
        self._time_seconds = 0.0
        self._time_delta = 0.0
        self._last_step_time = -1.0
        self._last_physics_step = -1
        self._gravity_no_physics_ready = False
        # Clear RigidPrim to avoid stale cached data
        self._rigid_prim = None

    def reset(self) -> None:
        """Reset sensor data buffers.

        Clears raw buffer and sensor readings without affecting configuration.
        """
        self._raw_buffer = [IMURawData() for _ in range(self._raw_buffer_size)]
        self._sensor_readings = [IMUSensorReading() for _ in range(self._raw_buffer_size)]
        self._gravity_no_physics_ready = False

    def get_sensor_reading(self, read_gravity: bool = True) -> IMUSensorReading:
        """Get the current IMU sensor reading.

        Args:
            read_gravity: If True, include gravity in acceleration readings.

        Returns:
            Reading with linear acceleration, angular velocity, and orientation.
            Returns invalid reading if sensor is disabled or prim is invalid.

        Example:

        .. code-block:: python

            >>> reading = backend.get_sensor_reading()  # doctest: +NO_CHECK
            >>> reading.is_valid  # doctest: +NO_CHECK
            False
        """
        # Validate prim exists and is correct type
        stage = stage_utils.get_current_stage(backend="usd")
        prim = stage.GetPrimAtPath(self._prim_path)
        if not prim.IsValid():
            return IMUSensorReading(is_valid=False, time=0.0)
        if prim.GetTypeName() != "IsaacImuSensor":
            return IMUSensorReading(is_valid=False, time=0.0)

        self._refresh_from_prim()
        sim_time = float(SimulationManager.get_simulation_time())

        # Ensure we have current data
        if SimulationManager.is_simulating():
            current_step = SimulationManager.get_num_physics_steps()
            if current_step != self._last_physics_step:
                self.on_physics_step(SimulationManager.get_physics_dt())
            elif self._last_physics_step < 0:
                # Physics hasn't run yet - use fallback gravity
                self._update_gravity_sensor_frame_no_physics(sim_time)
        else:
            self._update_gravity_sensor_frame_no_physics(sim_time)

        if not self._enabled:
            return IMUSensorReading(is_valid=False, time=0.0)

        reading = _clone_imu_reading(self._sensor_readings[0])

        # Add gravity component to acceleration if requested
        if read_gravity:
            reading.linear_acceleration_x += float(self._gravity_sensor_frame[0])
            reading.linear_acceleration_y += float(self._gravity_sensor_frame[1])
            reading.linear_acceleration_z += float(self._gravity_sensor_frame[2])

        # Final sanitization - replace any remaining invalid values
        if not np.isfinite(reading.linear_acceleration_x):
            reading.linear_acceleration_x = 0.0
        if not np.isfinite(reading.linear_acceleration_y):
            reading.linear_acceleration_y = 0.0
        if not np.isfinite(reading.linear_acceleration_z):
            reading.linear_acceleration_z = 0.0
        if not np.isfinite(reading.angular_velocity_x):
            reading.angular_velocity_x = 0.0
        if not np.isfinite(reading.angular_velocity_y):
            reading.angular_velocity_y = 0.0
        if not np.isfinite(reading.angular_velocity_z):
            reading.angular_velocity_z = 0.0

        # Normalize orientation quaternion
        orientation = _normalize_quaternion(
            np.array(
                [reading.orientation.w, reading.orientation.x, reading.orientation.y, reading.orientation.z],
                dtype=np.float64,
            )
        )
        reading.orientation = Quaternion(
            float(orientation[0]),  # w
            float(orientation[1]),  # x
            float(orientation[2]),  # y
            float(orientation[3]),  # z
        )

        reading.is_valid = True
        return reading
