import carb
import omni.ext
from omni import ui
from .utils.file_utils import *


EXTENSION_NAME = "Internal Tools"


class InternalTools(omni.ext.IExt):
    def on_startup(self):
        self._menu = omni.kit.ui.get_editor_menu().add_item(
            "Window/Isaac/" + EXTENSION_NAME, self.show_window, toggle=False, value=False
        )
        self._window = ui.Window(
            EXTENSION_NAME,
            width=800,
            height=400,
            menu_path="Window/Isaac/" + EXTENSION_NAME,
            visible=False,
            dock=ui.DockPreference.LEFT_BOTTOM,
        )
        with self._window.frame:
            with ui.VStack(height=0):
                with ui.HStack(height=0):
                    ui.Label("Base Path:", width=0)
                    self.path_txt = ui.StringField()
                ui.Button("Check for Absolute Path References", clicked_fn=self.check_for_abs_paths)
                ui.Button("Check for References Outside base folder", clicked_fn=self.check_for_external_refs)
                ui.Button("Assets not referenced by other assets", clicked_fn=self.get_assets_ref_count)
                ui.Button("Check for assets that cannot be released", clicked_fn=self.get_unreleasable)

    def show_window(self, menu, value):
        self._window.visible = not self._window.visible

    def check_for_abs_paths(self):
        items = check_for_abs_paths(self.path_txt.model.get_value_as_string())
        if len(items):
            for key, value in items.items():
                print(key, value)
        else:
            print("No absolute path references found")

    def check_for_external_refs(self):
        items = check_for_external_refs(self.path_txt.model.get_value_as_string())
        if len(items):
            for key, value in items.items():
                print(key, value)
        else:
            print("No external references found")

    def get_assets_ref_count(self):
        items = get_assets_ref_count(self.path_txt.model.get_value_as_string())
        for key, value in items.items():
            if value == 0:
                print(value, ":", key)

    def get_unreleasable(self):
        asset_paths = [
            "/Isaac/Robots/UR10/robotiq",
            "/Isaac/Robots/UR10/ur10_robotiq.usd",
            "/Isaac/Robots/UR10/ur10_schmalz.usd",
            "/Isaac/Samples/Leonardo/Stage/ur10_bin_stacking_robotiq.usd",
            "/Isaac/Samples/Leonardo/Stage/ur10_bin_stacking_srt.usd",
        ]
        for asset in asset_paths:
            path = "{}{}".format(self.path_txt.model.get_value_as_string(), asset)
            if check_if_exists(path):
                carb.log_error("Asset {} should not exist on this server for release".format(path))
            else:
                print("Asset {} not found".format(path))
