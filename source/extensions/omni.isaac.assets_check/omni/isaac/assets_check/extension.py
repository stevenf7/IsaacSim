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
from omni.client._omniclient import Result, CopyBehavior
from omni.kit.menu.utils import add_menu_items, remove_menu_items, MenuItemDescription


DOCS_URL = "https://docs.omniverse.nvidia.com"
ASSETS_GUIDE_URL = DOCS_URL + "/app_isaacsim/app_isaacsim/install_basic.html#isaac-sim-first-run"


class Extension(omni.ext.IExt):
    """Create Final Configuration"""

    def on_startup(self, ext_id: str):
        """ setup the window layout, menu, final configuration of the extensions etc """
        self._settings = carb.settings.get_settings()

        # this is a work around as some Extensions don't properly setup their default setting in time
        self._set_defaults()

        self._menu_items = [MenuItemDescription(name="Nucleus Check", onclick_fn=self._menu_callback)]
        add_menu_items(self._menu_items, "Isaac Utils")

        self.__await_new_scene = asyncio.ensure_future(self._nucleus_check_window())

    def _set_defaults(self):
        # do not display sever check pop-up on start up
        nucleus_check = carb.settings.get_settings().get("/exts/omni.isaac.assets_check/nucleusCheck")
        self._settings.set_default("/persistent/exts/omni.isaac.assets_check/nucleusCheck", nucleus_check)
        self._startup_run = True
        self._cancel_download_btn = None
        self._server_window = None
        self._check_success = None
        self.nucleus_check_result = Result.OK

        # get download assets defaults
        copy_assetsURL = carb.settings.get_settings().get("/exts/omni.isaac.assets_check/copyAssetsURL")
        self._settings.set_default("/persistent/exts/omni.isaac.assets_check/copyAssetsURL", copy_assetsURL)
        copy_concurrency = carb.settings.get_settings().get("/exts/omni.isaac.assets_check/copyConcurrency")
        self._settings.set_default("/persistent/exts/omni.isaac.assets_check/copyConcurrency", copy_concurrency)
        copy_behaviour = carb.settings.get_settings().get("/exts/omni.isaac.assets_check/copyBehaviour")
        self._settings.set_default("/persistent/exts/omni.isaac.assets_check/copyBehaviour", copy_behaviour)
        copy_after_delete = carb.settings.get_settings().get("/exts/omni.isaac.assets_check/copyAfterDelete")
        self._settings.set_default("/persistent/exts/omni.isaac.assets_check/copyAfterDelete", copy_after_delete)
        copy_timeout = carb.settings.get_settings().get("/exts/omni.isaac.assets_check/copyTimeout")
        self._settings.set_default("/persistent/exts/omni.isaac.assets_check/copyTimeout", copy_timeout)

    def _open_browser(self, path):
        import subprocess
        import platform

        if platform.system().lower() == "windows":
            webbrowser.open(path)
        else:
            # use native system level open, handles snap based browsers better
            subprocess.Popen(["xdg-open", path])

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
        nucleus_check = carb.settings.get_settings().get("/persistent/exts/omni.isaac.assets_check/nucleusCheck")
        self._check_success = ui.Window(
            "Isaac Sim Assets Check Successful",
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
                ui.Label("Isaac Sim assets found:", style={"font_size": 18}, alignment=ui.Alignment.CENTER)
                ui.Label("{}".format(self.nucleus_server), style={"font_size": 18}, alignment=ui.Alignment.CENTER)
                ui.Spacer(height=5)
                ui.Button(
                    "OK", spacing=10, alignment=ui.Alignment.CENTER, clicked_fn=lambda w=self._check_success: hide(w)
                )
                ui.Spacer(height=5)
                ui.Line()
                ui.Spacer(height=5)
                with ui.HStack(spacing=5, width=0, height=0):
                    ui.Label("Perform assets check on startup")
                    server_model = ui.CheckBox().model
                    server_model.set_value(nucleus_check)
                    server_model.add_value_changed_fn(
                        lambda m: carb.settings.get_settings().set_bool(
                            "/persistent/exts/omni.isaac.assets_check/nucleusCheck", m.get_value_as_bool()
                        )
                    )
                ui.Spacer()

        await omni.kit.app.get_app().next_update_async()

    async def _nucleus_check_window(self):
        # Check Nucleus server for assets
        nucleus_check = carb.settings.get_settings().get("/persistent/exts/omni.isaac.assets_check/nucleusCheck")
        # copy_after_delete = carb.settings.get_settings().get("/persistent/exts/omni.isaac.assets_check/copyAfterDelete")

        if nucleus_check is False and self._startup_run:
            self._startup_run = False
            pass
        else:
            from omni.isaac.core.utils.nucleus import get_assets_root_path

            omni.kit.app.get_app().print_and_log("Checking for Isaac Sim assets...")
            self._check_window = ui.Window("Check Isaac Sim assets", height=120, width=500)
            with self._check_window.frame:
                with ui.VStack(height=80):
                    ui.Spacer()
                    ui.Label("Checking for Isaac Sim assets", alignment=ui.Alignment.CENTER, style={"font_size": 18})
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

            # self.nucleus_check_result, self.nucleus_server = await find_nucleus_server_async("/Isaac", 20)

            self.nucleus_server = get_assets_root_path()

            # read persistent settings
            # copy_assetsURL = carb.settings.get_settings().get_as_string(
            #     "/persistent/exts/omni.isaac.assets_check/copyAssetsURL"
            # )
            # self.mount_version = ""
            # if self.nucleus_check_result is Result.OK or self.nucleus_check_result is Result.OK_NOT_YET_FOUND:
            #     self.nucleus_check_result, self.mount_version = await check_assets_version_async(
            #         copy_assetsURL, self.nucleus_server, "/Isaac"
            #     )
            self._check_window.visible = False
            self._check_window = None
            if self.nucleus_server is None:
                self._startup_run = False

                frame_height = 150
                self._server_window = ui.Window(
                    "Checking Isaac Sim Assets", width=350, height=frame_height, visible=True
                )
                with self._server_window.frame:
                    with ui.VStack():
                        ui.Label("Warning: Isaac Sim assets not found", style={"color": 0xFF00FFFF})
                        ui.Line()
                        ui.Label("See the documentation for details")
                        ui.Button("Open Documentation", clicked_fn=lambda: self._open_browser(ASSETS_GUIDE_URL))
                        ui.Spacer()
                        ui.Label("See terminal for additional information")
                        ui.Line()
                        with ui.HStack(spacing=5, width=0, height=0):
                            ui.Label("Perform Nucleus check on startup")
                            server_model = ui.CheckBox().model
                            server_model.set_value(nucleus_check)
                            server_model.add_value_changed_fn(
                                lambda m: carb.settings.get_settings().set_bool(
                                    "/persistent/exts/omni.isaac.assets_check/nucleusCheck", m.get_value_as_bool()
                                )
                            )
            else:
                omni.kit.app.get_app().print_and_log(f"Isaac Sim assets found: {self.nucleus_server}")
                if not self._startup_run:
                    asyncio.ensure_future(self._nucleus_check_success_window())
                self._startup_run = False

    def _on_download_assets(self):
        self._download_btn.visible = False
        self._cancel_download_btn.visible = True
        self._asset_download_error_label.visible = False
        self._download_task = asyncio.ensure_future(self._on_download_assets_async())
        omni.kit.app.get_app().print_and_log(f"Assets downloading to {self.nucleus_server} ...")

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
            "/persistent/exts/omni.isaac.assets_check/copyAssetsURL"
        )
        copy_concurrency = int(
            carb.settings.get_settings().get("/persistent/exts/omni.isaac.assets_check/copyConcurrency")
        )
        copy_timeout = float(carb.settings.get_settings().get("/persistent/exts/omni.isaac.assets_check/copyTimeout"))
        copy_behaviour_str = carb.settings.get_settings().get_as_string(
            "/persistent/exts/omni.isaac.assets_check/copyBehaviour"
        )
        if copy_behaviour_str == "CopyBehavior.OVERWRITE":
            copy_behaviour = CopyBehavior.OVERWRITE
        elif copy_behaviour_str == "CopyBehavior.ERROR_IF_EXISTS":
            copy_behaviour = CopyBehavior.ERROR_IF_EXISTS
        else:
            copy_behaviour = None
        copy_after_delete = carb.settings.get_settings().get("/persistent/exts/omni.isaac.assets_check/copyAfterDelete")

        # import download_assets_async only if nucleus_check is enabled
        from omni.isaac.core.utils.nucleus import download_assets_async

        result = await download_assets_async(
            copy_assetsURL,
            self.nucleus_server,
            progress_callback,
            copy_concurrency,
            copy_behaviour,
            copy_after_delete,
            copy_timeout,
        )
        if result != Result.OK:
            omni.kit.app.get_app().print_and_log(
                f"Assets download interrupted! Check your Internet connection and try downloading again."
            )
            self._download_btn.visible = True
            self._cancel_download_btn.visible = False
            self._asset_download_error_label.visible = True
            return result
        else:
            omni.kit.app.get_app().print_and_log(f"Assets download to {self.nucleus_server} completed!")
            self.nucleus_check_result = Result.OK
            self._download_label.visible = False
            self._download_btn.visible = False
            self._cancel_download_btn.visible = False
            self._downloaded_label.visible = True
            self._progress_bar_label.visible = False
            self._completed_label.visible = True
            self._asset_download_error_label.visible = False
            return result

    def on_shutdown(self):
        if self._cancel_download_btn and self._cancel_download_btn.visible:
            self._on_cancel_download()
        remove_menu_items(self._menu_items, "Isaac Utils")
        self._server_window = None
        self._check_success = None
