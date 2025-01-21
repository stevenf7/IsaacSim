import asyncio
import json
import os
import platform
import shutil
import stat
import tempfile
import time
import webbrowser
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Union

import aiohttp
import carb
import carb.settings
import omni.client
import toml
from omni import ui
from omni.kit.menu.utils import MenuAlignment, MenuItemDescription

from .semver import SemanticVersion
from .style import Styles
from .utils import (
    ZipFileWithPermissions,
    get_omniverse_config,
    get_pck_install_folder,
    get_token,
    log_http_error,
    try_post_notification,
)

VERSION_IS_HIGHER = 1  # semver value that represents when a version is higher


class UIState(Enum):
    HUB_RUNNING = 1
    HUB_NOT_DETECTED = 2
    HUB_INSTALLING = 3
    HUB_UPDATE_DETECTED = 4
    HUB_INSTALLED = 5


class CacheStateDelegate(ui.MenuDelegate):
    ngc_api_key = None
    ngc_token = None
    ngc_api = None
    ngc_org = None
    ngc_team = None
    ngc_resource = None
    check_updates = True
    pck_install_path = ""

    def __init__(self, cache_enabled, hub_enabled, **kwargs):
        super().__init__(**kwargs)

        self._hub_enabled = hub_enabled
        self._cache_enabled = cache_enabled
        self._cache_widget = None
        self.download_task = None
        self._installing = False
        self._hub_not_detected_button = None
        self._widget_width = 40
        self._state = UIState.HUB_NOT_DETECTED

        # get settings
        settings = carb.settings.get_settings()
        config = settings.get("/exts/omni.kit.widget.cache_indicator")
        self.ngc_api = config["ngc_api"]
        self.ngc_api_key = config["ngc_api_key"]
        self.ngc_org = config["ngc_org"]
        self.ngc_team = config["ngc_team"]
        self.check_updates = config["check_updates"]
        self.pck_install_path = config["pck_install_path"]
        self.ngc_resource = config["ngc_resource"]

    def ngc_path_prefix(self, org, team, resource) -> str:
        if self.ngc_api_key:
            return f"{self.ngc_api}/org/{org}/team/{team}/resources/{resource}"
        return f"{self.ngc_api}/resources/{org}/{team}/{resource}"

    def get_current_local_version(self) -> str:
        """
        Try to find the last installed version. By default, there should be only one, but...
        it's possible to be multiple versions, specially from Launcher days.
        """

        empty_version = "0.0.0"
        path = get_pck_install_folder(self.pck_install_path, get_omniverse_config())
        carb.log_info(f"Local install path found: {path} - {self.pck_install_path}")

        existing_versions = []
        if os.path.exists(path):
            for entry in os.listdir(path):
                entry_path = os.path.join(path, entry)

                # Check if it's a directory and its name starts with "hub-"
                if os.path.isdir(entry_path) and entry.startswith("hub-"):
                    existing_versions.append(entry)

        if len(existing_versions) == 0:
            return empty_version

        local_latest = empty_version
        for existing_version in existing_versions:
            # let's remove the 'hub-' part so that we can do semver comparison
            version = existing_version.replace("hub-", "")

            try:
                parsed_version = SemanticVersion.parse(version)
                parsed_local_latest = SemanticVersion.parse(local_latest)
                if parsed_version.compare(parsed_local_latest) == VERSION_IS_HIGHER:
                    local_latest = version.strip()
            except ValueError as e:
                carb.log_error(f"Not a semver. Error: {e}. Skipping...")
                continue

        carb.log_info(f"Local Latest: {local_latest}")

        return local_latest

    async def check_new_version(self):
        """
        Check differences between latest local and remote local and update the UI accordingly
        """
        if self.check_updates is False:
            return

        latest_version = await self.get_latest_version()
        carb.log_info(f"check_new_version: {latest_version}")
        if latest_version == "":
            return

        carb.log_info(f"Latest version found: {latest_version}")

        current_local_version = self.get_current_local_version()
        carb.log_info(f"Current local version found: {current_local_version}")

        try:
            parsed_latest_version = SemanticVersion.parse(latest_version)
            parsed_current_local_version = SemanticVersion.parse(current_local_version)
            if parsed_latest_version.compare(parsed_current_local_version) == VERSION_IS_HIGHER:
                self.toggle_ui_state(UIState.HUB_UPDATE_DETECTED)
        except ValueError as e:
            carb.log_error(f"Not a semver. Error: {e}. Skipping...")

    async def get_latest_version(self) -> str:
        """
        Uses NGC API to see if there is a new version of a specific file
        """

        carb.log_info(f"Lets check if there is a new version on resource: {self.ngc_resource}")
        uri = f"{self.ngc_path_prefix(self.ngc_org, self.ngc_team, self.ngc_resource)}/versions?page-size=3&page-number=0&sort-order=CREATED_DATE_DESC"
        carb.log_info(f"get_latest_version URI: {uri}")

        try:
            self.ngc_token = get_token(self.ngc_api_key, self.ngc_org, self.ngc_team)

            # example of what API partially returns
            # "recipeVersions": [
            #     {
            #         "status": "UPLOAD_COMPLETE",
            #         "totalSizeInBytes": 72943407,
            #         "totalFileCount": 1,
            #         "versionId": "2024.1.0-beta.5+3f5eaec6",
            #         "createdByUser": "7m11rd5vf86ceraaagh56b557p",
            #         "createdDate": "2024-11-05T15:41:52.498Z"
            #     }
            # ],

            json_data = None
            async with self.create_session_with_headers(self.ngc_token) as client:
                async with client.get(uri) as response:
                    if response.ok:
                        json_data = await response.json()

            if (
                json_data is not None
                and json_data.get("recipeVersions") is not None
                and len(json_data.get("recipeVersions")) > 0
            ):
                latest = json_data["recipeVersions"][0]
                if latest.get("status") == "UPLOAD_COMPLETE" and latest.get("totalSizeInBytes") > 0:
                    return latest.get("versionId")
                else:
                    return ""
            else:
                return ""
        except Exception as e:
            carb.log_warn(f"Error while checking if new version is available: {e}")
        return ""

    def destroy(self):
        self._cache_widget = None

    def build_item(self, item: ui.MenuHelper):
        with ui.HStack(width=0, style={"margin": 0}):
            self._cache_widget = ui.HStack(content_clipping=1, width=0, style=Styles.CACHE_STATE_ITEM_STYLE)
            ui.Spacer(width=10)

        self.update_cache_state(self._cache_enabled, self._hub_enabled)
        if self._hub_enabled:
            self.toggle_ui_state(UIState.HUB_RUNNING)
        else:
            self.toggle_ui_state(UIState.HUB_NOT_DETECTED)

        asyncio.ensure_future(self.check_new_version())

    def get_menu_alignment(self):
        return MenuAlignment.RIGHT

    def update_menu_item(self, menu_item: Union[ui.Menu, ui.MenuItem], menu_refresh: bool):
        if isinstance(menu_item, ui.MenuItem):
            menu_item.visible = False

    def create_session_with_headers(self, token: str):
        # Define custom headers
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if token:
            headers["Authorization"] = f"Bearer {token}"

        return aiohttp.ClientSession(headers=headers)

    async def download_file(self, resource: str, version: str, filename: str, download_to: str) -> None:
        uri = f"{self.ngc_path_prefix(self.ngc_org, self.ngc_team, resource)}/versions/{version}/files/{filename}"
        carb.log_info(f"download_file URI: {uri}")

        try:
            async with self.create_session_with_headers(self.ngc_token) as client:
                async with client.get(uri) as response:
                    if response.ok:
                        content = await response.read()
                        with open(download_to, "wb") as out_file:
                            out_file.write(content)
                    else:
                        carb.log_error(f"Error downloading the file with code {response.code}: {response.reason}")
        except Exception as e:
            carb.log_error(f"Error downloading the file: {e}")

    async def check_latest_hub_version(self, resource: str) -> str:
        carb.log_info(f"check_latest_hub_version {resource}")

        uri = f"{self.ngc_path_prefix(self.ngc_org, self.ngc_team, resource)}/versions?page-size=100&page-number=0&sort-order=CREATED_DATE_DESC"
        carb.log_info(f"check_latest_hub_version URI: {uri}")

        try:
            json_data = None
            async with self.create_session_with_headers(self.ngc_token) as client:
                async with client.get(uri) as response:
                    if response.ok:
                        json_data = await response.json()

            if json_data:
                versions = []
                for item in json_data["recipeVersions"]:
                    versions.append(item["versionId"])

                return versions[0]
            return ""

        except HTTPError as e:
            log_http_error(e, "Hub installation package")
        except Exception as e:
            carb.log_error(f"Error while downloading hub: ${e}")
        return ""

    def move_folder(self, source_folder, destination_folder) -> None:
        try:
            # Move the entire folder (including its contents) to the destination
            shutil.move(source_folder, destination_folder)
            carb.log_info(f"Folder '{source_folder}' moved to '{destination_folder}'")
        except Exception as e:
            carb.log_info(f"Error moving folder: {e}")

    async def get_correct_file(self, ngc_resource: str, hub_version: str) -> str:
        uri = f"{self.ngc_path_prefix(self.ngc_org, self.ngc_team, ngc_resource)}/versions/{hub_version}/files"
        carb.log_info(f"get_correct_file URI: {uri}")

        # {
        #     "sizeInBytes": 72942649,
        #     "path": "omni_hub.windows-x86_64@2024.1.0-beta.6+30030c02.zip",
        #     "createdDate": "2024-11-25T20:22:12.751Z"
        # }

        platform_name = platform.system()
        os_arch = "omni_hub.windows-x86_64"
        if platform_name == "Linux":
            os_arch = "omni_hub.linux-x86_64"

        try:
            json_data = None
            versions_os_available = {}
            async with self.create_session_with_headers(self.ngc_token) as client:
                async with client.get(uri) as response:
                    if response.ok:
                        json_data = await response.json()

            if json_data is not None and json_data.get("recipeFiles") is not None:
                for item in json_data.get("recipeFiles"):
                    if item.get("path") is not None and item.get("createdDate") is not None:
                        filename = str(item.get("path"))
                        if os_arch in filename and hub_version in filename:
                            # lets add to the dictionary the file with the createdDate so that we can sort it later
                            versions_os_available[filename] = item.get("createdDate")

            if len(versions_os_available) == 1:
                latest = list(versions_os_available.keys())[0]
                carb.log_info(f"Found correct version: {latest}")
                return latest

            # sort all the versions to get the most recent one, based on the creation date
            sorted_versions = dict(
                sorted(
                    versions_os_available.items(),
                    key=lambda item: datetime.strptime(item[1], "%Y-%m-%dT%H:%M:%S.%fZ"),
                    reverse=True,
                )
            )
            latest = list(sorted_versions.keys())[0]
            carb.log_info(f"Found correct sorted version: {latest}")

            return latest
        except Exception as e:
            carb.log_error(f"Error getting proper file: ${e}")
        return ""

    async def _on_download_hub(self) -> None:
        """This event will trigger the download of Hub"""
        try_post_notification("Downloading hub.", duration=3)
        self.toggle_ui_state(UIState.HUB_INSTALLING)

        try:
            # get NGC token
            self.ngc_token = get_token(self.ngc_api_key, self.ngc_org, self.ngc_team)

            hub_version = await self.check_latest_hub_version(self.ngc_resource)

            if hub_version is None:
                carb.log_info(f"Could not get Hub latest version.")
                return

            carb.log_info(f"Hub version found {hub_version}")

            file = await self.get_correct_file(self.ngc_resource, hub_version)
            temp_path = os.path.join(tempfile.gettempdir(), file)

            carb.log_info(f"Downloading hub {file} from: NGC, to: {temp_path}")

            await self.download_file(self.ngc_resource, hub_version, file, temp_path)

            try_post_notification("Installing hub.", duration=3)

            st = os.stat(temp_path)

            carb.log_info(f"Running installed hub script from {temp_path}")
            os.chmod(temp_path, st.st_mode | stat.S_IEXEC)

            try_post_notification("Extracting.", duration=3)

            final = os.path.join(tempfile.gettempdir(), f"hub-{hub_version}")

            with ZipFileWithPermissions(temp_path, "r") as zip_ref:
                zip_ref.extractall(final)

            library_root = get_pck_install_folder(self.pck_install_path, get_omniverse_config())

            if not os.path.exists(library_root):
                os.makedirs(library_root)

            self.move_folder(final, library_root)

            # create the .installed path
            installed_path = os.path.join(library_root, f"hub-{hub_version}", ".installed")
            with open(installed_path, "w"):
                carb.log_info(f"Empty file created: {installed_path}")

            self.toggle_ui_state(UIState.HUB_INSTALLED)
            # show a popup to the user informing about the end of installation process
            omni.kit.app.get_app().try_cancel_shutdown(
                reason="Hub installation: Asking for User confirmation to restart."
            )
            asyncio.ensure_future(self._prompt_for_confirmation_to_quit())

        except Exception as e:
            carb.log_error(f"Error while downloading hub: ${e}")

    async def _prompt_for_confirmation_to_quit(self) -> None:
        """Inform the user that the installation was successful."""

        def on_close() -> None:
            self._proceed_to_close = True

        try:
            from omni.kit.widget.prompt import Prompt

            confirm_dialog = Prompt(
                title=f"{omni.kit.ui.get_custom_glyph_code('${glyphs}/exclamation.svg')} Hub installed!",
                text="Hub has been installed. For these new installation to take effect, please restart your application.",
                ok_button_text="Ok",
                ok_button_fn=on_close,
                cancel_button_fn=lambda: confirm_dialog.hide(),
                modal=True,
            )
            confirm_dialog.show()
        except:
            pass

    async def _on_settings_open(self):
        url = self.get_hub_settings_url()

        try_post_notification("open cache settings", duration=4)

        # check if hub settings url is working
        try:
            async with self.create_session_with_headers(self.ngc_token) as client:
                async with client.get(url) as response:
                    if response.ok:
                        carb.log_info(f"Hub settings opening on: {url}")
                        webbrowser.open(url)
        except Exception as e:
            carb.log_error(f"Could not open Hub settings on {url}, {e}")

    def get_hub_settings_url(self):
        home = str(Path.home())

        omniverse_config = f"{home}/.nvidia-omniverse/config/omniverse.toml"

        try:
            toml_contents = toml.load(omniverse_config)
            port = 0

            try:
                cache_path = toml_contents["paths"]["cache_root"]
                hub_cache_port_file = f"{cache_path}/hub/hub.port"

                with open(hub_cache_port_file) as f:
                    port = f.readline().strip()
                url = f"http://localhost:{port}/index.html"
                return url
            except KeyError as error:
                raise ValueError(f"No [[paths.cache_root]] entry in {omniverse_config}") from error
            except IndexError as error:
                raise ValueError(
                    f"[[paths.cache_root]] in {omniverse_config} is empty but requires a module name"
                ) from error

        except toml.TomlDecodeError as error:
            raise ValueError(f"Could not read {omniverse_config}") from error
        except FileNotFoundError as error:
            carb.log_info(f"Could not read {omniverse_config}")
            return "http://127.0.0.1:14090"

    def toggle_ui_state(self, state: UIState):
        try:
            if self._state == UIState.HUB_INSTALLED:
                carb.log_info(f"Asked to set {state} but current state is {self._state}, rejecting state change")
                state = self._state
            else:
                carb.log_info(f"Changing UI to state: {state}")
            match state:
                case UIState.HUB_NOT_DETECTED:
                    self._hub_label0.visible = False
                    self._hub_label1.visible = False
                    self._hub_settings_button.visible = False
                    self._hub_not_detected_button.visible = True
                    self._hub_update_button.visible = False
                    self._is_downloading_label.visible = False
                    self._progress_bar.visible = False
                    self._is_installed_label.visible = False
                    self._widget_width = 200
                case UIState.HUB_INSTALLING:
                    self._hub_label0.visible = False
                    self._hub_label1.visible = False
                    self._hub_settings_button.visible = False
                    self._hub_not_detected_button.visible = False
                    self._hub_update_button.visible = False
                    self._is_downloading_label.visible = True
                    # self._progress_bar.visible = False
                    self._is_installed_label.visible = False
                    self._widget_width = 200
                case UIState.HUB_RUNNING:
                    self._hub_label0.visible = True
                    self._hub_label1.visible = True
                    self._hub_settings_button.visible = True
                    self._hub_not_detected_button.visible = False
                    self._hub_update_button.visible = False
                    self._is_downloading_label.visible = False
                    self._progress_bar.visible = False
                    self._is_installed_label.visible = False
                    self._widget_width = 40
                case UIState.HUB_UPDATE_DETECTED:
                    self._hub_label0.visible = False
                    self._hub_label1.visible = False
                    self._hub_settings_button.visible = False
                    self._hub_not_detected_button.visible = False
                    self._hub_update_button.visible = True
                    self._is_downloading_label.visible = False
                    self._progress_bar.visible = False
                    self._is_installed_label.visible = False
                    self._widget_width = 200
                case UIState.HUB_INSTALLED:
                    self._hub_label0.visible = False
                    self._hub_label1.visible = False
                    self._hub_settings_button.visible = False
                    self._hub_not_detected_button.visible = False
                    self._hub_update_button.visible = False
                    self._is_downloading_label.visible = False
                    self._progress_bar.visible = False
                    self._is_installed_label.visible = True
                    self._widget_width = 200
                case _:
                    carb.log_warn(f"Received some weird state in UIState: {state}")
                    return
            self._state = state
        except Exception as e:
            carb.log_info(f"UI was not loaded yet {e}")

    def update_cache_state(self, cache_enabled: bool, hub_enabled: bool):
        """Updates cache state and UI"""
        carb.log_info(f"update_cache_state: Hub Enabled: {hub_enabled}, Cache Enable: {cache_enabled}")

        self._hub_enabled = hub_enabled
        self._cache_enabled = cache_enabled

        if not self._cache_widget:
            return

        self._cache_widget.clear()
        with self._cache_widget:
            ui.Label("CACHE: ")
            with ui.HStack(width=self._widget_width):
                # HUB installing
                self._is_downloading_label = ui.Label(
                    "Downloading... Please wait.", style={"color": 0xFFFF9E3D}, visible=False
                )

                self._progress_bar = ui.ProgressBar(
                    tooltip="Downloading Hub. Please wait.",
                    style={"margin": 0, "height": 10, "font_size": 14, "color": 0xFFFF9E3D},
                    visible=False,
                )

                on_settings_open = lambda: asyncio.ensure_future(self._on_settings_open())
                on_download_hub = lambda: asyncio.ensure_future(self._on_download_hub())

                # HUB RUNNING
                self._hub_label0 = ui.Label("ON", visible=False)
                self._hub_label1 = ui.Label("|", visible=False)
                self._hub_settings_button = ui.Button("SET", style={"color": 0xFF00B86B}, visible=False)
                self._hub_settings_button.set_clicked_fn(on_settings_open)

                # HUB NOT DETECTED
                self._hub_not_detected_button = ui.Button(
                    "HUB NOT DETECTED", tooltip="Click to download and install", visible=False
                )
                self._hub_not_detected_button.set_clicked_fn(on_download_hub)

                # HUB NEW VERSION
                self._hub_update_button = ui.Button(
                    "NEW VERSION DETECTED", style={"color": 0xFF00B86B}, tooltip="Click to update", visible=False
                )
                self._hub_update_button.set_clicked_fn(on_download_hub)

                # HUB INSTALLED
                self._is_installed_label = ui.Label(
                    "Installed... Please restart.", style={"color": 0xFFFF9E3D}, visible=False
                )


class CacheStateMenu:
    def __init__(self):
        self._live_menu_name = "Cache State Widget"
        self._menu_list = [MenuItemDescription(name="placeholder", show_fn=lambda: False)]

        global_config_path = carb.tokens.get_tokens_interface().resolve("${omni_global_config}")
        self._omniverse_config_path = os.path.join(global_config_path, "omniverse.toml").replace("\\", "/")
        self._all_cache_apis = []
        self._hub_enabled = False
        self._cache_enabled = False
        self._last_time_check = 0
        self._ping_cache_future = None
        self._update_subscription = None
        self._cache_state_delegate = None

    def _load_cache_config(self):
        if os.path.exists(self._omniverse_config_path):
            try:
                contents = toml.load(self._omniverse_config_path)
            except Exception as e:
                carb.log_error(f"Unable to parse {self._omniverse_config_path}. File corrupted?")
                contents = None

            if contents:
                self._all_cache_apis = self._load_all_cache_server_apis(contents)
                if self._all_cache_apis:
                    self._cache_enabled = True
                    self._update_subscription = (
                        omni.kit.app.get_app()
                        .get_update_event_stream()
                        .create_subscription_to_pop(self._on_update, name="omni.kit.widget.live update")
                    )
                else:
                    carb.log_warn(
                        "Unable to detect Omniverse Cache Server. Consider installing it for better IO performance."
                    )
                    self._cache_enabled = False
        else:
            carb.log_warn(
                f"Unable to detect Omniverse Cache Server. File {self._omniverse_config_path} is not found."
                f" Consider installing it for better IO performance."
            )

    def _get_hub_version_cb(self, result, version):
        if result == omni.client.Result.OK:
            self._hub_enabled = True
        else:
            self._hub_enabled = False
            self._load_cache_config()
        if self._cache_state_delegate:
            carb.log_info(f"_cb HUB: {self._hub_enabled}, CACHE: {self._cache_enabled}, VERSION: {version}")
            self._cache_state_delegate.update_cache_state(self._cache_enabled, self._hub_enabled)
            if self._hub_enabled:
                self._cache_state_delegate.toggle_ui_state(UIState.HUB_RUNNING)
            pass

    def _initialize(self):
        self._get_hub_version_request = omni.client.get_hub_version_with_callback(self._get_hub_version_cb)

    def register_menu_widgets(self):
        self._initialize()

        carb.log_info(f"Cache Enable: {self._cache_enabled}, Hub Enable: {self._hub_enabled}")
        self._cache_state_delegate = CacheStateDelegate(self._cache_enabled, self._hub_enabled)
        omni.kit.menu.utils.add_menu_items(
            self._menu_list, name=self._live_menu_name, delegate=self._cache_state_delegate
        )

    def unregister_menu_widgets(self):
        omni.kit.menu.utils.remove_menu_items(self._menu_list, self._live_menu_name)
        if self._cache_state_delegate:
            self._cache_state_delegate.destroy()
        self._cache_state_delegate = None
        self._menu_list = None
        self._update_subscription = None
        self._all_cache_apis = []

        try:
            if self._ping_cache_future and not self._ping_cache_future.done():
                self._ping_cache_future.cancel()
                self._ping_cache_future = None
        except Exception:
            self._ping_cache_future = None

    def _on_update(self, dt):
        if not self._cache_state_delegate or not self._all_cache_apis:
            return

        if not self._ping_cache_future or self._ping_cache_future.done():
            now = time.monotonic()
            duration = now - self._last_time_check

            # 30s
            if duration < 30:
                return

            self._last_time_check = now

            async def _ping_cache():
                async with aiohttp.ClientSession() as session:

                    cache_enabled = None
                    for cache_api in self._all_cache_apis:
                        try:
                            async with session.head(cache_api):
                                """If we're here the service port is alive"""
                                cache_enabled = True
                        except Exception as e:
                            cache_enabled = False
                            break

                if cache_enabled is not None and self._cache_enabled != cache_enabled:
                    self._cache_enabled = cache_enabled
                    if self._cache_state_delegate:
                        self._cache_state_delegate.toggle_ui_state(UIState.HUB_NOT_DETECTED)

            self._ping_cache_future = asyncio.ensure_future(_ping_cache())

    def _load_all_cache_server_apis(self, config_contents):
        mapping = os.environ.get("OMNI_CONN_CACHE", None)
        if mapping:
            mapping = f"*#{mapping},f"
        else:
            mapping = os.environ.get("OMNI_CONN_REDIRECTION_DICT", None)
            if not mapping:
                mapping = os.environ.get("OM_REDIRECTION_DICT", None)

            if not mapping:
                connection_library_dict = config_contents.get("connection_library", None)
                if connection_library_dict:
                    mapping = connection_library_dict.get("proxy_dict", None)

        all_proxy_apis = set([])
        if mapping:
            mapping = mapping.lstrip('"')
            mapping = mapping.rstrip('"')
            mapping = mapping.lstrip("'")
            mapping = mapping.rstrip("'")

            redirections = mapping.split(";")
            for redirection in redirections:
                parts = redirection.split("#")
                if not parts or len(parts) < 2:
                    continue

                source, target = parts[0], parts[1]
                targets = target.split(",")
                if not targets:
                    continue

                if len(targets) > 1:
                    proxy_address = targets[0]
                else:
                    proxy_address = target

                if not proxy_address.startswith("http://") and not proxy_address.startswith("https://"):
                    proxy_address_api = f"http://{proxy_address}/ping"
                else:
                    if proxy_address.endswith("/"):
                        proxy_address_api = f"{proxy_address}ping"
                    else:
                        proxy_address_api = f"{proxy_address}/ping"
                all_proxy_apis.add(proxy_address_api)

        return all_proxy_apis
