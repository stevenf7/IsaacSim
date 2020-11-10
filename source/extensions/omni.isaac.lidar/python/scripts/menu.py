import carb
import omni.kit.editor
import omni.kit.commands
import omni.kit.ui
from pxr import Sdf, UsdGeom, Gf
import omni.isaac.LidarSchema as LidarSchema
from .. import _lidar

ADD_LIDAR_SCENE_MENU_ITEM = "Create/Isaac/Sensors/Lidar"


class LidarMenu:
    def __init__(self):
        self._usd_context = omni.usd.get_context()
        self.on_startup()

    def on_startup(self):
        self.menus = []

        editor_menu = omni.kit.ui.get_editor_menu()
        self._lidar = _lidar.acquire_lidar_interface()

        # add
        self.menus.append(editor_menu.add_item(ADD_LIDAR_SCENE_MENU_ITEM, self._on_scene_menu_click))

    def add_lidar(self, parent=None):
        stage = self._usd_context.get_stage()

        if parent:
            path = omni.kit.utils.get_stage_next_free_path(stage, parent + "/Lidar", False)
        else:
            path = omni.kit.utils.get_stage_next_free_path(stage, "/Lidar", True)

        lidar = LidarSchema.Lidar.Define(stage, Sdf.Path(path))
        lidar.CreateHorizontalFovAttr().Set(360.0)
        lidar.CreateVerticalFovAttr().Set(30.0)
        lidar.CreateRotationRateAttr().Set(20.0)
        lidar.CreateHorizontalResolutionAttr().Set(0.4)
        lidar.CreateVerticalResolutionAttr().Set(4.0)
        lidar.CreateMinRangeAttr().Set(0.4)
        lidar.CreateMaxRangeAttr().Set(100.0)
        lidar.CreateHighLodAttr().Set(False)
        lidar.CreateDrawLidarPointsAttr().Set(False)
        lidar.CreateDrawLidarLinesAttr().Set(False)
        lidar.CreateYawOffsetAttr().Set(0.0)

        xform = UsdGeom.Xformable(lidar)
        xform_op = xform.AddXformOp(UsdGeom.XformOp.TypeTransform, UsdGeom.XformOp.PrecisionDouble, "")

        # rotate lidar to align correctly if stage is y up
        if UsdGeom.GetStageUpAxis(stage) == UsdGeom.Tokens.y:
            xform_op.Set(Gf.Matrix4d().SetRotate(Gf.Rotation(Gf.Vec3d(1, 0, 0), 270)))

        return lidar

    def _on_scene_menu_click(self, menu, value):
        selectedPrims = self._usd_context.get_selection().get_selected_prim_paths()

        if menu == ADD_LIDAR_SCENE_MENU_ITEM:
            if len(selectedPrims) > 0:
                self.add_lidar(selectedPrims[-1])
            else:
                self.add_lidar()

    def shutdown(self):
        self.menus = []
