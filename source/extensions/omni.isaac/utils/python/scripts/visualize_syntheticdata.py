# Copyright (c) 2018-2020, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

import os
import gc
import numpy as np
import random
import math
import colorsys
import omni.ext
import omni.usd
import omni.kit.editor
import omni.ui
import omni.syntheticdata._syntheticdata as gt

EXTENSION_NAME = "Visualize Synthetic Data"

# Helper functions
def random_colours(N):
    start = random.random()
    hues = [(start + i / N) % 1.0 for i in range(N)]
    colours = [colorsys.hsv_to_rgb(h, 0.9, 1.0) for i, h in enumerate(hues)]
    random.shuffle(colours)
    return colours


def interpolate(p, a, b):
    p0 = 1.0 - p
    return [int(p0 * a[0] + p * b[0]), int(p0 * a[1] + p * b[1]), int(p0 * a[2] + p * b[2]), 255]


def colorize_depth(depth_image, width, height):
    color_image = []
    # color_pixels = [[51, 51, 51], [127, 51, 51], [255, 229, 165], [255, 255, 255], [216, 242, 255]]
    color_pixels = [[0, 0, 0], [255, 255, 255]]
    for row in range(height):
        for col in range(width):
            pixel_value = depth_image[row, col]
            normalize_pixel_value = pixel_value / 255.0
            gradient = normalize_pixel_value * (len(color_pixels) - 1)
            gradient_index = math.floor(gradient)
            if gradient_index == len(color_pixels) - 1:
                gradient_color = [216, 242, 255, 255]
            else:
                gradient_color = interpolate(
                    gradient - gradient_index, color_pixels[gradient_index], color_pixels[gradient_index + 1]
                )
            color_image.extend(gradient_color)
    return color_image


def colorize_instance(instance_image, width, height):
    color_image = []
    color_pixels = random_colours(np.max(instance_image[:, :, 0]) + 1)
    for row in range(height):
        for col in range(width):
            pixel_value = instance_image[row, col, 0]
            color_image.extend(
                [
                    int(color_pixels[pixel_value][0] * 255),
                    int(color_pixels[pixel_value][1] * 255),
                    int(color_pixels[pixel_value][2] * 255),
                    255,
                ]
            )
    return color_image


class Extension(omni.ext.IExt):
    def on_startup(self):
        """Caled to load the extension"""
        self._syntheticdata = gt.acquire_syntheticdata_interface()
        self._window = omni.ui.Window(EXTENSION_NAME, width=600, height=400)
        self._visualize_window = omni.ui.Window("Visualization", width=300, height=300)
        self._menu_entry = omni.kit.ui.get_editor_menu().add_item(f"Window/Isaac/{EXTENSION_NAME}", self._menu_callback)
        self._window.visible = False
        self._visualize_window.visible = False
        self._rgb_enable = False
        self._depth_enable = False
        self._semantic_enable = False
        self._instance_enable = False
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
                        depth_sensor = gt.SensorType.DepthLinear
                        depth_width = interface.get_sensor_width(depth_sensor)
                        depth_height = interface.get_sensor_height(depth_sensor)
                        depth_row_size = interface.get_sensor_row_size(depth_sensor)
                        depth_data = interface.get_sensor_host_float_texture_array(
                            depth_sensor, depth_width, depth_height, depth_row_size
                        )
                        depth_data = (depth_data - np.min(depth_data)) * 255 / (np.max(depth_data) - np.min(depth_data))
                        depth_data = np.clip(depth_data, 0, 255)
                        colorize_depth_image = colorize_depth(depth_data, depth_width, depth_height)

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
                        colorize_instance_image = colorize_instance(
                            image_instance_data, instance_width, instance_height
                        )

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
                        colorize_semantic_image = colorize_instance(
                            image_semantic_data, semantic_width, semantic_height
                        )

                    # Visualize via omni.ui
                    if self._rgb_enable:
                        self._rgb_byte_provider = omni.ui.ByteImageProvider()
                        self._rgb_byte_provider.set_data(rgb_image.tolist(), [rgb_width, rgb_height])

                    if self._depth_enable:
                        self._depth_byte_provider = omni.ui.ByteImageProvider()
                        self._depth_byte_provider.set_data(colorize_depth_image, [depth_width, depth_height])

                    if self._instance_enable:
                        self._instance_byte_provider = omni.ui.ByteImageProvider()
                        self._instance_byte_provider.set_data(
                            colorize_instance_image, [instance_width, instance_height]
                        )

                    if self._semantic_enable:
                        self._semantic_byte_provider = omni.ui.ByteImageProvider()
                        self._semantic_byte_provider.set_data(
                            colorize_semantic_image, [semantic_width, semantic_height]
                        )

                    with window.frame:
                        with omni.ui.VStack():
                            with omni.ui.HStack():
                                if self._rgb_enable:
                                    omni.ui.ImageWithProvider(self._rgb_byte_provider)
                                if self._depth_enable:
                                    omni.ui.ImageWithProvider(self._depth_byte_provider)
                            with omni.ui.HStack():
                                if self._semantic_enable:
                                    omni.ui.ImageWithProvider(self._semantic_byte_provider)
                                if self._instance_enable:
                                    omni.ui.ImageWithProvider(self._instance_byte_provider)

                def toggle_rgb_sensor(self, value):
                    self._rgb_enable = value
                    if value:
                        self._syntheticdata.create_sensor(gt.SensorType.Rgb)
                    else:
                        self._syntheticdata.destroy_sensor(gt.SensorType.Rgb)

                def toggle_depth_sensor(self, value):
                    self._depth_enable = value
                    if value:
                        self._syntheticdata.create_sensor(gt.SensorType.DepthLinear)
                    else:
                        self._syntheticdata.destroy_sensor(gt.SensorType.DepthLinear)

                def toggle_instance_segmentation_sensor(self, value):
                    self._instance_enable = value
                    if value:
                        self._syntheticdata.create_sensor(gt.SensorType.InstanceSegmentation)
                    else:
                        self._syntheticdata.destroy_sensor(gt.SensorType.InstanceSegmentation)

                def toggle_semantic_segmentation_sensor(self, value):
                    self._semantic_enable = value
                    if value:
                        self._syntheticdata.create_sensor(gt.SensorType.SemanticSegmentation)
                    else:
                        self._syntheticdata.destroy_sensor(gt.SensorType.SemanticSegmentation)

                with omni.ui.HStack(height=30):
                    omni.ui.Label("RGB", height=0)
                    self.rgb_checkbox = omni.ui.CheckBox()
                    self.rgb_checkbox.model.add_value_changed_fn(
                        lambda a, this=self: toggle_rgb_sensor(self, a.get_value_as_bool())
                    )
                with omni.ui.HStack(height=30):
                    omni.ui.Label("Depth", height=0)
                    self.depth_checkbox = omni.ui.CheckBox()
                    self.depth_checkbox.model.add_value_changed_fn(
                        lambda a, this=self: toggle_depth_sensor(self, a.get_value_as_bool())
                    )
                with omni.ui.HStack(height=30):
                    omni.ui.Label("Semantic Segmentation", height=0)
                    self.semantic_checkbox = omni.ui.CheckBox()
                    self.semantic_checkbox.model.add_value_changed_fn(
                        lambda a, this=self: toggle_semantic_segmentation_sensor(self, a.get_value_as_bool())
                    )
                with omni.ui.HStack(height=30):
                    omni.ui.Label("Instance Segmentation", height=0)
                    self.instance_checkbox = omni.ui.CheckBox()
                    self.instance_checkbox.model.add_value_changed_fn(
                        lambda a, this=self: toggle_instance_segmentation_sensor(self, a.get_value_as_bool())
                    )
                with omni.ui.HStack():
                    omni.ui.Button(
                        "Visualize",
                        width=70,
                        height=30,
                        clicked_fn=lambda w=self._visualize_window: visualize_synthetic_data(w),
                    )
