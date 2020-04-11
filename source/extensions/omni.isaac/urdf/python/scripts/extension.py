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

        layout = self._window.layout.add_child(omni.kit.ui.RowColumnLayout(2))
        layout.set_column_width(0, 150)

        self.urdf_path = layout.add_child(omni.kit.ui.TextBox("/path/to/robot.urdf"))
        self.urdf_path.width = -1
        self._create_btn = self._window.layout.add_child(omni.kit.ui.Button("Load URDF"))
        self._create_btn.set_clicked_fn(self._on_create_fn)

    def on_shutdown(self):
        print("Shutting down URDF Extension")
        _urdf.release_urdf_interface(self._urdf_interface)

    def _on_create_fn(self, widget):
        self._urdf_interface.importUrdf(self.urdf_path.value)
