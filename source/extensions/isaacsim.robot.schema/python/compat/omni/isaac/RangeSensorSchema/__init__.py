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
"""Drop-in compatibility wrapper for omni.isaac.RangeSensorSchema.

Replicates the generated schema API using generic USD attribute access,
so that existing callsites continue to work without changes.
"""

from pxr import Sdf, Tf, Usd, UsdGeom


class RangeSensor:
    """Compatibility wrapper for pxr::RangeSensorRangeSensor."""

    _TYPE_NAME = "RangeSensor"
    _TF_TYPE_NAME = "RangeSensorRangeSensor"

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

    # ── RangeSensor attributes ──────────────────────────────────────────

    def GetEnabledAttr(self):
        return self._prim.GetAttribute("enabled")

    def CreateEnabledAttr(self, value=None):
        attr = self._prim.CreateAttribute("enabled", Sdf.ValueTypeNames.Bool)
        if value is not None:
            attr.Set(value)
        return attr

    def GetDrawPointsAttr(self):
        return self._prim.GetAttribute("drawPoints")

    def CreateDrawPointsAttr(self, value=None):
        attr = self._prim.CreateAttribute("drawPoints", Sdf.ValueTypeNames.Bool)
        if value is not None:
            attr.Set(value)
        return attr

    def GetDrawLinesAttr(self):
        return self._prim.GetAttribute("drawLines")

    def CreateDrawLinesAttr(self, value=None):
        attr = self._prim.CreateAttribute("drawLines", Sdf.ValueTypeNames.Bool)
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


class Lidar(RangeSensor):
    """Compatibility wrapper for pxr::RangeSensorLidar."""

    _TYPE_NAME = "Lidar"
    _TF_TYPE_NAME = "RangeSensorLidar"

    # ── Lidar-specific attributes ───────────────────────────────────────

    def GetYawOffsetAttr(self):
        return self._prim.GetAttribute("yawOffset")

    def CreateYawOffsetAttr(self, value=None):
        attr = self._prim.CreateAttribute("yawOffset", Sdf.ValueTypeNames.Float)
        if value is not None:
            attr.Set(value)
        return attr

    def GetRotationRateAttr(self):
        return self._prim.GetAttribute("rotationRate")

    def CreateRotationRateAttr(self, value=None):
        attr = self._prim.CreateAttribute("rotationRate", Sdf.ValueTypeNames.Float)
        if value is not None:
            attr.Set(value)
        return attr

    def GetHighLodAttr(self):
        return self._prim.GetAttribute("highLod")

    def CreateHighLodAttr(self, value=None):
        attr = self._prim.CreateAttribute("highLod", Sdf.ValueTypeNames.Bool)
        if value is not None:
            attr.Set(value)
        return attr

    def GetHorizontalFovAttr(self):
        return self._prim.GetAttribute("horizontalFov")

    def CreateHorizontalFovAttr(self, value=None):
        attr = self._prim.CreateAttribute("horizontalFov", Sdf.ValueTypeNames.Float)
        if value is not None:
            attr.Set(value)
        return attr

    def GetVerticalFovAttr(self):
        return self._prim.GetAttribute("verticalFov")

    def CreateVerticalFovAttr(self, value=None):
        attr = self._prim.CreateAttribute("verticalFov", Sdf.ValueTypeNames.Float)
        if value is not None:
            attr.Set(value)
        return attr

    def GetHorizontalResolutionAttr(self):
        return self._prim.GetAttribute("horizontalResolution")

    def CreateHorizontalResolutionAttr(self, value=None):
        attr = self._prim.CreateAttribute("horizontalResolution", Sdf.ValueTypeNames.Float)
        if value is not None:
            attr.Set(value)
        return attr

    def GetVerticalResolutionAttr(self):
        return self._prim.GetAttribute("verticalResolution")

    def CreateVerticalResolutionAttr(self, value=None):
        attr = self._prim.CreateAttribute("verticalResolution", Sdf.ValueTypeNames.Float)
        if value is not None:
            attr.Set(value)
        return attr

    def GetEnableSemanticsAttr(self):
        return self._prim.GetAttribute("enableSemantics")

    def CreateEnableSemanticsAttr(self, value=None):
        attr = self._prim.CreateAttribute("enableSemantics", Sdf.ValueTypeNames.Bool)
        if value is not None:
            attr.Set(value)
        return attr


class Generic(RangeSensor):
    """Compatibility wrapper for pxr::RangeSensorGeneric."""

    _TYPE_NAME = "Generic"
    _TF_TYPE_NAME = "RangeSensorGeneric"

    # ── Generic-specific attributes ─────────────────────────────────────

    def GetSamplingRateAttr(self):
        return self._prim.GetAttribute("samplingRate")

    def CreateSamplingRateAttr(self, value=None):
        attr = self._prim.CreateAttribute("samplingRate", Sdf.ValueTypeNames.Int)
        if value is not None:
            attr.Set(value)
        return attr

    def GetStreamingAttr(self):
        return self._prim.GetAttribute("streaming")

    def CreateStreamingAttr(self, value=None):
        attr = self._prim.CreateAttribute("streaming", Sdf.ValueTypeNames.Bool)
        if value is not None:
            attr.Set(value)
        return attr
