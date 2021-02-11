import omni.ext
from .. import _manip


class Extension(omni.ext.IExt):
    def on_startup(self):
        self.manip = _manip.acquire()

    def on_shutdown(self):
        _manip.release(self.manip)
