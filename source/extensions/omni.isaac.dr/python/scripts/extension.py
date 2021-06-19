# Copyright (c) 2018-2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

import os
import omni.ext
from .. import _dr
from . import commands  # populates commands list
from .menu import DRMenu


class Extension(omni.ext.IExt):
    def on_startup(self):
        self._dr = _dr.acquire_dr_interface()
        self._menu = DRMenu(self._dr)
        self._menu._build_dr_ui()

    def on_shutdown(self):
        _dr.release_dr_interface(self._dr)
        self._menu.shutdown()
        self._menu = None
