# Copyright (c) 2018-2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

import carb
import omni
import omni.syntheticdata._syntheticdata as gt
import omni.ui as ui
from omni.kit.menu.utils import add_menu_items, remove_menu_items, MenuItemDescription

import asyncio
import os
import numpy as np
import weakref

from . import scenario, dataset, train
from carb.settings import get_settings
from PIL import Image
from omni.isaac.synthetic_utils import SyntheticDataHelper
from omni.isaac.ui.ui_utils import (
    setup_ui_headers,
    btn_builder,
    dropdown_builder,
    get_style,
    str_builder,
    progress_bar_builder,
    combo_floatfield_slider_builder,
)

EXTENSION_NAME = "Synthetic Data Workflow"


class Extension(omni.ext.IExt):
    def on_startup(self, ext_id: str):
        ext_manager = omni.kit.app.get_app().get_extension_manager()
        self._ext_id = ext_id
        self._extension_path = ext_manager.get_extension_path(ext_id)

        """Caled to load the extension"""
        self._timeline = omni.timeline.get_timeline_interface()
        self._interface = gt.acquire_syntheticdata_interface()
        self._counter = 0
        self._window = ui.Window(EXTENSION_NAME, width=600, height=400, visible=True)
        self._window.set_visibility_changed_fn(self._on_window)
        self._window.deferred_dock_in("Console", omni.ui.DockPolicy.DO_NOTHING)
        self._window.visible = False
        self._menu_items = [
            MenuItemDescription(name=EXTENSION_NAME, onclick_fn=lambda a=weakref.proxy(self): a._menu_callback())
        ]
        add_menu_items(self._menu_items, "Synthetic Data")
        self._settings = get_settings()
        self.progress = {}
        self._build_window_ui()
        self.sd_helper = SyntheticDataHelper()

        self._visualize_window = omni.ui.Window("Visualization", width=800, height=600)
        self._visualize_window.deferred_dock_in("Viewport", omni.ui.DockPolicy.CURRENT_WINDOW_IS_ACTIVE)
        self._visualize_window.visible = False

        self._stats_window = omni.ui.Window("Dataset Statistics", width=400, height=300)
        self._stats_window.visible = False

        self.is_training = False
        self.is_dataloading = False

        self._byte_providers = None

    def on_shutdown(self):
        """Called when the extesion us unloaded"""
        remove_menu_items(self._menu_items, "Synthetic Data")
        self._window = None

    def _on_window(self, status):
        if status:
            self._sub_update = omni.kit.app.get_app().get_update_event_stream().create_subscription_to_pop(self._update)
        else:
            self._sub_update = None

    def _menu_callback(self):
        self._window.visible = not self._window.visible

    def _build_window_ui(self):
        with self._window.frame:
            with ui.VStack(spacing=5):
                title = "Synthetic Data Workflow"
                doc_link = "https://docs.omniverse.nvidia.com/app_isaacsim/app_isaacsim/sample_syntheticdata.html"

                overview = "This extension presents the synthetic data workflow in Isaac Sim."
                overview += (
                    "\n\nLOAD a base scene, and then ADD randomization to the scene. Press PREVIEW SCENE to validate."
                )
                overview += "\n\nADD semantics using Semantic Schema Editor tool. Go to Synthetic Data -> Semantic Schema Editor."
                overview += "\n\nRECORD offline synthetic data using Synthetic Data Recorder tool. Go to Synthetic Data -> Synthetic Data Recorder."
                overview += "\n\nVISUALIZE recorded synthetic data. SELECT network and start training."
                overview += "\n\nPress the 'Open in IDE' button to view the source code."

                setup_ui_headers(self._ext_id, __file__, title, doc_link, overview)

                with ui.CollapsableFrame(
                    "Scene and Randomization",
                    height=0,
                    collapsed=False,
                    style=get_style(),
                    style_type_name_override="CollapsableFrame",
                    horizontal_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_AS_NEEDED,
                    vertical_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_ALWAYS_ON,
                ):
                    with ui.VStack(spacing=5):
                        args = {
                            "label": "Base Scene",
                            "default_val": 0,
                            "tooltip": "Select the base scene to load",
                            "items": ["Basic Assets", "Simple Room", "Simple Warehouse"],
                        }
                        self._selected_scenario = dropdown_builder(**args)

                        args = {
                            "label": "Load Scene",
                            "type": "button",
                            "text": "Load",
                            "tooltip": "Load the base scene",
                            "on_clicked_fn": self.load_scene_fn,
                        }
                        self._load_btn = btn_builder(**args)

                        args = {
                            "label": "Select randomization",
                            "default_val": 0,
                            "tooltip": "Select the type of randomization behavior",
                            "items": ["Color", "Texture", "Camera", "Light", "Transform"],
                        }
                        self._selected_dr = dropdown_builder(**args)

                        args = {
                            "label": "Add randomization",
                            "type": "button",
                            "text": "Add",
                            "tooltip": "Add the randomization behavior to the base scene",
                            "on_clicked_fn": self.add_dr_fn,
                        }
                        self._add_dr_btn = btn_builder(**args)

                        args = {
                            "label": "Preview Scene",
                            "type": "button",
                            "text": "Preview",
                            "tooltip": "Validate the randomized scene",
                            "on_clicked_fn": self.preview_scene_fn,
                        }
                        self._preview_scene_btn = btn_builder(**args)
                with ui.CollapsableFrame(
                    "Semantics",
                    height=0,
                    collapsed=False,
                    style=get_style(),
                    style_type_name_override="CollapsableFrame",
                    horizontal_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_AS_NEEDED,
                    vertical_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_ALWAYS_ON,
                ):
                    with ui.VStack(spacing=5):
                        self._sem_label = ui.Label(
                            "Use `Synthetic Data -> Semantic Schema Editor` tool to add semantics", width=100
                        )
                with ui.CollapsableFrame(
                    "Record dataset",
                    height=0,
                    collapsed=False,
                    style=get_style(),
                    style_type_name_override="CollapsableFrame",
                    horizontal_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_AS_NEEDED,
                    vertical_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_ALWAYS_ON,
                ):
                    with ui.VStack(spacing=5):
                        self._record_label = ui.Label(
                            "Use `Synthetic Data -> Synthetic Data Recorder` tool to record synthetic data offline",
                            width=100,
                        )
                with ui.CollapsableFrame(
                    "Training",
                    height=0,
                    collapsed=False,
                    style=get_style(),
                    style_type_name_override="CollapsableFrame",
                    horizontal_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_AS_NEEDED,
                    vertical_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_ALWAYS_ON,
                ):
                    with ui.VStack(spacing=5):
                        default_dir = os.path.join(os.getcwd(), "output")
                        kwargs = {
                            "label": "Input Directory",
                            "type": "stringfield",
                            "default_val": default_dir,
                            "tooltip": "Click the Folder Icon to Set Filepath",
                            "use_folder_picker": True,
                        }
                        self._ui_dir_name = str_builder(**kwargs)

                        args = {
                            "label": "Training Scenario",
                            "default_val": 0,
                            "tooltip": "Select which type of network to train",
                            "items": ["Object Detection", "Instance Segmentation"],
                        }
                        self._selected_train_scenario = dropdown_builder(**args)

                        # self._dataset_vis_label = ui.Label("Dataset Visualizer", width=100)
                        args = {
                            "label": "Load Data",
                            "type": "button",
                            "text": "Load",
                            "tooltip": "Load offine dataset",
                            "on_clicked_fn": self.load_fn,
                        }
                        self._load_btn = btn_builder(**args)

                        args = {
                            "label": "Statistics",
                            "type": "button",
                            "text": "Generate",
                            "tooltip": "Get statistics from offine dataset",
                            "on_clicked_fn": self.stats_fn,
                        }
                        self._stats_btn = btn_builder(**args)

                        args = {
                            "label": "Select data",
                            "default_val": 0,
                            "min": 0,
                            "max": 1,
                            "step": 0.00001,
                            "tooltip": ["", ""],
                        }
                        flt_field, self._data_slider = combo_floatfield_slider_builder(**args)

                        args = {
                            "label": "Visualize data",
                            "type": "button",
                            "text": "Visualize",
                            "tooltip": "Visualize offine dataset",
                            "on_clicked_fn": self.next_fn,
                        }
                        self._next_btn = btn_builder(**args)

                        # self._dataset_vis_label = ui.Label("Training Visualizer", width=100)
                        args = {
                            "label": "Start Training",
                            "type": "button",
                            "text": "Start",
                            "tooltip": "Start training based on the selected network",
                            "on_clicked_fn": self.train_fn,
                        }
                        self._train_btn = btn_builder(**args)

                        self.progress["bar1"] = progress_bar_builder("Training Progress")
                        # self.progress["bar1"] = ui.ProgressBar(width=400, style={"font_size": 15.0}).model

    def load_scene_fn(self):
        self.new_scene = scenario.RandomScenario()
        idx = self._selected_scenario.get_item_value_model().as_int
        if idx == 0:
            self.new_scene.setup_world()
        elif idx == 1:
            self.new_scene.add_simple_room_scene()
        elif idx == 2:
            self.new_scene.add_warehouse_scene()

    def add_dr_fn(self):
        idx = self._selected_dr.get_item_value_model().as_int
        self.new_scene.add_dr(idx)

    def preview_scene_fn(self):
        self.new_scene.preview_scene()

    def _build_visualization_ui(self, image, window):
        if image.shape[2] == 3:
            image = np.pad(image, ((0, 0), (0, 0), (0, 1)), constant_values=255)
        # Visualize via omni.ui
        self._byte_providers = omni.ui.ByteImageProvider()
        self._byte_providers.set_bytes_data(image.flatten().tolist(), [image.shape[1], image.shape[0]])

        self.build_sensor_grid(window)

    def _update_visualization_ui(self):
        self.build_sensor_grid(self._visualize_window)

    def build_sensor_grid(self, window):
        with window.frame:
            with omni.ui.VStack():
                omni.ui.ImageWithProvider(self._byte_providers, alignment=omni.ui.Alignment.CENTER_TOP)

    def setup_fn(self):
        pass

    async def _update_train_progress(self):
        while self.trainer.cur_iter <= self.trainer.iterations:
            self.progress["bar1"].set_value((self.trainer.cur_iter / self.trainer.iterations))
            await asyncio.sleep(0.5)  # check progress every 0.5 seconds

    async def track_load_fn(self, task):
        done, pending = await asyncio.wait({task})
        if task in done:
            self.is_dataloading = False

    def load_fn(self):
        self.data_folder_path = str(self._ui_dir_name.get_value_as_string())
        self.train_data = dataset.RandomObjects(self.data_folder_path)
        self.train_data.load_data()

    def next_fn(self):
        float_idx = self._data_slider.model.get_value_as_float()
        train_data_idx = int(len(self.train_data.gt_all) * float_idx)
        self._visualize_window.visible = True
        self.is_dataloading = True
        task = asyncio.ensure_future(dataset.visualize_data(self.train_data, train_data_idx))
        asyncio.ensure_future(self.track_load_fn(task))

    async def track_train_fn(self, task):
        await self._update_train_progress()
        done, pending = await asyncio.wait({task})
        if task in done:
            self.is_training = False
            self.trainer = None

    def train_fn(self):
        self.data_folder_path = str(self._ui_dir_name.get_value_as_string())
        network_index = self._selected_train_scenario.get_item_value_model().as_int
        network_name = "faster_rcnn" if network_index == 0 else "mask_rcnn"
        self._visualize_window.visible = True
        self.is_training = True
        self.trainer = train.Trainer(self.data_folder_path, iterations=148, network=network_name)
        task = asyncio.ensure_future(self.trainer.train())
        asyncio.ensure_future(self.track_train_fn(task))

    def pause_fn(self):
        self.is_dataloading = not self.is_dataloading
        if self.is_dataloading:
            self._pause_btn.text = "Pause"
        else:
            self._pause_btn.text = "Unpause"

    def visualize_train_fn(self):
        file_path = self.data_folder_path + "/train.png"
        if not os.path.exists(file_path):
            return
        image = np.asarray(Image.open(file_path))
        self._build_visualization_ui(image, self._visualize_window)

    def visualize_data_fn(self):
        file_path = self.data_folder_path + "/dataset.png"
        if not os.path.exists(file_path):
            return
        image = np.asarray(Image.open(file_path))
        self._build_visualization_ui(image, self._visualize_window)

    def stats_fn(self):
        self._stats_window.visible = True
        class_count = {}
        for entry in self.train_data.gt_all:
            gt_bbox = entry["boundingBox2DTight"]
            for bbox in gt_bbox:
                if bbox[2] not in class_count:
                    class_count[bbox[2]] = 0.0
                else:
                    class_count[bbox[2]] += 1.0
        with self._stats_window.frame:
            with omni.ui.VStack():
                with ui.HStack():
                    ui.Spacer(width=10)
                    label_data = ",".join([class_label for class_label in class_count])
                    ui.Label("Class Labels", width=160, alignment=ui.Alignment.LEFT_TOP)
                    ui.Label(label_data, width=160, alignment=ui.Alignment.LEFT_TOP)
                with ui.HStack():
                    ui.Spacer(width=10)
                    data = [class_count[class_label] for class_label in class_count]
                    ui.Label("Class Distribution", width=160, alignment=ui.Alignment.LEFT_TOP)
                    plot_height = 100
                    plot_width = ui.Fraction(1)
                    max_val = np.max(np.array(data))
                    with ui.ZStack():
                        ui.Rectangle(width=plot_width, height=plot_height)
                        color = 0xFFDDDDDD
                        ui.Plot(
                            ui.Type.HISTOGRAM,
                            0,
                            max_val,
                            *data,
                            value_stride=1,
                            width=plot_width,
                            height=plot_height,
                            style={"color": color, "background_color": 0x0},
                        )

    def _update(self, e: carb.events.IEvent):
        if self.is_training:
            self.visualize_train_fn()
        elif self.is_dataloading:
            self.visualize_data_fn()
