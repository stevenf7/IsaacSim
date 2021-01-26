import omni.kit.commands
import omni.kit.utils
import omni.isaac.RangeSensorSchema as RangeSensorSchema
import carb
from pxr import Gf, UsdGeom


def get_path(stage, path: str, parent=None) -> str:
    if parent:
        path = omni.kit.utils.get_stage_next_free_path(stage, parent + path, False)
    else:
        path = omni.kit.utils.get_stage_next_free_path(stage, path, True)
    return path


def setup_base_prim(prim, enabled, draw_points, draw_lines, min_range, max_range):
    prim.CreateEnabledAttr(enabled)
    prim.CreateDrawPointsAttr(draw_points)
    prim.CreateDrawLinesAttr(draw_lines)
    prim.CreateMinRangeAttr(min_range)
    prim.CreateMaxRangeAttr(max_range)


# this command is used to create each REB prim, it also handles undo so that each individual prim command doesn't have to
class CreateRangeSensorPrimCommand(omni.kit.commands.Command):
    def __init__(
        self,
        path: str = "",
        parent: str = "",
        scehma_type=RangeSensorSchema.RangeSensor,
        min_range: float = 0.4,
        max_range: float = 100.0,
        draw_points: bool = False,
        draw_lines: bool = False,
    ):
        # condensed way to copy all input arguments into self with an underscore prefix
        for name, value in vars().items():
            if name != "self":
                setattr(self, f"_{name}", value)
        self._prim_path = None
        pass

    def do(self):
        self._stage = omni.usd.get_context().get_stage()
        # make prim path unique
        self._prim_path = get_path(self._stage, self._path, self._parent)
        self._prim = self._scehma_type.Define(self._stage, self._prim_path)
        setup_base_prim(self._prim, True, self._draw_points, self._draw_lines, self._min_range, self._max_range)

        xform = UsdGeom.Xformable(self._prim)
        xform_op = xform.AddXformOp(UsdGeom.XformOp.TypeTransform, UsdGeom.XformOp.PrecisionDouble, "")

        # rotate sensor to align correctly if stage is y up
        if UsdGeom.GetStageUpAxis(self._stage) == UsdGeom.Tokens.y:
            xform_op.Set(Gf.Matrix4d().SetRotate(Gf.Rotation(Gf.Vec3d(1, 0, 0), 270)))
        return self._prim

    def undo(self):
        if self._prim_path is not None:
            return self._stage.RemovePrim(self._prim_path)


class CreateRangeSensorLidarCommand(omni.kit.commands.Command):
    def __init__(
        self,
        path: str = "/Lidar",
        parent=None,
        min_range: float = 0.4,
        max_range: float = 100.0,
        draw_points: bool = False,
        draw_lines: bool = False,
        horizontal_fov: float = 360.0,
        vertical_fov: float = 30.0,
        horizontal_resolution: float = 0.4,
        vertical_resolution: float = 4.0,
        rotation_rate: float = 20.0,
        high_lod: bool = False,
        yaw_offset: float = 0.0,
    ):
        # condensed way to copy all input arguments into self with an underscore prefix
        for name, value in vars().items():
            if name != "self":
                setattr(self, f"_{name}", value)
        self._prim = None
        pass

    def do(self):
        success, self._prim = omni.kit.commands.execute(
            "CreateRangeSensorPrimCommand",
            path=self._path,
            parent=self._parent,
            scehma_type=RangeSensorSchema.Lidar,
            draw_points=self._draw_points,
            draw_lines=self._draw_lines,
            min_range=self._min_range,
            max_range=self._max_range,
        )
        if success and self._prim:
            self._prim.CreateHorizontalFovAttr().Set(self._horizontal_fov)
            self._prim.CreateVerticalFovAttr().Set(self._vertical_fov)
            self._prim.CreateRotationRateAttr().Set(self._rotation_rate)
            self._prim.CreateHorizontalResolutionAttr().Set(self._horizontal_resolution)
            self._prim.CreateVerticalResolutionAttr().Set(self._vertical_resolution)
            self._prim.CreateHighLodAttr().Set(self._high_lod)
            self._prim.CreateYawOffsetAttr().Set(self._yaw_offset)
        else:
            carb.log.error("Could not create lidar prim")
        return self._prim

    def undo(self):
        # undo must be defined even if empty
        pass


class CreateRangeSensorUltrasonicArrayCommand(omni.kit.commands.Command):
    def __init__(
        self,
        path: str = "/UltrasonicArray",
        parent=None,
        min_range: float = 0.4,
        max_range: float = 100.0,
        draw_points: bool = False,
        draw_lines: bool = False,
        horizontal_fov: float = 360.0,
        vertical_fov: float = 30.0,
        rotation_rate: float = 20.0,
        horizontal_resolution: float = 0.4,
        vertical_resolution: float = 4.0,
        pulse_duration: float = 0.5,
        pulse_gap_delta: float = 1.0,
        num_bins: int = 224,
        emitter_prims=[],
    ):
        # condensed way to copy all input arguments into self with an underscore prefix
        for name, value in vars().items():
            if name != "self":
                setattr(self, f"_{name}", value)
        self._prim = None
        pass

    def do(self):
        success, self._prim = omni.kit.commands.execute(
            "CreateRangeSensorPrimCommand",
            path=self._path,
            parent=self._parent,
            scehma_type=RangeSensorSchema.UltrasonicArray,
            draw_points=self._draw_points,
            draw_lines=self._draw_lines,
            min_range=self._min_range,
            max_range=self._max_range,
        )
        if success and self._prim:
            self._prim.CreateHorizontalFovAttr().Set(self._horizontal_fov)
            self._prim.CreateVerticalFovAttr().Set(self._vertical_fov)
            self._prim.CreateHorizontalResolutionAttr().Set(self._horizontal_resolution)
            self._prim.CreateVerticalResolutionAttr().Set(self._vertical_resolution)
            self._prim.CreatePulseDurationAttr().Set(self._pulse_duration)
            self._prim.CreatePulseGapDeltaAttr().Set(self._pulse_gap_delta)
            self._prim.CreateNumBinsAttr().Set(self._num_bins)

            rel_paths = self._prim.CreateEmitterPrimsRel()
            for p in self._emitter_prims:
                rel_paths.AddTarget(p)
        return self._prim

    def undo(self):
        # undo must be defined even if empty
        pass


class CreateRangeSensorUltrasonicEmitterCommand(omni.kit.commands.Command):
    def __init__(
        self,
        path: str = "/UltrasonicEmitter",
        parent=None,
        per_ray_intensity: float = 0.4,
        yaw_offset: float = 0.0,
        firing_delay: float = 0.3,
    ):
        # condensed way to copy all input arguments into self with an underscore prefix
        for name, value in vars().items():
            if name != "self":
                setattr(self, f"_{name}", value)
        self._prim = None
        pass

    def do(self):
        self._stage = omni.usd.get_context().get_stage()
        # make prim path unique
        self._prim_path = get_path(self._stage, self._path, self._parent)
        self._prim = RangeSensorSchema.UltrasonicEmitter.Define(self._stage, self._prim_path)

        xform = UsdGeom.Xformable(self._prim)
        xform_op = xform.AddXformOp(UsdGeom.XformOp.TypeTransform, UsdGeom.XformOp.PrecisionDouble, "")

        # rotate sensor to align correctly if stage is y up
        if UsdGeom.GetStageUpAxis(self._stage) == UsdGeom.Tokens.y:
            xform_op.Set(Gf.Matrix4d().SetRotate(Gf.Rotation(Gf.Vec3d(1, 0, 0), 270)))
        if self._prim:
            self._prim.CreateEnabledAttr().Set(True)
            self._prim.CreatePerRayIntensityAttr().Set(self._per_ray_intensity)
            self._prim.CreateYawOffsetAttr().Set(self._yaw_offset)
            self._prim.CreateFiringDelayAttr().Set(self._firing_delay)
        return self._prim

    def undo(self):
        if self._prim_path is not None:
            return self._stage.RemovePrim(self._prim_path)
        pass


omni.kit.commands.register_all_commands_in_module(__name__)
