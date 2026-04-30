# SPDX-FileCopyrightText: Copyright (c) 2024-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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

"""Lidar sensor for 3D point cloud generation.

This module provides the Lidar class for creating/wrapping USD OmniLidar prims.
"""

from __future__ import annotations

import pathlib
from typing import Any

import carb
import isaacsim.core.experimental.utils.prim as prim_utils
import isaacsim.core.experimental.utils.stage as stage_utils
import numpy as np
import omni.replicator.core as rep
import warp as wp
from isaacsim.storage.native import get_assets_root_path

from ._sensor_base import _SensorAuthoring
from .rtx_lidar_configs import SUPPORTED_LIDAR_CONFIGS, SUPPORTED_LIDAR_VARIANT_SET_NAME


class Lidar(_SensorAuthoring):
    """High level class for creating/wrapping USD OmniLidar prims.

    This class uses ``omni.replicator.core.functional.create.omni_lidar`` to create new lidar prims,
    which handles defining the prim, applying schemas, and setting attributes.

    .. note::

        This class creates or wraps (one of both) USD OmniLidar prims according to the following rules:

        * If the prim path exists, a wrapper is placed over the USD OmniLidar prim.
        * If the prim path does not exist, a USD OmniLidar prim is created at the path and a wrapper is placed over it.

    Args:
        path: Single path to existing or non-existing (one of both) USD OmniLidar prim.
            Can include regular expression for matching a prim.
        accumulate_outputs: Set the ``omni:sensor:Core:accumulateOutputs`` attribute on the OmniLidar prim.
            When ``True`` (the default), the lidar model accumulates a full scan before generating an output.
        aux_output_level: Auxiliary data level for GenericModelOutput. Valid values:
            ``"NONE"`` (default), ``"BASIC"``, ``"EXTRA"``, ``"FULL"``.
        tick_rate: Sensor tick rate in Hz. A value of ``0`` (the default) enables autotrigger mode.
        schemas: Additional API schemas to apply to the prim.
        attributes: Attributes to set on the OmniLidar prim.
        positions: Positions in the world frame (shape ``(N, 3)``).
            If the input shape is smaller than expected, data will be broadcasted (following NumPy broadcast rules).
        translations: Translations in the local frame (shape ``(N, 3)``).
            If the input shape is smaller than expected, data will be broadcasted (following NumPy broadcast rules).
        orientations: Orientations in the world frame (shape ``(N, 4)``, quaternion ``wxyz``).
            If the input shape is smaller than expected, data will be broadcasted (following NumPy broadcast rules).
        scales: Scales to be applied to the prims (shape ``(N, 3)``).
            If the input shape is smaller than expected, data will be broadcasted (following NumPy broadcast rules).
        reset_xform_op_properties: Whether to reset the transformation operation attributes of the prims to a standard set.
            See :py:meth:`reset_xform_op_properties` for more details.

    Raises:
        ValueError: If no prim is found matching the specified path.
        ValueError: If the input argument refers to more than one prim.

    Example:

    .. code-block:: python

        >>> from isaacsim.sensors.experimental.rtx import Lidar
        >>>
        >>> # given a USD stage with the OmniLidar prim: /World/prim_0
        >>> lidar = Lidar("/World/prim_0")  # doctest: +NO_CHECK
    """

    _PRIM_TYPE = "OmniLidar"
    _SCHEMA = "OmniSensorGenericLidarCoreAPI"
    _VALID_AUX_OUTPUT_LEVELS = ("NONE", "BASIC", "EXTRA", "FULL")

    def __init__(
        self,
        path: str,
        *,
        accumulate_outputs: bool = True,
        aux_output_level: str = "NONE",
        tick_rate: float = 10,
        schemas: list[str] | None = None,
        attributes: dict[str, Any] | None = None,
        positions: list | np.ndarray | wp.array | None = None,
        translations: list | np.ndarray | wp.array | None = None,
        orientations: list | np.ndarray | wp.array | None = None,
        scales: list | np.ndarray | wp.array | None = None,
        reset_xform_op_properties: bool = True,
    ) -> None:
        super().__init__(
            path,
            aux_output_level=aux_output_level,
            tick_rate=tick_rate,
            schemas=schemas,
            attributes=attributes,
            positions=positions,
            translations=translations,
            orientations=orientations,
            scales=scales,
            reset_xform_op_properties=reset_xform_op_properties,
        )
        # resolve accumulate_outputs: attributes dict takes precedence over parameter
        _ATTR = "omni:sensor:Core:accumulateOutputs"
        if attributes is not None and _ATTR in attributes:
            if accumulate_outputs is not True:
                carb.log_warn(
                    "Both 'accumulate_outputs' parameter and 'omni:sensor:Core:accumulateOutputs' attribute "
                    "were provided. Using the value from 'attributes'."
                )
            accumulate_outputs = attributes[_ATTR]
        for prim in self.prims:
            if prim.HasAttribute(_ATTR):
                prim.GetAttribute(_ATTR).Set(accumulate_outputs)

    def _create_prim(self, path: str, attributes: dict[str, Any] | None) -> str:
        """Create an OmniLidar prim via the Replicator functional API.

        Args:
            path: USD prim path for the new lidar.
            attributes: Optional mapping of attribute names to values, forwarded to
                ``rep.functional.create.omni_lidar``.

        Returns:
            The USD prim path of the created lidar.
        """
        path_parts = path.rsplit("/", 1)
        parent = path_parts[0] if len(path_parts) > 1 and path_parts[0] else None
        name = path_parts[-1]
        # Replicator's parent-valid check runs against the pxr USD stage.
        # ``stage.DefinePrim`` is idempotent: it creates missing ancestors as
        # typeless overs and upgrades only untyped prims to the supplied type.
        if parent is not None:
            stage = stage_utils.get_current_stage(backend="usd")
            if not stage.GetPrimAtPath(parent).IsValid():
                stage.DefinePrim(parent, "Xform")
        prims = rep.functional.create.omni_lidar(
            name=name,
            parent=parent,
            **(attributes or {}),
        )
        prim = prims[0] if isinstance(prims, (list, tuple)) else prims
        return prim_utils.get_prim_path(prim)

    @staticmethod
    def create(
        path: str,
        *,
        accumulate_outputs: bool = True,
        aux_output_level: str = "NONE",
        tick_rate: float = 0,
        schemas: list[str] | None = None,
        attributes: dict[str, Any] | None = None,
        positions: list | np.ndarray | wp.array | None = None,
        translations: list | np.ndarray | wp.array | None = None,
        orientations: list | np.ndarray | wp.array | None = None,
        scales: list | np.ndarray | wp.array | None = None,
        reset_xform_op_properties: bool = True,
        config: str | None = None,
        usd_path: str | None = None,
        variant: str | None = None,
    ) -> Lidar:
        """Create a Lidar instance from a config name or USD file path.

        Args:
            path: Single path to existing or non-existing (one of both) USD OmniLidar prim.
            accumulate_outputs: Set the ``omni:sensor:Core:accumulateOutputs`` attribute on the OmniLidar prim.
                When ``True`` (the default), the lidar model accumulates a full scan before generating an output.
            tick_rate: Sensor tick rate in Hz. A value of ``0`` (the default) enables autotrigger mode.
            attributes: Attributes to set on the OmniLidar prim.
            positions: Positions in the world frame (shape ``(N, 3)``).
            translations: Translations in the local frame (shape ``(N, 3)``).
            orientations: Orientations in the world frame (shape ``(N, 4)``, quaternion ``wxyz``).
            scales: Scales to be applied to the prims (shape ``(N, 3)``).
            reset_xform_op_properties: Whether to reset the transformation operation attributes of the prims.
            config: Configuration name for the sensor (from ``SUPPORTED_LIDAR_CONFIGS``).
            usd_path: Path to a USD file containing the sensor asset.
            variant: Variant name for the sensor configuration.

        Returns:
            Lidar instance.

        Raises:
            ValueError: If both 'config' and 'usd_path' are provided.
            ValueError: If the specified config is not found.

        Example:

        .. code-block:: python

            >>> from isaacsim.sensors.experimental.rtx import Lidar
            >>>
            >>> lidar = Lidar.create(
            ...     path="/World/lidar",
            ...     config="OS1",
            ...     variant="OS1_REV6_32ch20hz512res",
            ... )
        """
        if config is not None and usd_path is not None:
            raise ValueError("Both 'config' and 'usd_path' cannot be provided")
        if config is not None:
            for config_path in SUPPORTED_LIDAR_CONFIGS:
                config_name = pathlib.Path(config_path).stem
                if config in [config_path, config_name]:
                    usd_path = get_assets_root_path() + config_path
                    break
            if usd_path is None:
                raise ValueError(
                    f"Config '{config}' not found. Supported configs: {list(SUPPORTED_LIDAR_CONFIGS.keys())}"
                )
        if usd_path is not None:
            path = Lidar._create_from_usd(
                path=path,
                usd_path=usd_path,
                variant=variant,
                variant_set_name=SUPPORTED_LIDAR_VARIANT_SET_NAME,
            )
        return Lidar(
            path=path,
            accumulate_outputs=accumulate_outputs,
            aux_output_level=aux_output_level,
            tick_rate=tick_rate,
            schemas=schemas,
            attributes=attributes,
            positions=positions,
            translations=translations,
            orientations=orientations,
            scales=scales,
            reset_xform_op_properties=reset_xform_op_properties,
        )
