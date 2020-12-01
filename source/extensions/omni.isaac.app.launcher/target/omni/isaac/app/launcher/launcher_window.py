import sys

import carb.settings
import carb.tokens

import omni.kit.app

from typing import List, Dict, Any

from pathlib import Path

CURRENT_PATH = Path(__file__).parent
ICON_PATH = CURRENT_PATH.parent.parent.parent.parent.joinpath("icons")

SHOW_CONSOLE_SETTING = "/persistent/ext/omni.isaac.launcher/show_console"
PERSISTENT_LAUNCHER_SETTING = "/persistent/ext/omni.isaac.launcher/persistent_launcher"

GRAY = 0xFF444444
LIGHT_GRAY = 0xFFBBBBBB
DARK_GRAY = 0xFF2A2A2A
GREEN = 0xFF00B976
BLACK = 0xFF000000

launcher_style = {
    "Rectangle::gray_bg": {"background_color": GRAY},
    "Rectangle::active_bg": {"background_color": GREEN},
    "ScrollingFrame": {"background_color": DARK_GRAY, "padding": 15},
    "RadioButton::app": {"color": 0x0, "background_color": BLACK, "margin": 10},
    "RadioButton.Label": {"color": 0x0},
    "RadioButton:checked": {"background_color": GREEN},
    "Label::app_label": {"font_size": 20, "color": LIGHT_GRAY},
}


class LauncherWindow:
    def __init__(self, ext_path: str) -> None:
        """ create the window """

        self._settings = carb.settings.get_settings()
        self._radio_collection = None
        self._ext_path = ext_path

        self._auto_launch = None
        self._app_as_default = None
        self._apps: List[str] = self._settings.get("/ext/omni.isaac.launcher/apps")
        self._auto_launch = self._settings.get("/persistent/ext/omni.isaac.launcher/auto_launch")
        self._default_app = self._settings.get("/persistent/ext/omni.isaac.launcher/default_app")

        self._app_list_frame = None  # the frame for the application list
        self._detail_label = None  # label of the active app
        self._detail_description = None  # label of the active app
        self._window = None
        self._build_window()

    def _launch_app(self, app_id: str):
        """ show the omniverse ui documentation as an external Application """
        # update default
        if self._app_as_default.get_value_as_bool():
            self._settings.set("/persistent/ext/omni.isaac.launcher/default_app", app_id)

        import subprocess
        import platform

        app_folder = self._settings.get_as_string("/app/folder")
        if app_folder == "":
            app_folder = carb.tokens.get_tokens_interface().resolve("${app}")

        launch_args = [f"{app_folder}/../{app_id}.bat"]

        kwargs: Dict[str, Any] = {"close_fds": False}
        if platform.system().lower() == "windows":
            kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
            if self._settings.get(SHOW_CONSOLE_SETTING):
                kwargs["creationflags"] |= subprocess.CREATE_NEW_CONSOLE

        subprocess.Popen(launch_args, **kwargs)

    def _launch_selected_app(self):
        application_index = self._radio_collection.model.get_value_as_int()
        self._launch_app(self._apps[application_index])

        # update the default app display if needed
        self._default_app = self._settings.get("/persistent/ext/omni.isaac.launcher/default_app")
        self._build_app_list()

    def _close(self):
        sys.exit()

    def destroy(self):
        self._window = None

    def _appid_to_title(self, app_id: str):
        app_title = app_id.replace("omni.", "")
        app_title = app_title.replace(".", " ")
        app_title = app_title.capitalize()
        return app_title

    def _exit(self):
        omni.kit.app.get_app().post_quit()

    def _build_app_list(self):
        import omni.ui as ui

        # Application Column
        if not self._app_list_frame:
            self._app_list_frame = ui.ScrollingFrame(width=620)
        else:
            self._app_list_frame.clear()

        with self._app_list_frame:

            self._radio_collection = ui.RadioCollection()
            with ui.VGrid(column_count=3, row_height=230):
                for an_app in self._apps:
                    with ui.VStack():
                        with ui.ZStack(style={"ZStack": {"margin": 10}}):
                            bg_color = "gray_bg"
                            if an_app == self._default_app:
                                bg_color = "active_bg"
                            ui.Rectangle(name=bg_color)
                            ui.RadioButton(
                                text=".",
                                style={"Button": {"padding": 20}, "Button.Image": {"alignment": ui.Alignment.CENTER}},
                                # image_url=f"{ICON_PATH}/{an_app}.png",
                                name="app",
                                height=175,
                                width=175,
                                clicked_fn=lambda app=an_app: self._show_details(app),
                                mouse_double_clicked_fn=lambda x, y, m, b, app=an_app: self._launch_app(app),
                                radio_collection=self._radio_collection,
                            )
                        app_title = self._appid_to_title(an_app)
                        ui.Label(app_title, name="app_label", height=0, alignment=ui.Alignment.CENTER)
                        ui.Spacer(height=20)

            default_index = 0
            if self._default_app:
                try:
                    default_index = self._apps.index(self._default_app)
                except:
                    default_index = 0

            self._radio_collection.model.set_value(default_index)

    def _show_details(self, app_id):
        app_title = self._appid_to_title(app_id)
        self._detail_label.text = app_title

        ext_manager = omni.kit.app.get_app().get_extension_manager()
        ext_dict = ext_manager.get_extension_dict(f"{app_id}-2020.3.0")

        description = ext_dict["package"]["description"]
        if "details_description" in ext_dict["package"]:
            description = ext_dict["package"]["details_description"]

        self._detail_description.text = description

    def _build_detail_panel(self):
        import omni.ui as ui

        with ui.VStack():
            ui.Spacer(height=30)
            with ui.HStack(height=200):
                ui.Spacer()
                with ui.ZStack(width=200, heigh=200):
                    ui.Rectangle(style={"background_color": 0xFF666666})
                    with ui.Frame(style={"margin": 3}):
                        ui.Rectangle(style={"background_color": 0xFF000000})
                ui.Spacer()
            ui.Spacer(height=10)
            self._detail_label = ui.Label(
                "isaac-sim", height=0, style={"font_size": 22, "alignment": ui.Alignment.CENTER}
            )
            ui.Spacer(height=20)
            ui.Label(
                "DESCRIPTIONS",
                height=0,
                width=150,
                style={"font_size": 22, "color": 0xFFFFAA44, "alignment": ui.Alignment.CENTER},
            )
            ui.Spacer(height=10)
            with ui.HStack():
                ui.Spacer(width=12)
                self._detail_description = ui.Label(
                    "",
                    width=350,
                    word_wrap=True,
                    style={"font_size": 18, "color": 0xFFBBBBBB, "alignment": ui.Alignment.LEFT},
                )

            with ui.HStack(height=0):
                ui.Spacer(width=10)
                self._show_app_console = ui.CheckBox(height=10, width=30).model

                def on_console_value_changed(model):
                    value = model.get_value_as_bool()
                    self._settings.set(SHOW_CONSOLE_SETTING, value)

                self._show_app_console.set_value(self._settings.get(SHOW_CONSOLE_SETTING))
                self._show_app_console.add_value_changed_fn(on_console_value_changed)

                ui.Label("Show startup console", width=100, style={"font_size": 18, "color": 0xFFBBBBBB})

            ui.Spacer(height=5)
            with ui.HStack(height=0):
                ui.Spacer(width=10)
                self._persistent_launcher = ui.CheckBox(height=10, width=30).model

                def on_persistent_launcher_value_changed(model):
                    value = model.get_value_as_bool()
                    self._settings.set(PERSISTENT_LAUNCHER_SETTING, value)

                self._persistent_launcher.set_value(self._settings.get(PERSISTENT_LAUNCHER_SETTING))
                self._persistent_launcher.add_value_changed_fn(on_persistent_launcher_value_changed)

                ui.Label("Keep Launcher Open on App Launch", width=100, style={"font_size": 18, "color": 0xFFBBBBBB})

            ui.Spacer(height=5)
            with ui.HStack(height=0):
                ui.Spacer(width=10)
                self._app_as_default = ui.CheckBox(height=10, width=30).model
                ui.Label("Set selection as new default", width=100, style={"font_size": 18, "color": 0xFFBBBBBB})

            ui.Spacer(height=5)
            with ui.HStack(height=0):
                ui.Spacer(width=10)

                def on_value_changed(model):
                    value = model.get_value_as_bool()
                    self._settings.set("/persistent/ext/omni.isaac.launcher/auto_launch", value)

                self._auto_launch_chk = ui.CheckBox(height=10, width=30).model
                self._auto_launch_chk.set_value(self._auto_launch)
                self._auto_launch_chk.add_value_changed_fn(on_value_changed)

                ui.Label("Automaticly launch default app", width=100, style={"font_size": 18, "color": 0xFFBBBBBB})

            ui.Spacer(height=5)
            with ui.HStack(height=50, style={"font_size": 20, "margin": 4}):
                ui.Button(
                    "LAUNCH",
                    clicked_fn=self._launch_selected_app,
                    style={
                        "Button": {"background_color": GREEN},
                        "Button.Label": {"color": 0xFFFFFFFF},
                        "Button:hovered": {"background_color": 0xFF00A922, "color": 0xFFFFFFFF},
                    },
                )
                ui.Button(
                    "CLOSE",
                    clicked_fn=lambda: self._exit(),
                    style={"background_color": 0xFFBBBBBB, "color": 0xFF444444},
                )
            ui.Spacer(height=5)

    def _build_nvidia_status_bar(self):
        import omni.ui as ui

        with ui.ZStack(height=30):
            ui.Rectangle(style={"background_color": 0xFF000000})
            with ui.HStack():
                ui.Spacer()
                with ui.VStack(width=0):
                    ui.Spacer()
                    ui.Image(f"{self._ext_path}/icons/NVIDIA_logo.png", height=18, width=150)
                    ui.Spacer()

    def _build_window(self):
        import omni.ui as ui

        self._window = ui.Window("Launcher", padding_x=0, padding_y=0, style={"Window": {"pading": 0}})
        self._window.frame.set_style(launcher_style)
        with self._window.frame:
            with ui.VStack():
                ui.Spacer(height=20)
                with ui.HStack():
                    # app List
                    self._build_app_list()
                    # Details Column
                    self._build_detail_panel()

                self._build_nvidia_status_bar()
