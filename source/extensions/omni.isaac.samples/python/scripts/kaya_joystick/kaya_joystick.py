# Copyright (c) 2020-2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

import carb
import omni.ext
import omni.appwindow
import gc
import numpy as np
from omni.isaac.core.prims.xform_prim import XFormPrim
from omni.isaac.kaya import Kaya
from omni.isaac.kaya.controllers import HolonomicController
from omni.isaac.core.utils.nucleus_utils import find_nucleus_server
from omni.isaac.core.utils.stage import add_reference_to_stage
from omni.isaac.core.tasks.task import BaseTask
from omni.isaac.core.scenes.scene import Scene
from omni.isaac.samples.scripts.base_sample import BaseSample
from omni.isaac.manip import _manip, GamePadAxis


class DriveTask(BaseTask):
    def __init__(self) -> None:
        super().__init__("Drive Kaya")
        self.kaya = None

    def set_up_scene(self, scene: Scene) -> None:
        super().set_up_scene(scene)

        result, nucleus_server = find_nucleus_server()
        if result is False:
            carb.log_error("Could not find nucleus server with /Isaac folder")
            return
        self.kaya = scene.add(
            Kaya(
                prim_path="/kaya",
                name="my_kaya",
                position=np.array([0, 0.0, 2.0]),
                orientation=np.array([1.0, 0.0, 0.0, 0.0]),
            )
        )

        add_reference_to_stage(
            usd_path=nucleus_server + "/Isaac/Environments/Grid/gridroom_curved.usd", prim_path="/World/background"
        )
        # TODO: change with new USD
        XFormPrim(prim_path="/World/background", position=np.array([0, 0, -9]))

    def reset(self) -> None:
        super().reset()
        viewport = omni.kit.viewport.get_default_viewport_window()
        viewport.set_camera_position("/OmniverseKit_Persp", 75, 75, 45, True)
        viewport.set_camera_target("/OmniverseKit_Persp", 0, 0, 0, True)
        return


class KayaJoystick(BaseSample):
    def __init__(self) -> None:
        super().__init__()
        self._controller = None
        self._command = [0.0, 0.0, 0.0]
        self._gains = (40.0, 40.0, 2.0)
        self._joystick_deadzone = 0.2

    def _load_task(self):
        return DriveTask()

    async def setup_load(self):
        self._controller = HolonomicController(name="simple_control")
        self._appwindow = omni.appwindow.get_default_app_window()
        self._manip = _manip.acquire_manip_interface()
        self._manip.bind_gamepad(self._sub_joystick_event)
        self._world.add_physics_callback("kaya_step", callback_fn=self._on_editor_step)
        await self._world.play_async()
        return

    def _on_editor_step(self, step):
        self._task.kaya.apply_wheel_actions(
            self._controller.forward(self._command[0], self._command[1], self._command[2])
        )
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

    async def setup_reset(self):
        self._controller.reset()
        self._world.remove_physics_callback("kaya_step")
        self._world.add_physics_callback("kaya_step", callback_fn=self._on_editor_step)
        await self._world.play_async()
        self._controller.reset()
        return

    def world_cleanup(self):
        super().world_cleanup()
        if self._controller:
            self._controller = None
            self._manip.unbind_gamepad()
        gc.collect()
        return
