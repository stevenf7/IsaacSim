import omni.ext
from .. import _motion_planning


class Extension(omni.ext.IExt):
    def on_startup(self):

        print("Starting Motion Planning Extension")
        self._mp = _motion_planning.acquire_motion_planning_interface()

    def on_shutdown(self):
        print("Shutting down Motion Planning")
        _motion_planning.release_motion_planning_interface(self._mp)
