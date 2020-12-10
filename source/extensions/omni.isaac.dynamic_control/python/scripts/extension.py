import omni.ext
import omni.kit.commands
import omni.kit.ui
import gc
from .. import _dynamic_control

EXTENSION_NAME = "Dynamic Control"


class Extension(omni.ext.IExt):
    def on_startup(self):
        self._dc = _dynamic_control.acquire_dynamic_control_interface()

    def on_shutdown(self):
        _dynamic_control.release_dynamic_control_interface(self._dc)
        gc.collect()
