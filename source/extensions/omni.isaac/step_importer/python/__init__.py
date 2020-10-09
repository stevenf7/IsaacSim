import sys
import os

if "sphinx" not in sys.modules:
    # install Python dependencies
    import omni.kit.pipapi

    # This seems to be necessary to load on windows
    omni.kit.pipapi.install("numpy")

from .scripts.extension import *
from .scripts.usd_exporter import *

__name__ = "Step Importer"
