# Copyright (c) 2018-2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
from pxr import Gf
import carb
import omni.usd
import omni.ext
import omni.ui as ui
from omni.kit.menu.utils import add_menu_items, remove_menu_items, MenuItemDescription

import asyncio
import gc
import weakref

from omni.isaac.dynamic_control import _dynamic_control
from .utils.simple_robot_controller import RobotController
from omni.isaac.utils.scripts.scene_utils import set_up_z_axis, setup_physics, create_background
from omni.isaac.utils.scripts.nucleus_utils import find_nucleus_server

EXTENSION_NAME = "Robot Navigation"


def create_xyz(init={"X": 100, "Y": 100, "Z": 0}):
    all_axis = ["X", "Y", "Z"]
    colors = {"X": 0xFF5555AA, "Y": 0xFF76A371, "Z": 0xFFA07D4F}
    float_drags = {}
    for axis in all_axis:
        with ui.HStack():
            with ui.ZStack(width=15):
                ui.Rectangle(
                    width=15,
                    height=20,
                    style={"background_color": colors[axis], "border_radius": 3, "corner_flag": ui.CornerFlag.LEFT},
                )
                ui.Label(axis, name="transform_label", alignment=ui.Alignment.CENTER)
            float_drags[axis] = ui.FloatDrag(name="transform", min=-1000000, max=1000000, step=1, width=100)
            float_drags[axis].model.set_value(init[axis])
    return float_drags


class Extension(omni.ext.IExt):
    def on_startup(self):
        self._timeline = omni.timeline.get_timeline_interface()
        self._viewport = omni.kit.viewport.get_default_viewport_window()
        self._usd_context = omni.usd.get_context()
        self._stage = self._usd_context.get_stage()
        self._window = ui.Window(EXTENSION_NAME, width=500, height=175, visible=False)
        self._window.set_visibility_changed_fn(self._on_window)

        menu_items = [
            MenuItemDescription(name=EXTENSION_NAME, onclick_fn=lambda a=weakref.proxy(self): a._menu_callback())
        ]
        self._menu_items = [
            MenuItemDescription(
                name="Controlling", sub_menu=[MenuItemDescription(name="Navigation", sub_menu=menu_items)]
            )
        ]
        add_menu_items(self._menu_items, "Isaac Examples")
        self._dc = _dynamic_control.acquire_dynamic_control_interface()
        self._create_ui()

        self._setup_done = False
        self._rc = None

    def _menu_callback(self):
        self._window.visible = not self._window.visible

    def _on_window(self, visible):
        if self._window.visible:
            self._sub_stage_event = self._usd_context.get_stage_event_stream().create_subscription_to_pop(
                self._on_stage_event
            )
        else:
            self._sub_stage_event = None

    def _create_ui(self):
        with self._window.frame:
            with omni.ui.VStack():
                with ui.HStack(height=5):
                    ui.Spacer(width=7)
                    self._robot_option = ui.ComboBox(0, "Transporter", "Carter", width=125)
                with ui.HStack(height=5):
                    ui.Spacer(width=5)
                    self._load_btn = ui.Button("Load Environment", width=125)
                    self._load_btn.set_clicked_fn(self._on_environment_setup)
                with ui.HStack(height=5):
                    ui.Spacer(width=9)
                    self._motion_label = ui.Label("Primitive Tasks", width=100)
                    self._motion_label.set_tooltip(
                        "Perform simple tasks like moving robot forward or rotating in-place"
                    )
                    self._move_btn = ui.Button("Move Robot", width=100, enabled=False)
                    self._move_btn.set_clicked_fn(self._on_move_fn)
                    self._rotate_btn = ui.Button("Rotate Robot", width=100, enabled=False)
                    self._rotate_btn.set_clicked_fn(self._on_rotate_fn)
                with ui.HStack(height=5):
                    ui.Spacer(width=9)
                    self._goal_label = ui.Label("Set Robot Goal", width=100)
                    self._goal_label.set_tooltip("Set robot target specified as (X, Y, theta)")
                    self.goal_coord = create_xyz(init={"X": -200, "Y": -400, "Z": 0})
                with ui.HStack(height=5):
                    ui.Spacer(width=5)
                    self._navigate_btn = ui.Button("Navigate Robot", width=100, enabled=False)
                    self._navigate_btn.set_clicked_fn(self._on_navigate_fn)
                    self._stop_btn = ui.Button("Stop Robot", width=100, enabled=False)
                    self._stop_btn.set_clicked_fn(self._on_navigate_stop_fn)

    async def _create_robot(self, task):
        done, pending = await asyncio.wait({task})
        if task in done:
            print("Loading Robot Enviornment")
            self._viewport.set_camera_position("/OmniverseKit_Persp", 300, 300, 100, True)
            self._viewport.set_camera_target("/OmniverseKit_Persp", 0, 0, 0, True)
            self._stage = self._usd_context.get_stage()
            result, nucleus_server = find_nucleus_server()
            if result is False:
                carb.log_error("Could not find nucleus server with /Isaac folder")
                return
            self._asset_path = nucleus_server + "/Isaac"

            current_robot_index = self._robot_option.model.get_item_value_model().as_int
            self._robot_prim_path = "/robot"
            if current_robot_index == 0:
                asset_path = self._asset_path + "/Robots/Transporter"
                robot_usd = asset_path + "/transporter.usd"
                self._robot_chassis = self._robot_prim_path + "/chassis"
                self._robot_wheels = ["left_wheel_joint", "right_wheel_joint"]
                self._robot_wheels_speed = [3, 3]
            elif current_robot_index == 1:
                asset_path = self._asset_path + "/Robots/Carter"
                robot_usd = asset_path + "/carter_sphere_wheels_lidar.usd"
                self._robot_chassis = self._robot_prim_path + "/chassis_link"
                self._robot_wheels = ["left_wheel", "right_wheel"]
                self._robot_wheels_speed = [2, 2]

            set_up_z_axis(self._stage)
            setup_physics(self._stage)

            create_background(
                self._stage,
                self._asset_path + "/Environments/Grid/gridroom_curved.usd",
                background_path="/background",
                offset=Gf.Vec3d(0, 0, -9),
            )

            # setup high-level robot prim
            self.prim = self._stage.DefinePrim(self._robot_prim_path, "Xform")
            self.prim.GetReferences().AddReference(robot_usd)

    def _on_stage_event(self, event):
        self.stage = self._usd_context.get_stage()
        if event.type == int(omni.usd.StageEventType.OPENED):
            self._move_btn.enabled = self._setup_done
            self._rotate_btn.enabled = self._setup_done
            self._navigate_btn.enabled = self._setup_done
            self._stop_btn.enabled = self._setup_done
            if self._rc:
                self._rc.enable_navigation(False)
            self._setup_done = False

    async def _play(self, task):
        done, pending = await asyncio.wait({task})
        if task in done:
            self._timeline.play()
            await asyncio.sleep(1)

    async def _on_setup_fn(self, task):
        done, pending = await asyncio.wait({task})
        if task in done:
            self._stage = self._usd_context.get_stage()
            # setup robot controller
            self._rc = RobotController(
                self._stage,
                self._timeline,
                self._dc,
                self._robot_prim_path,
                self._robot_chassis,
                self._robot_wheels,
                self._robot_wheels_speed,
                [1, 0.05],
            )
            self._rc.control_setup()
            # start stepping
            self._editor_event_subscription = (
                omni.kit.app.get_app().get_update_event_stream().create_subscription_to_pop(self._rc.update)
            )

    def _on_environment_setup(self):
        # wait for new stage before creating robot
        task = asyncio.ensure_future(omni.usd.get_context().new_stage_async())
        task1 = asyncio.ensure_future(self._create_robot(task))
        # set editor to play before setting up robot controller
        task2 = asyncio.ensure_future(self._play(task1))
        asyncio.ensure_future(self._on_setup_fn(task2))

        # self._load_btn.enabled=False
        self._move_btn.enabled = True
        self._rotate_btn.enabled = True
        self._navigate_btn.enabled = True
        self._stop_btn.enabled = True
        self._setup_done = True

    def _on_move_fn(self):
        print("Moving forward")
        self._rc.control_command(3, 3)

    def _on_rotate_fn(self):
        print("Rotating in-place")
        self._rc.control_command(3, -3)

    def _on_navigate_fn(self):
        goal_x = self.goal_coord["X"].model.get_value_as_float()
        goal_y = self.goal_coord["Y"].model.get_value_as_float()
        goal_z = self.goal_coord["Z"].model.get_value_as_float()
        print("Navigating to goal ({}, {}, {})".format(goal_x, goal_y, goal_z))
        self._rc.set_goal(goal_x, goal_y, goal_z)
        self._rc.enable_navigation(True)

    def _on_navigate_stop_fn(self):
        print("Navigation Stopped")
        self._rc.enable_navigation(False)
        self._rc.control_command(0, 0)

    def on_shutdown(self):
        self._rc = None
        self._timeline.stop()
        self._editor_event_subscription = None
        remove_menu_items(self._menu_items, "Isaac Examples")
        self._window = None
        gc.collect()
