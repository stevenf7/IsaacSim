import omni.ext
import omni.kit.commands
import omni.kit.editor
import omni.kit.ui
import gc
from .. import _dynamic_control

EXTENSION_NAME = "Dynamic Control"


class Extension(omni.ext.IExt):
    def on_startup(self):
        print("Loading Dynamic Control Extension")
        self._dc = _dynamic_control.acquire_dynamic_control_interface()

    def on_shutdown(self):
        print("Shutting down Dynamic Control")
        _dynamic_control.release_dynamic_control_interface(self._dc)
        gc.collect()
