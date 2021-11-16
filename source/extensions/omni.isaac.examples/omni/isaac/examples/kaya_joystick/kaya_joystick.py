# Copyright (c) 2020-2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

import omni.ext
import numpy as np
from omni.isaac.kaya import Kaya
from omni.isaac.kaya.controllers import HolonomicController
from omni.isaac.examples.base_sample import BaseSample
from omni.isaac.manip import _manip, GamePadAxis
from omni.isaac.core.utils.viewports import set_camera_view


class KayaJoystick(BaseSample):
    def __init__(self) -> None:
        super().__init__()
        self._controller = None
        self._command = [0.0, 0.0, 0.0]
        self._gains = (40.0, 40.0, 2.0)
        self._joystick_deadzone = 0.2
        self._manip = None

    async def setup_post_load(self):
        # Note: for hot reload you need to get handles of things defined in add_tasks here
        world = self.get_world()
        self._kaya = world.scene.get_object("my_kaya")
        self._controller = HolonomicController(name="simple_control")
        self._manip = _manip.acquire_manip_interface()
        self._manip.bind_gamepad(self._sub_joystick_event)
        self._world.add_physics_callback("kaya_step", callback_fn=self._on_sim_step)
        await self._world.play_async()
        return

    def setup_scene(self):
        world = self.get_world()
        self._kaya = world.scene.add(
            Kaya(
                prim_path="/kaya",
                name="my_kaya",
                position=np.array([0, 0.0, 2.0]),
                orientation=np.array([1.0, 0.0, 0.0, 0.0]),
            )
        )
        world.scene.add_default_ground_plane()
        set_camera_view(eye=np.array([75, 75, 45]), target=np.array([0, 0, 0]))
        return

    def _on_sim_step(self, step):
        self._kaya.apply_wheel_actions(self._controller.forward(self._command))
        return

    def _sub_joystick_event(self, axis, signal):
        if abs(signal) < self._joystick_deadzone:
            signal = 0

        if axis == GamePadAxis.eLeftStickY:
            self._command[0] = signal * self._gains[0]
        elif axis == GamePadAxis.eLeftStickX:
            self._command[1] = -signal * self._gains[1]
        elif axis == GamePadAxis.eRightStickX:
            self._command[2] = -signal * self._gains[2]
        else:
            pass

    async def setup_post_reset(self):
        self._controller.reset()
        self._world.remove_physics_callback("kaya_step")
        await omni.kit.app.get_app().next_update_async()
        self._world.add_physics_callback("kaya_step", callback_fn=self._on_sim_step)
        await self._world.play_async()
        return

    def world_cleanup(self):
        self._controller = None
        if self._manip:
            self._manip.unbind_gamepad()
        self._manip = None
        return
