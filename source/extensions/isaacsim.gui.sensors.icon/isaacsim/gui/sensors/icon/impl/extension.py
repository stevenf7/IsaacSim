from pathlib import Path

import carb.settings
import omni.ext
import omni.kit.widget.stage
from omni.kit.viewport.menubar.core import CategoryStateItem
from omni.kit.viewport.menubar.display import get_instance as get_menubar_display_instance
from omni.kit.viewport.registry import RegisterScene

from .model import IconModel
from .scene import VISIBLE_SETTING, IconScene

_extension = None


# Any class derived from `omni.ext.IExt` in top level module (defined in `python.modules` of `extension.toml`) will be
# instantiated when extension gets enabled and `on_startup(ext_id)` will be called. Later when extension gets disabled
# on_shutdown() is called.
class SensorIconExtension(omni.ext.IExt):
    # ext_id is current extension id. It can be used with extension manager to query additional information, like where
    # this extension is located on filesystem.
    def on_startup(self, ext_id):
        global _extension
        _extension = self
        self._vp2_scene = None
        self._vp2_scene = RegisterScene(IconScene, ext_id)

        # register sensor icon to stage widget
        self._sensor_icon_dir = omni.kit.app.get_app().get_extension_manager().get_extension_path_by_module(__name__)
        self._sensor_icon_path = str(Path(self._sensor_icon_dir).joinpath("icons/icoSensors.svg"))

        self._sensor_tpye = IconModel.SENSOR_TYPES
        self._stage_icons = omni.kit.widget.stage.StageIcons()
        for sensor_type in self._sensor_tpye:
            self._stage_icons.set(sensor_type, self._sensor_icon_path)

        # TODO: should we distinguish different viewport?
        # viewport_api_id = str(get_active_viewport().id)
        # sensor_icon_visible_setting = f"/persistent/app/viewport/{viewport_api_id}/sensor_icon/visible"
        sensor_icon_visible_setting = VISIBLE_SETTING
        carb.settings.get_settings().set(sensor_icon_visible_setting, True)
        self._menubar_display_inst = get_menubar_display_instance()
        self._custom_item = CategoryStateItem("Sensors", setting_path=sensor_icon_visible_setting)
        self._menubar_display_inst.register_custom_category_item("Show By Type", self._custom_item)

    def on_shutdown(self):  # pragma: no cover
        global _extension
        _extension = None
        self._vp2_scene = None

        # deregister sensor icon to stage widget
        for sensor_type in self._sensor_tpye:
            self._stage_icons.set(sensor_type, self._sensor_icon_path)

        self._menubar_display_inst.deregister_custom_category_item("Show By Type", self._custom_item)


def get_instance():
    return _extension
