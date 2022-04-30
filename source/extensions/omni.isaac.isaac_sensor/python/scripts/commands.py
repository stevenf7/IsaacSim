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
from omni.isaac.core.utils.stage import get_next_free_path
from pxr import Gf, UsdGeom
import omni.usd


class IsaacSensorCreatePrim(omni.kit.commands.Command):
    def __init__(
        self,
        path: str = "",
        parent: str = "",
        visualize: bool = False,
        position: Gf.Vec3d = Gf.Vec3d(0, 0, 0),
        orientation: Gf.Quatd = Gf.Quatd(1, 0, 0, 0),
        schema_type=IsaacSensorSchema.IsaacBaseSensor,
    ):
        # condensed way to copy all input arguments into self with an underscore prefix
        for name, value in vars().items():
            if name != "self":
                setattr(self, f"_{name}", value)
        self._prim_path = None

    def do(self):
        self._stage = omni.usd.get_context().get_stage()

        self._prim_path = get_next_free_path(self._path, self._parent)
        self._prim = self._schema_type.Define(self._stage, self._prim_path)
        self._prim.CreateEnabledAttr(True)
        self._prim.CreateVisualizeAttr(self._visualize)

        xform = UsdGeom.Xformable(self._prim)
        xform_trans = xform.AddXformOp(UsdGeom.XformOp.TypeTranslate, UsdGeom.XformOp.PrecisionDouble, "")
        xform_trans.Set(Gf.Vec3d(self._position))

        xform_orient = xform.AddXformOp(UsdGeom.XformOp.TypeOrient, UsdGeom.XformOp.PrecisionDouble, "")
        xform_orient.Set(self._orientation)

        return self._prim

    def undo(self):
        if self._prim_path is not None:
            return self._stage.RemovePrim(self._prim_path)


class IsaacSensorCreateContactSensor(omni.kit.commands.Command):
    def __init__(
        self,
        path: str = "/Contact_Sensor",
        parent=None,
        visualize: bool = False,
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
            visualize=self._visualize,
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


class IsaacSensorCreateImuSensor(omni.kit.commands.Command):
    def __init__(
        self,
        path: str = "/Imu_Sensor",
        parent=None,
        visualize: bool = False,
        sensor_period: float = -1,
        offset: Gf.Vec3d = Gf.Vec3d(0, 0, 0),
        orientation: Gf.Quatd = Gf.Quatd(1, 0, 0, 0),
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
            schema_type=IsaacSensorSchema.IsaacImuSensor,
            position=self._offset,
            orientation=self._orientation,
            visualize=self._visualize,
        )

        if success and self._prim:
            self._prim.CreateSensorPeriodAttr().Set(self._sensor_period)
        else:
            print("Could not create Imu sensor prim")

    def undo(self):
        # undo must be defined even if empty
        pass


omni.kit.commands.register_all_commands_in_module(__name__)
