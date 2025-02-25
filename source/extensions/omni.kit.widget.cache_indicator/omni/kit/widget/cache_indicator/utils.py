import base64
import json
import os
import platform
import subprocess
import urllib
import urllib.request
from pathlib import Path
from typing import Union
from urllib.error import *
from zipfile import ZipFile, ZipInfo

import carb
import carb.settings
import omni.client
import toml


def log_http_error(e, missing):
    msg = f"{missing} was not found. Can be a permission issue. Error: ${e}"
    if e.code in [401, 403, 404]:
        carb.log_warn(msg)
    else:
        carb.log_error(msg)


def try_post_notification(message, duration=3):
    try:
        from omni.kit.notification_manager import NotificationStatus, post_notification

        post_notification(message, duration=duration, status=NotificationStatus.INFO)
        return True
    except:
        carb.log_info("notification_manager not loaded.")
        pass
    return False


def try_post_warning(message, duration=3):
    try:
        from omni.kit.notification_manager import NotificationStatus, post_notification

        post_notification(message, duration=duration, status=NotificationStatus.WARNING)
        return True
    except:
        carb.log_info("notification_manager not loaded.")
        pass
    return False


# @lru_cache()
def is_windows():
    return platform.system().lower() == "windows"


def run_process(args):
    print(f"running process: {args}")
    kwargs = {"close_fds": False}
    if is_windows():
        kwargs["creationflags"] = subprocess.CREATE_NEW_CONSOLE | subprocess.CREATE_NEW_PROCESS_GROUP
    subprocess.Popen(args, **kwargs)


def os_pck_default_path() -> str:
    """
    Tries to get the default installation path for Windows/Linux
    """
    home = Path.home()
    if platform.system() == "Windows":
        return os.path.join(home, "AppData", "Local", "ov", "pkg")
    else:
        return os.path.join(home, ".local", "share", "ov", "pkg")


def get_omniverse_config() -> str:
    home = str(Path.home())
    return os.path.join(home, ".nvidia-omniverse", "config", "omniverse.toml")


def get_pck_install_folder(cfg_default_install_path: str, omniverse_config: str) -> str:
    """
    This goes through several steps to try to get the correct installation folder.
    1. Tries to check the extension.toml which contains the default and pass by flag arguments
    2. Tries to check if an environment variable with the name of HUBMANAGER_PCK_INSTALL_PATH exists and is not empty
    3. Tries to check if the omniverse.toml configuration file exists and if it contains the library_root key
    4. If any of these fails it will return the OS default folder
    """

    # print(f"CFG Path: {cfg_default_install_path}")

    # check if the path to install was passed in default config and/or by argument
    if len(cfg_default_install_path.strip()) > 0:
        carb.log_info(f"PCK Install folder found by passed arguments: {cfg_default_install_path}")
        return cfg_default_install_path.strip()

    # check if the path to install was passed in environment variable
    env_pck_path = os.environ.get("HUBMANAGER_PCK_INSTALL_PATH", "")
    if env_pck_path:
        carb.log_info(f"PCK Install folder found in environment variable (HUBMANAGER_PCK_INSTALL_PATH): {env_pck_path}")
        return env_pck_path

    carb.log_info(f"Path to Omniverse config: {omniverse_config}")

    if os.path.exists(omniverse_config):
        try:
            toml_contents = toml.load(omniverse_config)

            try:
                paths = toml_contents.get("paths")
                if paths is None:
                    carb.log_warn("No [paths] found in omniverse.toml")
                    return os_pck_default_path()

                library_root = paths.get("library_root")
                if library_root is None:
                    carb.log_warn("No library_root key found in omniverse.toml")
                    return os_pck_default_path()

                if len(library_root.strip()) == 0:
                    carb.log_warn("No library_root key valid in omniverse.toml")
                    return os_pck_default_path()

                if not os.path.exists(library_root):
                    carb.log_warn("No library_root key valid path in omniverse.toml")
                    return os_pck_default_path()

                carb.log_info(f"Found library_root in omniverse.toml: {library_root}")
                return library_root.strip()

            except KeyError as error:
                default_path = os_pck_default_path()
                carb.info_warn(
                    f"No [[paths.library_root]] entry in {omniverse_config.name} with error: {error}. Using default path: {default_path}"
                )
                return default_path
            except IndexError as error:
                default_path = os_pck_default_path()
                carb.info_warn(
                    f"[[paths.library_root]] in {omniverse_config.name} is empty but requires a module name, with error: {error}. Using default path: {default_path}"
                )
                return default_path

        except toml.TomlDecodeError as error:
            raise ValueError(f"Could not read {omniverse_config.name}") from error
    else:
        carb.log_info("omniverse.toml config file does not exist")
        return os_pck_default_path()


def get_token(api_key: str, org: str, team: str) -> str:
    """
    Returns the NGC auth token
    """

    # an empty api_key indicates that the user is pulling from
    # the public repository and so no auth is needed
    if not api_key:
        return ""

    # convert user:api_key to base64
    user_pass = f"$oauthtoken:{api_key}"
    string_bytes = user_pass.encode("utf-8")
    base64_bytes = base64.b64encode(string_bytes)
    auth_token = f"Basic {base64_bytes.decode('utf-8')}"

    headers = {"Content-Type": "application/json", "Accept": "application/json", "Authorization": auth_token}

    # Create a request object with the custom headers
    opener = urllib.request.build_opener()
    opener.addheaders = [(key, value) for key, value in headers.items()]

    url = f"https://authn.nvidia.com/token?service=ngc&scope=group/ngc:{org}&group/ngc:{org}/{team}"

    try:
        with opener.open(url) as response:
            data = response.read().decode("utf-8")

        json_data = json.loads(data)
        return json_data["token"]

    except HTTPError as e:
        log_http_error(e, "Hub script file")
    except Exception as e:
        carb.log_error(f"Error while trying to downloading hub script: ${e}")


class ZipFileWithPermissions(ZipFile):
    """Custom ZipFile class handling file permissions."""

    def _extract_member(self, member, targetpath, pwd):
        if not isinstance(member, ZipInfo):
            member = self.getinfo(member)

        targetpath = super()._extract_member(member, targetpath, pwd)

        attr = member.external_attr >> 16
        if attr != 0:
            os.chmod(targetpath, attr)
        return targetpath
