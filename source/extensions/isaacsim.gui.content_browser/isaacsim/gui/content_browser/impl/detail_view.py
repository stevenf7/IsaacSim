# Copyright (c) 2018-2024, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

import os
from collections import namedtuple
from datetime import datetime
from pathlib import Path
from typing import Dict, List

import omni.client
import omni.kit.app
import omni.ui as ui
from omni.kit.async_engine import run_coroutine
from omni.kit.helper.file_utils import asset_types
from omni.kit.widget.filebrowser import FileBrowserItem
from omni.kit.window.filepicker import DetailFrameController
from pxr import Usd

EXTENSION_FOLDER_PATH = Path(omni.kit.app.get_app().get_extension_manager().get_extension_path_by_module(__name__))
ICON_PATH = EXTENSION_FOLDER_PATH.joinpath("icons")
USD_FILETYPES = (".usd", ".usda", ".usdc", ".usdz")
IMPORTER_FILETYPES = (".urdf", ".mjcf")
TXT_FILETYPES = (".json", ".yaml", ".yml", ".pt", ".txt", ".log")


class ExtendedFileInfo(DetailFrameController):
    """Extended file info show in detail view"""

    MockListEntry = namedtuple("MockListEntry", "relative_path modified_time created_by modified_by size")
    _empty_list_entry = MockListEntry("File info", datetime.now(), "", "", 0)

    def __init__(self):
        super().__init__(
            build_fn=self._build_ui_impl,
            selection_changed_fn=self._on_selection_changed_impl,
            destroy_fn=self._destroy_impl,
        )
        self._widget = None
        self._current_url = ""
        self._resolve_subscription = None
        self._time_label = None
        self._created_by_label = None
        self._modified_by_label = None
        self._size_label = None

    def build_header(self, collapsed: bool, title: str):
        """
        Builds the header. It is used to show the header of the file info.
        Args:
            collapsed (bool): True if the header is collapsed.
            title (str): title of the header to be shown.
        """
        with ui.HStack(style_type_name_override="DetailFrame.Header"):
            if collapsed:
                ui.ImageWithProvider(f"{ICON_PATH}/arrow_right.svg", width=20, height=20)
            else:
                ui.ImageWithProvider(f"{ICON_PATH}/arrow_down.svg", width=20, height=20)
            icon = asset_types.get_icon(title)
            if icon is not None:
                ui.ImageWithProvider(icon, width=18, style_type_name_override="DetailFrame.Header.Icon")
                ui.Spacer(width=4)
            ui.Label(
                "File Information", elided_text=True, tooltip=title, style_type_name_override="DetailFrame.Header.Label"
            )

    def _build_ui_impl(self, selected: List[str] = []):
        self._widget = ui.Frame()
        run_coroutine(self._build_ui_async(selected))

    async def _build_ui_async(self, selected: List[str] = []):
        entry = None
        if len(selected) == 0:
            self._frame.title = "No files selected"
        elif len(selected) > 1:
            self._frame.title = "Multiple files selected"
        else:
            result, entry = await omni.client.stat_async(selected[-1])
            if result == omni.client.Result.OK and entry:
                self._frame.title = entry.relative_path or os.path.basename(selected[-1])
                if self._current_url != selected[-1]:
                    self._current_url = selected[-1]
                    self._resolve_subscription = omni.client.resolve_subscribe_with_callback(
                        self._current_url,
                        [self._current_url],
                        None,
                        lambda result, event, entry, url: self._on_file_change_event(result, entry),
                    )
            else:
                self._frame.title = os.path.basename(selected[-1])
                entry = None
            entry = entry or self._empty_list_entry

            # check for variants
            variant_set_names = []
            if entry.size < 50000 and entry.relative_path.endswith(USD_FILETYPES):
                stage = Usd.Stage.Open(self._current_url, load=Usd.Stage.LoadNone)
                if stage.HasDefaultPrim():
                    vset = stage.GetDefaultPrim().GetVariantSets()
                    variant_set_names = vset.GetNames()

            # build variant options
            with self._widget:
                with ui.ZStack():
                    ui.Rectangle()
                    with ui.VStack():
                        ui.Rectangle(height=2, style_type_name_override="DetailFrame.Separator")
                        with ui.VStack():
                            if variant_set_names:
                                ui.Label("Variant Options", font_size=10)
                                for name in variant_set_names:
                                    ui.Spacer(height=8)
                                    ui.Label(name, style_type_name_override="DetailFrame.LineItem.left_aligned")
                                    variant_set = vset.GetVariantSet(name)
                                    variants = variant_set.GetVariantNames()
                                    for variant in variants:
                                        with ui.HStack():
                                            ui.Spacer(width=10)
                                            ui.Label(
                                                variant, style_type_name_override="DetailFrame.LineItem.left_aligned"
                                            )
                                ui.Spacer(height=8)

                            elif entry.relative_path.endswith(IMPORTER_FILETYPES):
                                ui.Label("URDF file, use File->Import to convert to USD")
                            elif entry.relative_path.endswith(TXT_FILETYPES):
                                ui.Label("Text file, Right Click and select Download to download file")
                            else:
                                ui.Label("No Additional Information")

    def _on_file_change_event(self, result: omni.client.Result, entry: omni.client.ListEntry):
        if result == omni.client.Result.OK and self._current_url:
            self._time_label.text = FileBrowserItem.datetime_as_string(entry.modified_time)
            self._created_by_label.text = entry.created_by
            self._modified_by_label.text = entry.modified_by
            self._size_label.text = FileBrowserItem.size_as_string(entry.size)

    def _on_selection_changed_impl(self, selected: List[str] = []):
        self._build_ui_impl(selected)

    def _destroy_impl(self, _):
        if self._widget:
            self._widget.destroy()
        self._widget = None
        self._resolve_subscription = None
