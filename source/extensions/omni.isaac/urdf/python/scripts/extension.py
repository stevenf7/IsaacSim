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
        menu_path = f"Window/{EXTENSION_NAME}"
        self._window = omni.kit.ui.Window(EXTENSION_NAME, 960, 600, menu_path=menu_path)
        self._btn_load = self._window.layout.add_child(omni.kit.ui.Button("Load URDF"))
        self._btn_load.set_clicked_fn(self._select_file)

    def _select_picked_folder_callback(self, path):
        if path.startswith("file:"):
            path = path[5:]
            self._urdf_interface.importUrdf(path)
        else:
            print("Only local paths supported currently")

    def _select_file(self, btn_widget):
        self._filepicker = omni.kit.ui.FilePicker("Select URDF File", file_type=omni.kit.ui.FileDialogSelectType.FILE)
        self._filepicker.set_file_selected_fn(self._select_picked_folder_callback)
        self._filepicker.add_filter("URDF Files (*.urdf)", r".*.urdf$")
        self._filepicker.show()

    def on_shutdown(self):
        print("Shutting down URDF Extension")
        _urdf.release_urdf_interface(self._urdf_interface)
