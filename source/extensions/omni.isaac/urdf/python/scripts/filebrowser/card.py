# Copyright (c) 2018-2020, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
"""
Base Model classes for the filebrowser entity.
"""
import os, sys
import asyncio
import time

from omni import ui
from .model import FileBrowserModel, FileBrowserItem
from .style import UI_STYLES


class FileBrowserItemCard(ui.Widget):
    def __init__(self, item: FileBrowserItem, **kwargs):
        print("Card: ", item.name)
        self._item = item
        self._widget = None
        self._image_frame = None

        self._theme = kwargs.get("theme", "NvidiaDark")
        self._style = kwargs.get("style", UI_STYLES[self._theme])
        self._width = kwargs.get("width", 60)
        self._height = kwargs.get("height", 60)
        self._mouse_pressed_fn = kwargs.get("mouse_pressed_fn", None)
        self._mouse_double_clicked_fn = kwargs.get("mouse_double_clicked_fn", None)
        self._build_ui()

    def _build_ui(self):
        if not self._item:
            return

        self._widget = ui.ZStack(width=0, height=0, style=self._style)

        with self._widget:
            mouse_pressed_fn = None
            if self._mouse_pressed_fn:
                mouse_pressed_fn = lambda x, y, b, _: self._mouse_pressed_fn(b, self._item)

            mouse_double_clicked_fn = None
            if self._mouse_double_clicked_fn:
                mouse_double_clicked_fn = lambda x, y, b, _: self._mouse_double_clicked_fn(b, self._item)

            ui.Rectangle(
                style_type_name_override="Card",
                mouse_pressed_fn=mouse_pressed_fn,
                mouse_double_clicked_fn=mouse_double_clicked_fn,
            )
            with ui.VStack(spacing=0):
                self._image_frame = ui.Frame(width=self._width, height=0.8 * self._height)
                with self._image_frame:
                    ui.ImageWithProvider(
                        self.get_icon(),
                        fill_policy=ui.IwpFillPolicy.IWP_PRESERVE_ASPECT_FIT,
                        style_type_name_override="Card.Image",
                    )
                with ui.HStack(height=20):
                    ui.Label(
                        self._item.name,
                        style_type_name_override="Card.Label",
                        word_wrap=True,
                        tooltip=self.get_tooltip(),
                    )
                ui.Spacer()

        # Background loading custom thumbnails if they exist
        asyncio.ensure_future(self.load_thumbnail_async())

    def get_icon(self):
        assert self._item is not None
        if self._item.is_folder:
            return "resources/icons/folder_gray.png"
        else:
            return "resources/icons/image.png"

    def get_tooltip(self):
        item = self._item
        assert item is not None
        tooltip = f"Path:  {item.path}\n"
        tooltip += f"Size:  {int(item.fields.size/1000)} Kb\n"
        tooltip += f"Modified:  {item.fields.date.strftime('%x %I:%M%p')}"
        return tooltip

    async def load_thumbnail_async(self):
        item = self._item
        assert item is not None
        if item.is_folder or not item.parent:
            return
        if ".thumbs" in item.path:
            # Skip if this file itself is a thumbnail
            return

        thumbnail_path = f"{item.parent.path}/.thumbs/256x256/{item.name}.png"
        try:
            stats = await FileBrowserModel.stat_path_async(thumbnail_path, timeout=1.0)
        except Exception as e:
            return

        with self._image_frame:
            self._image = ui.Image(
                thumbnail_path, fill_policy=ui.FillPolicy.PRESERVE_ASPECT_FIT, style_type_name_override="Card.Image"
            )

    def destroy(self):
        self._item = None
        self._widget = None
        self._image_frame = None
