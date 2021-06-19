# Copyright (c) 2020-2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

import carb
import omni.kit.commands
import omni.ext
import omni.appwindow
import weakref
import omni.kit.settings
import gc
import numpy as np
import asyncio
import omni.ui as ui
import omni.physx as _physx
from omni.kit.menu.utils import add_menu_items, remove_menu_items, MenuItemDescription

from omni.isaac.dynamic_control import _dynamic_control
from omni.isaac.manip import _manip, GamePadAxis

from pxr import Gf

from .utils.kaya import Kaya
from omni.isaac.utils.scripts.scene_utils import set_up_z_axis, setup_physics, create_background
from omni.isaac.utils.scripts.nucleus_utils import find_nucleus_server

EXTENSION_NAME = "Kaya Joystick"


class Extension(omni.ext.IExt):
    def on_startup(self):
        """Initialize extension and UI elements
        """
        self._timeline = omni.timeline.get_timeline_interface()
        self._viewport = omni.kit.viewport.get_default_viewport_window()
        self._usd_context = omni.usd.get_context()
        self._stage = self._usd_context.get_stage()
        self.kaya = None

        self._manip = _manip.acquire_manip_interface()
        self._joystick_deadzone = 0.2
        self._gains = (4, 4, 0.5)
        self._vel_target = np.zeros(3)
        self._dc = _dynamic_control.acquire_dynamic_control_interface()

        self._window = None
        self._load_kaya_btn = None
        self._gamepad_setup_btn = None
        menu_items = [
            MenuItemDescription(name=EXTENSION_NAME, onclick_fn=lambda a=weakref.proxy(self): a._menu_callback())
        ]
        self._menu_items = [
            MenuItemDescription(
                name="Controlling", sub_menu=[MenuItemDescription(name="Input Devices", sub_menu=menu_items)]
            )
        ]
        add_menu_items(self._menu_items, "Isaac Examples")

    def _menu_callback(self):
        self._build_ui()

    def _build_ui(self):
        if not self._window:
            self._window = ui.Window(
                title=EXTENSION_NAME, width=200, height=150, visible=True, dockPreference=ui.DockPreference.LEFT_BOTTOM
            )
            with self._window.frame:
                with ui.VStack():
                    self._load_kaya_btn = ui.Button(
                        "Load Kaya",
                        tooltip="Reset the stage and load the kaya environment",
                        clicked_fn=self._on_environment_setup,
                    )
                    self._gamepad_setup_btn = ui.Button(
                        "Press Load Kaya First",
                        tooltip="Connect the gamepad to the robot and begin simulation",
                        clicked_fn=self._on_gamepad_setup,
                    )
                    self._gamepad_setup_btn.enabled = False
        self._window.visible = True

    def _on_gamepad_setup(self):
        if self.kaya is None:
            print("Cannot start gamepad, kaya not valid")
            return
        # must start editor before setting up gamepad to move
        self._timeline.play()
        self._manip.bind_gamepad(self._on_event_fn)

    async def _create_kaya(self, task):
        done, pending = await asyncio.wait({task})
        if task in done:
            print("Loading Kaya Enviornment")
            self._viewport.set_camera_position("/OmniverseKit_Persp", 150, 150, 50, True)
            self._viewport.set_camera_target("/OmniverseKit_Persp", 0, 0, 0, True)
            self._stage = self._usd_context.get_stage()
            result, nucleus_server = find_nucleus_server()
            if result is False:
                carb.log_error("Could not find nucleus server with /Isaac folder")
                return
            asset_path = nucleus_server + "/Isaac"
            kaya_usd = asset_path + "/Robots/Kaya/kaya.usd"
            speed_gain = 10.0

            set_up_z_axis(self._stage)
            setup_physics(self._stage)

            self.kaya = Kaya(
                stage=self._stage, dc=self._dc, usd_path=kaya_usd, prim_path="/kaya", speed_gain=speed_gain
            )
            create_background(
                self._stage,
                asset_path + "/Environments/Grid/gridroom_curved.usd",
                background_path="/background",
                offset=Gf.Vec3d(0, 0, -9),
            )
            self._gamepad_setup_btn.enabled = True
            self._gamepad_setup_btn.text = "Connect GamePad"

            # start stepping after kaya is created
            self._physx_subs = _physx.get_physx_interface().subscribe_physics_step_events(self._on_step)

    def _on_environment_setup(self):
        # wait for new stage before creating kaya
        task = asyncio.ensure_future(omni.usd.get_context().new_stage_async())
        asyncio.ensure_future(self._create_kaya(task))

    def _on_event_fn(self, axis, signal):
        if abs(signal) < self._joystick_deadzone:
            signal = 0

        if axis == GamePadAxis.eLeftStickY:
            self._vel_target[0] = signal * self._gains[0]
        elif axis == GamePadAxis.eLeftStickX:
            self._vel_target[1] = -signal * self._gains[1]
        elif axis == GamePadAxis.eRightStickX:
            self._vel_target[2] = -signal * self._gains[2]
        else:
            pass

    def _on_step(self, step):
        """Update kaya physics once per step
        """
        if self.kaya is not None:
            self.kaya.move(self._vel_target)

    def on_shutdown(self):
        """Cleanup objects on extension shutdown
        """

        self._manip.unbind_gamepad()
        self._timeline.stop()
        self._physx_subs = None
        self.kaya = None
        remove_menu_items(self._menu_items, "Isaac Examples")
        self._window = None
        gc.collect()
