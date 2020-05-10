import numpy as np

from .device import Device

from omni.isaac.manip import _manip


class Gamepad(Device):
    def __init__(self, joystick_deadzone=0.2, gains=(4, 4, 0.5)):
        """
        """
        self._manip = _manip.acquire()
        self._manip.bind_gamepad(self._on_event_fn)

        self.joystick_deadzone = joystick_deadzone

        self._enabled = False
        self._reset_state()
        self._gains = gains

    def _reset_state(self):
        """
        """
        print("resetting state")
        self.vel_target = np.zeros(3)

    def start_control(self):
        """
        """
        self._reset_state()
        self._enabled = True

    def stop_control(self):
        """
        """
        self._reset_state()
        self._enabled = False

    def bind_object(self, kaya):
        self.bound_fn = kaya.move

    def unbind_object(self):
        self.bound_fn = None

    def _on_event_fn(self, axis, signal):
        """
        """
        if not self._enabled:
            return

        if abs(signal) < self.joystick_deadzone:
            signal = 0

        if axis == 1:
            self.vel_target[0] = signal * self._gains[0]
        elif axis == 0:
            self.vel_target[1] = -signal * self._gains[1]
        elif axis == 2:
            self.vel_target[2] = -signal * self._gains[2]
        else:
            pass

        self.bound_fn(self.vel_target)
