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
