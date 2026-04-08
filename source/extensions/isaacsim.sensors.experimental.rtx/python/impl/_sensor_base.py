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

"""Base classes for RTX sensor authoring and runtime."""

from __future__ import annotations

from typing import Any, Literal, get_args

import carb
import isaacsim.core.experimental.utils.prim as prim_utils
import isaacsim.core.experimental.utils.stage as stage_utils
import numpy as np
import omni.replicator.core as rep
import warp as wp
from isaacsim.core.experimental.prims import XformPrim
from pxr import UsdRender

from ._common import ANNOTATOR_SPEC

ANNOTATOR = Literal[
    "generic-model-output",
    "stable-id-map",
]


class _SensorAuthoring(XformPrim):
    """Base class for RTX sensor authoring (USD prim creation and wrapping).

    Handles path resolution, prim type/schema validation, attribute application,
    tick rate configuration, and USD reference loading. Subclasses define the
    sensor-specific prim type, schema, and creation logic.

    Subclasses must define:
        _PRIM_TYPE: str — USD prim type name (e.g. ``"OmniLidar"``)
        _SCHEMA: str — API schema name (e.g. ``"OmniSensorGenericLidarCoreAPI"``)
        _create_prim(path, attributes) -> str — create a new prim and return its actual path
    """

    _PRIM_TYPE: str
    _SCHEMA: str

    def __init__(
        self,
        path: str,
        *,
        tick_rate: float = 0,
        attributes: dict[str, Any] | None = None,
        # XformPrim
        positions: list | np.ndarray | wp.array | None = None,
        translations: list | np.ndarray | wp.array | None = None,
        orientations: list | np.ndarray | wp.array | None = None,
        scales: list | np.ndarray | wp.array | None = None,
        reset_xform_op_properties: bool = True,
    ) -> None:
        existent_paths, nonexistent_paths = XformPrim.resolve_paths(path)
        if len(existent_paths) > 1 or len(nonexistent_paths) > 1:
            raise ValueError(
                f"Only one {self._PRIM_TYPE} prim is supported, "
                f"but the provided argument refers to {len(existent_paths) + len(nonexistent_paths)} prims: "
                f"{existent_paths + nonexistent_paths}",
            )
        # wrap existing prims
        if existent_paths:
            paths = existent_paths
            for path in existent_paths:
                prim = prim_utils.get_prim_at_path(path)
                type_name = prim.GetPrimTypeInfo().GetTypeName()
                if type_name != self._PRIM_TYPE:
                    raise ValueError(f"Prim at {path} is not an '{self._PRIM_TYPE}' prim but a '{type_name}' prim")
                if not prim.HasAPI(self._SCHEMA):
                    raise ValueError(f"Prim at {path} does not have the '{self._SCHEMA}' schema")
            if attributes is not None:
                for path in existent_paths:
                    self._apply_attributes(path, attributes)
        # create new prims
        else:
            paths = []
            for path in nonexistent_paths:
                actual_path = self._create_prim(path, attributes)
                paths.append(actual_path)
        # resolve tick rate: attributes dict takes precedence over tick_rate parameter
        if attributes is not None and "omni:sensor:tickRate" in attributes:
            if tick_rate != 0:
                carb.log_warn(
                    "Both 'tick_rate' parameter and 'omni:sensor:tickRate' attribute were provided. "
                    "Using the value from 'attributes'."
                )
            tick_rate = attributes["omni:sensor:tickRate"]
        for p in paths:
            prim = prim_utils.get_prim_at_path(p)
            if prim.HasAttribute("omni:sensor:tickRate"):
                prim.GetAttribute("omni:sensor:tickRate").Set(tick_rate)
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

    def _create_prim(self, path: str, attributes: dict[str, Any] | None) -> str:
        """Create a new sensor prim. Override in subclasses.

        Args:
            path: USD path for the new prim.
            attributes: Attributes to set on the prim.

        Returns:
            Actual prim path after creation.
        """
        raise NotImplementedError

    @staticmethod
    def _apply_attributes(path: str, attributes: dict[str, Any]) -> None:
        """Apply attributes to an existing prim."""
        prim = prim_utils.get_prim_at_path(path)
        for attribute, value in attributes.items():
            if prim.HasAttribute(attribute):
                prim.GetAttribute(attribute).Set(value)
            else:
                carb.log_warn(
                    f"Prim (at path '{prim_utils.get_prim_path(prim)}') " f"does not have attribute '{attribute}'"
                )

    @classmethod
    def _create_from_usd(
        cls,
        *,
        path: str,
        usd_path: str,
        variant: str | None = None,
        variant_set_name: str = "sensor",
    ) -> str:
        """Add a USD reference to the stage and find the sensor prim within it.

        Args:
            path: Target prim path on stage.
            usd_path: Path to the USD file.
            variant: Optional variant name.
            variant_set_name: Variant set name.

        Returns:
            Path to the sensor prim found within the reference.
        """
        prim_type = cls._PRIM_TYPE if usd_path.endswith(".usda") else "Xform"
        variants = [(variant_set_name, variant)] if variant is not None else []
        stage_utils.add_reference_to_stage(usd_path=usd_path, path=path, prim_type=prim_type, variants=variants)
        predicate = lambda prim, path: prim.GetTypeName() == cls._PRIM_TYPE
        sensor_prim = prim_utils.get_first_matching_child_prim(path, predicate=predicate, include_self=True)
        if sensor_prim is None:
            raise ValueError(f"Unable to find {cls._PRIM_TYPE} prim in the USD file {usd_path} (variant: {variant})")
        return prim_utils.get_prim_path(sensor_prim)


class _SensorRuntime:
    """Base class for RTX sensor runtime (annotator management and data retrieval).

    Wraps a sensor authoring object, creates a Replicator render product, and
    provides methods to attach/detach annotators and fetch sensor data. Subclasses
    define the authoring class type and a typed property to expose it.

    Subclasses must define:
        _AUTHORING_CLASS: type — the authoring class (e.g. ``Lidar``)
        _AUTHORING_ATTR: str — attribute name for the encapsulated object (e.g. ``"_lidar"``)
    """

    _AUTHORING_CLASS: type
    _AUTHORING_ATTR: str

    def __init__(
        self,
        path: str | _SensorAuthoring,
        *,
        annotators: ANNOTATOR | list[ANNOTATOR],
    ) -> None:
        # define properties
        self._hydra_texture = None
        self._annotators = {}
        if not hasattr(self, "_annotators_spec"):
            self._annotators_spec = {annotator: ANNOTATOR_SPEC[annotator] for annotator in get_args(ANNOTATOR)}
        # check for supported annotators
        self._validate_annotators(annotators)
        # get or create authoring object
        authoring_obj = path if isinstance(path, self._AUTHORING_CLASS) else self._AUTHORING_CLASS(path)
        setattr(self, self._AUTHORING_ATTR, authoring_obj)
        if len(authoring_obj) > 1:
            raise ValueError(
                f"The sensor only supports one {self._AUTHORING_CLASS._PRIM_TYPE} prim, "
                f"but the provided argument refers to {len(authoring_obj)} prims: {authoring_obj.paths}",
            )
        # initialize instance from arguments
        self._initialize_sensor(annotators)

    def __del__(self) -> None:
        """Clean up instance."""
        self._invalidate_sensor()

    @property
    def authoring_object(self) -> _SensorAuthoring:
        """The authoring object (prim wrapper) encapsulated by the sensor.

        Returns:
            The sensor's authoring object (e.g. :class:`Lidar`, :class:`Radar`, or :class:`Acoustic`).
        """
        return getattr(self, self._AUTHORING_ATTR)

    @property
    def annotators(self) -> list[str]:
        """Annotators.

        Returns:
            Sorted list of registered annotators.
        """
        return sorted(self._annotators.keys())

    @property
    def render_product(self) -> UsdRender.Product:
        """Render product.

        Returns:
            Render product of the sensor.
        """
        prim = prim_utils.get_prim_at_path(self._hydra_texture.path)
        if prim.IsValid() and prim.IsA(UsdRender.Product):
            return UsdRender.Product(prim)
        raise RuntimeError(f"Invalid render product at path '{self._hydra_texture.path}'")

    def attach_annotators(self, annotators: str | list[str]) -> None:
        """Attach annotators to the sensor.

        Args:
            annotators: Annotator/sensor types to attach.

        Raises:
            ValueError: If the specified annotator is not supported.
        """
        annotators = [annotators] if isinstance(annotators, str) else annotators
        self._validate_annotators(annotators)
        for annotator in annotators:
            spec = self._get_annotator_spec(annotator)
            device = "cuda"
            if annotator in ["stable-id-map", "generic-model-output"]:
                device = "cpu"
            self._annotators[annotator] = rep.AnnotatorRegistry.get_annotator(
                spec["name"], device=device, do_array_copy=False
            )
        for annotator in annotators:
            self._annotators[annotator].attach(self._hydra_texture.path)

    def detach_annotators(self, annotators: str | list[str]) -> None:
        """Detach annotators from the sensor.

        Args:
            annotators: Annotator/sensor types to detach. If the annotator is not attached,
                or it has already been detached, a warning is logged and the method does nothing.

        Raises:
            ValueError: If the specified annotator is not supported.
        """
        annotators = [annotators] if isinstance(annotators, str) else annotators
        self._validate_annotators(annotators)
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
        """
        self._validate_annotators(annotator)
        if annotator not in self._annotators:
            raise ValueError(f"The annotator '{annotator}' was not configured. Enable it when instantiating the class")
        data = self._annotators[annotator].get_data("cuda")
        if isinstance(data, dict):
            info = data["info"]
            data = data["data"]
        else:
            info = {}
        return data, info

    def _invalidate_sensor(self) -> None:
        """Invalidate sensor by detaching annotators and destroying the hydra texture."""
        if self._hydra_texture is not None:
            self.detach_annotators(list(self._annotators.keys()))
            self._hydra_texture.destroy()
        self._annotators = {}
        self._hydra_texture = None

    def _initialize_sensor(self, annotators: str | list[str]) -> None:
        """Initialize sensor by creating the hydra texture and attaching annotators."""
        self._hydra_texture = rep.create.render_product(
            camera=self.authoring_object.paths[0],
            resolution=(300, 300),  # (width, height), needed but unused by the RTX sensor
            name=f"rtx_sensor_{hash(self)}",
        )
        self.attach_annotators(annotators)

    def _get_annotator_spec(self, annotator: str) -> dict[str, Any]:
        """Get the specification of the given annotator."""
        try:
            return self._annotators_spec[annotator]
        except KeyError:
            raise ValueError(
                f"Unsupported annotator '{annotator}'. Supported annotator are {list(self._annotators_spec.keys())}"
            )

    def _validate_annotators(self, annotators: str | list[str]) -> None:
        """Validate the given annotators."""
        annotators = [annotators] if isinstance(annotators, str) else annotators
        for annotator in annotators:
            if annotator not in self._annotators_spec:
                raise ValueError(
                    f"Unsupported annotator '{annotator}'. Supported annotator are {list(self._annotators_spec.keys())}"
                )
