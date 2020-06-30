# Copyright (c) 2018-2020, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

import carb
import os
import omni.usd
import omni.syntheticdata._syntheticdata as gt
import omni.kit.ui
import omni.kit.editor
import omni.ui as ui
import numpy as np
from omni.kit.settings import get_settings_interface
from omni.kit import pipapi
from PIL import Image
from pxr import Usd, UsdGeom, Semantics

pipapi.install("pillow")
pipapi.install("matplotlib")

EXTENSION_NAME = "Synthetic Data Recorder"


class Extension(omni.ext.IExt):
    def on_startup(self):
        """Caled to load the extension"""
        self._editor = omni.kit.editor.get_editor_interface()
        self._stage = omni.usd.get_context()
        self._display_paths = []
        self._interface = gt.acquire_syntheticdata_interface()
        self._enable_record = False
        self._counter = 0
        self._window = ui.Window(EXTENSION_NAME, width=600, height=400)
        self._menu_entry = omni.kit.ui.get_editor_menu().add_item(f"Window/Isaac/{EXTENSION_NAME}", self._menu_callback)
        self._window.visible = False
        self.sub_update = self._editor.subscribe_to_update_events(self._update)
        self._settings = get_settings_interface()
        self._build_window_ui()
        self._accumulated_time = 0

    def on_shutdown(self):
        """Called when the extesion us unloaded"""
        self._window = None

    def _menu_callback(self, a, b):
        self._window.visible = not self._window.visible

    def _build_window_ui(self):
        with self._window.frame:
            with ui.CollapsableFrame("Settings"):
                with ui.VStack(spacing=5):
                    with ui.HStack():
                        ui.Spacer(width=10)
                        self._ui_dir_label = ui.Label("Output Directory:", width=100)
                        default_dir = os.path.join(os.getcwd(), "data")
                        self._ui_dir_name = ui.StringField(width=300)
                        self._ui_dir_name.model.set_value(default_dir)
                    with ui.HStack():
                        ui.Spacer(width=10)
                        self._ui_render_mode_label = ui.Label("Render Mode: ", width=100)
                        self._ui_render_mode = ui.ComboBox(0, "Use Current", "RayTracing", "PathTracing", width=300)
                    with ui.HStack():
                        ui.Spacer(width=10)
                        self._ui_dir_label = ui.Label("Capture period in seconds:", width=150)
                        self._capture_period = ui.FloatField(width=250)
                        # 0 means capture every frame
                        self._capture_period.model.set_value(0.0)
                    with ui.HStack():
                        ui.Spacer(width=5)
                        self._capture_btn = ui.Button("Start Recording", width=100)
                        self._capture_btn.set_clicked_fn(self.generate_data_fn)
                        self._reset_btn = ui.Button("Reset", width=50)
                        self._reset_btn.set_clicked_fn(self.reset_counter_fn)

    def generate_data_fn(self):
        current_render_index = self._ui_render_mode.model.get_item_value_model().as_int
        self._enable_record = not self._enable_record
        if current_render_index == 1:
            self._settings.set_string("/rtx/rendermode", "RayTracing")
            carb.log_warn("Switching to RayTracing Mode")
        elif current_render_index == 2:
            self._settings.set_string("/rtx/rendermode", "PathTracing")
            carb.log_warn("Switching to PathTracing Mode")
        else:
            carb.log_warn("Keeping current Render Mode")

        if self._enable_record:
            print("Generating Data!")
            self._capture_btn.text = "Stop Recording"
        else:
            self._capture_btn.text = "Start Recording"

    def reset_counter_fn(self):
        self._counter = 0

    def _update(self, dt):
        if self._enable_record == False:
            return

        if self._accumulated_time < self._capture_period.model.get_value_as_float():
            self._accumulated_time += dt
            return

        # reset _accumulated_time
        self._accumulated_time = 0

        data_dir = str(self._ui_dir_name.model.get_value_as_string())
        if not os.path.exists(data_dir):
            os.mkdir(data_dir)
        self._render_mode = str(self._settings.get("/rtx/rendermode"))
        self._enable_rgb = self._settings.get("/syntheticdata/sensors/rgbSensor")
        self._enable_depth = self._settings.get("/syntheticdata/sensors/depthLinearSensor")
        self._enable_instance = self._settings.get("/syntheticdata/sensors/instanceSegmentationSensor")

        # RGB
        if self._enable_rgb:
            rgb_sensor = gt.SensorType.Rgb
            rgb_width = self._interface.get_sensor_width(rgb_sensor)
            rgb_height = self._interface.get_sensor_height(rgb_sensor)
            rgb_row_size = self._interface.get_sensor_row_size(rgb_sensor)
            rgb_data = self._interface.get_sensor_host_uint32_texture_array(
                rgb_sensor, rgb_width, rgb_height, rgb_row_size
            )
            rgb_image_data = np.frombuffer(rgb_data, dtype=np.uint8).reshape(*rgb_data.shape, -1)
            # Save ground truth data locally as png
            rgb_folder = data_dir + "/rgb/"
            if not os.path.exists(rgb_folder):
                os.mkdir(rgb_folder)
            rgb_render = Image.fromarray(rgb_image_data)
            rgb_render.save(rgb_folder + str(self._counter) + ".png")

        # Depth
        if self._enable_depth and "Ray" in self._render_mode:
            depth_sensor = gt.SensorType.DepthLinear
            depth_width = self._interface.get_sensor_width(depth_sensor)
            depth_height = self._interface.get_sensor_height(depth_sensor)
            depth_row_size = self._interface.get_sensor_row_size(depth_sensor)
            depth_data = self._interface.get_sensor_host_float_texture_array(
                depth_sensor, depth_width, depth_height, depth_row_size
            )
            depth_data = np.clip(depth_data, 0, 255)
            depth_image_data = depth_data.astype(np.uint8)
            # Save ground truth data locally as png
            depth_folder = data_dir + "/depth/"
            if not os.path.exists(depth_folder):
                os.mkdir(depth_folder)
            depth_render = Image.fromarray(depth_image_data)
            depth_render.save(depth_folder + str(self._counter) + ".png")

        # Instance Segmentation
        if self._enable_instance and "Ray" in self._render_mode:
            instance_sensor = gt.SensorType.InstanceSegmentation
            instance_width = self._interface.get_sensor_width(instance_sensor)
            instance_height = self._interface.get_sensor_height(instance_sensor)
            instance_row_size = self._interface.get_sensor_row_size(instance_sensor)
            instance_size = self._interface.get_sensor_size(instance_sensor)
            instance_data = self._interface.get_sensor_host_uint32_texture_array(
                instance_sensor, instance_width, instance_height, instance_row_size
            )
            # Save ground truth data locally as npy
            instance_folder = data_dir + "/segmentation/"
            if not os.path.exists(instance_folder):
                os.mkdir(instance_folder)
            np.save(instance_folder + str(self._counter) + ".npy", instance_data)

        self._counter = self._counter + 1
