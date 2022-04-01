"""
Support required by the Carbonite extension loader
"""
import omni.ext

# Any class derived from `omni.ext.IExt` in a top level module (defined in `python.modules` of `extension.toml`) will be
# instantiated when the extension is enabled and `on_startup(ext_id)` will be called. Later when extension gets disabled
# on_shutdown() will be called.

from ..bindings._omni_isaac_core_nodes import acquire_interface, release_interface


class Extension(omni.ext.IExt):
    def on_startup(self):
        self.__interface = acquire_interface()
        pass

    def on_shutdown(self):
        release_interface(self.__interface)
        self.__interface = None
        pass
