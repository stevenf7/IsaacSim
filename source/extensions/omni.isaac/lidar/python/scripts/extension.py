import os
import sys

import omni.ext
from .. import _lidar
from .menu import LidarMenu

EXTENSION_NAME = "Lidar"


class Extension(omni.ext.IExt):
    def on_startup(self):
        print("Starting Lidar extension")
        self._lidar = _lidar.acquire_lidar_interface()

        self._menu = LidarMenu()

    def on_shutdown(self):
        self._menu.shutdown()
        self._menu = None
        _lidar.release_lidar_interface(self._lidar)
