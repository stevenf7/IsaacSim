# Copyright (c) 2018-2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

from abc import abstractmethod
import omni.ext
import omni.ui as ui
from omni.kit.menu.utils import add_menu_items, remove_menu_items, MenuItemDescription
import weakref
import gc
from omni.isaac.core import World
from omni.isaac.ui.ui_utils import setup_ui_headers, get_style, btn_builder
import asyncio


class BaseSample(omni.ext.IExt):
    def on_startup(self, ext_id: str):
        self._world = None
        self._menu_items = None
        self._buttons = None
        self._task = None
        self._ext_id = ext_id
        return

    def _on_startup(
        self,
        menu_name: str,
        submenu_name: str,
        name: str,
        buttons_mapping: dict,
        title: str,
        doc_link: str,
        overview: str,
        file_path: str,
        physics_dt: float = 1.0 / 60.0,
        stage_units_in_meters: float = 1.0,
    ):
        self._world = None
        menu_items = [MenuItemDescription(name=name, onclick_fn=lambda a=weakref.proxy(self): a._menu_callback())]
        self._menu_items = [
            MenuItemDescription(name=menu_name, sub_menu=[MenuItemDescription(name=submenu_name, sub_menu=menu_items)])
        ]

        add_menu_items(self._menu_items, "Isaac Examples")
        self._buttons = dict()
        self._build_ui(
            name=name,
            title=title,
            doc_link=doc_link,
            overview=overview,
            buttons_mapping=buttons_mapping,
            file_path=file_path,
        )

        self._world_settings = {"physics_dt": physics_dt, "stage_units_in_meters": stage_units_in_meters}
        return

    def _build_ui(self, name, title, doc_link, overview, buttons_mapping, file_path):
        self._window = omni.ui.Window(
            name, width=500, height=0, visible=False, dockPreference=ui.DockPreference.LEFT_BOTTOM
        )
        with self._window.frame:
            with ui.VStack(spacing=5, height=0):

                setup_ui_headers(self._ext_id, file_path, title, doc_link, overview)

                frame = ui.CollapsableFrame(
                    title="Command Panel",
                    height=0,
                    collapsed=False,
                    style=get_style(),
                    style_type_name_override="CollapsableFrame",
                    horizontal_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_AS_NEEDED,
                    vertical_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_ALWAYS_ON,
                )
                with frame:
                    with ui.VStack(style=get_style(), spacing=5):
                        dict = {
                            "label": "Load World",
                            "type": "button",
                            "text": "Load",
                            "tooltip": "Load World and Task",
                            "on_clicked_fn": self._on_setup_world,
                        }
                        self._buttons["Load World"] = btn_builder(**dict)
                        self._buttons["Load World"].enabled = True
                        dict = {
                            "label": "Reset",
                            "type": "button",
                            "text": "Reset",
                            "tooltip": "Reset robot and environment",
                            "on_clicked_fn": self._on_reset,
                        }
                        self._buttons["Reset"] = btn_builder(**dict)
                        self._buttons["Reset"].enabled = False
                        for button_name, button_fn in buttons_mapping.items():
                            dict = {
                                "label": button_name,
                                "type": "button",
                                "text": button_name,
                                "tooltip": button_name,
                                "on_clicked_fn": button_fn,
                            }
                            self._buttons[button_name] = btn_builder(**dict)
                            self._buttons[button_name].enabled = False
        return

    def _set_button_tooltip(self, button_name, tool_tip):
        self._buttons[button_name].set_tooltip(tool_tip)
        return

    def _on_setup_world(self):
        async def _on_setup_world_async():
            self._world = World(**self._world_settings)
            await self._world.init_world_async()
            self._task = self._load_task()
            self._world.load_task(self._task)
            await self._world.reset_async()
            self._world.add_physics_callback("task_step", self.task_simulation_step)
            self._setup_controllers()
            self._buttons["Load World"].enabled = False
            self._enable_all_buttons(True)
            self._world.add_stage_callback("stage_event_1", self._on_stage_event)
            self._reset_call()
            return

        asyncio.ensure_future(_on_setup_world_async())
        return

    @abstractmethod
    def _load_task(self):
        raise NotImplementedError

    @abstractmethod
    def _setup_controllers(self):
        raise NotImplementedError

    def _enable_all_buttons(self, flag):
        for btn_name, btn in self._buttons.items():
            if btn_name != "Load World":
                btn.enabled = flag
        return

    def _on_reset(self):
        async def _on_reset_async():
            await self._world.reset_async()
            self._enable_all_buttons(True)
            self._reset_call()
            self._world.remove_physics_callback("task_step")
            if self._world._scene_finalized and self._world._current_task is not None:
                self._world.add_physics_callback("task_step", self.task_simulation_step)

        asyncio.ensure_future(_on_reset_async())
        return

    def task_simulation_step(self, step_size):
        self._world._current_task.step(self._world.time_step_index, self._world.time)
        return

    def _reset_call(self):
        raise NotImplementedError

    def _menu_callback(self):
        self._window.visible = not self._window.visible
        return

    def _on_window(self, status):
        if status:
            # TODO: logging
            print("openning window..")
        return

    def on_shutdown(self):
        if self._world is not None:
            self._world_cleanup()
        if self._menu_items is not None:
            self._sample_window_cleanup()
        return

    def _sample_window_cleanup(self):
        remove_menu_items(self._menu_items, "Isaac Examples")
        self._window = None
        self._menu_items = None
        self._buttons = None
        gc.collect()
        return

    def _world_cleanup(self):
        self._world.stop()
        self._world.clear_physics_callbacks()
        self._world.clear_stage_callbacks()
        gc.collect()
        self._world = None
        self._task = None
        if self._buttons is not None:
            self._buttons["Load World"].enabled = True
            self._enable_all_buttons(False)
        return

    def _on_stage_event(self, event):
        if event.type == int(omni.usd.StageEventType.CLOSED):
            if self._world is not None:
                self._world_cleanup()
        return
