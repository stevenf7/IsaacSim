# Copyright (c) 2018-2024, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

import sys

import carb
import omni.isaac.IsaacSensorSchema as IsaacSensorSchema
import omni.kit.commands
import omni.kit.utils
import omni.usd
from isaacsim.core.utils.prims import delete_prim
from isaacsim.core.utils.stage import get_next_free_path
from isaacsim.core.utils.xforms import reset_and_set_xform_ops
from pxr import Gf, PhysxSchema, Sdf, UsdGeom


class IsaacSensorCreateRtxLidar(omni.kit.commands.Command):
    def __init__(
        self,
        path: str = "/RtxLidar",
        parent: str = None,
        config: str = "Example_Rotary",
        translation: Gf.Vec3d = Gf.Vec3d(0, 0, 0),
        orientation: Gf.Quatd = Gf.Quatd(1, 0, 0, 0),
        visibility: bool = False,
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
        IsaacSensorSchema.IsaacRtxLidarSensorAPI.Apply(self._prim)
        camSensorTypeAttr = self._prim.CreateAttribute("cameraSensorType", Sdf.ValueTypeNames.Token, False)
        camSensorTypeAttr.Set("lidar")
        tokens = camSensorTypeAttr.GetMetadata("allowedTokens")
        if not tokens:
            camSensorTypeAttr.SetMetadata("allowedTokens", ["camera", "radar", "lidar"])
        self._prim.CreateAttribute("sensorModelPluginName", Sdf.ValueTypeNames.String, False).Set(
            "omni.sensors.nv.lidar.lidar_core.plugin"
        )
        self._prim.CreateAttribute("sensorModelConfig", Sdf.ValueTypeNames.String, False).Set(self._config)
        if self._visibility is False:
            UsdGeom.Imageable(self._prim).MakeInvisible()
        reset_and_set_xform_ops(self._prim.GetPrim(), self._translation, self._orientation)

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
        camSensorTypeAttr.Set("lidar")
        tokens = camSensorTypeAttr.GetMetadata("allowedTokens")
        if not tokens:
            camSensorTypeAttr.SetMetadata("allowedTokens", ["camera", "radar", "lidar"])
        self._prim.CreateAttribute("sensorModelPluginName", Sdf.ValueTypeNames.String, False).Set(
            "omni.sensors.nv.ids.ids.plugin"
        )
        self._prim.CreateAttribute("sensorModelConfig", Sdf.ValueTypeNames.String, False).Set(self._config)
        if self._visibility is False:
            UsdGeom.Imageable(self._prim).MakeInvisible()
        reset_and_set_xform_ops(self._prim.GetPrim(), self._translation, self._orientation)

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
        path: str = "/RtxRadar",
        parent: str = None,
        config: str = "Example",
        translation: Gf.Vec3d = Gf.Vec3d(0, 0, 0),
        orientation: Gf.Quatd = Gf.Quatd(1, 0, 0, 0),
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
        IsaacSensorSchema.IsaacRtxRadarSensorAPI.Apply(self._prim)
        camSensorTypeAttr = self._prim.CreateAttribute("cameraSensorType", Sdf.ValueTypeNames.Token, False)
        camSensorTypeAttr.Set("radar")
        tokens = camSensorTypeAttr.GetMetadata("allowedTokens")
        if not tokens:
            camSensorTypeAttr.SetMetadata("allowedTokens", ["camera", "radar", "lidar"])
        self._prim.CreateAttribute("sensorModelPluginName", Sdf.ValueTypeNames.String, False).Set(
            "omni.sensors.nv.radar.wpm_dmatapprox.plugin"
        )
        self._prim.CreateAttribute("sensorModelConfig", Sdf.ValueTypeNames.String, False).Set(self._config)
        reset_and_set_xform_ops(self._prim.GetPrim(), self._translation, self._orientation)

        if self._prim:
            return self._prim
        else:
            carb.log_error("Could not create RTX Radar Prim")
            return None

    def undo(self):
        # undo must be defined even if empty
        pass


omni.kit.commands.register_all_commands_in_module(__name__)
