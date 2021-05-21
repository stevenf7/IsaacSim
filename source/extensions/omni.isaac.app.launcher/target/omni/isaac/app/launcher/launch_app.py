import os
import sys
from .settings import DEFAULT_APP_SETTING, SHOW_CONSOLE_SETTING

from typing import Dict, Any
import carb.settings
import carb.tokens

import omni.kit.app


def launch_app(app_id: str, app_version: str, app_become_new_default=False, close_on_launch=False):
    """ show the omniverse ui documentation as an external Application """
    _settings = carb.settings.get_settings()

    # update default
    if app_become_new_default:
        _settings.set(DEFAULT_APP_SETTING, app_id)

    import subprocess
    import platform

    app_folder = _settings.get_as_string("/app/folder")
    if app_folder == "":
        app_folder = carb.tokens.get_tokens_interface().resolve("${app}")

    script_extension = "bat"
    if not sys.platform == "win32":
        script_extension = "sh"

    app_execFile = app_id
    ext_manager = omni.kit.app.get_app().get_extension_manager()
    ext_dict = ext_manager.get_extension_dict(f"{app_id}-{app_version}")
    if ext_dict:
        app_execFile = ext_dict["package"]["execFile"]

    app_launch_folder = os.path.normpath(os.path.join(app_folder, os.pardir))
    launch_args = [f"{app_launch_folder}/{app_execFile}.{script_extension}"]

    kwargs: Dict[str, Any] = {"close_fds": False}
    if platform.system().lower() == "windows":
        kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
        if _settings.get(SHOW_CONSOLE_SETTING):
            kwargs["creationflags"] |= subprocess.CREATE_NEW_CONSOLE
    else:
        if _settings.get(SHOW_CONSOLE_SETTING):
            kwargs["shell"] = True
            launch_args = f"gnome-terminal -- {launch_args[0]}"
    subprocess.Popen(launch_args, **kwargs)

    if close_on_launch:
        omni.kit.app.get_app().post_quit()
