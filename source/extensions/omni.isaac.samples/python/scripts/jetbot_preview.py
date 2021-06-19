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
import omni.ui as ui
import weakref
import omni.kit.settings
import gc
import numpy as np
import asyncio
from omni.kit.menu.utils import add_menu_items, remove_menu_items, MenuItemDescription

from omni.isaac.dynamic_control import _dynamic_control

from pxr import Gf

from omni.isaac.utils.scripts.scene_utils import set_up_z_axis, setup_physics, create_background
from omni.isaac.utils.scripts.nucleus_utils import find_nucleus_server

EXTENSION_NAME = "Jetbot Sample"


class Extension(omni.ext.IExt):
    def on_startup(self):
        """Initialize extension and UI elements
        """
        self._timeline = omni.timeline.get_timeline_interface()
        self._viewport = omni.kit.viewport.get_default_viewport_window()
        self._usd_context = omni.usd.get_context()
        self._stage = self._usd_context.get_stage()
        self._dc = _dynamic_control.acquire_dynamic_control_interface()
        self._appwindow = omni.appwindow.get_default_app_window()
        self._input = carb.input.acquire_input_interface()
        self._keyboard = self._appwindow.get_keyboard()
        self._sub_keyboard = self._input.subscribe_to_keyboard_events(self._keyboard, self._sub_keyboard_event)
        self._sub_stage_event = self._usd_context.get_stage_event_stream().create_subscription_to_pop(
            self._on_stage_event
        )

        self._max_velocity = 20
        self._wheel_check = None
        self._jetbot = False  # is jetbot loaded and exist

        self._vel_target = np.zeros(2)
        self._accel = np.zeros(2)
        self._ar = _dynamic_control.INVALID_HANDLE
        self._window = None
        self._load_jetbot_btn = None
        self._reset_btn = False
        menu_items = [
            MenuItemDescription(name="Jetbot Keyboard", onclick_fn=lambda a=weakref.proxy(self): a._menu_callback())
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
                title=EXTENSION_NAME, width=300, height=200, visible=True, dockPreference=ui.DockPreference.LEFT_BOTTOM
            )
            # self._window.set_update_fn(self._on_update_ui)

            with self._window.frame:
                with ui.VStack():
                    self._load_jetbot_btn = ui.Button(
                        "Load Jetbot",
                        clicked_fn=self._on_environment_setup,
                        height=0,
                        tooltip="Reset the stage and load the jetbot environment",
                    )
                    self._reset_btn = ui.Button(
                        "Reset Robot", height=0, clicked_fn=self._on_reset, tooltip="Reset Robot to origin"
                    )

                    self._load_jetbot_btn.enabled = True
                    self._reset_btn.enabled = False

                    ui.Separator(height=3)
                    ui.Label("keyboard map:\nw: forward\ns: reverse\na: left spin\nd: right spin")
        self._window.visible = True

    def _sub_keyboard_event(self, event, *args, **kwargs):
        """Handle keyboard events
        w,s,a,d as arrow keys for jetbot movement
        
        Args:
            event (int): keyboard event type
        """
        if event.type == carb.input.KeyboardEventType.KEY_PRESS:
            if event.input == carb.input.KeyboardInput.W:
                self._vel_target = np.ones(2) * 10  # starting speed
                self._accel = np.array([1.0, 1.0])
            if event.input == carb.input.KeyboardInput.S:
                self._vel_target = np.ones(2) * -10
                self._accel = np.array([-1.0, -1.0])
            if event.input == carb.input.KeyboardInput.A:
                self._vel_target = np.array([-4.0, 4.0])  # starting turn speed
                self._accel = np.array([-1, 1]) * 0.1  # let it turn slower
            if event.input == carb.input.KeyboardInput.D:
                self._vel_target = np.array([4.0, -4.0])
                self._accel = np.array([1, -1]) * 0.1
        if event.type == carb.input.KeyboardEventType.KEY_REPEAT:
            self._vel_target += self._accel
        if event.type == carb.input.KeyboardEventType.KEY_RELEASE:
            self._vel_target = np.zeros(2)

        return True

    def _on_reset(self):
        self._dc.wake_up_articulation(self._ar)
        root_body = self._dc.get_articulation_root_body(self._ar)
        new_pose_p = (0, 0.0, 2.0)
        new_pose_r = (0, 0, 0.0, 1)
        new_pose = _dynamic_control.Transform(new_pose_p, new_pose_r)
        self._dc.set_rigid_body_pose(root_body, new_pose)

    async def _create_jetbot(self, task):
        done, pending = await asyncio.wait({task})
        if task in done:
            print("Loading Jetbot Enviornment")
            self._viewport.set_camera_position("/OmniverseKit_Persp", 150, 150, 50, True)
            self._viewport.set_camera_target("/OmniverseKit_Persp", 0, 0, 0, True)
            self._stage = self._usd_context.get_stage()
            result, nucleus_server = find_nucleus_server()
            if result is False:
                carb.log_error("Could not find nucleus server with /Isaac folder")
                return
            asset_path = nucleus_server + "/Isaac"
            jetbot_usd = asset_path + "/Robots/Jetbot/jetbot.usd"

            prim_path = "/jetbot"
            self.prim = self._stage.DefinePrim(prim_path, "Xform")
            self.prim.GetReferences().AddReference(jetbot_usd)

            set_up_z_axis(self._stage)
            setup_physics(self._stage)

            create_background(
                self._stage,
                asset_path + "/Environments/Grid/gridroom_curved.usd",
                background_path="/background",
                offset=Gf.Vec3d(0, 0, -9),
            )

            # start stepping after jetbot is created
            self._editor_event_subscription = (
                omni.kit.app.get_app().get_update_event_stream().create_subscription_to_pop(self._on_editor_step)
            )
            self._jetbot = True

    def _on_environment_setup(self):
        # wait for new stage before creating jetbot
        self._wheel_check = False
        self._ar = _dynamic_control.INVALID_HANDLE
        task = asyncio.ensure_future(omni.usd.get_context().new_stage_async())
        asyncio.ensure_future(self._create_jetbot(task))

    def _on_stage_event(self, event):
        """This function is called when stage events occur.
        Enables UI elements when stage is opened.
        Prevents tasks from being started until all assets are loaded
        
        Arguments:
            event (int): event type
        """
        if event.type == int(omni.usd.StageEventType.OPENED):
            if self._window:
                self._load_jetbot_btn.enabled = True
                self._reset_btn.enabled = False
                self._timeline.stop()
                self._editor_event_subscription = None
                self._stop_tasks()

    def _stop_tasks(self):
        self._jetbot = None
        gc.collect()

    def _on_editor_step(self, step):
        """Update jetbot physics once per step
        """
        if not self._timeline.is_playing():
            self._reset_btn.text = "Press Play to Enable Controller"
            self._reset_btn.enabled = False
            return
        if not self._dc.is_simulating():
            return
        if not self._wheel_check:
            self._control_setup()

        # Wake up articulation every move command to ensure commands are applied
        if self._jetbot:
            self._dc.wake_up_articulation(self._ar)
            self._dc.set_dof_velocity_target(
                self._wheel_right, np.clip(self._vel_target[0], -self._max_velocity, self._max_velocity)
            )
            self._dc.set_dof_velocity_target(
                self._wheel_left, np.clip(self._vel_target[1], -self._max_velocity, self._max_velocity)
            )
            self._reset_btn.text = "Reset Robot"
            self._load_jetbot_btn.enabled = False
            self._reset_btn.enabled = True
        else:
            self._load_jetbot_btn.enabled = True
            self._reset_btn.enabled = False

    def _control_setup(self):
        """ set up velocity control on the joints
        """
        if self._ar == _dynamic_control.INVALID_HANDLE:
            self._ar = self._dc.get_articulation(str(self.prim.GetPath()))

        self._wheel_right = self._dc.find_articulation_dof(self._ar, "left_wheel_joint")
        self._wheel_left = self._dc.find_articulation_dof(self._ar, "right_wheel_joint")

        vel_props = _dynamic_control.DofProperties()
        vel_props.drive_mode = _dynamic_control.DRIVE_VEL
        vel_props.damping = 1e7
        vel_props.stiffness = 0
        self._dc.set_dof_properties(self._wheel_right, vel_props)
        self._dc.set_dof_properties(self._wheel_left, vel_props)

        self._wheel_check = True

    def on_shutdown(self):
        """Cleanup objects on extension shutdown
        """

        self._timeline.stop()
        self._editor_event_subscription = None
        self._stop_tasks()
        self._input.unsubscribe_to_keyboard_events(self._keyboard, self._sub_keyboard)
        remove_menu_items(self._menu_items, "Isaac Examples")
        self._window = None
        gc.collect()
