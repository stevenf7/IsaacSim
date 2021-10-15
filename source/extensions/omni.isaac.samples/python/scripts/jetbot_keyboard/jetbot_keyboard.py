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
from omni.isaac.jetbot import Jetbot
from omni.isaac.jetbot.controllers import DifferentialController
from omni.isaac.core.utils.nucleus_utils import find_nucleus_server
from omni.isaac.core.utils.stage import add_reference_to_stage
from omni.isaac.core.tasks.task import BaseTask
from omni.isaac.core.scenes.scene import Scene
from omni.isaac.samples.scripts.base_sample import BaseSample


class DriveTask(BaseTask):
    def __init__(self) -> None:
        super().__init__("Drive Jetbot")
        self.jetbot = None

    def set_up_scene(self, scene: Scene) -> None:
        super().set_up_scene(scene)
        result, nucleus_server = find_nucleus_server()
        if result is False:
            carb.log_error("Could not find nucleus server with /Isaac folder")
            return

        self.jetbot = scene.add(
            Jetbot(
                prim_path="/jetbot",
                name="my_jetbot",
                position=np.array([0, 0.0, 2.0]),
                orientation=np.array([1.0, 0.0, 0.0, 0.0]),
            )
        )
        add_reference_to_stage(
            usd_path=nucleus_server + "/Isaac/Environments/Grid/gridroom_curved.usd", prim_path="/World/background"
        )
        # TODO: change with new USD
        XFormPrim(prim_path="/World/background", name="background", position=np.array([0, 0, -9]))

    def reset(self) -> None:
        super().reset()
        viewport = omni.kit.viewport.get_default_viewport_window()
        viewport.set_camera_position("/OmniverseKit_Persp", 75, 75, 45, True)
        viewport.set_camera_target("/OmniverseKit_Persp", 0, 0, 0, True)
        pass


class JetbotKeyboard(BaseSample):
    def __init__(self) -> None:
        super().__init__()
        self._controller = None
        self._command = [0.0, 0.0]

    def _load_task(self):
        return DriveTask()

    async def setup_load(self):
        self._controller = DifferentialController(name="simple_control")
        self._appwindow = omni.appwindow.get_default_app_window()
        self._input = carb.input.acquire_input_interface()
        self._keyboard = self._appwindow.get_keyboard()
        self._sub_keyboard = self._input.subscribe_to_keyboard_events(self._keyboard, self._sub_keyboard_event)
        self._world.add_physics_callback("jetbot_step", callback_fn=self._on_editor_step)
        await self._world.play_async()
        return

    def _on_editor_step(self, step):
        self._task.jetbot.apply_wheel_actions(self._controller.forward(command=self._command))
        return

    def _sub_keyboard_event(self, event, *args, **kwargs):
        """Handle keyboard events
        w,s,a,d as arrow keys for jetbot movement

        Args:
            event (int): keyboard event type
        """
        if (
            event.type == carb.input.KeyboardEventType.KEY_PRESS
            or event.type == carb.input.KeyboardEventType.KEY_REPEAT
        ):
            if event.input == carb.input.KeyboardInput.W:
                self._command = [0.5, 0.0]
            if event.input == carb.input.KeyboardInput.S:
                self._command = [-0.5, 0.0]
            if event.input == carb.input.KeyboardInput.A:
                self._command = [0.0, 1.0]
            if event.input == carb.input.KeyboardInput.D:
                self._command = [0.0, -1.0]
        if event.type == carb.input.KeyboardEventType.KEY_RELEASE:
            self._command = [0.0, 0.0]

        return True

    async def setup_reset(self):
        self._controller.reset()
        self._world.remove_physics_callback("jetbot_step")
        await omni.kit.app.get_app().next_update_async()
        self._world.add_physics_callback("jetbot_step", callback_fn=self._on_editor_step)
        return

    def world_cleanup(self):
        super().world_cleanup()
        self._controller = None
        self._sub_keyboard = None
        gc.collect()
        return
