import os
import omni.ext
from .. import _dr
from .menu import DRMenu
from .tests.test_domain_randomizer import *


class Extension(omni.ext.IExt):
    def on_startup(self):
        self._dr = _dr.acquire_dr_interface()
        self._menu = DRMenu(self._dr)
        self._menu._build_dr_ui()

    def on_shutdown(self):
        print("Shutting down Domain Randomizer")
        _dr.release_dr_interface(self._dr)
        self._menu.shutdown()
        self._menu = None
