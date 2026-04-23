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

"""Raycast sensor wrapper providing high-level sensor access."""
from __future__ import annotations

from typing import Any

import carb
import numpy as np
import omni.isaac.IsaacSensorSchema as IsaacSensorSchema
from isaacsim.core.experimental.prims import XformPrim
from isaacsim.core.experimental.utils import prim as prim_utils
from isaacsim.core.simulation_manager import SimulationManager
from isaacsim.sensors.experimental.physics.impl.common import _create_sensor_prim
from isaacsim.sensors.experimental.physics.impl.raycast_sensor_backend import RaycastSensorBackend
from pxr import Gf, Vt


class RaycastSensor(XformPrim):
    """High-level raycast sensor wrapper with frame-based data access.

    Provides a convenient interface for raycast sensing including automatic
    sensor creation if the prim doesn't exist, configurable ray geometry,
    and structured frame data output.

    Args:
        prim_path: USD path where the sensor should be located.
        name: Human-readable name for the sensor.
        translation: Local translation offset from parent. Cannot be used with position.
        position: World position. Cannot be used with translation.
        orientation: Sensor orientation as [w, x, y, z] quaternion.
        min_range: Minimum detection range in stage length units.
        max_range: Maximum detection range in stage length units.
        ray_origins: Per-ray origin translations as Nx3 array.
        ray_directions: Per-ray direction vectors as Nx3 array.
        ray_time_offsets: Per-ray time offsets in seconds.
        output_frame: Output coordinate frame ("SENSOR" or "WORLD").
        report_hit_prim_paths: Whether to resolve hit prim USD paths.

    Raises:
        ValueError: If both position and translation are specified.
        RuntimeError: If sensor creation fails.

    Example:

        .. code-block:: python

            from isaacsim.sensors.experimental.physics import RaycastSensor

            sensor = RaycastSensor(
                "/World/Robot/body/raycast",
                ray_origins=[[0, 0, 0]],
                ray_directions=[[1, 0, 0]],
            )

            frame = sensor.get_current_frame()
            print(f"Depths: {frame['depths']}")
            print(f"Hit positions: {frame['hit_positions']}")
    """

    @staticmethod
    def create(
        path: str,
        *,
        min_range: float = 0.4,
        max_range: float = 100.0,
        ray_origins: list | np.ndarray | None = None,
        ray_directions: list | np.ndarray | None = None,
        ray_time_offsets: list | np.ndarray | None = None,
        output_frame: str = "SENSOR",
        report_hit_prim_paths: bool = False,
        translation: Gf.Vec3d = Gf.Vec3d(0, 0, 0),
        orientation: Gf.Quatd = Gf.Quatd(1, 0, 0, 0),
    ) -> RaycastSensor:
        """Create a new raycast sensor at the specified path.

        Args:
            path: Full USD path for the sensor (e.g., ``/World/Robot/body/raycast``).
            min_range: Minimum detection range in stage length units.
            max_range: Maximum detection range in stage length units.
            ray_origins: Per-ray origin translations as Nx3 array.
            ray_directions: Per-ray direction vectors as Nx3 array.
            ray_time_offsets: Per-ray time offsets in seconds.
            output_frame: Output coordinate frame (``"SENSOR"`` or ``"WORLD"``).
            report_hit_prim_paths: Whether to resolve hit prim USD paths.
            translation: Local translation offset from parent.
            orientation: Sensor orientation as a quaternion.

        Returns:
            RaycastSensor instance wrapping the created prim.

        Raises:
            RuntimeError: If sensor creation fails.

        Example:

        .. code-block:: python

            >>> from isaacsim.sensors.experimental.physics import RaycastSensor
            >>>
            >>> sensor = RaycastSensor.create(
            ...     "/World/Robot/body/raycast",
            ...     ray_origins=[[0, 0, 0]],
            ...     ray_directions=[[1, 0, 0]],
            ... )  # doctest: +NO_CHECK
        """
        parent = "/".join(path.rstrip("/").split("/")[:-1])
        sensor_name = path.rstrip("/").split("/")[-1]
        if not parent:
            raise RuntimeError(f"Path must include a parent prim (e.g., '/World/Cube/{sensor_name}')")
        prim = RaycastSensor._create_prim(
            path="/" + sensor_name,
            parent=parent,
            min_range=min_range,
            max_range=max_range,
            ray_origins=ray_origins,
            ray_directions=ray_directions,
            ray_time_offsets=ray_time_offsets,
            output_frame=output_frame,
            report_hit_prim_paths=report_hit_prim_paths,
            translation=translation,
            orientation=orientation,
        )
        return RaycastSensor(prim.GetPath().pathString)

    @staticmethod
    def _create_prim(
        path: str,
        parent: str,
        min_range: float = 0.4,
        max_range: float = 100.0,
        ray_origins: list | np.ndarray | None = None,
        ray_directions: list | np.ndarray | None = None,
        ray_time_offsets: list | np.ndarray | None = None,
        output_frame: str = "SENSOR",
        report_hit_prim_paths: bool = False,
        translation: Gf.Vec3d = Gf.Vec3d(0, 0, 0),
        orientation: Gf.Quatd = Gf.Quatd(1, 0, 0, 0),
    ) -> IsaacSensorSchema.IsaacRaycastSensor:
        if ray_origins is not None and ray_directions is not None:
            if len(ray_origins) != len(ray_directions):
                raise ValueError(
                    f"ray_origins length ({len(ray_origins)}) != " f"ray_directions length ({len(ray_directions)})"
                )

        if ray_origins is not None:
            num_rays = len(ray_origins)
        elif ray_directions is not None:
            num_rays = len(ray_directions)
        else:
            num_rays = 1

        if ray_time_offsets is not None and len(ray_time_offsets) != num_rays:
            raise ValueError(f"ray_time_offsets length ({len(ray_time_offsets)}) != num_rays ({num_rays})")

        prim, _ = _create_sensor_prim(
            path, parent, IsaacSensorSchema.IsaacRaycastSensor, translation=translation, orientation=orientation
        )

        prim.CreateMinRangeAttr(min_range)
        prim.CreateMaxRangeAttr(max_range)

        if ray_origins is not None:
            origins = Vt.Vec3fArray([(float(o[0]), float(o[1]), float(o[2])) for o in ray_origins])
            prim.CreateRayOriginsAttr(origins)

        if ray_directions is not None:
            directions = Vt.Vec3fArray([(float(d[0]), float(d[1]), float(d[2])) for d in ray_directions])
            prim.CreateRayDirectionsAttr(directions)

        if ray_time_offsets is not None:
            offsets = Vt.FloatArray([float(t) for t in ray_time_offsets])
            prim.CreateRayTimeOffsetsAttr(offsets)

        prim.CreateNumRaysAttr(num_rays)
        prim.CreateOutputFrameOfReferenceAttr(output_frame)
        prim.CreateReportHitPrimPathsAttr(report_hit_prim_paths)

        return prim

    def __init__(
        self,
        prim_path: str,
        name: str | None = "raycast_sensor",
        translation: np.ndarray | None = None,
        position: np.ndarray | None = None,
        orientation: np.ndarray | None = None,
        min_range: float | None = None,
        max_range: float | None = None,
        ray_origins: np.ndarray | list | None = None,
        ray_directions: np.ndarray | list | None = None,
        ray_time_offsets: np.ndarray | list | None = None,
        output_frame: str | None = None,
        report_hit_prim_paths: bool | None = None,
    ) -> None:
        if position is not None and translation is not None:
            raise ValueError("Sensor position and translation can't be both specified")

        self._body_prim_path = "/".join(prim_path.split("/")[:-1])
        self._sensor_name = prim_path.split("/")[-1]

        if ray_origins is not None and ray_directions is not None:
            if len(ray_origins) != len(ray_directions):
                raise ValueError(
                    f"ray_origins length ({len(ray_origins)}) != ray_directions length ({len(ray_directions)})"
                )

        num_rays = None
        if ray_origins is not None:
            num_rays = len(ray_origins)
        elif ray_directions is not None:
            num_rays = len(ray_directions)

        if ray_time_offsets is not None and num_rays is not None:
            if len(ray_time_offsets) != num_rays:
                raise ValueError(f"ray_time_offsets length ({len(ray_time_offsets)}) != num_rays ({num_rays})")

        prim = prim_utils.get_prim_at_path(prim_path)
        if prim.IsValid():
            self._isaac_sensor_prim = IsaacSensorSchema.IsaacRaycastSensor(prim)
            super().__init__(
                prim_path,
                positions=position,
                translations=translation,
                orientations=orientation,
                reset_xform_op_properties=True,
            )
            if min_range is not None:
                self._isaac_sensor_prim.CreateMinRangeAttr(min_range)
            if max_range is not None:
                self._isaac_sensor_prim.CreateMaxRangeAttr(max_range)
            if ray_origins is not None or ray_directions is not None or ray_time_offsets is not None:
                if ray_origins is not None:
                    origins = Vt.Vec3fArray([(float(o[0]), float(o[1]), float(o[2])) for o in ray_origins])
                    self._isaac_sensor_prim.CreateRayOriginsAttr(origins)
                    self._isaac_sensor_prim.CreateNumRaysAttr(len(ray_origins))
                if ray_directions is not None:
                    directions = Vt.Vec3fArray([(float(d[0]), float(d[1]), float(d[2])) for d in ray_directions])
                    self._isaac_sensor_prim.CreateRayDirectionsAttr(directions)
                    if ray_origins is None:
                        self._isaac_sensor_prim.CreateNumRaysAttr(len(ray_directions))
                if ray_time_offsets is not None:
                    offsets = Vt.FloatArray([float(t) for t in ray_time_offsets])
                    self._isaac_sensor_prim.CreateRayTimeOffsetsAttr(offsets)
            if output_frame is not None:
                self._isaac_sensor_prim.CreateOutputFrameOfReferenceAttr(output_frame)
            if report_hit_prim_paths is not None:
                self._isaac_sensor_prim.CreateReportHitPrimPathsAttr(report_hit_prim_paths)
        else:
            carb.log_info(f"Creating a new raycast sensor prim at path {prim_path}")
            self._isaac_sensor_prim = RaycastSensor._create_prim(
                path="/" + self._sensor_name,
                parent=self._body_prim_path,
                min_range=min_range if min_range is not None else 0.4,
                max_range=max_range if max_range is not None else 100.0,
                ray_origins=ray_origins,
                ray_directions=ray_directions,
                ray_time_offsets=ray_time_offsets,
                output_frame=output_frame if output_frame is not None else "SENSOR",
                report_hit_prim_paths=report_hit_prim_paths if report_hit_prim_paths is not None else False,
            )
            super().__init__(
                prim_path,
                positions=position,
                translations=translation,
                orientations=orientation,
                reset_xform_op_properties=True,
            )

        self._backend: RaycastSensorBackend = RaycastSensorBackend(prim_path)

    @property
    def prim_path(self) -> str:
        """Get the USD path of this sensor.

        Returns:
            USD path string.
        """
        return self.paths[0]

    def initialize(self, physics_sim_view: Any = None) -> None:
        """Initialize the sensor for simulation.

        This method is provided for API compatibility and currently performs
        no action as initialization happens automatically.

        Args:
            physics_sim_view: Unused. Provided for API compatibility.
        """

    def get_current_frame(self) -> dict:
        """Get the current raycast sensor data as a structured frame.

        Returns:
            Frame data containing:
            - "depths": Per-ray depth values.
            - "hit_positions": Per-ray hit positions as Nx3 array.
            - "hit_normals": Per-ray surface normals as Nx3 array.
            - "hit_prim_paths": Per-ray hit prim USD paths.
            - "time": Simulation time of reading.
            - "physics_step": Physics step number.

        Example:

        .. code-block:: python

            >>> frame = sensor.get_current_frame()  # doctest: +NO_CHECK
            >>> frame["depths"]  # doctest: +NO_CHECK
            array([2.5], dtype=float32)
        """
        reading = self._backend.get_sensor_reading()

        if reading.is_valid:
            return {
                "depths": reading.depths,
                "hit_positions": reading.hit_positions,
                "hit_normals": reading.hit_normals,
                "hit_prim_paths": reading.hit_prim_paths,
                "time": reading.time,
                "physics_step": int(SimulationManager.get_num_physics_steps()),
            }

        return {
            "depths": np.array([], dtype=np.float32),
            "hit_positions": np.zeros((0, 3), dtype=np.float32),
            "hit_normals": np.zeros((0, 3), dtype=np.float32),
            "hit_prim_paths": [],
            "time": 0.0,
            "physics_step": int(SimulationManager.get_num_physics_steps()),
        }

    def get_sensor_reading(self) -> object:
        """Get the raw C++ sensor reading struct.

        Returns:
            The C++ RaycastSensorReading struct. Access fields via
            ``reading.depths``, ``reading.hit_positions``, etc.
        """
        return self._backend.get_sensor_reading()
