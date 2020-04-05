import os
import sys

print(sys.path)
import omni.kit.extensions

from ..bindings import _lidar

from .menu import LidarMenu


# import pkgutil
# import pxr

EXTENSION_NAME = "Lidar"
EXTENSION_DESC = "Extension providing Lidar functionality"


class Extension:
    def on_startup(self):
        ext_folder = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
        lib_path = omni.kit.extensions.build_plugin_path(ext_folder, "omni.isaac.lidar.plugin")

        print("Starting Lidar from '%s'" % lib_path)
        self._lidar = _lidar.acquire_lidar_interface(library_path=lib_path)

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
