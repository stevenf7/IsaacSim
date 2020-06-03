import os
import omni.ext
import omni.kit.commands
import omni.kit.editor
import omni.kit.ui
import carb.tokens
import asyncio

from .. import _urdf

EXTENSION_NAME = "URDF Importer"


class Extension(omni.ext.IExt):
    def on_startup(self):
        print("Starting URDF Extension")
        self._urdf_interface = _urdf.acquire_urdf_interface()
        menu_path = f"Window/Isaac/{EXTENSION_NAME}"
        self._window = omni.kit.ui.Window(EXTENSION_NAME, 960, 600, menu_path=menu_path)

        self._clean_stage_checkbox = self._window.layout.add_child(omni.kit.ui.CheckBox("Clean Stage"))
        self._clean_stage_checkbox.value = True
        self._clean_stage_checkbox.tooltip = omni.kit.ui.Label("Check this box to load URDF on a clean stage")

        self._merge_fixed_joints_checkbox = self._window.layout.add_child(omni.kit.ui.CheckBox("Merge Fixed Joints"))
        self._merge_fixed_joints_checkbox.tooltip = omni.kit.ui.Label(
            "Check this box to skip adding articulation on fixed joints"
        )

        self._enable_convex_decomp = self._window.layout.add_child(omni.kit.ui.CheckBox("Enable Convex Decomposition"))

        self._zup_checkbox = self._window.layout.add_child(omni.kit.ui.CheckBox("Force Z Up"))
        self._zup_checkbox.value = True

        self._scale_input = self._window.layout.add_child(omni.kit.ui.FieldDouble("Scaling Factor", 100))
        self._scale_input.tooltip = omni.kit.ui.Label("Kit unit is in centimeter, adjust unit scale accordingly")

        self._btn_load = self._window.layout.add_child(omni.kit.ui.Button("Load URDF"))
        self._btn_load.set_clicked_fn(self._select_file)

    def _select_picked_folder_callback(self, path):
        if path.startswith("file:"):
            path = path[5:]
            config = _urdf.ImportConfig()
            config.merge_fixed_joints = self._merge_fixed_joints_checkbox.value
            config.enable_convex_decomp = self._enable_convex_decomp.value
            config.distance_scale = self._scale_input.value
            config.force_z_up = self._zup_checkbox.value
            config.add_debug_info = False
            self._urdf_interface.import_urdf(path, config)
        else:
            print("Only local paths supported currently")

    def _select_file(self, btn_widget):
        if self._clean_stage_checkbox.value:
            asyncio.ensure_future(omni.kit.asyncapi.new_stage())

        self._filepicker = omni.kit.ui.FilePicker("Select URDF File", file_type=omni.kit.ui.FileDialogSelectType.FILE)
        self._filepicker.set_file_selected_fn(self._select_picked_folder_callback)
        self._filepicker.add_filter("URDF Files (*.urdf)", r".*.urdf$")
        data_dir = os.path.abspath(carb.tokens.get_tokens_interface().resolve("${app}/../data/urdf"))
        self._filepicker.set_current_directory(data_dir)
        self._filepicker.show()

    def on_shutdown(self):
        print("Shutting down URDF Extension")
        _urdf.release_urdf_interface(self._urdf_interface)
