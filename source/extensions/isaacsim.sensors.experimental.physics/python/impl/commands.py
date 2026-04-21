# SPDX-FileCopyrightText: Copyright (c) 2018-2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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

"""Kit commands for creating physics-based sensors.

This module provides undoable commands for creating Isaac Sensor prims
in the USD stage, including contact sensors and IMU sensors.
"""
from __future__ import annotations

import carb
import numpy as np
import omni.isaac.IsaacSensorSchema as IsaacSensorSchema
import omni.kit.commands
import omni.kit.utils
import omni.usd
from isaacsim.core.experimental.prims import XformPrim
from isaacsim.core.experimental.utils import stage as stage_utils
from pxr import Gf, PhysxSchema


class IsaacSensorExperimentalCreatePrim(omni.kit.commands.Command):
    """Base command for creating Isaac Sensor prims.

    Creates a sensor prim at the specified path with the given schema type
    and transform. This is a base command used by specific sensor creation
    commands.

    Args:
        path: Relative path for the new prim (appended to parent).
        parent: Parent prim path. If empty, path is used as absolute.
        translation: Local translation offset.
        orientation: Local orientation as quaternion [w, x, y, z].
        schema_type: USD schema type for the sensor prim.
    """

    def __init__(
        self,
        path: str = "",
        parent: str = "",
        translation: Gf.Vec3d = Gf.Vec3d(0, 0, 0),
        orientation: Gf.Quatd = Gf.Quatd(1, 0, 0, 0),
        schema_type: type = IsaacSensorSchema.IsaacBaseSensor,
    ):
        # Copy all arguments to instance variables with underscore prefix
        for name, value in vars().items():
            if name != "self":
                setattr(self, f"_{name}", value)
        self._prim_path = None

    def do(self) -> object | None:
        """Execute the command to create the sensor prim.

        Returns:
            The created USD prim, or None if creation failed.
        """
        self._stage = omni.usd.get_context().get_stage()

        # Build full path from parent and relative path
        if self._parent:
            base_path = f"{self._parent.rstrip('/')}/{self._path.lstrip('/')}"
        else:
            base_path = self._path

        # Generate unique path if one already exists
        self._prim_path = stage_utils.generate_next_free_path(base_path, prepend_default_prim=False)

        # Create the prim with the specified schema
        self._prim = self._schema_type.Define(self._stage, self._prim_path)

        # Enable the sensor by default
        IsaacSensorSchema.IsaacBaseSensor(self._prim).CreateEnabledAttr(True)

        # Set transform using XformPrim
        translation = np.array(self._translation, dtype=np.float64)
        orientation = np.array([self._orientation.GetReal(), *self._orientation.GetImaginary()], dtype=np.float64)
        xform_prim = XformPrim(self._prim_path, reset_xform_op_properties=True)
        xform_prim.set_local_poses(translations=translation, orientations=orientation)

        return self._prim

    def undo(self):
        """Undo the command by deleting the created prim."""
        if self._prim_path is not None:
            stage_utils.delete_prim(self._prim_path)


class IsaacSensorExperimentalCreateContactSensor(omni.kit.commands.Command):
    """Command for creating a contact sensor prim.

    Creates an IsaacContactSensor prim under the specified parent with
    configurable threshold, radius, and color. Also applies the
    PhysxContactReportAPI to the parent prim to enable contact reporting.

    Args:
        path: Relative path for the sensor (appended to parent).
        parent: Parent prim path. Must have a collision-enabled prim.
        min_threshold: Minimum force threshold in Newtons.
        max_threshold: Maximum force threshold in Newtons.
        color: Visualization color as [r, g, b, a].
        radius: Contact detection radius. Negative disables radius filtering.
        translation: Local translation offset.
    """

    def __init__(
        self,
        path: str = "/Contact_Sensor",
        parent: str | None = None,
        min_threshold: float = 0,
        max_threshold: float = 100000,
        color: Gf.Vec4f = Gf.Vec4f(1, 1, 1, 1),
        radius: float = -1,
        translation: Gf.Vec3d = Gf.Vec3d(0, 0, 0),
    ):
        # Copy all arguments to instance variables with underscore prefix
        for name, value in vars().items():
            if name != "self":
                setattr(self, f"_{name}", value)
        self._prim = None

    def do(self) -> object | None:
        """Execute the command to create the contact sensor.

        Creates the sensor prim and configures its attributes. Also applies
        PhysxContactReportAPI to the parent prim.

        Returns:
            The created IsaacContactSensor prim, or None if creation failed.
        """
        if self._parent is None:
            carb.log_error("Valid parent prim must be selected before creating contact sensor prim.")
            return None

        # Create base sensor prim
        success, self._prim = omni.kit.commands.execute(
            "IsaacSensorExperimentalCreatePrim",
            path=self._path,
            parent=self._parent,
            schema_type=IsaacSensorSchema.IsaacContactSensor,
            translation=self._translation,
        )

        if success and self._prim:
            # Configure sensor attributes
            self._prim.CreateThresholdAttr().Set((self._min_threshold, self._max_threshold))
            self._prim.CreateColorAttr().Set(self._color)
            self._prim.CreateRadiusAttr().Set(self._radius)

            # Apply contact report API to parent for PhysX contact events
            stage = omni.usd.get_context().get_stage()
            parent_prim = stage.GetPrimAtPath(self._parent)
            contact_report = PhysxSchema.PhysxContactReportAPI.Apply(parent_prim)
            contact_report.CreateThresholdAttr(self._min_threshold)

            return self._prim

        else:
            carb.log_error("Could not create contact sensor prim")
            return None

    def undo(self):
        """Undo the command.

        Note: Does not remove PhysxContactReportAPI from parent.
        """


class IsaacSensorExperimentalCreateImuSensor(omni.kit.commands.Command):
    """Command for creating an IMU sensor prim.

    Creates an IsaacImuSensor prim under the specified parent with
    configurable filter widths.

    Args:
        path: Relative path for the sensor (appended to parent).
        parent: Parent prim path.
        translation: Local translation offset.
        orientation: Local orientation as quaternion [w, x, y, z].
        linear_acceleration_filter_size: Rolling average window for acceleration.
        angular_velocity_filter_size: Rolling average window for angular velocity.
        orientation_filter_size: Rolling average window for orientation.
    """

    def __init__(
        self,
        path: str = "/Imu_Sensor",
        parent: str | None = None,
        translation: Gf.Vec3d = Gf.Vec3d(0, 0, 0),
        orientation: Gf.Quatd = Gf.Quatd(1, 0, 0, 0),
        linear_acceleration_filter_size: int = 1,
        angular_velocity_filter_size: int = 1,
        orientation_filter_size: int = 1,
    ):
        # Copy all arguments to instance variables with underscore prefix
        for name, value in vars().items():
            if name != "self":
                setattr(self, f"_{name}", value)
        self._prim = None

    def do(self) -> object | None:
        """Execute the command to create the IMU sensor.

        Creates the sensor prim and configures its filter attributes.

        Returns:
            The created IsaacImuSensor prim, or None if creation failed.
        """
        # Create base sensor prim with orientation
        success, self._prim = omni.kit.commands.execute(
            "IsaacSensorExperimentalCreatePrim",
            path=self._path,
            parent=self._parent,
            schema_type=IsaacSensorSchema.IsaacImuSensor,
            translation=self._translation,
            orientation=self._orientation,
        )

        if success and self._prim:
            # Configure sensor attributes
            self._prim.CreateLinearAccelerationFilterWidthAttr().Set(self._linear_acceleration_filter_size)
            self._prim.CreateAngularVelocityFilterWidthAttr().Set(self._angular_velocity_filter_size)
            self._prim.CreateOrientationFilterWidthAttr().Set(self._orientation_filter_size)

            return self._prim
        else:
            carb.log_error("Could not create Imu sensor prim")
            return None

    def undo(self):
        """Undo the command.

        Note: Prim deletion is handled by IsaacSensorExperimentalCreatePrim.undo().
        """


class IsaacSensorExperimentalCreateRaycastSensor(omni.kit.commands.Command):
    """Command for creating a physics raycast sensor prim.

    Creates an IsaacRaycastSensor prim under the specified parent with
    configurable ray geometry, range, output frame, and hit prim resolution.

    Args:
        path: Relative path for the sensor (appended to parent).
        parent: Parent prim path.
        min_range: Minimum detection range in stage length units.
        max_range: Maximum detection range in stage length units.
        ray_origins: Per-ray origin translations as list of (x,y,z).
        ray_directions: Per-ray direction vectors as list of (x,y,z).
        ray_time_offsets: Per-ray time offsets in seconds.
        output_frame: "SENSOR" or "WORLD".
        report_hit_prim_paths: Whether to resolve hit prim USD paths.
        translation: Local translation offset.
        orientation: Local orientation as quaternion.
    """

    def __init__(
        self,
        path: str = "/Raycast_Sensor",
        parent: str | None = None,
        min_range: float = 0.4,
        max_range: float = 100.0,
        ray_origins: list | np.ndarray | None = None,
        ray_directions: list | np.ndarray | None = None,
        ray_time_offsets: list | np.ndarray | None = None,
        output_frame: str = "SENSOR",
        report_hit_prim_paths: bool = False,
        translation: Gf.Vec3d = Gf.Vec3d(0, 0, 0),
        orientation: Gf.Quatd = Gf.Quatd(1, 0, 0, 0),
    ):
        for name, value in vars().items():
            if name != "self":
                setattr(self, f"_{name}", value)
        self._prim = None

    def do(self) -> object | None:
        """Execute the command to create the physics raycast sensor.

        Creates the sensor prim and configures ray geometry, range, output
        frame, and hit prim path reporting attributes.

        Returns:
            The created IsaacRaycastSensor prim, or None if creation failed.
        """
        if self._parent is None:
            carb.log_error("Valid parent prim must be selected before creating physics raycast sensor prim.")
            return None

        if self._ray_origins is not None and self._ray_directions is not None:
            if len(self._ray_origins) != len(self._ray_directions):
                carb.log_error(
                    f"ray_origins length ({len(self._ray_origins)}) != "
                    f"ray_directions length ({len(self._ray_directions)})"
                )
                return None

        if self._ray_origins is not None:
            num_rays = len(self._ray_origins)
        elif self._ray_directions is not None:
            num_rays = len(self._ray_directions)
        else:
            num_rays = 1

        if self._ray_time_offsets is not None and len(self._ray_time_offsets) != num_rays:
            carb.log_error(f"ray_time_offsets length ({len(self._ray_time_offsets)}) != num_rays ({num_rays})")
            return None

        success, self._prim = omni.kit.commands.execute(
            "IsaacSensorExperimentalCreatePrim",
            path=self._path,
            parent=self._parent,
            schema_type=IsaacSensorSchema.IsaacRaycastSensor,
            translation=self._translation,
            orientation=self._orientation,
        )

        if success and self._prim:
            from pxr import Vt

            self._prim.CreateMinRangeAttr(self._min_range)
            self._prim.CreateMaxRangeAttr(self._max_range)

            if self._ray_origins is not None:
                origins = Vt.Vec3fArray([(float(o[0]), float(o[1]), float(o[2])) for o in self._ray_origins])
                self._prim.CreateRayOriginsAttr(origins)

            if self._ray_directions is not None:
                directions = Vt.Vec3fArray([(float(d[0]), float(d[1]), float(d[2])) for d in self._ray_directions])
                self._prim.CreateRayDirectionsAttr(directions)

            if self._ray_time_offsets is not None:
                offsets = Vt.FloatArray([float(t) for t in self._ray_time_offsets])
                self._prim.CreateRayTimeOffsetsAttr(offsets)

            self._prim.CreateNumRaysAttr(num_rays)
            self._prim.CreateOutputFrameOfReferenceAttr(self._output_frame)
            self._prim.CreateReportHitPrimPathsAttr(self._report_hit_prim_paths)

            return self._prim
        else:
            carb.log_error("Could not create physics raycast sensor prim")
            return None

    def undo(self):
        """Undo the command.

        Note: Prim deletion is handled by IsaacSensorExperimentalCreatePrim.undo().
        """


# Register all command classes in this module with Kit
omni.kit.commands.register_all_commands_in_module(__name__)
