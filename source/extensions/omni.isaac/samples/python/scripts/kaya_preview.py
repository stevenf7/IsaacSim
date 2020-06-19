# Copyright (c) 2020, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

import omni.kit.commands
import omni.kit.editor
import omni.ext
import omni.appwindow
import omni.kit.ui
import omni.kit.settings
import gc
import numpy as np
import asyncio

from omni.isaac.dynamic_control import _dynamic_control
from omni.isaac.manip import _manip
from omni.physx import _physx
from omni.physx.scripts.physicsUtils import add_ground_plane

from pxr import Sdf, Gf, PhysicsSchema

from .utils.kaya import Kaya
from omni.isaac.utils.scripts.scene_utils import setUpZAxis, SetupPhysics, CreateBackground

EXTENSION_NAME = "Kaya Joystick"


class Extension(omni.ext.IExt):
    def on_startup(self):
        """Initialize extension and UI elements
        """
        self._editor = omni.kit.editor.get_editor_interface()
        self._usd_context = omni.usd.get_context()
        self._stage = self._usd_context.get_stage()
        self._window = omni.kit.ui.Window(
            EXTENSION_NAME,
            300,
            200,
            menu_path="Isaac Robotics/Samples/" + EXTENSION_NAME,
            open=False,
            dock=omni.kit.ui.DockPreference.LEFT_BOTTOM,
        )

        self._dc = _dynamic_control.acquire_dynamic_control_interface()

        self._load_kaya_btn = self._window.layout.add_child(omni.kit.ui.Button("Load Kaya"))
        self._load_kaya_btn.set_clicked_fn(self._on_environment_setup)
        self._load_kaya_btn.tooltip = omni.kit.ui.Label("Reset the stage and load the kaya environment")
        self._gamepad_setup_btn = self._window.layout.add_child(omni.kit.ui.Button("Press Load Kaya First"))
        self._gamepad_setup_btn.set_clicked_fn(self._on_gamepad_setup)
        self._gamepad_setup_btn.enabled = False
        self._gamepad_setup_btn.tooltip = omni.kit.ui.Label("Connect the gamepad to the robot and begin simulation")
        self.kaya = None

        self._settings = omni.kit.settings.get_settings_interface()
        self._settings.set("/persistent/physics/updateToUsd", False)
        self._settings.set("/persistent/physics/useFastCache", True)

        self._manip = _manip.acquire()
        self._joystick_deadzone = 0.2
        self._gains = (4, 4, 0.5)
        self._vel_target = np.zeros(3)

        print("Kaya Preview Startup Complete")

    def _on_gamepad_setup(self, widget):
        if self.kaya is None:
            print("Cannot start gamepad, kaya not valid")
            return
        # must start editor before setting up gamepad to move
        self._editor.play()
        self._manip.bind_gamepad(self._on_event_fn)

    async def _create_kaya(self, task):
        done, pending = await asyncio.wait({task})
        if task in done:
            print("Loading Kaya Enviornment")
            self._editor.set_camera_position("/OmniverseKit_Persp", 150, 150, 50, True)
            self._editor.set_camera_target("/OmniverseKit_Persp", 0, 0, 0, True)
            self._stage = self._usd_context.get_stage()
            asset_path = "omniverse://ov-isaac-dev/Isaac/Robots/Kaya"
            kaya_usd = asset_path + "/kaya.usd"
            speed_gain = 10.0

            setUpZAxis(self._stage)
            SetupPhysics(self._stage)

            self.kaya = Kaya(
                stage=self._stage, dc=self._dc, usd_path=kaya_usd, prim_path="/kaya", speed_gain=speed_gain
            )
            CreateBackground(
                self._stage,
                "omniverse://ov-isaac-dev/Isaac/Environments/Grid/gridroom_curved.usd",
                background_path="/background",
                offset=Gf.Vec3d(0, 0, -9),
            )
            self._gamepad_setup_btn.enabled = True
            self._gamepad_setup_btn.text = "Connect GamePad"

            # start stepping after kaya is created
            self._editor_event_subscription = self._editor.subscribe_to_update_events(self._on_editor_step)

    def _on_environment_setup(self, widget):
        # wait for new stage before creating kaya
        task = asyncio.ensure_future(omni.kit.asyncapi.new_stage())
        asyncio.ensure_future(self._create_kaya(task))

    def _on_event_fn(self, axis, signal):
        if abs(signal) < self._joystick_deadzone:
            signal = 0

        if axis == 1:
            self._vel_target[0] = signal * self._gains[0]
        elif axis == 0:
            self._vel_target[1] = -signal * self._gains[1]
        elif axis == 2:
            self._vel_target[2] = -signal * self._gains[2]
        else:
            pass

    def _on_editor_step(self, step):
        """Update kaya physics once per step
        """
        if self.kaya is not None:
            self.kaya.move(self._vel_target)

    def on_shutdown(self):
        """Cleanup objects on extension shutdown
        """
        print("Shutting down Kaya Preview")

        self._manip.unbind_gamepad()
        self._editor.stop()
        self.kaya = None
        self._window = None
        gc.collect()
