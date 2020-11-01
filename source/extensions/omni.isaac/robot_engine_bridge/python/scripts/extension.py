import os
import omni.ext
import omni.kit.commands
import omni.kit.editor
import omni.kit.ui
import carb.tokens

from .. import _robot_engine_bridge
from .menu import RobotEngineBridgeMenu


EXTENSION_NAME = "Robot Engine Bridge"


class Extension(omni.ext.IExt):
    def on_startup(self):
        self._re_bridge = _robot_engine_bridge.acquire_robot_engine_bridge_interface()

        menu_path = f"Window/Isaac/{EXTENSION_NAME}"
        self._editor = omni.kit.editor.get_editor_interface()
        # active script
        self._script = None
        self._window = omni.kit.ui.Window(
            EXTENSION_NAME, 960, 300, menu_path=menu_path, dock=omni.kit.ui.DockPreference.LEFT_BOTTOM
        )

        self._settings = omni.kit.settings.get_settings_interface()
        json_path_input = self._settings.get("/isaac/robot_engine_bridge/json")

        # The default app json is copied to the resources folder as part of the build process
        # exec_folder resolves automatically to the folder containing the kit binary
        json_path = os.path.abspath(
            carb.tokens.get_tokens_interface().resolve(
                "${app}/../exts/omni.isaac.robot_engine_bridge/resources/isaac_engine/json/isaacsim.app.json"
            )
        )

        if json_path_input is not None:
            json_path = json_path_input

        stage_load_layout = self._window.layout.add_child(omni.kit.ui.RowColumnLayout(5))
        layout_collapsing = omni.kit.ui.CollapsingFrame("Scene Loader Settings", False)
        self._window.layout.add_child(layout_collapsing)

        stage_load_layout = omni.kit.ui.RowColumnLayout(2, True)
        layout_collapsing.add_child(stage_load_layout)
        stage_load_layout.set_column_width(0, 150)
        stage_load_layout.set_column_width(1, 150)

        stage_load_layout.add_child(omni.kit.ui.Label("Input Component"))
        inp_txt = omni.kit.ui.TextBox("input")
        self._inp_comp = stage_load_layout.add_child(inp_txt)
        stage_load_layout.add_child(omni.kit.ui.Label("Request Channel"))
        req_channel_txt = omni.kit.ui.TextBox("scenario_control")
        self._req_channel = stage_load_layout.add_child(req_channel_txt)
        stage_load_layout.add_child(omni.kit.ui.Label("Camera Control"))
        camera_channel_txt = omni.kit.ui.TextBox("camera_switch")
        self._cam_channel = stage_load_layout.add_child(camera_channel_txt)
        stage_load_layout.add_child(omni.kit.ui.Label("Output Component"))
        out_txt = omni.kit.ui.TextBox("output")
        self._out_comp = stage_load_layout.add_child(out_txt)
        stage_load_layout.add_child(omni.kit.ui.Label("Reply Channel"))
        rep_channel_txt = omni.kit.ui.TextBox("scenario_reply")
        self._rep_channel = stage_load_layout.add_child(rep_channel_txt)

        inp_txt.set_text_changed_fn(self._on_init_stage_load_fn)
        req_channel_txt.set_text_changed_fn(self._on_init_stage_load_fn)
        out_txt.set_text_changed_fn(self._on_init_stage_load_fn)
        rep_channel_txt.set_text_changed_fn(self._on_init_stage_load_fn)

        layout = self._window.layout.add_child(omni.kit.ui.RowColumnLayout(2))
        layout.set_column_width(0, 150)
        path_label = layout.add_child(omni.kit.ui.Label("Application Json Path"))
        path_label.tooltip = omni.kit.ui.Label(
            'Can specify with: --carb/isaac/robot_engine_bridge/json="path/to/app.json" \n Or by entering in this text box'
        )
        self.application_path = layout.add_child(omni.kit.ui.TextBox(json_path))
        self.application_path.width = -1
        self._create_destroy_btn = self._window.layout.add_child(omni.kit.ui.Button("Create Application"))
        self._create_destroy_btn.set_clicked_fn(self._on_create_destroy_fn)

        self._menu = RobotEngineBridgeMenu()
        self._is_created = False

    def on_shutdown(self):
        self._menu.shutdown()
        self._menu = None
        _robot_engine_bridge.release_robot_engine_bridge_interface(self._re_bridge)

    def _on_init_stage_load_fn(self, widget):
        self._re_bridge.initialize_stage_loader(
            self._inp_comp.value,
            self._req_channel.value,
            self._cam_channel.value,
            self._out_comp.value,
            self._rep_channel.value,
        )

    def _on_create_destroy_fn(self, widget):
        if self._is_created is False:
            asset_path = os.path.abspath(
                carb.tokens.get_tokens_interface().resolve("${app}/../exts/omni.isaac.robot_engine_bridge/")
            )
            self._re_bridge.create_application(asset_path, self.application_path.value, [], [])
            self._re_bridge.initialize_stage_loader(
                self._inp_comp.value,
                self._req_channel.value,
                self._cam_channel.value,
                self._out_comp.value,
                self._rep_channel.value,
            )
            self._is_created = True
            widget.text = "Destroy Application"
        else:
            self._re_bridge.destroy_application()
            self._is_created = False
            widget.text = "Create Application"
