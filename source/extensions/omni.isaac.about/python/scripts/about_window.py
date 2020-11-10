import asyncio
import carb
import carb.datasource
import omni.client
import omni.kit.ui
import omni.kit.editor

WINDOW_NAME = "About"
DISCONNECTED = "** disconnected **"
QUERYING = "** querying **"


class Extension(omni.ext.IExt):
    def on_startup(self):
        self.editor = omni.kit.editor.get_editor_interface()
        self.kit_version = self.editor.get_build_version()
        self.nucleus_version = DISCONNECTED
        self.client_library_version = omni.client.get_version()
        self.versions_label = omni.kit.ui.Label("", useclipboard=True)

        self.set_versions_label()

        menu_path = f"Help/{WINDOW_NAME}"
        self._window = omni.kit.ui.Window(
            WINDOW_NAME,
            0,
            0,
            menu_path=menu_path,
            open=False,
            dock=omni.kit.ui.DockPreference.DISABLED,
            is_toggle_menu=False,
        )
        self._window.layout.add_child(self.versions_label)
        self._window.layout.add_child(omni.kit.ui.Label(f"Loaded Plugins:"))
        self._window.layout.add_child(omni.kit.ui.Label(f"---------------"))

        scrollable = self._window.layout.add_child(omni.kit.ui.ScrollingFrame("ScrollingFrame", 500, 200))
        scr_layout = scrollable.add_child(omni.kit.ui.RowColumnLayout(1, True))

        plugins = carb.get_framework().get_plugins()
        plugins = sorted(plugins, key=lambda x: x.impl.name)
        for p in plugins:
            label = scr_layout.add_child(omni.kit.ui.Label(f"{p.impl.name} {p.interfaces}"))
            label.tooltip = omni.kit.ui.Label(p.libPath)

        button = omni.kit.ui.Button("OK")
        button.set_clicked_fn(lambda *_: self._window.hide())
        self._window.layout.add_child(button)

    def set_versions_label(self):
        self.versions_label.text = (
            f"Omniverse Kit {self.kit_version}\n"
            f"Client Library Version: {self.client_library_version}\n"
            # f"Nucleus Server Version: {self.nucleus_version}\n" # TODO JS
        )
