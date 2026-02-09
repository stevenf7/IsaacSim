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
"""Common utilities, data classes, and managers for physics-based sensors.

This module provides shared functionality for IMU and contact sensors including:
- Data classes for sensor readings (ContactSensorReading, IMUSensorReading, IMURawData)
- Quaternion representation with compatibility for existing APIs
- Utility functions for vector/quaternion operations
- Singleton managers for sensor lifecycle and contact events
"""
from __future__ import annotations

import weakref
from collections.abc import Iterator
from dataclasses import dataclass, field
from typing import Any, cast

import numpy as np
from isaacsim.core.experimental.utils import prim as prim_utils
from isaacsim.core.experimental.utils import stage as stage_utils
from isaacsim.core.experimental.utils import transform as transform_utils
from isaacsim.core.simulation_manager import SimulationEvent, SimulationManager
from omni.physics.core import ContactEventType, get_physics_simulation_interface
from pxr import PhysicsSchemaTools, PhysxSchema, UsdPhysics


@dataclass
class ContactSensorReading:
    """Contact sensor reading data."""

    _in_contact: bool = field(default=False, init=False)
    value: float = 0.0
    #: Contact force magnitude in Newtons.
    time: float = 0.0
    #: Simulation time when the reading was taken.
    is_valid: bool = False
    #: Whether this reading contains valid data.

    @property
    def in_contact(self) -> bool:
        """Whether the sensor is currently in contact."""
        return self._in_contact

    @in_contact.setter
    def in_contact(self, value: bool) -> None:
        self._in_contact = value


@dataclass
class IMUSensorReading:
    """IMU sensor reading data."""

    linear_acceleration_x: float = 0.0
    #: Linear acceleration along X axis in m/s^2.
    linear_acceleration_y: float = 0.0
    #: Linear acceleration along Y axis in m/s^2.
    linear_acceleration_z: float = 0.0
    #: Linear acceleration along Z axis in m/s^2.
    angular_velocity_x: float = 0.0
    #: Angular velocity around X axis in rad/s.
    angular_velocity_y: float = 0.0
    #: Angular velocity around Y axis in rad/s.
    angular_velocity_z: float = 0.0
    #: Angular velocity around Z axis in rad/s.
    orientation: "Quaternion" = field(default_factory=lambda: Quaternion(1.0, 0.0, 0.0, 0.0))
    #: Sensor orientation as a quaternion.
    time: float = 0.0
    #: Simulation time when the reading was taken.
    is_valid: bool = False
    #: Whether this reading contains valid data.


@dataclass
class Quaternion:
    """Quaternion class for storing orientation.

    Internally stores components in [w, x, y, z] order but provides iteration
    and array conversion in [x, y, z, w] format for compatibility with existing code.
    """

    w: float
    #: Scalar (real) component.
    x: float
    #: First imaginary component.
    y: float
    #: Second imaginary component.
    z: float
    #: Third imaginary component.

    def __len__(self) -> int:
        """Return the number of quaternion components.

        Returns:
            Always returns 4.
        """
        return 4

    def __iter__(self) -> Iterator[float]:
        """Iterate over components in [x, y, z, w] order.

        Yields:
            Each quaternion component in [x, y, z, w] order.
        """
        yield self.x
        yield self.y
        yield self.z
        yield self.w

    def __array__(self, dtype: type | None = None) -> np.ndarray:
        """Convert to numpy array in [x, y, z, w] order.

        Args:
            dtype: Optional numpy dtype for the output array.

        Returns:
            Numpy array with components in [x, y, z, w] order.
        """
        return np.array([self.x, self.y, self.z, self.w], dtype=dtype)

    def __getitem__(self, index: int) -> float:
        """Access components by index in [x, y, z, w] order.

        Args:
            index: Component index (0=x, 1=y, 2=z, 3=w).

        Returns:
            The component value at the given index.

        Raises:
            IndexError: If index is out of range.
        """
        if index == 0:
            return self.x
        if index == 1:
            return self.y
        if index == 2:
            return self.z
        if index == 3:
            return self.w
        raise IndexError(index)


@dataclass
class IMURawData:
    """Raw IMU sensor data before processing.

    Contains velocity and orientation data captured at each physics step
    before filtering and acceleration computation.
    """

    time: float = 0.0
    #: Simulation time of this sample.
    dt: float = 0.0
    #: Physics timestep duration.
    linear_velocity_x: float = 0.0
    #: Linear velocity along X axis in m/s.
    linear_velocity_y: float = 0.0
    #: Linear velocity along Y axis in m/s.
    linear_velocity_z: float = 0.0
    #: Linear velocity along Z axis in m/s.
    angular_velocity_x: float = 0.0
    #: Angular velocity around X axis in rad/s.
    angular_velocity_y: float = 0.0
    #: Angular velocity around Y axis in rad/s.
    angular_velocity_z: float = 0.0
    #: Angular velocity around Z axis in rad/s.
    orientation_w: float = 1.0
    #: Quaternion w component.
    orientation_x: float = 0.0
    #: Quaternion x component.
    orientation_y: float = 0.0
    #: Quaternion y component.
    orientation_z: float = 0.0
    #: Quaternion z component.


def _to_numpy(value: Any) -> np.ndarray:
    """Convert a value to a numpy array.

    Args:
        value: Value to convert (array-like or numpy-compatible).

    Returns:
        Numpy array representation of the value.
    """
    if hasattr(value, "numpy"):
        return value.numpy()
    return np.array(value)


def _sanitize_vector(value: np.ndarray) -> np.ndarray:
    """Replace NaN and infinite values with zeros.

    Args:
        value: Input vector.

    Returns:
        Vector with non-finite values replaced by zeros.
    """
    return np.nan_to_num(value, nan=0.0, posinf=0.0, neginf=0.0)


def _normalize_quaternion(value: np.ndarray) -> np.ndarray:
    """Normalize a quaternion to unit length.

    Args:
        value: Quaternion vector.

    Returns:
        Normalized quaternion.
    """
    value = _sanitize_vector(np.array(value, dtype=np.float64))
    norm = np.linalg.norm(value)
    if not np.isfinite(norm) or norm == 0.0:
        return np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float64)
    return value / norm


def _quat_multiply(first: np.ndarray, second: np.ndarray) -> np.ndarray:
    """Multiply two quaternions using Hamilton product.

    Args:
        first: First quaternion in [w, x, y, z] order.
        second: Second quaternion in [w, x, y, z] order.

    Returns:
        Product quaternion in [w, x, y, z] order.
    """
    return _to_numpy(transform_utils.quaternion_multiplication(first, second))


def _vec3_to_dict(value: Any) -> dict[str, float]:
    """Convert a 3D vector to a dictionary with x, y, z keys.

    Args:
        value: 3D vector-like value.

    Returns:
        Dict with x, y, z float entries.
    """
    return {"x": float(value[0]), "y": float(value[1]), "z": float(value[2])}


def _get_contact_header_field(header: Any, *names: str, default: Any = None) -> Any:
    """Get a field from a contact header, trying multiple attribute names.

    Args:
        header: Contact header object to query.
        *names: Attribute names to try in order.
        default: Default value if no attribute exists.

    Returns:
        Attribute value or default.
    """
    for name in names:
        if hasattr(header, name):
            return getattr(header, name)
    return default


def _clone_imu_reading(reading: IMUSensorReading) -> IMUSensorReading:
    """Create a deep copy of an IMU reading.

    Args:
        reading: IMU reading to clone.

    Returns:
        New IMU reading with copied values.
    """
    return IMUSensorReading(
        linear_acceleration_x=reading.linear_acceleration_x,
        linear_acceleration_y=reading.linear_acceleration_y,
        linear_acceleration_z=reading.linear_acceleration_z,
        angular_velocity_x=reading.angular_velocity_x,
        angular_velocity_y=reading.angular_velocity_y,
        angular_velocity_z=reading.angular_velocity_z,
        orientation=Quaternion(
            reading.orientation.w,
            reading.orientation.x,
            reading.orientation.y,
            reading.orientation.z,
        ),
        time=reading.time,
        is_valid=reading.is_valid,
    )


def _find_rigid_body_parent_path(prim_path: str) -> tuple[str | None, bool]:
    """Find the nearest ancestor prim with a rigid body API.

    Args:
        prim_path: USD prim path to start from.

    Returns:
        Tuple of rigid body prim path (or None) and articulation link flag.
    """
    prim = prim_utils.get_prim_at_path(prim_path)
    articulation_link_api = getattr(PhysxSchema, "PhysxArticulationLinkAPI", None)
    articulation_api = getattr(PhysxSchema, "PhysxArticulationAPI", None)

    while prim.IsValid():
        path_str = prim_utils.get_prim_path(prim)
        if path_str == "/":
            break

        has_rigid = prim_utils.has_api(prim, UsdPhysics.RigidBodyAPI)
        has_articulation_link = articulation_link_api is not None and prim_utils.has_api(prim, articulation_link_api)
        has_articulation = articulation_api is not None and prim_utils.has_api(prim, articulation_api)

        if has_rigid:
            enabled_attr = prim.GetAttribute("physics:rigidBodyEnabled")
            if not enabled_attr.IsValid() or enabled_attr.Get() is None:
                return path_str, has_articulation_link
            if enabled_attr.Get():
                return path_str, has_articulation_link

        if has_articulation_link:
            return path_str, True

        if has_articulation:
            enabled_attr = prim.GetAttribute("physics:rigidBodyEnabled")
            if not enabled_attr.IsValid() or enabled_attr.Get() is None:
                return path_str, False
            if enabled_attr.Get():
                return path_str, False

        prim = prim.GetParent()
    return None, False


def _resolve_rigid_body_token(body_token: int) -> int:
    """Resolve a physics body token to its rigid body ancestor.

    Args:
        body_token: Token representing a physics body prim.

    Returns:
        Token for the rigid body ancestor, or the input token if not found.
    """
    prim_path = PhysicsSchemaTools.intToSdfPath(body_token)
    prim = prim_utils.get_prim_at_path(str(prim_path))

    while prim.IsValid() and prim_utils.get_prim_path(prim) != "/":
        if prim_utils.has_api(prim, UsdPhysics.RigidBodyAPI):
            return PhysicsSchemaTools.sdfPathToInt(prim.GetPath())
        prim = prim.GetParent()
    return body_token


class _SensorStepManager:
    """Singleton manager for physics sensor lifecycle events."""

    _instance: "_SensorStepManager | None" = None

    def __init__(self) -> None:
        self._sensors: "weakref.WeakSet[_PhysicsSensorBase]" = weakref.WeakSet()
        self._imu_backends: dict[str, "_PhysicsSensorBase"] = {}

        self._post_step_callback = SimulationManager.register_callback(
            self._on_physics_step, event=SimulationEvent.PHYSICS_POST_STEP
        )
        self._stop_callback = SimulationManager.register_callback(
            self._on_timeline_stop, event=SimulationEvent.SIMULATION_STOPPED
        )
        self._start_callback = SimulationManager.register_callback(
            self._on_simulation_start, event=SimulationEvent.SIMULATION_STARTED
        )

    @classmethod
    def instance(cls) -> "_SensorStepManager":
        """Get the singleton instance, creating it if necessary.

        Returns:
            Singleton instance of the manager.
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def register(self, sensor: "_PhysicsSensorBase") -> None:
        """Register a sensor to receive physics step updates.

        Args:
            sensor: Sensor instance to register.
        """
        self._sensors.add(sensor)

    def get_imu_backend(self, prim_path: str) -> "_PhysicsSensorBase | None":
        """Get an auto-discovered IMU backend by prim path.

        Args:
            prim_path: IMU prim path to look up.

        Returns:
            IMU backend instance or None if not found.
        """
        return self._imu_backends.get(prim_path)

    def _on_simulation_start(self, event: Any) -> None:
        _ContactReportManager.instance().reset()

        from .imu_sensor_backend import ImuSensorBackend

        stage = stage_utils.get_current_stage(backend="usd")
        if stage is None:
            return

        for prim in stage.Traverse():
            if prim.GetTypeName() == "IsaacImuSensor":
                prim_path = str(prim.GetPath())
                if prim_path not in self._imu_backends:
                    try:
                        backend = ImuSensorBackend(prim_path)
                        self._imu_backends[prim_path] = backend
                    except Exception:
                        pass

    def _on_physics_step(self, step_dt: float, context: Any) -> None:
        _ContactReportManager.instance().on_physics_step()
        for sensor in list(self._sensors):
            sensor.on_physics_step(step_dt)

    def _on_timeline_stop(self, event: Any) -> None:
        for sensor in list(self._sensors):
            sensor.on_timeline_stop()
        self._imu_backends.clear()
        _ContactReportManager.instance().reset()


class _ContactReportManager:
    """Singleton manager for physics contact events."""

    _instance: "_ContactReportManager | None" = None

    def __init__(self) -> None:
        self._contact_raw: list[dict[str, object]] = []
        self._contact_raw_map: dict[int, list[dict[str, object]]] = {}
        self._current_time = 0.0
        self._current_dt = 0.0
        self._last_step_num = -1

        self._subscription = get_physics_simulation_interface().subscribe_physics_contact_report_events(
            self._on_contact_event
        )

    @classmethod
    def instance(cls) -> "_ContactReportManager":
        """Get the singleton instance, creating it if necessary.

        Returns:
            Singleton instance of the manager.
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def reset(self) -> None:
        """Reset all contact data."""
        self._contact_raw.clear()
        self._contact_raw_map.clear()
        self._last_step_num = -1

    def on_physics_step(self) -> None:
        """Clear contact data at start of each new physics step."""
        current_step = SimulationManager.get_num_physics_steps()
        if current_step != self._last_step_num:
            self._contact_raw.clear()
            self._contact_raw_map.clear()
            self._last_step_num = current_step
            self._current_time = float(SimulationManager.get_simulation_time())
            self._current_dt = float(SimulationManager.get_physics_dt())

    def _remove_pair_from_list(
        self, contact_list: list[dict[str, object]], body0: int, body1: int
    ) -> list[dict[str, object]]:
        return [
            entry
            for entry in contact_list
            if not (entry["body0"] == body0 and entry["body1"] == body1)
            and not (entry["body0"] == body1 and entry["body1"] == body0)
        ]

    def _on_contact_event(self, contact_headers: Any, contact_data: Any, friction_anchors: Any) -> None:
        sim_time = float(SimulationManager.get_simulation_time())
        sim_dt = float(SimulationManager.get_physics_dt())
        current_step = SimulationManager.get_num_physics_steps()

        if current_step != self._last_step_num:
            self._contact_raw.clear()
            self._contact_raw_map.clear()
            self._last_step_num = current_step
            self._current_time = sim_time
            self._current_dt = sim_dt

        data_index = 0
        for header in contact_headers:
            event_type = _get_contact_header_field(header, "type")
            body0 = _get_contact_header_field(header, "actor0", "collider0")
            body1 = _get_contact_header_field(header, "actor1", "collider1")
            if body0 is None or body1 is None:
                continue

            body0 = _resolve_rigid_body_token(int(body0))
            body1 = _resolve_rigid_body_token(int(body1))
            count = _get_contact_header_field(header, "numContactData", "num_contact_data", default=0)

            if event_type in (ContactEventType.CONTACT_FOUND, ContactEventType.CONTACT_PERSIST):
                self._contact_raw = self._remove_pair_from_list(self._contact_raw, body0, body1)

                if body0 in self._contact_raw_map:
                    del self._contact_raw_map[body0]
                if body1 in self._contact_raw_map:
                    del self._contact_raw_map[body1]

                for i in range(int(count)):
                    data = contact_data[data_index + i]
                    entry = {
                        "body0": int(body0),
                        "body1": int(body1),
                        "position": _vec3_to_dict(data.position),
                        "normal": _vec3_to_dict(data.normal),
                        "impulse": _vec3_to_dict(data.impulse),
                        "time": sim_time,
                        "dt": sim_dt,
                    }
                    self._contact_raw.append(entry)
                data_index += int(count)

            elif event_type == ContactEventType.CONTACT_LOST:
                self._contact_raw = self._remove_pair_from_list(self._contact_raw, body0, body1)
                if body0 in self._contact_raw_map:
                    del self._contact_raw_map[body0]
                if body1 in self._contact_raw_map:
                    del self._contact_raw_map[body1]

    def get_raw_contacts_for_body(self, body_token: int) -> list[dict[str, object]]:
        """Get raw contact data for a specific rigid body.

        Args:
            body_token: Token for the rigid body prim.

        Returns:
            List of raw contact entries.
        """
        current_step = SimulationManager.get_num_physics_steps()
        sim_time = float(SimulationManager.get_simulation_time())

        is_new_simulation = current_step < self._last_step_num
        has_future_timestamps = self._contact_raw and any(
            cast(float, entry["time"]) > sim_time + 0.1 for entry in self._contact_raw
        )

        if is_new_simulation or has_future_timestamps:
            self._contact_raw.clear()
            self._contact_raw_map.clear()
            self._last_step_num = current_step

        if body_token not in self._contact_raw_map or not self._contact_raw_map[body_token]:
            self._contact_raw_map[body_token] = [
                entry
                for entry in self._contact_raw
                if cast(int, entry["body0"]) == body_token or cast(int, entry["body1"]) == body_token
            ]
        return list(self._contact_raw_map[body_token])


class _PhysicsSensorBase:
    """Abstract base class for physics-based sensors."""

    def on_physics_step(self, step_dt: float) -> None:
        """Called after each physics simulation step.

        Args:
            step_dt: Physics step duration in seconds.

        Raises:
            NotImplementedError: If the base class method is called directly.
        """
        raise NotImplementedError

    def on_timeline_stop(self) -> None:
        """Called when the simulation timeline stops.

        Raises:
            NotImplementedError: If the base class method is called directly.
        """
        raise NotImplementedError
