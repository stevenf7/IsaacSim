# Copyright (c) 2018-2024, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

import asyncio
import weakref
from abc import abstractmethod

import omni.ext
import omni.ui as ui
from isaacsim.core.api import World
from isaacsim.examples.browser import get_instance as get_browser_instance
from isaacsim.examples.interactive.base_sample import BaseSample
from isaacsim.gui.components.ui_utils import btn_builder, get_style, setup_ui_headers


class BaseSampleExtension(omni.ext.IExt):
    def on_startup(self, ext_id: str):
        self._buttons = None
        self._ext_id = ext_id
        self._sample = None
        self._extra_frames = []
        self._menu_dicts = None
        return

    def start_extension(
        self,
        menu_name: str,
        submenu_name: str,
        name: str,
        title: str,
        doc_link: str,
        overview: str,
        file_path: str,
        sample=None,
    ):
        if sample is None:
            self._sample = BaseSample()
        else:
            self._sample = sample

        self.example_name = name
        self.category = menu_name

        self._menu_dicts = {
            "file_path": file_path,
            "title": title,
            "doc_link": doc_link,
            "overview": overview,
        }

        self._buttons = dict()

        # register the example with examples browser
        get_browser_instance().register_example(
            name=name, execute_entrypoint=self.build_window, ui_hook=self.build_ui, category=menu_name
        )

        # note: can't use weakref here, cause it's gets garbage collected during hotloading?
        # instances of what is getting garbage collected?

        return

    @property
    def sample(self):
        return self._sample

    def get_world(self):
        return World.instance()

    def build_window(self):
        # separating out building the window and building the UI, so that example browser can build_ui but not the window
        # self._window = omni.ui.Window(
        #     self.example_name, width=350, height=0, visible=True, dockPreference=ui.DockPreference.LEFT_BOTTOM
        # )
        # with self._window.frame:
        #     self.build_ui()
        # return self._window
        pass

    def build_ui(self):
        # separating out building default frame and extra frames, so examples can override the extra frames function
        self.build_default_frame()
        self.build_extra_frames()
        return

    def build_default_frame(self):
        file_path = self._menu_dicts["file_path"]
        title = self._menu_dicts["title"]
        doc_link = self._menu_dicts["doc_link"]
        overview = self._menu_dicts["overview"]

        self._main_stack = ui.VStack(spacing=5, height=0)
        with self._main_stack:
            setup_ui_headers(self._ext_id, file_path, title, doc_link, overview, info_collapsed=False)
            self._controls_frame = ui.CollapsableFrame(
                title="World Controls",
                width=ui.Fraction(1),
                height=0,
                collapsed=False,
                style=get_style(),
                horizontal_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_AS_NEEDED,
                vertical_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_ALWAYS_ON,
            )
            extra_stacks = ui.VStack(margin=5, spacing=5, height=0)

        with self._controls_frame:
            with ui.VStack(style=get_style(), spacing=5, height=0):
                dict = {
                    "label": "Load World",
                    "type": "button",
                    "text": "Load",
                    "tooltip": "Load World and Task",
                    "on_clicked_fn": self._on_load_world,
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

        return extra_stacks

    def build_extra_frames(self):
        # print("no extra frames to build here")
        return

    def _on_load_world(self):
        async def _on_load_world_async():
            await self._sample.load_world_async()
            await omni.kit.app.get_app().next_update_async()
            self._sample._world.add_stage_callback("stage_event_1", self.on_stage_event)
            self._enable_all_buttons(True)
            self._buttons["Load World"].enabled = False
            self.post_load_button_event()
            self._sample._world.add_timeline_callback("stop_reset_event", self._reset_on_stop_event)

        asyncio.ensure_future(_on_load_world_async())
        return

    def _on_reset(self):
        async def _on_reset_async():
            await self._sample.reset_async()
            await omni.kit.app.get_app().next_update_async()
            self.post_reset_button_event()

        asyncio.ensure_future(_on_reset_async())
        return

    @abstractmethod
    def post_reset_button_event(self):
        return

    @abstractmethod
    def post_load_button_event(self):
        return

    @abstractmethod
    def post_clear_button_event(self):
        return

    def _enable_all_buttons(self, flag):
        for btn_name, btn in self._buttons.items():
            if isinstance(btn, omni.ui._ui.Button):
                btn.enabled = flag
        return

    def on_shutdown(self):

        self._extra_frames = []
        self._buttons = {}
        # if self._sample._world is not None:
        #     self._sample._world_cleanup()
        if self._buttons is not None:  ## something about passing this point triggers another error
            self._buttons["Load World"].enabled = True
            self._enable_all_buttons(False)
        self.shutdown_cleanup()
        return

    def shutdown_cleanup(self):
        get_browser_instance().deregister_example(name=self.example_name, category=self.category)
        return

    def _sample_window_cleanup(self):
        self._window = None
        self._buttons = None
        return

    def on_stage_event(self, event):
        if event.type == int(omni.usd.StageEventType.CLOSED):
            if World.instance() is not None:
                self.sample._world_cleanup()
                self.sample._world.clear_instance()
                if hasattr(self, "_buttons"):
                    if self._buttons is not None:
                        self._enable_all_buttons(False)
                        self._buttons["Load World"].enabled = True
        return

    def _reset_on_stop_event(self, e):
        if e.type == int(omni.timeline.TimelineEventType.STOP):
            self._buttons["Load World"].enabled = False
            self._buttons["Reset"].enabled = True
            self.post_clear_button_event()
        return
