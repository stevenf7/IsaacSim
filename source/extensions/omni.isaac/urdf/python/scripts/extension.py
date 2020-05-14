import os
import omni.ext
import omni.kit.commands
import omni.kit.editor
import omni.kit.ui
import carb.tokens

from .. import _urdf


EXTENSION_NAME = "URDF Importer"


class Extension(omni.ext.IExt):
    def on_startup(self):
        print("Starting URDF Extension")
        self._urdf_interface = _urdf.acquire_urdf_interface()
        menu_path = f"Window/Isaac/{EXTENSION_NAME}"
        self._window = omni.kit.ui.Window(EXTENSION_NAME, 960, 600, menu_path=menu_path)
        merge_fixed_joints_checkbox = omni.kit.ui.CheckBox("Merge Fixed Joints")
        merge_fixed_joints_checkbox.set_on_changed_fn(self._on_merge_fixed_joints_fn)
        self._window.layout.add_child(merge_fixed_joints_checkbox)
        self._btn_load = self._window.layout.add_child(omni.kit.ui.Button("Load URDF"))
        self._btn_load.set_clicked_fn(self._select_file)

    def _select_picked_folder_callback(self, path):
        if path.startswith("file:"):
            path = path[5:]
            self._urdf_interface.importUrdf(path)
        else:
            print("Only local paths supported currently")

    def _on_merge_fixed_joints_fn(self, value):
        self._urdf_interface.merge_fixed_joints(value)

    def _select_file(self, btn_widget):
        self._filepicker = omni.kit.ui.FilePicker("Select URDF File", file_type=omni.kit.ui.FileDialogSelectType.FILE)
        self._filepicker.set_file_selected_fn(self._select_picked_folder_callback)
        self._filepicker.add_filter("URDF Files (*.urdf)", r".*.urdf$")
        data_dir = os.path.abspath(carb.tokens.get_tokens_interface().resolve("${app}/../data/urdf"))
        self._filepicker.set_current_directory(data_dir)
        self._filepicker.show()

    def on_shutdown(self):
        print("Shutting down URDF Extension")
        _urdf.release_urdf_interface(self._urdf_interface)
