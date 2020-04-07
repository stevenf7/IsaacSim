import os
import sys

import omni.ext
import omni.kit.extensions

from .. import _lidar

from .menu import LidarMenu

# import pkgutil
# import pxr

EXTENSION_NAME = "Lidar"
EXTENSION_DESC = "Extension providing Lidar functionality"


class Extension(omni.ext.IExt):
    def on_startup(self):
        print("Starting Lidar extension")
        self._lidar = _lidar.acquire_lidar_interface()

        self._menu = LidarMenu()

    def on_shutdown(self):
        self._menu.shutdown()
        self._menu = None
        _lidar.release_lidar_interface(self._lidar)

    def get_name(self):
        return EXTENSION_NAME

    def get_description(self):
        return EXTENSION_DESC

    def get_deps(self):
        return "omni.physx"


def get_extension():
    return Extension()
