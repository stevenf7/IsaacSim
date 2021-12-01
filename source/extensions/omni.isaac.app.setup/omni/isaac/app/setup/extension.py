# Copyright (c) 2018-2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

import asyncio
import sys
import os.path
import omni.ext
import omni.ui as ui
import carb.settings
import omni.kit.commands
import carb.imgui as _imgui
import carb.tokens
import webbrowser

import omni.kit.app
import omni.kit.ui
import omni.appwindow
import omni.kit.stage_templates as stage_templates
from omni.kit.window.title import get_main_window_title
from carb.input import KeyboardInput as Key
from omni.client._omniclient import Result, CopyBehavior
from omni.kit.menu.utils import add_menu_items, remove_menu_items, MenuItemDescription

DOCS_URL = "https://docs.omniverse.nvidia.com"
REFERENCE_GUIDE_URL = DOCS_URL + "/isaacsim"
ASSETS_GUIDE_URL = DOCS_URL + "/app_isaacsim/app_isaacsim/setup.html#isaac-sim-setup-nucleus-add-assets"
FORUMS_URL = "https://forums.developer.nvidia.com/c/agx-autonomous-machines/isaac/simulation/69"
KIT_MANUAL_URL = DOCS_URL + "/py/kit/index.html"


class CreateSetupExtension(omni.ext.IExt):
    """Create Final Configuration"""

    def on_startup(self, ext_id: str):
        """ setup the window layout, menu, final configuration of the extensions etc """
        self._settings = carb.settings.get_settings()

        # this is a work around as some Extensions don't properly setup their default setting in time
        self._set_defaults()

        # adjust couple of viewport settings
        self._settings.set("/app/viewport/grid/enabled", True)
        self._settings.set("/app/viewport/outline/enabled", True)
        self._settings.set("/app/viewport/boundingBoxes/enabled", False)

        # Adjust the Window Title to show the Isaac Sim Version
        window_title = get_main_window_title()
        app_version = self._settings.get("/app/version")
        app_folder = self._settings.get_as_string("/app/folder")
        if not app_folder:
            app_folder = carb.tokens.get_tokens_interface().resolve("${app}")
        # if not app_version:
        app_launch_folder = os.path.normpath(os.path.join(app_folder, os.pardir))
        app_version = open(f"{app_launch_folder}/VERSION").read()

        if app_version:
            app_version, _ = app_version.split("+")
            # for GM version remove this details
            # app_version, _ = app_version.split("-")
            window_title.set_app_version(app_version)

        # setup some imgui Style overide
        imgui = _imgui.acquire_imgui()
        imgui.push_style_color(_imgui.StyleColor.ScrollbarGrab, carb.Float4(0.4, 0.4, 0.4, 1))
        imgui.push_style_color(_imgui.StyleColor.ScrollbarGrabHovered, carb.Float4(0.6, 0.6, 0.6, 1))
        imgui.push_style_color(_imgui.StyleColor.ScrollbarGrabActive, carb.Float4(0.8, 0.8, 0.8, 1))

        imgui.push_style_var_float(_imgui.StyleVar.DockSplitterSize, 2)

        self.__setup_window_task = asyncio.ensure_future(self.__dock_windows())
        self.__setup_property_window = asyncio.ensure_future(self.__property_window())

        self._menu_items = [MenuItemDescription(name="Nucleus Check", onclick_fn=self._menu_callback)]
        add_menu_items(self._menu_items, "Isaac Utils")

        self.__menu_update()
        self.__add_app_icon(ext_id)
        self.__await_new_scene = asyncio.ensure_future(self.__new_stage())

    def _set_defaults(self):
        """ this is trying to setup some defaults for extensions to avoid warning """
        self._settings.set_default("/persistent/app/omniverse/bookmarks", {})
        self._settings.set_default("/persistent/app/stage/timeCodeRange", [0, 100])

        self._settings.set_default("/persistent/audio/context/closeAudioPlayerOnStop", False)

        self._settings.set_default("/persistent/app/primCreation/PrimCreationWithDefaultXformOps", True)
        self._settings.set_default("/persistent/app/primCreation/DefaultXformOpType", "Scale, Rotate, Translate")
        self._settings.set_default("/persistent/app/primCreation/DefaultRotationOrder", "ZYX")
        self._settings.set_default("/persistent/app/primCreation/DefaultXformOpPrecision", "Double")

        # omni.kit.property.tagging
        self._settings.set_default("/persistent/exts/omni.kit.property.tagging/showAdvancedTagView", False)
        self._settings.set_default("/persistent/exts/omni.kit.property.tagging/showHiddenTags", False)
        self._settings.set_default("/persistent/exts/omni.kit.property.tagging/modifyHiddenTags", False)

        # force this on startup for better performance on larger scenes when selecting objects.
        self._settings.set("persistent/app/viewport/pickingMode", "models")
        # camera settings
        self._settings.set("persistent/app/viewport/camShowSpeedOnStart", False)
        self._settings.set("persistent/app/omniverse/gamepadCameraControl", False)

        # do not display sever check pop-up on start up
        nucleus_check = carb.settings.get_settings().get("/exts/omni.isaac.app.setup/nucleusCheck")
        self._settings.set_default("/persistent/exts/omni.isaac.app.setup/nucleusCheck", nucleus_check)
        self._startup_run = True
        self._cancel_download_btn = None
        self._server_window = None
        self._check_success = None
        self.nucleus_check_result = Result.OK

        # get download assets defaults
        copy_assetsURL = carb.settings.get_settings().get("/exts/omni.isaac.app.setup/copy_assetsURL")
        self._settings.set_default("/persistent/exts/omni.isaac.app.setup/copy_assetsURL", copy_assetsURL)
        copy_concurrency = carb.settings.get_settings().get("/exts/omni.isaac.app.setup/copy_concurrency")
        self._settings.set_default("/persistent/exts/omni.isaac.app.setup/copy_concurrency", copy_concurrency)
        copy_behaviour = carb.settings.get_settings().get("/exts/omni.isaac.app.setup/copy_behaviour")
        self._settings.set_default("/persistent/exts/omni.isaac.app.setup/copy_behaviour", copy_behaviour)
        copy_timeout = carb.settings.get_settings().get("/exts/omni.isaac.app.setup/copy_timeout")
        self._settings.set_default("/persistent/exts/omni.isaac.app.setup/copy_timeout", copy_timeout)

    async def __new_stage(self):

        window = ui.Window("STARTING RTX", height=100, flags=ui.WINDOW_FLAGS_NO_TITLE_BAR)
        with window.frame:
            with ui.VStack(height=80):
                ui.Spacer()
                ui.Label("... RTX Loading ....", alignment=ui.Alignment.CENTER, style={"font_size": 18})
                ui.Spacer()

        # 10 frame delay to allow Layout
        for i in range(10):
            await omni.kit.app.get_app().next_update_async()

        stage_templates.new_stage(template=None)

        await omni.kit.app.get_app().next_update_async()

        window.visible = False
        window = None

        # Let users know when app is ready for use and live-streaming
        app_title = self._settings.get("/app/window/title")
        omni.kit.app.get_app().print_and_log(f"{app_title} App is loaded.")

        await omni.kit.app.get_app().next_update_async()
        await self._nucleus_check_window()

    def _menu_callback(self):
        if self._cancel_download_btn and self._cancel_download_btn.visible:
            self._server_window.visible = True
        else:
            if self._server_window and self._server_window.visible:
                self._server_window.visible = False
                self._server_window = None
            if self._check_success and self._check_success.visible:
                self._check_success.visible = False
                self._check_success = None
            asyncio.ensure_future(self._nucleus_check_window())

    async def _nucleus_check_success_window(self):
        nucleus_check = carb.settings.get_settings().get("/persistent/exts/omni.isaac.app.setup/nucleusCheck")
        self._check_success = ui.Window(
            "Check Successful",
            style={"alignment": ui.Alignment.CENTER},
            height=0,
            width=0,
            padding_x=10,
            padding_y=10,
            auto_resize=True,
            flags=ui.WINDOW_FLAGS_NO_RESIZE | ui.WINDOW_FLAGS_NO_SCROLLBAR | ui.WINDOW_FLAGS_NO_TITLE_BAR,
            visible=True,
        )

        def hide(w):
            w.visible = False

        with self._check_success.frame:
            with ui.VStack():
                ui.Spacer(height=1)
                ui.Label("Nucleus detected successfully:", style={"font_size": 18}, alignment=ui.Alignment.CENTER)
                ui.Label("{}".format(self.nucleus_server), style={"font_size": 18}, alignment=ui.Alignment.CENTER)
                ui.Spacer(height=5)
                ui.Button(
                    "OK", spacing=10, alignment=ui.Alignment.CENTER, clicked_fn=lambda w=self._check_success: hide(w)
                )
                ui.Spacer(height=5)
                ui.Line()
                ui.Spacer(height=5)
                with ui.HStack(spacing=5, width=0, height=0):
                    ui.Label("Perform Nucleus check on startup")
                    server_model = ui.CheckBox().model
                    server_model.set_value(nucleus_check)
                    server_model.add_value_changed_fn(
                        lambda m: carb.settings.get_settings().set_bool(
                            "/persistent/exts/omni.isaac.app.setup/nucleusCheck", m.get_value_as_bool()
                        )
                    )
                ui.Spacer()

        await omni.kit.app.get_app().next_update_async()

    async def _nucleus_check_window(self):
        # Check Nucleus server for assets
        nucleus_check = carb.settings.get_settings().get("/persistent/exts/omni.isaac.app.setup/nucleusCheck")

        # Override Nucleus check in warmup
        override_nucleus_check = carb.settings.get_settings().get("/exts/omni.isaac.app.setup/nucleusCheckOverride")

        if (nucleus_check is False and self._startup_run) or (nucleus_check is True and override_nucleus_check is True):
            self._startup_run = False
            pass
        else:
            from omni.isaac.core.utils.nucleus import find_nucleus_server_async

            omni.kit.app.get_app().print_and_log("Checking for Isaac Sim assets on Nucleus ")
            self._check_window = ui.Window("Check Nucleus", height=100, width=500, flags=ui.WINDOW_FLAGS_NO_TITLE_BAR)
            with self._check_window.frame:
                with ui.VStack(height=80):
                    ui.Spacer()
                    ui.Label(
                        "Checking for Isaac Sim assets on Nucleus",
                        alignment=ui.Alignment.CENTER,
                        style={"font_size": 18},
                    )
                    ui.Label(
                        "Please login to the Nucleus if a browser window appears",
                        alignment=ui.Alignment.CENTER,
                        style={"font_size": 18},
                    )
                    ui.Label(
                        "This dialog will close as soon as a login occurs or when it timeouts",
                        alignment=ui.Alignment.CENTER,
                        style={"font_size": 18},
                    )
                    ui.Spacer()
            await omni.kit.app.get_app().next_update_async()

            self.nucleus_check_result, self.nucleus_server = await find_nucleus_server_async("/Isaac", 20)

            self._check_window.visible = False
            self._check_window = None
            if self.nucleus_check_result is not Result.OK:
                self._startup_run = False

                if self.nucleus_check_result is Result.ERROR_CONNECTION:
                    carb.log_warn(
                        "Connection login timeout. Enter login information on the browser or restart Isaac Sim."
                    )

                if self.nucleus_check_result is Result.OK_NOT_YET_FOUND:
                    frame_height = 360
                else:
                    frame_height = 250
                self._server_window = ui.Window(
                    "Checking Nucleus for Isaac Sim Assets", width=350, height=frame_height, visible=True
                )
                with self._server_window.frame:
                    with ui.VStack():
                        ui.Label("Warning: Nucleus not configured correctly", style={"color": 0xFF00FFFF})
                        ui.Label(
                            "/Isaac folder containing sample assets was not found\nMost Isaac Sim samples will not work correctly"
                        )
                        ui.Line()
                        ui.Label(
                            "Add a new connection in the Content tab \nto a Nucleus with the Isaac Sim Sample Assets"
                        )
                        ui.Spacer()
                        ui.Label("See the documentation for details")
                        ui.Button("Open Documentation", clicked_fn=lambda: self._open_browser(ASSETS_GUIDE_URL))
                        if self.nucleus_check_result is Result.OK_NOT_YET_FOUND:
                            ui.Line()
                            self.nucleus_server = self.nucleus_server + "/Isaac"
                            self._download_label = ui.Label("Click the button below to copy assets to folder:\n")
                            self._downloaded_label = ui.Label("Assets downloaded to folder:\n", visible=False)
                            ui.Label("{}".format(self.nucleus_server))
                            ui.Spacer()
                            self._download_btn = ui.Button("Download assets", clicked_fn=self._on_download_assets)
                            self._cancel_download_btn = ui.Button(
                                "Cancel download", clicked_fn=self._on_cancel_download, visible=False
                            )
                            ui.Spacer()
                            with ui.HStack(spacing=5, width=0, height=0):
                                self._progress_bar_label = ui.Label("Current Progress")
                                self._completed_label = ui.Label(
                                    "Completed!", style={"color": 0xFF00FF00}, visible=False
                                )
                                self._progress_bar = ui.ProgressBar(style={"color": 0x76F90000, "padding": 1}).model
                                self._progress_bar.set_value(0)
                        ui.Spacer()
                        ui.Label("See terminal for additional information")
                        ui.Line()
                        with ui.HStack(spacing=5, width=0, height=0):
                            ui.Label("Perform Nucleus check on startup")
                            server_model = ui.CheckBox().model
                            server_model.set_value(nucleus_check)
                            server_model.add_value_changed_fn(
                                lambda m: carb.settings.get_settings().set_bool(
                                    "/persistent/exts/omni.isaac.app.setup/nucleusCheck", m.get_value_as_bool()
                                )
                            )
            else:
                omni.kit.app.get_app().print_and_log(f"Nucleus detected successfully: {self.nucleus_server}")
                if not self._startup_run:
                    asyncio.ensure_future(self._nucleus_check_success_window())
                self._startup_run = False

    def _on_download_assets(self):
        self._download_btn.visible = False
        self._cancel_download_btn.visible = True
        self._download_task = asyncio.ensure_future(self._on_download_assets_async())
        omni.kit.app.get_app().print_and_log(f"Assets downloading to {self.nucleus_server}...")

    def _on_cancel_download(self):
        self._download_btn.visible = True
        self._cancel_download_btn.visible = False
        self._download_task.cancel()
        self._download_task = None
        omni.kit.app.get_app().print_and_log("Assets download cancelled.")

    async def _on_download_assets_async(self):
        def progress_callback(progress, total_steps):
            self._progress_bar.set_value(progress / total_steps)
            pass

        # read persistent settings
        copy_assetsURL = carb.settings.get_settings().get_as_string(
            "/persistent/exts/omni.isaac.app.setup/copy_assetsURL"
        )
        copy_concurrency = int(
            carb.settings.get_settings().get("/persistent/exts/omni.isaac.app.setup/copy_concurrency")
        )
        copy_timeout = float(carb.settings.get_settings().get("/persistent/exts/omni.isaac.app.setup/copy_timeout"))
        copy_behaviour_str = carb.settings.get_settings().get_as_string(
            "/persistent/exts/omni.isaac.app.setup/copy_behaviour"
        )
        if copy_behaviour_str == "CopyBehavior.OVERWRITE":
            copy_behaviour = CopyBehavior.OVERWRITE
        elif copy_behaviour_str == "CopyBehavior.ERROR_IF_EXISTS":
            copy_behaviour = CopyBehavior.ERROR_IF_EXISTS
        else:
            copy_behaviour = None

        # import download_assets_async only if nucleus_check is enabled
        from omni.isaac.core.utils.nucleus import download_assets_async

        result = await download_assets_async(
            copy_assetsURL, self.nucleus_server, progress_callback, copy_concurrency, copy_behaviour, copy_timeout
        )
        omni.kit.app.get_app().print_and_log(f"Assets download to {self.nucleus_server} completed!")
        self.nucleus_check_result = Result.OK
        self._download_label.visible = False
        self._download_btn.visible = False
        self._cancel_download_btn.visible = False
        self._downloaded_label.visible = True
        self._progress_bar_label.visible = False
        self._completed_label.visible = True
        return result

    def _launch_app(self, app_id, console=True, custom_args=None):
        """launch an other Kit app with the same settings"""
        import sys
        import subprocess
        import platform

        app_path = carb.tokens.get_tokens_interface().resolve("${app}")
        kit_file_path = os.path.join(app_path, app_id)

        launch_args = [sys.argv[0]]
        launch_args += [kit_file_path]
        if custom_args:
            launch_args.extend(custom_args)

        # Pass all exts folders
        exts_folders = self._settings.get("/app/exts/folders")
        if exts_folders:
            for folder in exts_folders:
                launch_args.extend(["--ext-folder", folder])

        kwargs = {"close_fds": False}
        if platform.system().lower() == "windows":
            if console:
                kwargs["creationflags"] = subprocess.CREATE_NEW_CONSOLE | subprocess.CREATE_NEW_PROCESS_GROUP
            else:
                kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP

        subprocess.Popen(launch_args, **kwargs)

    def _show_ui_docs(self):
        """ show the omniverse ui documentation as an external Application """
        self._launch_app("omni.app.uidoc.kit")

    def _show_launcher(self):
        """ show the omniverse ui documentation as an external Application """
        self._launch_app("omni.isaac.sim.launcher.kit", console=False, custom_args={"--/app/auto_launch=false"})

    async def __dock_windows(self):
        """ setup all the docking properly for create """
        content = ui.Workspace.get_window("Content")
        stage = ui.Workspace.get_window("Stage")
        layer = ui.Workspace.get_window("Layer")
        console = ui.Workspace.get_window("Console")
        collection = ui.Workspace.get_window("Collection")
        camera_tool = ui.Workspace.get_window("Camera Animation")

        # hack to remove the wrong timeline window
        timeline = ui.Workspace.get_window("TIMELINE")
        if timeline:
            timeline.visible = False

        stage.dock_order = 0
        stage.focus()

        # dock with the console
        if console:
            content.dock_in(console, ui.DockPosition.SAME)
        else:
            print("failed to get console")

        render_settings = ui.Workspace.get_window("RTX Settings")
        if render_settings:
            render_settings.visible = True
            render_settings.dock_in(stage, ui.DockPosition.SAME)
            await omni.kit.app.get_app().next_update_async()
            render_settings.dock_in(stage, ui.DockPosition.SAME)
            await omni.kit.app.get_app().next_update_async()
            stage.focus()

        if camera_tool:
            camera_tool.dock_in(console, ui.DockPosition.SAME)

        if collection:
            collection.dock_in(stage, ui.DockPosition.SAME)

        await omni.kit.app.get_app().next_update_async()

        stage.dock_order = 0
        layer.dock_order = 1
        if collection:
            collection.dock_order = 2

        await omni.kit.app.get_app().next_update_async()

        content.dock_order = 0
        console.dock_order = 1
        content.focus()

    async def __reset_layout(self):
        """Setup all the docking properly for Create"""
        ui.Workspace.clear()

        # Show the window we need
        already_visible = ui.Workspace.show_window("Console")
        already_visible = ui.Workspace.show_window("Content") and already_visible
        already_visible = ui.Workspace.show_window("Layer") and already_visible
        already_visible = ui.Workspace.show_window("Main ToolBar") and already_visible
        already_visible = ui.Workspace.show_window("Property") and already_visible
        already_visible = ui.Workspace.show_window("RTX Settings") and already_visible
        already_visible = ui.Workspace.show_window("Stage") and already_visible
        already_visible = ui.Workspace.show_window("Viewport") and already_visible
        already_visible = ui.Workspace.show_window("Collection") and already_visible

        if not already_visible:
            # One of the windows is just created. ImGui needs to initialize it
            # to dock it. Wait one frame.
            await omni.kit.app.get_app().next_update_async()

        # Get windows
        console = ui.Workspace.get_window("Console")
        content = ui.Workspace.get_window("Content")
        dockspace = ui.Workspace.get_window("DockSpace")
        layer = ui.Workspace.get_window("Layer")
        main_toolbar = ui.Workspace.get_window("Main ToolBar")
        property = ui.Workspace.get_window("Property")
        rtx_settings = ui.Workspace.get_window("RTX Settings")
        stage = ui.Workspace.get_window("Stage")
        viewport = ui.Workspace.get_window("Viewport")
        collection = ui.Workspace.get_window("Collection")

        # Dock windows
        main_toolbar.dock_in(dockspace, ui.DockPosition.SAME)
        stage.dock_in(main_toolbar, ui.DockPosition.RIGHT, 0.31)
        content.dock_in(main_toolbar, ui.DockPosition.BOTTOM, 0.31)
        viewport.dock_in(main_toolbar, ui.DockPosition.RIGHT, 0.96)
        if console:
            console.dock_in(content, ui.DockPosition.SAME)
        property.dock_in(stage, ui.DockPosition.BOTTOM, 0.5)
        layer.dock_in(stage, ui.DockPosition.SAME)
        if rtx_settings:
            rtx_settings.dock_in(stage, ui.DockPosition.SAME)

        if collection:
            rtx_settings.dock_in(stage, ui.DockPosition.SAME)

        # Wait a frame to set docking order. We need it because ImGui needs the
        # window to be already created and docked.
        await omni.kit.app.get_app().next_update_async()

        stage.dock_order = 0
        layer.dock_order = 1
        collection.dock_order = 2

        content.dock_order = 0

        # Open default tab
        stage.focus()
        content.focus()

    async def __property_window(self):
        await omni.kit.app.get_app().next_update_async()
        import omni.kit.window.property as property_window_ext

        property_window = property_window_ext.get_window()
        property_window.set_scheme_delegate_layout(
            "Create Layout", ["path_prim", "material_prim", "xformable_prim", "shade_prim", "camera_prim"]
        )

    def _add_menu(self, *argv, **kwargs):
        new_menu = omni.kit.ui.get_editor_menu().add_item(*argv, **kwargs)
        self.menus.append(new_menu)
        return new_menu

    def _set_ui_hidden(self, hide):
        self._settings.set("/app/window/hideUi", hide)

    def _is_ui_hidden(self):
        return self._settings.get("/app/window/hideUi")

    def _on_toggle_ui(self):
        self._set_ui_hidden(not self._is_ui_hidden())

    def _on_fullscreen(self):
        display_mode_lock = self._settings.get("/app/window/displayModeLock")
        if display_mode_lock:
            # Always stay in fullscreen_mode, only hide or show UI.
            self._set_ui_hidden(not self._is_ui_hidden())
        else:
            # Only toggle fullscreen on/off when not display_mode_lock
            was_fullscreen = self._appwindow.is_fullscreen()
            self._appwindow.set_fullscreen(not was_fullscreen)

            # Always hide UI in fullscreen
            self._set_ui_hidden(not was_fullscreen)

    def _open_browser(self, path):
        import subprocess
        import platform

        if platform.system().lower() == "windows":
            webbrowser.open(path)
        else:
            # use native system level open, handles snap based browsers better
            subprocess.Popen(["xdg-open", path])

    def _open_web_file(self, path):
        filepath = os.path.abspath(path)
        if os.path.exists(filepath):
            self._open_browser("file://" + filepath)
        else:
            carb.log_warn("Failed to open " + filepath)

    def get_manual_url_path(self):
        manual_path = os.path.abspath(carb.tokens.get_tokens_interface().resolve("${app}/../docs/py/index.html"))
        if os.path.isfile(manual_path):
            return manual_path
        return None

    def __menu_update(self):
        self._viewport = None
        try:
            self._viewport = omni.kit.viewport.get_viewport_interface()
        except:
            pass
        self._appwindow = omni.appwindow.get_default_app_window()
        self._settings = carb.settings.get_settings()
        self._selection = omni.usd.get_context().get_selection()

        self.WINDOW_UI_TOGGLE_VISIBILITY_MENU = "Window/UI Toggle Visibility"
        self.WINDOW_FULLSCREEN_MODE_MENU = "Window/Fullscreen Mode"
        self.HELP_REFERENCE_GUIDE_MENU = (
            f'Help/{omni.kit.ui.get_custom_glyph_code("${glyphs}/cloud.svg")} Isaac Sim Online Guide'
        )
        self.HELP_SCRIPTING_MANUAL = (
            f'Help/{omni.kit.ui.get_custom_glyph_code("${glyphs}/book.svg")} Isaac Sim Scripting Manual'
        )
        self.HELP_FORUMS_URL = (
            f'Help/{omni.kit.ui.get_custom_glyph_code("${glyphs}/cloud.svg")} Isaac Sim Online Forums'
        )
        self.KIT_MANUAL = "Help/Kit Scripting Manual"
        self.menus = []

        # seperator
        priority = 50

        editor_menu = omni.kit.ui.get_editor_menu()

        window_ui_toggle_visibility_menu = editor_menu.add_item(
            self.WINDOW_UI_TOGGLE_VISIBILITY_MENU, None, priority=priority + 1
        )
        window_ui_toggle_visibility_action = omni.kit.menu.utils.add_action_to_menu(
            self.WINDOW_UI_TOGGLE_VISIBILITY_MENU, lambda *_: self._on_toggle_ui(), "UiToggle", (0, Key.F7)
        )
        self.menus.append((window_ui_toggle_visibility_menu, window_ui_toggle_visibility_action))

        window_fullscreen_mode_menu = editor_menu.add_item(
            self.WINDOW_FULLSCREEN_MODE_MENU, None, priority=priority + 2
        )
        window_fullscreen_mode_menu_action = omni.kit.menu.utils.add_action_to_menu(
            self.WINDOW_FULLSCREEN_MODE_MENU, lambda *_: self._on_fullscreen(), "FullscreenMode", (0, Key.F11)
        )
        self.menus.append((window_fullscreen_mode_menu, window_fullscreen_mode_menu_action))

        ref_guide_menu = editor_menu.add_item(self.HELP_REFERENCE_GUIDE_MENU, None, priority=-23)
        ref_guide_menu_action = omni.kit.menu.utils.add_action_to_menu(
            self.HELP_REFERENCE_GUIDE_MENU,
            lambda *_: self._open_browser(REFERENCE_GUIDE_URL),
            "OpenRefGuide",
            (0, Key.F1),
        )
        self.menus.append((ref_guide_menu, ref_guide_menu_action))

        manual_url_path = self.get_manual_url_path()
        self._add_menu(self.HELP_SCRIPTING_MANUAL, lambda *_: self._open_web_file(manual_url_path), priority=-22)
        if manual_url_path is None:
            editor_menu.set_enabled(self.HELP_SCRIPTING_MANUAL, False)

        forums_link = editor_menu.add_item(self.HELP_FORUMS_URL, None, priority=-21)
        forums_link_action = omni.kit.menu.utils.add_action_to_menu(
            self.HELP_FORUMS_URL, lambda *_: self._open_browser(FORUMS_URL), "OpenForums"
        )
        self.menus.append((forums_link, forums_link_action))

        kit_manual = editor_menu.add_item(self.KIT_MANUAL, None, priority=-9)
        kit_manual_action = omni.kit.menu.utils.add_action_to_menu(
            self.KIT_MANUAL, lambda *_: self._open_browser(KIT_MANUAL_URL), "OpenKitManual"
        )
        self.menus.append((kit_manual, kit_manual_action))

        # Sort top level menus:
        editor_menu.set_priority("Window", -6)
        editor_menu.set_priority("Help", 99)

        editor_menu.set_priority("Rendering/Render Settings", -100)
        editor_menu.set_priority("Rendering/Movie Capture", 100)

        # set omnu.ui Help Menu
        self._ui_doc_menu_path = "Help/Omni UI Docs"
        self._ui_doc_menu_item = editor_menu.add_item(self._ui_doc_menu_path, lambda *_: self._show_ui_docs())
        editor_menu.set_priority(self._ui_doc_menu_path, -10)

        # reset_menu_path = "Window/Layout/Reset Layout"
        # self._reset_menu = editor_menu.add_item(
        #     reset_menu_path, lambda *_: asyncio.ensure_future(self.__reset_layout())
        # )
        # editor_menu.set_priority(reset_menu_path, 10)

    def __add_app_icon(self, ext_id):
        ext_manager = omni.kit.app.get_app().get_extension_manager()
        extension_path = ext_manager.get_extension_path(ext_id)
        if sys.platform == "win32":
            pass
        else:
            user_apps_fodler = os.path.expanduser("~/.local/share/applications")
            if os.path.exists(user_apps_fodler):
                with open(os.path.expanduser("~/.local/share/applications/IsaacSim.desktop"), "w") as file:
                    omni.kit.app.get_app().print_and_log("Writing Isaac Sim icon file")
                    file.write(
                        f"""[Desktop Entry]
Version=1.0
Name=Isaac Sim
Icon={extension_path}/data/omni.isaac.sim.png
Terminal=false
Type=Application
StartupWMClass=IsaacSim"""
                    )

    def on_shutdown(self):
        if self._cancel_download_btn and self._cancel_download_btn.visible:
            self._on_cancel_download()
        self._ui_doc_menu_item = None
        self._launcher_menu = None
        self._reset_menu = None
        self._isaac_python_doc_menu_item = None
        remove_menu_items(self._menu_items, "Isaac Utils")
        self._server_window = None
        self._check_success = None
