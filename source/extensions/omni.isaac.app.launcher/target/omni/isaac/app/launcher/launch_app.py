import os
from .settings import DEFAULT_APP_SETTING, SHOW_CONSOLE_SETTING

from typing import Dict, Any
import carb.settings

import omni.kit.app


def launch_app(app_id: str, app_become_new_default=False, close_on_launch=False):
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

    launch_args = [f"{app_folder}/../{app_id}.bat"]

    kwargs: Dict[str, Any] = {"close_fds": False}
    if platform.system().lower() == "windows":
        kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
        if _settings.get(SHOW_CONSOLE_SETTING):
            kwargs["creationflags"] |= subprocess.CREATE_NEW_CONSOLE

    subprocess.Popen(launch_args, **kwargs)

    if close_on_launch:
        omni.kit.app.get_app().post_quit()
