# Copyright (c) 2018-2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

import omni.ext
from .. import _manip
from enum import IntEnum


class GamePadAxis(IntEnum):
    """Enum used for convenience when checking the axis sent to the registered callback from bind_gamepad
    """

    eNone = -1
    eLeftStickX = 0
    eLeftStickY = 1
    eRightStickX = 2
    eRightStickY = 3
    eLeftTrigger = 4
    eRightTrigger = 5
    eCount = 6


class Extension(omni.ext.IExt):
    def on_startup(self):
        self.manip = _manip.acquire_manip_interface()

    def on_shutdown(self):
        _manip.release_manip_interface(self.manip)
