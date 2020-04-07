import os
import omni.ext
import omni.kit.extensions
from .. import _motion_planning

EXTENSION_NAME = "Motion Planning"
EXTENSION_DESC = "Interface for interacting with RMP motion planning"


class Extension(omni.ext.IExt):
    def on_startup(self):

        print("Starting Motion Planning Extension")
        self._mp = _motion_planning.acquire_motion_planning_interface()

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
