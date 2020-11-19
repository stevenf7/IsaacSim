import carb
import omni.kit.editor
import omni.kit.commands
import omni.kit.ui
from pxr import Sdf, UsdGeom, Gf
import omni.isaac.RangeSensorSchema as RangeSensorSchema

ADD_LIDAR_SCENE_MENU_ITEM = "Create/Isaac/Sensors/Lidar"
ADD_ULTRASONIC_SCENE_MENU_ITEM = "Create/Isaac/Sensors/Ultrasonic"
ADD_RADAR_SCENE_MENU_ITEM = "Create/Isaac/Sensors/Radar"


class RangeSensorMenu:
    def __init__(self):
        self._usd_context = omni.usd.get_context()
        self.on_startup()

    def on_startup(self):
        self.menus = []
        editor_menu = omni.kit.ui.get_editor_menu()

        # add
        self.menus.append(editor_menu.add_item(ADD_LIDAR_SCENE_MENU_ITEM, self._on_scene_menu_click))
        self.menus.append(editor_menu.add_item(ADD_ULTRASONIC_SCENE_MENU_ITEM, self._on_scene_menu_click))
        self.menus.append(editor_menu.add_item(ADD_RADAR_SCENE_MENU_ITEM, self._on_scene_menu_click))

    def add_lidar(self, parent=None):
        stage = self._usd_context.get_stage()

        if parent:
            path = omni.kit.utils.get_stage_next_free_path(stage, parent + "/Lidar", False)
        else:
            path = omni.kit.utils.get_stage_next_free_path(stage, "/Lidar", True)

        lidar = RangeSensorSchema.Lidar.Define(stage, Sdf.Path(path))
        lidar.CreateHorizontalFovAttr().Set(360.0)
        lidar.CreateVerticalFovAttr().Set(30.0)
        lidar.CreateRotationRateAttr().Set(20.0)
        lidar.CreateHorizontalResolutionAttr().Set(0.4)
        lidar.CreateVerticalResolutionAttr().Set(4.0)
        lidar.CreateMinRangeAttr().Set(0.4)
        lidar.CreateMaxRangeAttr().Set(100.0)
        lidar.CreateHighLodAttr().Set(False)
        lidar.CreateDrawPointsAttr().Set(False)
        lidar.CreateDrawLinesAttr().Set(False)
        lidar.CreateYawOffsetAttr().Set(0.0)

        xform = UsdGeom.Xformable(lidar)
        xform_op = xform.AddXformOp(UsdGeom.XformOp.TypeTransform, UsdGeom.XformOp.PrecisionDouble, "")

        # rotate sensor to align correctly if stage is y up
        if UsdGeom.GetStageUpAxis(stage) == UsdGeom.Tokens.y:
            xform_op.Set(Gf.Matrix4d().SetRotate(Gf.Rotation(Gf.Vec3d(1, 0, 0), 270)))

        return lidar

    def add_ultrasonic(self, parent=None):
        stage = self._usd_context.get_stage()

        if parent:
            path = omni.kit.utils.get_stage_next_free_path(stage, parent + "/Ultrasonic", False)
        else:
            path = omni.kit.utils.get_stage_next_free_path(stage, "/Ultrasonic", True)

        ultrasonic = RangeSensorSchema.Ultrasonic.Define(stage, Sdf.Path(path))
        ultrasonic.CreateHorizontalFovAttr().Set(360.0)
        ultrasonic.CreateVerticalFovAttr().Set(30.0)
        ultrasonic.CreateHorizontalResolutionAttr().Set(0.4)
        ultrasonic.CreateVerticalResolutionAttr().Set(4.0)
        ultrasonic.CreateMinRangeAttr().Set(0.4)
        ultrasonic.CreateMaxRangeAttr().Set(100.0)
        ultrasonic.CreateDrawPointsAttr().Set(False)
        ultrasonic.CreateDrawLinesAttr().Set(False)
        ultrasonic.CreateYawOffsetAttr().Set(0.0)

        xform = UsdGeom.Xformable(ultrasonic)
        xform_op = xform.AddXformOp(UsdGeom.XformOp.TypeTransform, UsdGeom.XformOp.PrecisionDouble, "")

        # rotate sensor to align correctly if stage is y up
        if UsdGeom.GetStageUpAxis(stage) == UsdGeom.Tokens.y:
            xform_op.Set(Gf.Matrix4d().SetRotate(Gf.Rotation(Gf.Vec3d(1, 0, 0), 270)))

        return ultrasonic

    def add_radar(self, parent=None):
        stage = self._usd_context.get_stage()

        if parent:
            path = omni.kit.utils.get_stage_next_free_path(stage, parent + "/Radar", False)
        else:
            path = omni.kit.utils.get_stage_next_free_path(stage, "/Radar", True)

        radar = RangeSensorSchema.Radar.Define(stage, Sdf.Path(path))
        radar.CreateHorizontalFovAttr().Set(360.0)
        radar.CreateVerticalFovAttr().Set(30.0)
        radar.CreateRotationRateAttr().Set(20.0)
        radar.CreateHorizontalResolutionAttr().Set(0.4)
        radar.CreateVerticalResolutionAttr().Set(4.0)
        radar.CreateMinRangeAttr().Set(0.4)
        radar.CreateMaxRangeAttr().Set(100.0)
        radar.CreateDrawPointsAttr().Set(False)
        radar.CreateDrawLinesAttr().Set(False)
        radar.CreateYawOffsetAttr().Set(0.0)

        xform = UsdGeom.Xformable(radar)
        xform_op = xform.AddXformOp(UsdGeom.XformOp.TypeTransform, UsdGeom.XformOp.PrecisionDouble, "")

        # rotate sensor to align correctly if stage is y up
        if UsdGeom.GetStageUpAxis(stage) == UsdGeom.Tokens.y:
            xform_op.Set(Gf.Matrix4d().SetRotate(Gf.Rotation(Gf.Vec3d(1, 0, 0), 270)))

        return radar

    def _on_scene_menu_click(self, menu, value):
        selectedPrims = self._usd_context.get_selection().get_selected_prim_paths()

        if menu == ADD_LIDAR_SCENE_MENU_ITEM:
            if len(selectedPrims) > 0:
                self.add_lidar(selectedPrims[-1])
            else:
                self.add_lidar()
        elif menu == ADD_ULTRASONIC_SCENE_MENU_ITEM:
            if len(selectedPrims) > 0:
                self.add_ultrasonic(selectedPrims[-1])
            else:
                self.add_ultrasonic()
        elif menu == ADD_RADAR_SCENE_MENU_ITEM:
            if len(selectedPrims) > 0:
                self.add_radar(selectedPrims[-1])
            else:
                self.add_radar()

    def shutdown(self):
        self.menus = []
