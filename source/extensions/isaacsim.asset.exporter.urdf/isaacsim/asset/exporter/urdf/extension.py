# SPDX-FileCopyrightText: Copyright (c) 2018-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: LicenseRef-NvidiaProprietary
#
# NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
# property and proprietary rights in and to this material, related
# documentation and any modifications thereto. Any use, reproduction,
# disclosure or distribution of this material and related documentation
# without an express license agreement from NVIDIA CORPORATION or
# its affiliates is strictly prohibited.


import gc
from typing import List

import omni.ext
import omni.ui as ui
import omni.usd
from isaacsim.gui.components.menu import MenuItemDescription
from omni.kit.menu.utils import add_menu_items, remove_menu_items
from omni.kit.window.file_exporter import ExportOptionsDelegate, get_file_exporter

from .exporter import UrdfExporter

EXTENSION_TITLE = "URDF Exporter"


class Extension(omni.ext.IExt):
    def on_startup(self):
        self._export_options = None

        # Menu Setup
        self._menu_items = [MenuItemDescription(name=EXTENSION_TITLE, onclick_fn=self._show_dialog)]
        add_menu_items(self._menu_items, "File")

    def _show_dialog(self):
        # File Exporter Dialog setup
        file_exporter = get_file_exporter()
        if not file_exporter:
            return

        self._export_options = UrdfExporterDelegate()

        file_exporter.show_window(
            title="Export As ...",
            file_extension_types=[(".urdf", "URDF format")],
            export_handler=self._export_options.export,
        )

        # UrdfExporter specific options inside the file exporter dialog
        file_exporter.add_export_options_frame("Export Options", self._export_options)

    def _hide_dialog(self):
        file_exporter = get_file_exporter()
        if file_exporter:
            file_exporter.hide_window()

    def on_shutdown(self):
        # Cleanup Delegate
        if self._export_options:
            self._export_options.cleanup()
        # Cleanup Dialog
        self._hide_dialog()
        # Cleanup Menu
        remove_menu_items(self._menu_items, "File")
        # Cleanup Garbage
        gc.collect()


class UrdfExporterDelegate(ExportOptionsDelegate):
    def __init__(self):
        # Initialize the delegate
        super().__init__(
            build_fn=self._build_ui_impl,
            destroy_fn=self._destroy_impl,
        )
        self._widget = None
        self._exporter = UrdfExporter()

    def _build_ui_impl(self):
        self._widget = ui.Frame()
        with self._widget:
            self._exporter.build_exporter_options()

    def export(self, filename: str, dirname: str, extension: str = "", selections: List[str] = []):
        result = self._exporter._on_export_button_clicked_fn(dirname, filename)
        if result:
            print(f"Export to URDF successful")
        else:
            print(f"Error: Failed to export to URDF")

    def _destroy_impl(self):
        if self._widget:
            self._widget.destroy()
        self._widget = None

    def cleanup(self):
        self._exporter.cleanup()
        self._destroy_impl()
