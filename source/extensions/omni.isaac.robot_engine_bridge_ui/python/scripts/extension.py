import os
import carb
import omni.ext
import omni.ui
import omni.kit.menu

from .menu import RobotEngineBridgeMenu

EXTENSION_NAME = "Robot Engine Bridge UI"


class Extension(omni.ext.IExt):
    def on_startup(self, ext_id: str):
        self._menu = RobotEngineBridgeMenu()

    def on_shutdown(self):
        if self._menu is not None:
            self._menu.shutdown()
            self._menu = None
