import asyncio
import carb
import carb.datasource
import omni.connection as connlib
import omni.kit.ui
import omni.kit.connectionhub
import omni.kit.editor
import omni.usd_plugin
import omni.ext

WINDOW_NAME = "About"
DISCONNECTED = "** disconnected **"
QUERYING = "** querying **"


class Extension(omni.ext.IExt):
    def on_startup(self):
        self.editor = omni.kit.editor.get_editor_interface()
        self.connection_hub = omni.kit.connectionhub.get_connection_hub_interface()
        self.oc = connlib.OmniverseConnection("not_needed")
        self.connection_events = None  # this holds a subscription to connection events
        self.kit_version = self.editor.get_build_version()
        connlib_major = connlib.omniGetVersionMajor()
        connlib_minor = connlib.omniGetVersionMinor()
        connlib_build = connlib.omniGetVersionBuild()
        if connlib_build == 0:
            connlib_build = "no_git_hash"
        else:
            connlib_build = str(hex(connlib_build))[2:]
        self.connlib_version = f"{connlib_major}.{connlib_minor}.{connlib_build}"
        self.nucleus_version = DISCONNECTED
        self.usd_plugin_version = omni.usd_plugin.GetVersion()
        self.versions_label = omni.kit.ui.Label("", useclipboard=True)

        self.set_versions_label()

        # first setup our connection information and subscriptions
        self.connection_events = self.connection_hub.subscribe_to_connection_events(self.handle_connection_event)

        if len(self.connection_hub.get_connection_handles()) > 0:
            self.populate_nucleus_version(self.connection_hub.get_latest_connection_id())
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

    def on_shutdown(self):
        self.connection_events = None

    def set_versions_label(self):
        self.versions_label.text = (
            f"Omniverse Isaac Sim {self.kit_version}\n"
            f"USD Plugin Version: {self.usd_plugin_version}\n"
            f"Connection Library Version: {self.connlib_version}\n"
            f"Nucleus Server Version: {self.nucleus_version}\n"
        )

    def populate_nucleus_version(self, handle):
        connection_id = self.connection_hub.get_connection_id_from_handle(handle)
        self.oc.connection = connlib.omniGetConnectionWithId(connection_id)
        asyncio.ensure_future(self._get_nucleus_version())

    async def _get_nucleus_version(self):
        res = await self.oc.ping()
        self.nucleus_version = res.version
        self.set_versions_label()

    def handle_connection_event(self, connection_event):
        if connection_event.type == int(carb.datasource.ConnectionEventType.CONNECTED):
            payload_dict = connection_event.payload.get_dict()
            self.connected = True
            self.nucleus_version = QUERYING
            self.set_versions_label()
            self.populate_nucleus_version(payload_dict.get("handle"))

        else:
            self.connected = False
            self.nucleus_version = DISCONNECTED
            self.set_versions_label()
