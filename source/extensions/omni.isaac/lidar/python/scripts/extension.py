import os
import sys

import omni.ext
from .. import _lidar
from .menu import LidarMenu

# any unit tests for the extension should be imported here
from .tests.test_lidar import *
from .samples.lidar_info import lidar_info

EXTENSION_NAME = "Lidar"


class Extension(omni.ext.IExt):
    def on_startup(self):
        print("Starting Lidar extension")
        self._lidar = _lidar.acquire_lidar_interface()
        self._sample_lidar_info = lidar_info(self._lidar)
        self._menu = LidarMenu()

    def on_shutdown(self):
        self._menu.shutdown()
        self._menu = None
        self._sample_lidar_info = None
        _lidar.release_lidar_interface(self._lidar)
