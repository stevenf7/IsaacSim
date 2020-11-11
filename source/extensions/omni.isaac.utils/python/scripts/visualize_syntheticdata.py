# Copyright (c) 2018-2020, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

import colorsys
import math
import numpy as np
import random
import omni.ext
import omni.usd
import omni.kit.editor
import omni.ui
import omni.syntheticdata._syntheticdata as gt
from carb.settings import get_settings
from omni.isaac.synthetic_utils import visualization as vis

EXTENSION_NAME = "Visualize Synthetic Data"


class Extension(omni.ext.IExt):
    def on_startup(self):
        """Caled to load the extension"""
        self._syntheticdata = gt.acquire_syntheticdata_interface()
        self._window = omni.ui.Window(EXTENSION_NAME, width=600, height=400)
        self._visualize_window = omni.ui.Window("Visualization", width=300, height=300)
        self._window.deferred_dock_in("Details")
        self._visualize_window.deferred_dock_in("Stage")
        self._menu_entry = omni.kit.ui.get_editor_menu().add_item(f"Window/Isaac/{EXTENSION_NAME}", self._menu_callback)
        self._settings = get_settings()
        self._window.visible = False
        self._visualize_window.visible = False
        self._rgb_enable = False
        self._depth_enable = False
        self._semantic_enable = False
        self._instance_enable = False
        self._bbox_2d_tight_enable = False
        self._bbox_2d_loose_enable = False
        self._build_window_ui()

    def on_shutdown(self):
        """Called when the extesion us unloaded"""
        self._window = None
        self._visualize_window = None

    def _menu_callback(self, a, b):
        self._window.visible = not self._window.visible
        self._visualize_window.visible = not self._visualize_window.visible

    def _build_window_ui(self):
        with self._window.frame:
            with omni.ui.VStack():

                def visualize_synthetic_data(window):
                    interface = gt.acquire_syntheticdata_interface()
                    # RGB - Numpy
                    if self._rgb_enable:
                        rgb_sensor = gt.SensorType.Rgb
                        rgb_width = interface.get_sensor_width(rgb_sensor)
                        rgb_height = interface.get_sensor_height(rgb_sensor)
                        rgb_row_size = interface.get_sensor_row_size(rgb_sensor)
                        rgb_data = interface.get_sensor_host_uint32_texture_array(
                            rgb_sensor, rgb_width, rgb_height, rgb_row_size
                        )
                        rgb_image = np.frombuffer(rgb_data, dtype=np.uint8).reshape(*rgb_data.shape, -1).flatten()

                    # Depth - Numpy
                    if self._depth_enable:
                        depth_sensor = gt.SensorType.Depth
                        depth_width = interface.get_sensor_width(depth_sensor)
                        depth_height = interface.get_sensor_height(depth_sensor)
                        depth_row_size = interface.get_sensor_row_size(depth_sensor)
                        depth_data = interface.get_sensor_host_float_texture_array(
                            depth_sensor, depth_width, depth_height, depth_row_size
                        )
                        colorize_depth_image = vis.colorize_depth(depth_data, depth_width, depth_height, num_channels=4)
                        colorize_depth_image = colorize_depth_image.reshape(colorize_depth_image.size).tolist()

                    # Instance Segmentation - Numpy
                    if self._instance_enable:
                        instance_sensor = gt.SensorType.InstanceSegmentation
                        instance_width = interface.get_sensor_width(instance_sensor)
                        instance_height = interface.get_sensor_height(instance_sensor)
                        instance_row_size = interface.get_sensor_row_size(instance_sensor)
                        instance_size = interface.get_sensor_size(instance_sensor)
                        instance_data = interface.get_sensor_host_uint32_texture_array(
                            instance_sensor, instance_width, instance_height, instance_row_size
                        )
                        image_instance_data = np.frombuffer(instance_data, dtype=np.uint8).reshape(
                            *instance_data.shape, -1
                        )
                        colorize_instance_image = vis.colorize_segmentation(
                            image_instance_data, instance_width, instance_height, num_channels=4
                        )
                        colorize_instance_image = colorize_instance_image.reshape(colorize_instance_image.size).tolist()

                    # Semantic Segmentation - Numpy
                    if self._semantic_enable:
                        semantic_sensor = gt.SensorType.SemanticSegmentation
                        semantic_width = interface.get_sensor_width(semantic_sensor)
                        semantic_height = interface.get_sensor_height(semantic_sensor)
                        semantic_row_size = interface.get_sensor_row_size(semantic_sensor)
                        semantic_size = interface.get_sensor_size(semantic_sensor)
                        semantic_data = interface.get_sensor_host_uint32_texture_array(
                            semantic_sensor, semantic_width, semantic_height, semantic_row_size
                        )
                        image_semantic_data = np.frombuffer(semantic_data, dtype=np.uint8).reshape(
                            *semantic_data.shape, -1
                        )
                        colorize_semantic_image = vis.colorize_segmentation(
                            image_semantic_data, semantic_width, semantic_height, num_channels=4, num_colors=20
                        )
                        colorize_semantic_image = colorize_semantic_image.reshape(colorize_semantic_image.size).tolist()

                    # BBox 2D Tight - Numpy
                    if self._bbox_2d_tight_enable and self._rgb_enable:
                        bboxes_2d_tight_sensor = gt.SensorType.BoundingBox2DTight
                        bboxes_2d_tight_size = interface.get_sensor_size(bboxes_2d_tight_sensor)
                        bboxes_2d_tight_data = interface.get_sensor_host_bounding_box_2d_buffer_array(
                            bboxes_2d_tight_sensor, bboxes_2d_tight_size
                        )
                        bboxes_2d_tight_rgb = np.frombuffer(rgb_data, dtype=np.uint8).reshape(
                            (rgb_height, rgb_width, 4)
                        )
                        bboxes_2d_tight_rgb = vis.colorize_bboxes(
                            bboxes_2d_tight_data, bboxes_2d_tight_rgb, num_channels=4
                        )
                        bboxes_2d_tight_rgb = bboxes_2d_tight_rgb.reshape(bboxes_2d_tight_rgb.size)

                    # BBox 2D Loose - Numpy
                    if self._bbox_2d_loose_enable and self._rgb_enable:
                        bboxes_2d_loose_sensor = gt.SensorType.BoundingBox2DLoose
                        bboxes_2d_loose_size = interface.get_sensor_size(bboxes_2d_loose_sensor)
                        bboxes_2d_loose_data = interface.get_sensor_host_bounding_box_2d_buffer_array(
                            bboxes_2d_loose_sensor, bboxes_2d_loose_size
                        )
                        bboxes_2d_loose_rgb = np.frombuffer(rgb_data, dtype=np.uint8).reshape(
                            (rgb_height, rgb_width, 4)
                        )
                        bboxes_2d_loose_rgb = vis.colorize_bboxes(
                            bboxes_2d_loose_data, bboxes_2d_loose_rgb, num_channels=4
                        )
                        bboxes_2d_loose_rgb = bboxes_2d_loose_rgb.reshape(bboxes_2d_loose_rgb.size)

                    # Visualize via omni.ui
                    label_list = []
                    byte_provider_list = []
                    if self._rgb_enable:
                        self._rgb_byte_provider = omni.ui.ByteImageProvider()
                        self._rgb_byte_provider.set_data(rgb_image.tolist(), [rgb_width, rgb_height])
                        label_list.append("RGB")
                        byte_provider_list.append(self._rgb_byte_provider)

                    if self._depth_enable:
                        self._depth_byte_provider = omni.ui.ByteImageProvider()
                        self._depth_byte_provider.set_data(colorize_depth_image, [depth_width, depth_height])
                        label_list.append("Depth")
                        byte_provider_list.append(self._depth_byte_provider)

                    if self._instance_enable:
                        self._instance_byte_provider = omni.ui.ByteImageProvider()
                        self._instance_byte_provider.set_data(
                            colorize_instance_image, [instance_width, instance_height]
                        )
                        label_list.append("Instance Segmentation")
                        byte_provider_list.append(self._instance_byte_provider)

                    if self._semantic_enable:
                        self._semantic_byte_provider = omni.ui.ByteImageProvider()
                        self._semantic_byte_provider.set_data(
                            colorize_semantic_image, [semantic_width, semantic_height]
                        )
                        label_list.append("Semantic Segmentation")
                        byte_provider_list.append(self._semantic_byte_provider)

                    if self._bbox_2d_tight_enable:
                        self._bbox_2d_tight_byte_provider = omni.ui.ByteImageProvider()
                        self._bbox_2d_tight_byte_provider.set_data(
                            bboxes_2d_tight_rgb.tolist(), [rgb_width, rgb_height]
                        )
                        label_list.append("2D Tight BBox")
                        byte_provider_list.append(self._bbox_2d_tight_byte_provider)

                    if self._bbox_2d_loose_enable:
                        self._bbox_2d_loose_byte_provider = omni.ui.ByteImageProvider()
                        self._bbox_2d_loose_byte_provider.set_data(
                            bboxes_2d_loose_rgb.tolist(), [rgb_width, rgb_height]
                        )
                        label_list.append("2D Loose BBox")
                        byte_provider_list.append(self._bbox_2d_loose_byte_provider)

                    num_sensors = len(label_list)
                    num_rows = math.floor(math.sqrt(num_sensors))
                    num_cols = math.ceil(num_sensors / num_rows)
                    with window.frame:
                        with omni.ui.VStack():
                            for r in range(num_rows):
                                with omni.ui.HStack():
                                    for c in range(num_cols):
                                        with omni.ui.VStack():
                                            idx = r * num_cols + c
                                            if idx < num_sensors:
                                                omni.ui.Label(
                                                    label_list[idx], alignment=omni.ui.Alignment.CENTER, height=0
                                                )
                                                omni.ui.ImageWithProvider(byte_provider_list[idx])

                def toggle_rgb_sensor(self, value):
                    self._rgb_enable = value
                    self._settings.set("/syntheticdata/sensors/rgbSensor", value)
                    self.bbox_2d_tight_checkbox.enabled = value
                    self.bbox_2d_loose_checkbox.enabled = value
                    if value == False:
                        self.bbox_2d_tight_checkbox.model.set_value(False)
                        self.bbox_2d_loose_checkbox.model.set_value(False)

                def toggle_depth_sensor(self, value):
                    self._depth_enable = value
                    self._settings.set("/syntheticdata/sensors/depthSensor", value)

                def toggle_instance_segmentation_sensor(self, value):
                    self._instance_enable = value
                    self._settings.set("/syntheticdata/sensors/instanceSegmentationSensor", value)

                def toggle_semantic_segmentation_sensor(self, value):
                    self._semantic_enable = value
                    self._settings.set("/syntheticdata/sensors/semanticSegmentationSensor", value)

                def toggle_bbox_2d_tight_sensor(self, value):
                    self._bbox_2d_tight_enable = value
                    self._settings.set("/syntheticdata/sensors/boundingBox2DTightSensor", value)

                def toggle_bbox_2d_loose_sensor(self, value):
                    self._bbox_2d_loose_enable = value
                    self._settings.set("/syntheticdata/sensors/boundingBox2DLooseSensor", value)

                with omni.ui.HStack(height=30):
                    omni.ui.Spacer(width=10)
                    omni.ui.Label("RGB", height=0, width=200)
                    self.rgb_checkbox = omni.ui.CheckBox()
                    self.rgb_checkbox.model.add_value_changed_fn(
                        lambda a, this=self: toggle_rgb_sensor(self, a.get_value_as_bool())
                    )
                with omni.ui.HStack(height=30):
                    omni.ui.Spacer(width=10)
                    omni.ui.Label("Depth", height=0, width=200)
                    self.depth_checkbox = omni.ui.CheckBox()
                    self.depth_checkbox.model.add_value_changed_fn(
                        lambda a, this=self: toggle_depth_sensor(self, a.get_value_as_bool())
                    )
                with omni.ui.HStack(height=30):
                    omni.ui.Spacer(width=10)
                    omni.ui.Label("Semantic Segmentation", height=0, width=200)
                    self.semantic_checkbox = omni.ui.CheckBox()
                    self.semantic_checkbox.model.add_value_changed_fn(
                        lambda a, this=self: toggle_semantic_segmentation_sensor(self, a.get_value_as_bool())
                    )
                with omni.ui.HStack(height=30):
                    omni.ui.Spacer(width=10)
                    omni.ui.Label("Instance Segmentation", height=0, width=200)
                    self.instance_checkbox = omni.ui.CheckBox()
                    self.instance_checkbox.model.add_value_changed_fn(
                        lambda a, this=self: toggle_instance_segmentation_sensor(self, a.get_value_as_bool())
                    )
                with omni.ui.HStack(height=30):
                    omni.ui.Spacer(width=10)
                    bbox_2d_tight_label = omni.ui.Label("2D Tight BBox", height=0, width=200)
                    bbox_2d_tight_label.set_tooltip("To visualize this sensor, enable RGB")
                    self.bbox_2d_tight_checkbox = omni.ui.CheckBox(enabled=False)
                    self.bbox_2d_tight_checkbox.model.add_value_changed_fn(
                        lambda a, this=self: toggle_bbox_2d_tight_sensor(self, a.get_value_as_bool())
                    )
                with omni.ui.HStack(height=30):
                    omni.ui.Spacer(width=10)
                    bbox_2d_loose_label = omni.ui.Label("2D Loose BBox", height=0, width=200)
                    bbox_2d_loose_label.set_tooltip("To visualize this sensor, enable RGB")
                    self.bbox_2d_loose_checkbox = omni.ui.CheckBox(enabled=False)
                    self.bbox_2d_loose_checkbox.model.add_value_changed_fn(
                        lambda a, this=self: toggle_bbox_2d_loose_sensor(self, a.get_value_as_bool())
                    )
                with omni.ui.HStack():
                    omni.ui.Spacer(width=6)
                    omni.ui.Button(
                        "Visualize",
                        width=70,
                        height=30,
                        clicked_fn=lambda w=self._visualize_window: visualize_synthetic_data(w),
                    )
