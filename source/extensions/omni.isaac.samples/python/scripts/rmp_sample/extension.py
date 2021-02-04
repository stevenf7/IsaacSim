import omni.ext
import omni.ui as ui
from omni.kit.menu.utils import add_menu_items, remove_menu_items, MenuItemDescription

import gc
import asyncio
import weakref
import omni.physx as _physx
from .sample import RMPSample

EXTENSION_NAME = "RMP Sample"


class Extension(omni.ext.IExt):
    def on_startup(self):
        self._window = ui.Window(EXTENSION_NAME, width=800, height=400, visible=False)
        self._window.set_visibility_changed_fn(self._on_window)
        self._menu_items = [
            MenuItemDescription(
                name="Samples",
                sub_menu=[
                    MenuItemDescription(
                        name=EXTENSION_NAME, onclick_fn=lambda a=weakref.proxy(self): a._menu_callback()
                    )
                ],
            )
        ]
        add_menu_items(self._menu_items, "Isaac")
        self._viewport = omni.kit.viewport.get_default_viewport_window()
        self._timeline = omni.timeline.get_timeline_interface()
        self._sample = RMPSample()
        # Simple button style that grays out the button if disabled
        self._button_style = {":disabled": {"color": 0xFF000000}}
        with self._window.frame:
            with omni.ui.VStack(style=self._button_style):
                self._create_robot_btn = ui.Button("Load Robot", enabled=True)
                self._create_robot_btn.set_clicked_fn(self._on_setup_environment)
                self._create_robot_btn.set_tooltip("Load robot and environment")
                self._target_following_btn = ui.Button("Target Following", enabled=False)
                self._target_following_btn.set_clicked_fn(self._sample.follow_target)
                self._target_following_btn.set_tooltip("Follow Target Prim")
                self._add_obstacle_btn = ui.Button("Add Obstacles", enabled=False)
                self._add_obstacle_btn.set_clicked_fn(self._sample.add_obstacle)
                self._add_obstacle_btn.set_tooltip("Add obstacles to environment")
                self._toggle_obstacle_btn = ui.Button("Toggle Obstacles", enabled=False)
                self._toggle_obstacle_btn.set_clicked_fn(self._sample.toggle_obstacle)
                self._toggle_obstacle_btn.set_tooltip("Enable/Disable obstacles")
                self._gripper_btn = ui.Button("Toggle Gripper", enabled=False)
                self._gripper_btn.set_clicked_fn(self._sample.toggle_gripper)
                self._gripper_btn.set_tooltip("Toggle gripper open/close state")
                self._get_states_btn = ui.Button("Get States", enabled=False)
                self._get_states_btn.set_clicked_fn(self._sample.get_states)
                self._get_states_btn.set_tooltip("click to print state of the robot and block in terminal")
                self._reset_btn = ui.Button("Reset", enabled=False)
                self._reset_btn.set_clicked_fn(self._sample.reset)
                self._reset_btn.set_tooltip("Reset Robot to default position")

    def _on_window(self, status):
        if status:
            self._sub_stage_event = (
                omni.usd.get_context().get_stage_event_stream().create_subscription_to_pop(self._on_stage_event)
            )
            self._physx_subs = _physx.get_physx_interface().subscribe_physics_step_events(self._on_simulation_step)
            self._timeline_sub = self._timeline.get_timeline_event_stream().create_subscription_to_pop(
                self._on_timeline_event
            )
        else:
            self._sub_stage_event = None
            self._physx_subs = None
            self._timeline_sub = None

    def _menu_callback(self):
        self._window.visible = not self._window.visible

    def _on_stage_event(self, event):
        """This function is called when stage events occur.
        Enables UI elements when stage is opened.
        Prevents tasks from being started until all assets are loaded
        
        Arguments:
            event (int): event type
        """
        if event.type == int(omni.usd.StageEventType.OPENED):
            self._create_robot_btn.enabled = True
            self._target_following_btn.enabled = False
            self._add_obstacle_btn.enabled = False
            self._toggle_obstacle_btn.enabled = False
            self._gripper_btn.enabled = False
            self._reset_btn.enabled = False
            self._get_states_btn.enabled = False

            self._timeline.stop()
            self._sample.stop_tasks()

    def _on_simulation_step(self, step):
        if self._sample.created:
            self._create_robot_btn.text = "Robot Already Loaded"
            if self._timeline.is_playing():
                self._sample.step(step)
                if self._sample.obstacle_on:
                    self._toggle_obstacle_btn.enabled = True
                    self._toggle_obstacle_btn.text = "Press to Suppress Block"
                else:
                    self._toggle_obstacle_btn.text = "Press to Unsuppress Block"
                if self._sample.gripper_open:
                    self._gripper_btn.text = "Press to Close Gripper"
                else:
                    self._gripper_btn.text = "Press to Open Gripper"

                self._target_following_btn.text = "Follow Target"
                self._add_obstacle_btn.text = "Add Obstacles"
                self._gripper_btn.text = "Toggle Gripper"
                self._get_states_btn.text = "Get States"
            else:
                self._target_following_btn.text = "Press Play To Enable"
                self._add_obstacle_btn.text = "Press Play To Enable"
                self._toggle_obstacle_btn.text = "Press Play To Enable"
                self._gripper_btn.text = "Press Play To Enable"
                self._get_states_btn.text = "Press Play To Enable"
        else:
            self._create_robot_btn.text = "Load Robot"
            self._target_following_btn.text = "Press Load Robot To Enable"
            self._add_obstacle_btn.text = "Press Load Robot To Enable"
            self._toggle_obstacle_btn.text = "Press Load Robot To Enable"
            self._gripper_btn.text = "Press Load Robot To Enable"
            self._get_states_btn.text = "Press Load Robot To Enable"

    def _on_timeline_event(self, e):
        if e.type == int(omni.timeline.TimelineEventType.PLAY):
            self._target_following_btn.enabled = True
            self._add_obstacle_btn.enabled = True
            self._gripper_btn.enabled = True
            self._get_states_btn.enabled = True
            self._reset_btn.enabled = True
        if e.type == int(omni.timeline.TimelineEventType.STOP) or e.type == int(omni.timeline.TimelineEventType.PAUSE):
            self._target_following_btn.enabled = False
            self._add_obstacle_btn.enabled = False
            self._gripper_btn.enabled = False
            self._get_states_btn.enabled = False
            self._toggle_obstacle_btn.enabled = False

    def _on_setup_environment(self):
        self._timeline.stop()
        task = asyncio.ensure_future(omni.usd.get_context().new_stage_async())
        asyncio.ensure_future(self._on_create_robot(task))

    async def _on_create_robot(self, task):
        done, pending = await asyncio.wait({task})
        if task not in done:
            return
        self._sample.create_robot()
        self._viewport.set_camera_position("/OmniverseKit_Persp", 142, -127, 56, True)
        self._viewport.set_camera_target("/OmniverseKit_Persp", -180, 234, -27, True)

        self._create_robot_btn.enabled = False
        self._reset_btn.enabled = True

    def on_shutdown(self):
        self._physx_subs = None
        self._sub_stage_event = None
        self._timeline_sub = None

        self._timeline.stop()
        self._sample.stop_tasks()
        self._sample = None
        remove_menu_items(self._menu_items, "Isaac")
        gc.collect()
        pass
