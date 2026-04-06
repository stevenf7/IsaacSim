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

"""RTX lidar sensor implementation."""

from __future__ import annotations

import pathlib
from typing import Any, Literal, get_args

import carb
import isaacsim.core.experimental.utils.prim as prim_utils
import isaacsim.core.experimental.utils.stage as stage_utils
import numpy as np
import omni.kit.commands
import omni.replicator.core as rep
import warp as wp
from isaacsim.core.experimental.prims import XformPrim
from isaacsim.storage.native import get_assets_root_path
from pxr import UsdRender

from ._common import ANNOTATOR_SPEC
from .rtx_lidar_configs import SUPPORTED_LIDAR_CONFIGS, SUPPORTED_LIDAR_VARIANT_SET_NAME

ANNOTATOR = Literal[
    "generic-model-output",
    "stable-id-map",
]


class RtxLidarSensor(XformPrim):
    """High level class for creating/wrapping and operating single RTX-based lidar sensor.

    Args:
        path: Single path to existing or non-existing (one of both) USD OmniLidar prim.
            Can include regular expression for matching a prim.
        annotators: Annotator/sensor types to configure.
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
        ValueError: If an unsupported annotator type is specified.

    Example:

    .. code-block:: python

        >>> import isaacsim.core.experimental.utils.app as app_utils
        >>> from isaacsim.sensors.experimental.rtx import RtxLidarSensor
        >>>
        >>> # given a USD stage with the OmniLidar prim: /World/prim_0
        >>> # and a USD Cube prim: /World/cube
        >>> sensor = RtxLidarSensor(
        ...     "/World/prim_0",
        ...     annotators=["generic-model-output"],
        ... )  # doctest: +NO_CHECK
        >>>
        >>> # play the simulation so the sensor can fetch data
        >>> app_utils.play(commit=True)
    """

    def __init__(
        self,
        path: str,
        *,
        # RtxLidarSensor
        annotators: ANNOTATOR | list[ANNOTATOR],
        attributes: dict[str, Any] | None = None,
        # XformPrim
        positions: list | np.ndarray | wp.array | None = None,
        translations: list | np.ndarray | wp.array | None = None,
        orientations: list | np.ndarray | wp.array | None = None,
        scales: list | np.ndarray | wp.array | None = None,
        reset_xform_op_properties: bool = True,
    ):
        # define properties
        self._hydra_texture = None
        self._annotators = {}
        if not hasattr(self, "_annotators_spec"):
            self._annotators_spec = {annotator: ANNOTATOR_SPEC[annotator] for annotator in get_args(ANNOTATOR)}
        # check for supported annotators
        self._validate_annotators(annotators)
        # get or create lidarsobject
        existent_paths, nonexistent_paths = XformPrim.resolve_paths(path)
        if len(existent_paths) > 1 or len(nonexistent_paths) > 1:
            raise ValueError(
                "The sensor only supports one OmniLidar prim, "
                f"but the provided argument refers to {len(existent_paths) + len(nonexistent_paths)} prims: "
                f"{existent_paths + nonexistent_paths}",
            )
        # get lidars
        if existent_paths:
            paths = existent_paths
            for path in existent_paths:
                prim = prim_utils.get_prim_at_path(path)
                type_name = prim.GetPrimTypeInfo().GetTypeName()
                if type_name != "OmniLidar":
                    raise ValueError(f"Prim at {path} is not an 'OmniLidar' prim but a '{type_name}' prim")
                if not prim.HasAPI("OmniSensorGenericLidarCoreAPI"):
                    raise ValueError(f"Prim at {path} does not have the 'OmniSensorGenericLidarCoreAPI' schema")
        # create lidars
        else:
            paths = nonexistent_paths
            for path in nonexistent_paths:
                prim = stage_utils.define_prim(path, "OmniLidar")
                prim.ApplyAPI("OmniSensorGenericLidarCoreAPI")
        # initialize base class
        super().__init__(
            paths,
            resolve_paths=False,
            positions=positions,
            translations=translations,
            orientations=orientations,
            scales=scales,
            reset_xform_op_properties=reset_xform_op_properties,
        )
        # initialize instance from arguments
        if attributes is not None:
            for prim in self.prims:
                for attribute, value in attributes.items():
                    if prim.HasAttribute(attribute):
                        prim.GetAttribute(attribute).Set(value)
                    else:
                        carb.log_warn(
                            f"Sensor (at path '{prim_utils.get_prim_path(prim)}') does not have attribute '{attribute}'"
                        )
        self._initialize_sensor(annotators)

    def __del__(self) -> None:
        """Clean up instance."""
        self._invalidate_sensor()

    """
    Properties.
    """

    @property
    def annotators(self) -> list[str]:
        """Annotators.

        Returns:
            Sorted list of registered annotators.

        Example:

        .. code-block:: python

            >>> sensor.annotators
            ['generic-model-output']
        """
        return sorted(list(self._annotators.keys()))

    @property
    def render_product(self) -> UsdRender.Product:
        """Render product.

        Returns:
            Render product of the sensor.

        Example:

        .. code-block:: python

            >>> sensor.render_product
            UsdRender.Product(Usd.Prim(</Render/OmniverseKit/HydraTextures/rtx_sensor_...>))
        """
        prim = prim_utils.get_prim_at_path(self._hydra_texture.path)
        if prim.IsValid() and prim.IsA(UsdRender.Product):
            return UsdRender.Product(prim)
        raise RuntimeError(f"Invalid render product at path '{self._hydra_texture.path}'")

    """
    Static methods.
    """

    @staticmethod
    def create_sensor(
        *,
        path: str,
        # RtxLidarSensor
        annotators: ANNOTATOR | list[ANNOTATOR],
        attributes: dict[str, Any] | None = None,
        # XformPrim
        positions: list | np.ndarray | wp.array | None = None,
        translations: list | np.ndarray | wp.array | None = None,
        orientations: list | np.ndarray | wp.array | None = None,
        scales: list | np.ndarray | wp.array | None = None,
        reset_xform_op_properties: bool = True,
        # sensor creation (static method specific arguments)
        config: str | None = None,
        usd_path: str | None = None,
        variant: str | None = None,
    ) -> RtxLidarSensor:
        """Create a RtxLidarSensor instance.

        Args:
            path: Single path to existing or non-existing (one of both) USD OmniLidar prim.
                Can include regular expression for matching a prim.
            annotators: Annotator/sensor types to configure.
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
            config: Configuration name for the sensor.
                If provided, the sensor will be created from the supported sensor configurations
                (added to the USD stage as a reference).
            usd_path: Path to a USD file containing the sensor asset.
                If provided, the sensor will be created from the specified USD file
                (added to the USD stage as a reference).
            variant: Variant name for the sensor configuration.
                This argument is only used if ``config`` or ``usd_path`` is provided.

        Returns:
            RtxLidarSensor instance.

        Raises:
            ValueError: If both 'config' and 'usd_path' are provided.
            ValueError: If the specified variant is not supported.
            ValueError: If no prim is found matching the specified path.
            ValueError: If the input argument refers to more than one prim.
            ValueError: If an unsupported annotator type is specified.

        Example:

        .. code-block:: python

            >>> from isaacsim.sensors.experimental.rtx import RtxLidarSensor
            >>>
            >>> lidar_sensor = RtxLidarSensor.create_sensor(
            ...     path="/World/sensor",
            ...     annotators=["generic-model-output"],
            ...     config="OS1",
            ...     variant="OS1_REV6_32ch20hz512res",
            ... )
            >>> lidar_sensor.annotators
            ['generic-model-output']
        """
        if config is not None and usd_path is not None:
            raise ValueError("Both 'config' and 'usd_path' cannot be provided")
        # parse config
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
        # create sensor from USD file path
        if usd_path is not None:
            # add reference to stage
            prim_type = "OmniLidar" if usd_path.endswith(".usda") else "Xform"
            variants = [(SUPPORTED_LIDAR_VARIANT_SET_NAME, variant)] if variant is not None else []
            stage_utils.add_reference_to_stage(usd_path=usd_path, path=path, prim_type=prim_type, variants=variants)
            # get lidar prim
            predicate = lambda prim, path: prim.GetTypeName() == "OmniLidar"
            lidar_prim = prim_utils.get_first_matching_child_prim(path, predicate=predicate, include_self=True)
            if lidar_prim is None:
                raise ValueError(f"Unable to find OmniLidar prim in the USD file {usd_path} (variant: {variant})")
            path = prim_utils.get_prim_path(lidar_prim)
        # create sensor
        return RtxLidarSensor(
            path=path,
            annotators=annotators,
            attributes=attributes,
            positions=positions,
            translations=translations,
            orientations=orientations,
            scales=scales,
            reset_xform_op_properties=reset_xform_op_properties,
        )

    """
    Methods.
    """

    def attach_annotators(self, annotators: str | list[str]) -> None:
        """Attach annotators to the sensor.

        Args:
            annotators: Annotator/sensor types to attach.

        Raises:
            ValueError: If the specified annotator is not supported.

        Example:

        .. code-block:: python

            >>> sensor.annotators
            ['generic-model-output']
            >>> sensor.attach_annotators("stable-id-map")
            >>> sensor.annotators
            ['generic-model-output', 'stable-id-map']
        """
        annotators = [annotators] if isinstance(annotators, str) else annotators
        self._validate_annotators(annotators)
        # define annotator instances
        for annotator in annotators:
            spec = self._get_annotator_spec(annotator)
            device = "cuda"
            if annotator in ["stable-id-map", "generic-model-output"]:
                device = "cpu"
            self._annotators[annotator] = rep.AnnotatorRegistry.get_annotator(
                spec["name"], device=device, do_array_copy=False
            )
        # attach annotator instances to the hydra texture
        for annotator in annotators:
            self._annotators[annotator].attach(self._hydra_texture.path)

    def detach_annotators(self, annotators: str | list[str]) -> None:
        """Detach annotators from the sensor.

        Args:
            annotators: Annotator/sensor types to detach. If the annotator is not attached,
                or it has already been detached, a warning is logged and the method does nothing.

        Raises:
            ValueError: If the specified annotator is not supported.

        Example:

        .. code-block:: python

            >>> sensor.annotators
            ['generic-model-output', 'stable-id-map']
            >>> sensor.detach_annotators(["generic-model-output"])
            >>> sensor.annotators
            ['stable-id-map']
        """
        annotators = [annotators] if isinstance(annotators, str) else annotators
        self._validate_annotators(annotators)
        # detach annotator instances from the hydra texture
        for annotator in annotators:
            if annotator not in self._annotators:
                carb.log_warn(f"Unable to detach annotator '{annotator}'. It might have been already detached")
                continue
            self._annotators[annotator].detach([self._hydra_texture.path])
            del self._annotators[annotator]

    def get_data(self, annotator: str) -> tuple[wp.array | None, dict[str, Any]]:
        """Fetch the specified annotator/sensor data for the sensor.

        Args:
            annotator: Annotator/sensor type from which fetch the data.

        Returns:
            Two-elements tuple. 1) Array containing the fetched data.
            If no data is available at the moment of calling the method, ``None`` is returned.
            2) Dictionary containing additional information according to the requested annotator/sensor.

        Raises:
            ValueError: If the specified annotator is not supported.
            ValueError: If the specified annotator is not configured.

        Example:

        .. code-block:: python

            >>> from isaacsim.sensors.experimental.rtx import parse_stable_id_map_data
            >>>
            >>> data, info = sensor.get_data("stable-id-map")  # doctest: +NO_CHECK
            >>> data.numpy()  # doctest: +NO_CHECK
            array([ 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 11, 0, 0, 0, 24, 0, 0,
                    0, 47, 87, 111, 114, 108, 100, 47, 99, 117, 98, 101, 0, 1, 0, 0, 0], dtype=uint8)
            >>>
            >>> # parse the fetched stable ID map data
            >>> parse_stable_id_map_data(data) # doctest: +NO_CHECK
            {0: '/World/cube'}
        """
        self._validate_annotators(annotator)
        if annotator not in self._annotators:
            raise ValueError(f"The annotator '{annotator}' was not configured. Enable it when instantiating the class")
        # fetch data from annotator
        data = self._annotators[annotator].get_data("cuda")
        if isinstance(data, dict):
            info = data["info"]
            data = data["data"]
        else:
            info = {}
        return data, info

    """
    Internal methods.
    """

    def _invalidate_sensor(self):
        """Invalidate sensor by detaching annotators and destroying the hydra texture."""
        # detach annotators and destroy the hydra texture
        if self._hydra_texture is not None:
            self.detach_annotators(list(self._annotators.keys()))
            self._hydra_texture.destroy()
        # reset properties
        self._annotators = {}
        self._hydra_texture = None

    def _initialize_sensor(self, annotators: str | list[str]):
        """Initialize sensor by creating the hydra texture and attaching annotators.

        Args:
            annotators: Annotator name or list of annotator names to attach.
        """
        # create the hydra texture
        self._hydra_texture = rep.create.render_product(
            camera=self.paths[0],
            resolution=(300, 300),  # (width, height), needed but unused by the RTX sensor
            name=f"rtx_sensor_{hash(self)}",
        )
        # attach annotators
        self.attach_annotators(annotators)

    def _get_annotator_spec(self, annotator: str) -> dict[str, Any]:
        """Get the specification of the given annotator.

        Args:
            annotator: Name of the annotator to look up.

        Returns:
            Dictionary containing the annotator specification.
        """
        try:
            return self._annotators_spec[annotator]
        except KeyError:
            raise ValueError(
                f"Unsupported annotator '{annotator}'. Supported annotator are {list(self._annotators_spec.keys())}"
            )

    def _validate_annotators(self, annotators: str | list[str]) -> None:
        """Validate the given annotators.

        Args:
            annotators: Annotator name or list of annotator names to validate.
        """
        annotators = [annotators] if isinstance(annotators, str) else annotators
        for annotator in annotators:
            if annotator not in self._annotators_spec:
                raise ValueError(
                    f"Unsupported annotator '{annotator}'. Supported annotator are {list(self._annotators_spec.keys())}"
                )
