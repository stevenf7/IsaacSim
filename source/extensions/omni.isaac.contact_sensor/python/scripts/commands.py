# Copyright (c) 2018-2022, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

import omni.kit.commands
import omni.kit.utils
import omni.isaac.IsaacSensorSchema as IsaacSensorSchema
import carb
from pxr import Gf, UsdGeom
from typing import List
import omni.usd


def get_path(stage, path: str, parent=None) -> str:
    if parent is not None:
        path = omni.usd.get_stage_next_free_path(stage, parent.strip("/") + "/" + path.strip("/"), False)
    else:
        path = omni.usd.get_stage_next_free_path(stage, path, True)
    return path


class IsaacSensorCreatePrim(omni.kit.commands.Command):
    def __init__(
        self,
        path: str = "",
        parent: str = "",
        position: Gf.Vec3d = Gf.Vec3d(0, 0, 0),
        schema_type=IsaacSensorSchema.IsaacBaseSensor,
    ):
        # condensed way to copy all input arguments into self with an underscore prefix
        for name, value in vars().items():
            if name != "self":
                setattr(self, f"_{name}", value)
        self._prim_path = None

    def do(self):
        self._stage = omni.usd.get_context().get_stage()

        self._prim_path = get_path(self._stage, self._path, self._parent)
        self._prim = self._schema_type.Define(self._stage, self._prim_path)
        self._prim.CreateEnabledAttr(True)
        self._prim.CreateVisualizeAttr(True)

        xform = UsdGeom.Xformable(self._prim)
        xform_trans = xform.AddXformOp(UsdGeom.XformOp.TypeTranslate, UsdGeom.XformOp.PrecisionDouble, "")
        xform_trans.Set(Gf.Vec3d(self._position))

        xform_rot = xform.AddXformOp(UsdGeom.XformOp.TypeRotateXYZ, UsdGeom.XformOp.PrecisionDouble, "")

        # rotate sensor to align correctly if stage is y up
        if UsdGeom.GetStageUpAxis(self._stage) == UsdGeom.Tokens.y:
            xform_rot.Set(Gf.Vec3d(270, 0, 0))
        return self._prim

    def undo(self):
        if self._prim_path is not None:
            return self._stage.RemovePrim(self._prim_path)


class IsaacSensorCreateContactSensor(omni.kit.commands.Command):
    def __init__(
        self,
        path: str = "/Contact_Sensor",
        parent=None,
        min_threshold: float = 0,
        max_threshold: float = 100000,
        color: Gf.Vec4f = Gf.Vec4f(1, 1, 1, 1),
        radius: float = -1,
        sensor_period: float = -1,
        offset: Gf.Vec3d = Gf.Vec3d(0, 0, 0),
    ):
        # condensed way to copy all input arguments into self with an underscore prefix
        for name, value in vars().items():
            if name != "self":
                setattr(self, f"_{name}", value)
        self._prim = None
        pass

    def do(self):
        success, self._prim = omni.kit.commands.execute(
            "IsaacSensorCreatePrim",
            path=self._path,
            parent=self._parent,
            schema_type=IsaacSensorSchema.IsaacContactSensor,
            position=self._offset,
        )

        if success and self._prim:
            self._prim.CreateThresholdAttr().Set((self._min_threshold, self._max_threshold))
            self._prim.CreateColorAttr().Set(self._color)
            self._prim.CreateSensorPeriodAttr().Set(self._sensor_period)
            self._prim.CreateRadiusAttr().Set(self._radius)

        else:
            print("Could not create contact sensor prim")

    def undo(self):
        # undo must be defined even if empty
        pass


omni.kit.commands.register_all_commands_in_module(__name__)
