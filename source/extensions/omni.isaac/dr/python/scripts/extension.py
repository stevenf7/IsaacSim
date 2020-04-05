import os
import omni.ext
import omni.kit.extensions
from .. import _dr
from .menu import DRMenu

EXTENSION_NAME = "DR"


class Extension(omni.ext.IExt):
    def get_name(self):
        return EXTENSION_NAME

    def get_description(self):
        return "Domain Randomizer Extension"

    def on_startup(self):

        self._dr = _dr.acquire_dr_interface()
        self._menu = DRMenu(self._dr)

        self._menu._build_dr_ui()

    def on_shutdown(self):
        print("Shutting down Domain Randomizer")
        _dr.release_dr_interface(self._dr)
        self._menu.shutdown()
        self._menu = None


def get_extension():
    return Extension()
