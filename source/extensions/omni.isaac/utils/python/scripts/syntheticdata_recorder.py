# Copyright (c) 2018-2020, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

import carb
import omni.syntheticdata._syntheticdata as gt
import omni.kit.ui
import omni.kit.editor
import omni.ui as ui

import atexit
import queue
import os
import threading
import numpy as np

from omni.kit.settings import get_settings_interface
from omni.kit import pipapi
from PIL import Image

pipapi.install("pillow")
pipapi.install("matplotlib")

EXTENSION_NAME = "Synthetic Data Recorder"


class DataWriter:
    def __init__(self, data_dir):
        atexit.register(self.stop_threads)
        self.data_dir = data_dir

        # Threading for multiple scenes
        self.num_worker_threads = 4
        self.q = queue.Queue()
        self.threads = []

        self.check_for_output_folder()

    def start_threads(self):
        # Start worker threads
        for _ in range(self.num_worker_threads):
            t = threading.Thread(target=self.worker, daemon=True)
            t.start()
            self.threads.append(t)

    def stop_threads(self):
        print(f"Finish writing data...")

        # Block until all tasks are done
        self.q.join()

        # Stop workers
        for _ in range(self.num_worker_threads):
            self.q.put(None)
        for t in self.threads:
            t.join()

        print(f"Done.")

    def worker(self):
        while True:
            groundtruth = self.q.get()
            if groundtruth is None:
                break
            filename = groundtruth["METADATA"]["image_id"]
            for gt_type, data in groundtruth["DATA"].items():
                if gt_type in ["DEPTH", "RGB"]:
                    self.save_image(gt_type, data, filename)
                elif gt_type == "INSTANCE":
                    self.save_segmentation(data, filename)
                else:
                    raise NotImplementedError
            self.q.task_done()

    def save_segmentation(self, data, filename):
        # Save ground truth data locally as npy
        np.save(self.instance_folder + filename + ".npy", data)

    def save_image(self, img_type, image_data, filename):
        if img_type == "RGB":
            # Save ground truth data locally as png
            rgb_img = Image.fromarray(image_data, "RGBA")
            rgb_img.save(f"{self.rgb_folder}/{filename}.png")
        elif img_type == "DEPTH":
            # Save ground truth data locally as png
            image_data[image_data == 0.0] = 1e-5
            image_data = np.clip(image_data, 0, 255)
            image_data -= np.min(image_data)
            image_data /= np.max(image_data)
            depth_img = Image.fromarray((image_data * 255.0).astype(np.uint8))
            depth_img.save(f"{self.depth_folder}/{filename}.png")

    def check_for_output_folder(self):
        if not os.path.exists(self.data_dir):
            os.mkdir(self.data_dir)
        self.rgb_folder = self.data_dir + "/rgb/"
        if not os.path.exists(self.rgb_folder):
            os.mkdir(self.rgb_folder)
        self.depth_folder = self.data_dir + "/depth/"
        if not os.path.exists(self.depth_folder):
            os.mkdir(self.depth_folder)
        self.instance_folder = self.data_dir + "/segmentation/"
        if not os.path.exists(self.instance_folder):
            os.mkdir(self.instance_folder)


class Extension(omni.ext.IExt):
    def on_startup(self):
        """Caled to load the extension"""
        self._editor = omni.kit.editor.get_editor_interface()
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
        self.data_writer = None

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

    def rename_button(self):
        if self._enable_record:
            print("Generating Data!")
            self.data_writer = None
            self._capture_btn.text = "Stop Recording"
        else:
            self._capture_btn.text = "Start Recording"

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
        self.rename_button()

    def reset_counter_fn(self):
        self._counter = 0

    def _update(self, dt):
        if self._enable_record == False:
            return

        if not self._editor.is_playing():
            print("Cannot Generate Data! Editor is not playing.")
            self._enable_record = False
            self.rename_button()
            return

        if self._accumulated_time < self._capture_period.model.get_value_as_float():
            self._accumulated_time += dt
            return

        # reset _accumulated_time
        self._accumulated_time = 0

        data_dir = str(self._ui_dir_name.model.get_value_as_string())

        if self.data_writer is None:
            self.data_writer = DataWriter(data_dir)
            self.data_writer.start_threads()

        self._render_mode = str(self._settings.get("/rtx/rendermode"))
        self._enable_rgb = self._settings.get("/syntheticdata/sensors/rgbSensor")
        self._enable_depth = self._settings.get("/syntheticdata/sensors/depthLinearSensor")
        self._enable_instance = self._settings.get("/syntheticdata/sensors/instanceSegmentationSensor")

        groundtruth = {"METADATA": {"image_id": str(self._counter)}, "DATA": {}}
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
            groundtruth["DATA"]["RGB"] = rgb_image_data

        # Depth
        if self._enable_depth and "Ray" in self._render_mode:
            depth_sensor = gt.SensorType.DepthLinear
            depth_width = self._interface.get_sensor_width(depth_sensor)
            depth_height = self._interface.get_sensor_height(depth_sensor)
            depth_row_size = self._interface.get_sensor_row_size(depth_sensor)
            depth_data = self._interface.get_sensor_host_float_texture_array(
                depth_sensor, depth_width, depth_height, depth_row_size
            )
            groundtruth["DATA"]["DEPTH"] = depth_data

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
            groundtruth["DATA"]["INSTANCE"] = instance_data

        self.data_writer.q.put(groundtruth)

        self._counter = self._counter + 1
