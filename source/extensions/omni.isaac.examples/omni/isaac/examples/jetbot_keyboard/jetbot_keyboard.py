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
from omni.isaac.jetbot import Jetbot
from omni.isaac.jetbot.controllers import DifferentialController
from omni.isaac.core.utils.nucleus import find_nucleus_server
from omni.isaac.examples.base_sample import BaseSample
from omni.isaac.core.utils.viewports import set_camera_view


class JetbotKeyboard(BaseSample):
    def __init__(self) -> None:
        super().__init__()
        self._controller = None
        self._command = [0.0, 0.0]

    def setup_scene(self):
        world = self.get_world()
        result, nucleus_server = find_nucleus_server()
        if result is False:
            carb.log_error("Could not find nucleus server with /Isaac folder")
            return
        self._jetbot = world.scene.add(
            Jetbot(
                prim_path="/jetbot",
                name="my_jetbot",
                position=np.array([0, 0.0, 2.0]),
                orientation=np.array([1.0, 0.0, 0.0, 0.0]),
            )
        )
        world.scene.add_default_ground_plane()
        set_camera_view(eye=np.array([75, 75, 45]), target=np.array([0, 0, 0]))
        return

    async def setup_post_load(self):
        # Note: for hot reload you need to get handles of things defined in add_tasks here
        world = self.get_world()
        self._jetbot = world.scene.get_object("my_jetbot")
        self._controller = DifferentialController(name="simple_control")
        self._appwindow = omni.appwindow.get_default_app_window()
        self._input = carb.input.acquire_input_interface()
        self._keyboard = self._appwindow.get_keyboard()
        self._sub_keyboard = self._input.subscribe_to_keyboard_events(self._keyboard, self._sub_keyboard_event)
        self._world.add_physics_callback("jetbot_step", callback_fn=self._on_sim_step)
        await self._world.play_async()
        return

    def _on_sim_step(self, step):
        self._jetbot.apply_wheel_actions(self._controller.forward(command=self._command))
        print(self._jetbot.get_linear_velocity())
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
                self._command = [20, 0.0]
            if event.input == carb.input.KeyboardInput.S:
                self._command = [-20, 0.0]
            if event.input == carb.input.KeyboardInput.A:
                self._command = [0.0, np.pi / 5]
            if event.input == carb.input.KeyboardInput.D:
                self._command = [0.0, -np.pi / 5]
        if event.type == carb.input.KeyboardEventType.KEY_RELEASE:
            self._command = [0.0, 0.0]

        return True

    async def setup_post_reset(self):
        self._controller.reset()
        self._world.remove_physics_callback("jetbot_step")
        await omni.kit.app.get_app().next_update_async()
        self._world.add_physics_callback("jetbot_step", callback_fn=self._on_sim_step)
        return

    def world_cleanup(self):
        self._controller = None
        self._sub_keyboard = None
        gc.collect()
        return
