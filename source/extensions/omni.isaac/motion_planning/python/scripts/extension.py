import os
import omni.kit.extensions
from ..bindings import _motion_planning

EXTENSION_NAME = "Motion Planning"
EXTENSION_DESC = "Interface for interacting with RMP motion planning"


class Extension:
    def on_startup(self):
        ext_folder = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
        lib_path = omni.kit.extensions.build_plugin_path(ext_folder, "omni.isaac.motion_planning.plugin")
        print("Starting Motion Planning from '%s'" % lib_path)
        self._mp = _motion_planning.acquire_motion_planning_interface(library_path=lib_path)

    def on_shutdown(self):
        print("Shutting down Motion Planning")
        _motion_planning.release_motion_planning_interface(self._mp)

    def get_name(self):
        return EXTENSION_NAME

    def get_description(self):
        return EXTENSION_DESC

    def get_deps(self):
        return "omni.isaac.dynamic_control"


def get_extension():
    return Extension()
