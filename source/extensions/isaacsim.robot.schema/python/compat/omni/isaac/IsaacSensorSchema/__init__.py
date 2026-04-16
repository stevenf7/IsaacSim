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
"""Drop-in compatibility wrapper for omni.isaac.IsaacSensorSchema.

Replicates the generated schema API using generic USD attribute access,
so that existing callsites continue to work without changes.
"""

from pxr import Sdf, Tf, Usd, UsdGeom


class IsaacBaseSensor:
    """Compatibility wrapper for pxr::IsaacSensorIsaacBaseSensor."""

    _TYPE_NAME = "IsaacBaseSensor"
    _TF_TYPE_NAME = "IsaacSensorIsaacBaseSensor"

    def __init__(self, prim):
        if isinstance(prim, Usd.Prim):
            self._prim = prim
        elif hasattr(prim, "GetPrim"):
            self._prim = prim.GetPrim()
        else:
            self._prim = prim

    @classmethod
    def Define(cls, stage: Usd.Stage, path: str):
        prim = stage.DefinePrim(path, cls._TYPE_NAME)
        return cls(prim)

    @classmethod
    def _GetStaticTfType(cls):
        return Tf.Type.FindByName(cls._TF_TYPE_NAME)

    def GetPrim(self) -> Usd.Prim:
        return self._prim

    def GetPath(self):
        return self._prim.GetPath()

    # ── IsaacBaseSensor attributes ──────────────────────────────────────

    def GetEnabledAttr(self):
        return self._prim.GetAttribute("enabled")

    def CreateEnabledAttr(self, value=None):
        attr = self._prim.CreateAttribute("enabled", Sdf.ValueTypeNames.Bool)
        if value is not None:
            attr.Set(value)
        return attr

    def GetSensorPeriodAttr(self):
        return self._prim.GetAttribute("sensorPeriod")

    def CreateSensorPeriodAttr(self, value=None):
        attr = self._prim.CreateAttribute("sensorPeriod", Sdf.ValueTypeNames.Float)
        if value is not None:
            attr.Set(value)
        return attr


class IsaacContactSensor(IsaacBaseSensor):
    """Compatibility wrapper for pxr::IsaacSensorIsaacContactSensor."""

    _TYPE_NAME = "IsaacContactSensor"
    _TF_TYPE_NAME = "IsaacSensorIsaacContactSensor"

    # ── IsaacContactSensor attributes ───────────────────────────────────

    def GetThresholdAttr(self):
        return self._prim.GetAttribute("threshold")

    def CreateThresholdAttr(self, value=None):
        attr = self._prim.CreateAttribute("threshold", Sdf.ValueTypeNames.Float2)
        if value is not None:
            attr.Set(value)
        return attr

    def GetRadiusAttr(self):
        return self._prim.GetAttribute("radius")

    def CreateRadiusAttr(self, value=None):
        attr = self._prim.CreateAttribute("radius", Sdf.ValueTypeNames.Float)
        if value is not None:
            attr.Set(value)
        return attr

    def GetColorAttr(self):
        return self._prim.GetAttribute("color")

    def CreateColorAttr(self, value=None):
        attr = self._prim.CreateAttribute("color", Sdf.ValueTypeNames.Float4)
        if value is not None:
            attr.Set(value)
        return attr


class IsaacImuSensor(IsaacBaseSensor):
    """Compatibility wrapper for pxr::IsaacSensorIsaacImuSensor."""

    _TYPE_NAME = "IsaacImuSensor"
    _TF_TYPE_NAME = "IsaacSensorIsaacImuSensor"

    # ── IsaacImuSensor attributes ───────────────────────────────────────

    def GetLinearAccelerationFilterWidthAttr(self):
        return self._prim.GetAttribute("linearAccelerationFilterWidth")

    def CreateLinearAccelerationFilterWidthAttr(self, value=None):
        attr = self._prim.CreateAttribute("linearAccelerationFilterWidth", Sdf.ValueTypeNames.Int)
        if value is not None:
            attr.Set(value)
        return attr

    def GetAngularVelocityFilterWidthAttr(self):
        return self._prim.GetAttribute("angularVelocityFilterWidth")

    def CreateAngularVelocityFilterWidthAttr(self, value=None):
        attr = self._prim.CreateAttribute("angularVelocityFilterWidth", Sdf.ValueTypeNames.Int)
        if value is not None:
            attr.Set(value)
        return attr

    def GetOrientationFilterWidthAttr(self):
        return self._prim.GetAttribute("orientationFilterWidth")

    def CreateOrientationFilterWidthAttr(self, value=None):
        attr = self._prim.CreateAttribute("orientationFilterWidth", Sdf.ValueTypeNames.Int)
        if value is not None:
            attr.Set(value)
        return attr


class IsaacLightBeamSensor(IsaacBaseSensor):
    """Compatibility wrapper for pxr::IsaacSensorIsaacLightBeamSensor."""

    _TYPE_NAME = "IsaacLightBeamSensor"
    _TF_TYPE_NAME = "IsaacSensorIsaacLightBeamSensor"

    # ── IsaacLightBeamSensor attributes ─────────────────────────────────

    def GetNumRaysAttr(self):
        return self._prim.GetAttribute("numRays")

    def CreateNumRaysAttr(self, value=None):
        attr = self._prim.CreateAttribute("numRays", Sdf.ValueTypeNames.Int)
        if value is not None:
            attr.Set(value)
        return attr

    def GetCurtainLengthAttr(self):
        return self._prim.GetAttribute("curtainLength")

    def CreateCurtainLengthAttr(self, value=None):
        attr = self._prim.CreateAttribute("curtainLength", Sdf.ValueTypeNames.Float)
        if value is not None:
            attr.Set(value)
        return attr

    def GetForwardAxisAttr(self):
        return self._prim.GetAttribute("forwardAxis")

    def CreateForwardAxisAttr(self, value=None):
        attr = self._prim.CreateAttribute("forwardAxis", Sdf.ValueTypeNames.Float3)
        if value is not None:
            attr.Set(value)
        return attr

    def GetCurtainAxisAttr(self):
        return self._prim.GetAttribute("curtainAxis")

    def CreateCurtainAxisAttr(self, value=None):
        attr = self._prim.CreateAttribute("curtainAxis", Sdf.ValueTypeNames.Float3)
        if value is not None:
            attr.Set(value)
        return attr

    def GetMinRangeAttr(self):
        return self._prim.GetAttribute("minRange")

    def CreateMinRangeAttr(self, value=None):
        attr = self._prim.CreateAttribute("minRange", Sdf.ValueTypeNames.Float)
        if value is not None:
            attr.Set(value)
        return attr

    def GetMaxRangeAttr(self):
        return self._prim.GetAttribute("maxRange")

    def CreateMaxRangeAttr(self, value=None):
        attr = self._prim.CreateAttribute("maxRange", Sdf.ValueTypeNames.Float)
        if value is not None:
            attr.Set(value)
        return attr


class _APISchemaWrapper:
    """Base for API schema compatibility wrappers.

    Supports ``SchemaClass.Apply(prim)`` and ``prim.HasAPI(SchemaClass)``
    by exposing a ``_GetStaticTfType()`` classmethod that USD's ``HasAPI``
    dispatches to when passed a Python type instead of a ``TfType``.
    """

    _SCHEMA_NAME = ""

    def __init__(self, prim):
        if isinstance(prim, Usd.Prim):
            self._prim = prim
        elif hasattr(prim, "GetPrim"):
            self._prim = prim.GetPrim()
        else:
            self._prim = prim

    @classmethod
    def Apply(cls, prim: Usd.Prim):
        prim.AddAppliedSchema(cls._SCHEMA_NAME)
        return cls(prim)

    def GetPrim(self) -> Usd.Prim:
        return self._prim

    def GetPath(self):
        return self._prim.GetPath()

    @classmethod
    def _GetStaticTfType(cls):
        return Tf.Type.FindByName(cls._TF_TYPE_NAME)


class IsaacRtxLidarSensorAPI(_APISchemaWrapper):
    """Compatibility wrapper for pxr::IsaacSensorIsaacRtxLidarSensorAPI."""

    _SCHEMA_NAME = "IsaacRtxLidarSensorAPI"
    _TF_TYPE_NAME = "IsaacSensorIsaacRtxLidarSensorAPI"


class IsaacRtxRadarSensorAPI(_APISchemaWrapper):
    """Compatibility wrapper for pxr::IsaacSensorIsaacRtxRadarSensorAPI."""

    _SCHEMA_NAME = "IsaacRtxRadarSensorAPI"
    _TF_TYPE_NAME = "IsaacSensorIsaacRtxRadarSensorAPI"
