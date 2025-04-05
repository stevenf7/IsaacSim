# SPDX-FileCopyrightText: Copyright (c) 2018-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: LicenseRef-NvidiaProprietary
#
# NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
# property and proprietary rights in and to this material, related
# documentation and any modifications thereto. Any use, reproduction,
# disclosure or distribution of this material and related documentation
# without an express license agreement from NVIDIA CORPORATION or
# its affiliates is strictly prohibited.

from typing import Optional

import carb
import omni.isaac.IsaacSensorSchema as IsaacSensorSchema
import omni.kit.commands
import omni.kit.utils
import omni.usd
from isaacsim.core.utils.stage import add_reference_to_stage, get_next_free_path
from isaacsim.core.utils.xforms import reset_and_set_xform_ops
from pxr import Gf, Sdf, UsdGeom


class IsaacSensorCreateRtxLidar(omni.kit.commands.Command):
    def __init__(
        self,
        path: Optional[str] = "/RtxLidar",
        parent: Optional[str] = None,
        config: Optional[str] = None,
        asset_path: Optional[str] = None,
        translation: Optional[Gf.Vec3d] = Gf.Vec3d(0, 0, 0),
        orientation: Optional[Gf.Quatd] = Gf.Quatd(1, 0, 0, 0),
        visibility: Optional[bool] = False,
        variant: Optional[str] = None,
    ):
        # condensed way to copy all input arguments into self with an underscore prefix
        for name, value in vars().items():
            if name != "self":
                setattr(self, f"_{name}", value)
        self._prim = None
        pass

    def do(self):
        self._stage = omni.usd.get_context().get_stage()
        self._prim_path = get_next_free_path(self._path, self._parent)
        if self._asset_path:
            self._prim = add_reference_to_stage(usd_path=self._asset_path, prim_path=self._prim_path)
        elif self._config:
            carb.log_warn(
                "Creating RTX Lidar from config file is deprecated as of Isaac Sim 5.0 and will be removed in a future release. Use an OmniLidar prim instead by optionally specifying the asset_path argument."
            )
            self._prim = UsdGeom.Camera.Define(self._stage, Sdf.Path(self._prim_path)).GetPrim()
            IsaacSensorSchema.IsaacRtxLidarSensorAPI.Apply(self._prim)
            camSensorTypeAttr = self._prim.CreateAttribute("cameraSensorType", Sdf.ValueTypeNames.Token, False)
            camSensorTypeAttr.Set("lidar")
            tokens = camSensorTypeAttr.GetMetadata("allowedTokens")
            if not tokens:
                camSensorTypeAttr.SetMetadata("allowedTokens", ["camera", "radar", "lidar", "ids", "ultrasonic"])
            self._prim.CreateAttribute("sensorModelPluginName", Sdf.ValueTypeNames.String, False).Set(
                "omni.sensors.nv.lidar.lidar_core.plugin"
            )
            self._prim.CreateAttribute("sensorModelConfig", Sdf.ValueTypeNames.String, False).Set(self._config)
        else:
            self._prim = self._stage.DefinePrim(self._prim_path, "OmniLidar")
            self._prim.ApplyAPI("OmniSensorGenericLidarCoreAPI")

        if self._visibility is False:
            UsdGeom.Imageable(self._prim).MakeInvisible()
        reset_and_set_xform_ops(self._prim.GetPrim(), self._translation, self._orientation)

        if self._variant:
            variant_set = self._prim.GetVariantSet("Sensor")
            if not variant_set:
                carb.log_warn(f"Variant set 'Sensor' not found for RTX Lidar at {self._prim_path}.")
            if not variant_set.SetVariantSelection(self._variant):
                carb.log_warn(f"Variant '{self._variant}' not found for RTX Lidar at {self._prim_path}.")

        if self._prim:
            return self._prim
        else:
            carb.log_error("Could not create RTX Lidar Prim")
            return None

    def undo(self):
        # undo must be defined even if empty
        pass


class IsaacSensorCreateRtxIDS(omni.kit.commands.Command):
    def __init__(
        self,
        path: str = "/RtxIDS",
        parent: str = None,
        config: str = "idsoccupancy",
        translation: Gf.Vec3d = Gf.Vec3d(0, 0, 0),
        orientation: Gf.Quatd = Gf.Quatd(1, 0, 0, 0),
        visibility: bool = False,
        variant: Optional[str] = None,
    ):
        # condensed way to copy all input arguments into self with an underscore prefix
        for name, value in vars().items():
            if name != "self":
                setattr(self, f"_{name}", value)
        self._prim = None
        pass

    def do(self):
        self._stage = omni.usd.get_context().get_stage()
        self._prim_path = get_next_free_path(self._path, self._parent)
        self._prim = UsdGeom.Camera.Define(self._stage, Sdf.Path(self._prim_path)).GetPrim()
        camSensorTypeAttr = self._prim.CreateAttribute("cameraSensorType", Sdf.ValueTypeNames.Token, False)
        camSensorTypeAttr.Set("ids")
        tokens = camSensorTypeAttr.GetMetadata("allowedTokens")
        if not tokens:
            camSensorTypeAttr.SetMetadata("allowedTokens", ["camera", "radar", "lidar", "ids", "ultrasonic"])
        self._prim.CreateAttribute("sensorModelPluginName", Sdf.ValueTypeNames.String, False).Set(
            "omni.sensors.nv.ids.ids.plugin"
        )
        self._prim.CreateAttribute("sensorModelConfig", Sdf.ValueTypeNames.String, False).Set(self._config)
        if self._visibility is False:
            UsdGeom.Imageable(self._prim).MakeInvisible()
        reset_and_set_xform_ops(self._prim.GetPrim(), self._translation, self._orientation)

        if self._variant:
            variant_set = self._prim.GetVariantSet("Sensor")
            if not variant_set:
                carb.log_warn(f"Variant set 'Sensor' not found for RTX IDS at {self._prim_path}.")
            if not variant_set.SetVariantSelection(self._variant):
                carb.log_warn(f"Variant '{self._variant}' not found for RTX IDS at {self._prim_path}.")

        if self._prim:
            return self._prim
        else:
            carb.log_error("Could not create RTX IDS Prim")
            return None

    def undo(self):
        # undo must be defined even if empty
        pass


class IsaacSensorCreateRtxRadar(omni.kit.commands.Command):
    def __init__(
        self,
        path: Optional[str] = "/RtxRadar",
        parent: Optional[str] = None,
        config: Optional[str] = None,
        asset_path: Optional[str] = None,
        translation: Optional[Gf.Vec3d] = Gf.Vec3d(0, 0, 0),
        orientation: Optional[Gf.Quatd] = Gf.Quatd(1, 0, 0, 0),
        visibility: Optional[bool] = False,
        variant: Optional[str] = None,
    ):
        # condensed way to copy all input arguments into self with an underscore prefix
        for name, value in vars().items():
            if name != "self":
                setattr(self, f"_{name}", value)
        self._prim = None
        pass

    def do(self):
        self._stage = omni.usd.get_context().get_stage()
        self._prim_path = get_next_free_path(self._path, self._parent)
        if self._asset_path:
            self._prim = add_reference_to_stage(usd_path=self._asset_path, prim_path=self._prim_path)
        elif self._config:
            carb.log_warn(
                "Creating RTX Radar from config file is deprecated as of Isaac Sim 5.0 and will be removed in a future release. Use an OmniRadar prim instead by optionally specifying the asset_path argument."
            )
            self._prim = UsdGeom.Camera.Define(self._stage, Sdf.Path(self._prim_path)).GetPrim()
            IsaacSensorSchema.IsaacRtxRadarSensorAPI.Apply(self._prim)
            camSensorTypeAttr = self._prim.CreateAttribute("cameraSensorType", Sdf.ValueTypeNames.Token, False)
            camSensorTypeAttr.Set("radar")
            tokens = camSensorTypeAttr.GetMetadata("allowedTokens")
            if not tokens:
                camSensorTypeAttr.SetMetadata("allowedTokens", ["camera", "radar", "lidar", "ids", "ultrasonic"])
            self._prim.CreateAttribute("sensorModelPluginName", Sdf.ValueTypeNames.String, False).Set(
                "omni.sensors.nv.radar.wpm_dmatapprox.plugin"
            )
            self._prim.CreateAttribute("sensorModelConfig", Sdf.ValueTypeNames.String, False).Set(self._config)
        else:
            self._prim = self._stage.DefinePrim(self._prim_path, "OmniRadar")
            self._prim.ApplyAPI("OmniSensorGenericRadarWpmDmatAPI")

        if self._visibility is False:
            UsdGeom.Imageable(self._prim).MakeInvisible()
        reset_and_set_xform_ops(self._prim.GetPrim(), self._translation, self._orientation)

        if self._variant:
            variant_set = self._prim.GetVariantSet("Sensor")
            if not variant_set:
                carb.log_warn(f"Variant set 'Sensor' not found for RTX Radar at {self._prim_path}.")
            if not variant_set.SetVariantSelection(self._variant):
                carb.log_warn(f"Variant '{self._variant}' not found for RTX Radar at {self._prim_path}.")

        if self._prim:
            return self._prim
        else:
            carb.log_error("Could not create RTX Radar Prim")
            return None

    def undo(self):
        # undo must be defined even if empty
        pass


class IsaacSensorCreateRtxUltrasonic(omni.kit.commands.Command):
    def __init__(
        self,
        path: Optional[str] = "/RtxUltrasonic",
        parent: Optional[str] = None,
        config: Optional[str] = None,
        asset_path: Optional[str] = None,
        translation: Optional[Gf.Vec3d] = Gf.Vec3d(0, 0, 0),
        orientation: Optional[Gf.Quatd] = Gf.Quatd(1, 0, 0, 0),
        visibility: Optional[bool] = False,
        variant: Optional[str] = None,
    ):
        # condensed way to copy all input arguments into self with an underscore prefix
        for name, value in vars().items():
            if name != "self":
                setattr(self, f"_{name}", value)
        self._prim = None
        pass

    def do(self):
        self._stage = omni.usd.get_context().get_stage()
        self._prim_path = get_next_free_path(self._path, self._parent)
        if self._asset_path:
            self._prim = add_reference_to_stage(usd_path=self._asset_path, prim_path=self._prim_path)
        else:
            self._prim = self._stage.DefinePrim(self._prim_path, "OmniUltrasonic")

        if self._visibility is False:
            UsdGeom.Imageable(self._prim).MakeInvisible()
        reset_and_set_xform_ops(self._prim.GetPrim(), self._translation, self._orientation)

        if self._variant:
            variant_set = self._prim.GetVariantSet("Sensor")
            if not variant_set:
                carb.log_warn(f"Variant set 'Sensor' not found for RTX Ultrasonic at {self._prim_path}.")
            if not variant_set.SetVariantSelection(self._variant):
                carb.log_warn(f"Variant '{self._variant}' not found for RTX Ultrasonic at {self._prim_path}.")

        if self._prim:
            return self._prim
        else:
            carb.log_error("Could not create RTX Ultrasonic Prim")
            return None

    def undo(self):
        # undo must be defined even if empty
        pass


omni.kit.commands.register_all_commands_in_module(__name__)
