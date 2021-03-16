import omni.ext
import omni.kit.commands
import omni.kit.ui
import gc
from .. import _isaac_utils


class Extension(omni.ext.IExt):
    def on_startup(self):
        self._draw = _isaac_utils.debug_draw.acquire_debug_draw_interface()

    def on_shutdown(self):
        _isaac_utils.debug_draw.release_debug_draw_interface(self._draw)
        gc.collect()
