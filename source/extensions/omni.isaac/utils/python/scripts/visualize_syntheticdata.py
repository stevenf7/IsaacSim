# Copyright (c) 2018-2020, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

import numpy as np
import random
import colorsys
import omni.ext
import omni.usd
import omni.kit.editor
import omni.ui
import omni.syntheticdata._syntheticdata as gt
from omni.kit.settings import get_settings_interface
from omni.kit import pipapi
from PIL import Image, ImageDraw

EXTENSION_NAME = "Visualize Synthetic Data"

# Helper functions
def random_colours(N):
    start = 0
    hues = [(start + i / N) % 1.0 for i in range(N)]
    colours = [list(colorsys.hsv_to_rgb(h, 0.9, 1.0)) for i, h in enumerate(hues)]
    for color in colours:
        color.append(1.0)
    return colours


def interpolate(p, a, b):
    p0 = 1.0 - p
    return [int(p0 * a[0] + p * b[0]), int(p0 * a[1] + p * b[1]), int(p0 * a[2] + p * b[2]), 255]


def colorize_depth(depth_image, width, height):
    colorized_image = np.zeros((height, width, 4))
    depth_image[depth_image == 0.0] = 1e-5
    depth_image = np.clip(depth_image, 0, 255)
    depth_image -= np.min(depth_image)
    depth_image /= np.max(depth_image)
    colorized_image[:, :, 0] = depth_image
    colorized_image[:, :, 1] = depth_image
    colorized_image[:, :, 2] = depth_image
    colorized_image[:, :, 3] = 1
    colorized_image = (colorized_image * 255).astype(int)
    colorized_image = colorized_image.reshape(colorized_image.size)
    return colorized_image.tolist()


def colorize_instance(instance_image, width, height):
    instance_mappings = instance_image[:, :, 0]
    instance_list = np.unique(instance_mappings)
    color_pixels = random_colours(len(instance_list))
    instance_masks = np.zeros((len(instance_list), *instance_mappings.shape), dtype=np.bool)
    for index, instance_id in enumerate(instance_list):
        instance_masks[index] = instance_mappings == instance_id
    color_image = np.zeros((height, width, 4))
    for mask, colour in zip(instance_masks, color_pixels):
        color_image[mask] = colour
    color_image_list = (color_image * 255).astype(int)
    color_image_list = color_image_list.reshape(color_image_list.size)
    return color_image_list.tolist()


def colorize_bboxes(bboxes_2d_data, bboxes_2d_rgb):
    semantic_id_list = []
    bbox_2d_list = []
    rgb_img = Image.fromarray(bboxes_2d_rgb)
    rgb_img_draw = ImageDraw.Draw(rgb_img)
    for bbox_2d in bboxes_2d_data:
        if bbox_2d[1] > 0:
            semantic_id_list.append(bbox_2d[1])
            bbox_2d_list.append(bbox_2d)
    semantic_id_list_np = np.unique(np.array(semantic_id_list))
    color_list = random_colours(len(semantic_id_list_np.tolist()))
    for bbox_2d in bbox_2d_list:
        index = np.where(semantic_id_list_np == bbox_2d[1])[0][0]
        bbox_color = color_list[index]
        rgb_img_draw.rectangle(
            [(bbox_2d[2], bbox_2d[3]), (bbox_2d[4], bbox_2d[5])],
            outline=(
                int(255 * bbox_color[0]),
                int(255 * bbox_color[1]),
                int(255 * bbox_color[2]),
                int(255 * bbox_color[3]),
            ),
            width=2,
        )
    bboxes_2d_rgb = np.array(rgb_img)
    bboxes_2d_rgb = bboxes_2d_rgb.reshape(bboxes_2d_rgb.size)
    return bboxes_2d_rgb


class Extension(omni.ext.IExt):
    def on_startup(self):
        """Caled to load the extension"""
        self._syntheticdata = gt.acquire_syntheticdata_interface()
        self._window = omni.ui.Window(EXTENSION_NAME, width=600, height=400)
        self._visualize_window = omni.ui.Window("Visualization", width=300, height=300)
        self._menu_entry = omni.kit.ui.get_editor_menu().add_item(f"Window/Isaac/{EXTENSION_NAME}", self._menu_callback)
        self._settings = get_settings_interface()
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
                        bboxes_2d_tight_rgb = colorize_bboxes(bboxes_2d_tight_data, bboxes_2d_tight_rgb)

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
                        bboxes_2d_loose_rgb = colorize_bboxes(bboxes_2d_loose_data, bboxes_2d_loose_rgb)

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

                    if self._bbox_2d_tight_enable:
                        self._bbox_2d_tight_byte_provider = omni.ui.ByteImageProvider()
                        self._bbox_2d_tight_byte_provider.set_data(
                            bboxes_2d_tight_rgb.tolist(), [rgb_width, rgb_height]
                        )

                    if self._bbox_2d_loose_enable:
                        self._bbox_2d_loose_byte_provider = omni.ui.ByteImageProvider()
                        self._bbox_2d_loose_byte_provider.set_data(
                            bboxes_2d_loose_rgb.tolist(), [rgb_width, rgb_height]
                        )

                    with window.frame:
                        with omni.ui.VStack():
                            with omni.ui.HStack(height=0):
                                with omni.ui.VStack():
                                    omni.ui.Label("RGB", alignment=omni.ui.Alignment.CENTER)
                                with omni.ui.VStack():
                                    omni.ui.Label("Depth", alignment=omni.ui.Alignment.CENTER)
                            with omni.ui.HStack():
                                with omni.ui.VStack():
                                    if self._rgb_enable:
                                        omni.ui.ImageWithProvider(self._rgb_byte_provider)
                                with omni.ui.VStack():
                                    if self._depth_enable:
                                        omni.ui.ImageWithProvider(self._depth_byte_provider)
                            with omni.ui.HStack(height=0):
                                with omni.ui.VStack():
                                    omni.ui.Label("Semantic Segmentation", alignment=omni.ui.Alignment.CENTER)
                                with omni.ui.VStack():
                                    omni.ui.Label("Instance Segmentation", alignment=omni.ui.Alignment.CENTER)
                            with omni.ui.HStack():
                                with omni.ui.VStack():
                                    if self._semantic_enable:
                                        omni.ui.ImageWithProvider(self._semantic_byte_provider)
                                with omni.ui.VStack():
                                    if self._instance_enable:
                                        omni.ui.ImageWithProvider(self._instance_byte_provider)
                            with omni.ui.HStack(height=0):
                                with omni.ui.VStack():
                                    omni.ui.Label("2D Tight BBox", alignment=omni.ui.Alignment.CENTER)
                                with omni.ui.VStack():
                                    omni.ui.Label("2D Loose BBox", alignment=omni.ui.Alignment.CENTER)
                            with omni.ui.HStack():
                                with omni.ui.VStack():
                                    if self._bbox_2d_tight_enable:
                                        omni.ui.ImageWithProvider(self._bbox_2d_tight_byte_provider)
                                with omni.ui.VStack():
                                    if self._bbox_2d_loose_enable:
                                        omni.ui.ImageWithProvider(self._bbox_2d_loose_byte_provider)

                def toggle_rgb_sensor(self, value):
                    self._rgb_enable = value
                    self._settings.set("/syntheticdata/sensors/rgbSensor", value)

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
                    omni.ui.Label("2D Tight BBox", height=0, width=200)
                    self.bbox_2d_tight_checkbox = omni.ui.CheckBox()
                    self.bbox_2d_tight_checkbox.model.add_value_changed_fn(
                        lambda a, this=self: toggle_bbox_2d_tight_sensor(self, a.get_value_as_bool())
                    )
                with omni.ui.HStack(height=30):
                    omni.ui.Spacer(width=10)
                    omni.ui.Label("2D Loose BBox", height=0, width=200)
                    self.bbox_2d_loose_checkbox = omni.ui.CheckBox()
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
