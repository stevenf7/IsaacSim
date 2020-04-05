import carb
from omni.kit.settings import create_setting_widget, create_setting_widget_combo, SettingType, get_settings_interface
import omni.kit.ui
import omni.kit.commands
from pxr import Gf
from collections import OrderedDict


EXTENSION_NAME = "Shapenet Settings"
EXTENSION_DESC = "Adjust shapenet settings"
WIDGET_WIDTH = 200


class ShapenetSettings:
    def get_name(self):
        return EXTENSION_NAME

    def get_description(self):
        return EXTENSION_DESC

    def __init__(self):
        self._window = omni.kit.ui.Window(EXTENSION_NAME, 800, 600, menu_path="Window/" + EXTENSION_NAME)

        self._settings = get_settings_interface()

        # note: Not sure this is the best place to set default values.
        self._settings.set("/isaac/shapenet/synsetId", "random")
        self._settings.set("/isaac/shapenet/modelId", "random")
        self._settings.set("/isaac/shapenet/posx", 0.0)
        self._settings.set("/isaac/shapenet/posy", 0.0)
        self._settings.set("/isaac/shapenet/posz", 0.0)
        self._settings.set("/isaac/shapenet/rotx", 0.0)
        self._settings.set("/isaac/shapenet/roty", 1.0)
        self._settings.set("/isaac/shapenet/rotz", 0.0)
        self._settings.set("/isaac/shapenet/rotangle", 0.0)
        self._settings.set("/isaac/shapenet/scale", 1.0)

        self._build_window_ui()

    def _add_setting(self, layout, setting_type: SettingType, name, path, range_from=0, range_to=0, speed=1):
        setting_widget = create_setting_widget(path, setting_type, range_from, range_to, speed)
        if setting_widget:
            layout.add_child(omni.kit.ui.Label(name))
            layout.add_child(setting_widget)
            setting_widget.width = WIDGET_WIDTH

    def _add_frame(self, layout, name):
        collapsible_frame = omni.kit.ui.CollapsingFrame(name, True)
        collapsible_frame.add_child(layout)
        self._window.layout.add_child(collapsible_frame)

    def _build_window_ui(self):
        """ Add Shape Settings """
        layout = omni.kit.ui.RowColumnLayout(2, True)
        # Could not get double3 to work with values of 1 or 0.
        self._add_setting(layout, SettingType.STRING, "synsetId to add", "/isaac/shapenet/synsetId")
        self._add_setting(layout, SettingType.STRING, "modelId to add", "/isaac/shapenet/modelId")
        self._add_setting(layout, SettingType.FLOAT, "X Position of add", "/isaac/shapenet/posx")
        self._add_setting(layout, SettingType.FLOAT, "Y Position of add", "/isaac/shapenet/posy")
        self._add_setting(layout, SettingType.FLOAT, "Z Position of add", "/isaac/shapenet/posz")
        self._add_setting(layout, SettingType.FLOAT, "X Axis of Rotation of add", "/isaac/shapenet/rotx")
        self._add_setting(layout, SettingType.FLOAT, "Y Axis of Rotation of add", "/isaac/shapenet/roty")
        self._add_setting(layout, SettingType.FLOAT, "Z Axis of Rotation of add", "/isaac/shapenet/rotz")
        self._add_setting(layout, SettingType.FLOAT, "Angle of Rotation of add", "/isaac/shapenet/rotangle")
        self._add_setting(layout, SettingType.FLOAT, "Scale of add", "/isaac/shapenet/scale")
        self._add_frame(layout, "Shapenet Add Values")

    def getPos(self):
        x = self._settings.get("/isaac/shapenet/posx")
        y = self._settings.get("/isaac/shapenet/posy")
        z = self._settings.get("/isaac/shapenet/posz")
        return Gf.Vec3d(x, y, z)

    def getRot(self):
        x = self._settings.get("/isaac/shapenet/rotx")
        y = self._settings.get("/isaac/shapenet/roty")
        z = self._settings.get("/isaac/shapenet/rotz")
        a = self._settings.get("/isaac/shapenet/rotangle")
        return Gf.Rotation(Gf.Vec3d(x, y, z), a)

    def getScale(self):
        s = self._settings.get("/isaac/shapenet/scale")
        return s

    def getSynsetId(self):
        s = self._settings.get("/isaac/shapenet/synsetId")
        return s

    def getModelId(self):
        s = self._settings.get("/isaac/shapenet/modelId")
        return s
