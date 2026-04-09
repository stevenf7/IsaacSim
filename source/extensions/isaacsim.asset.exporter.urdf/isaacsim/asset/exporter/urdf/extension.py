# SPDX-FileCopyrightText: Copyright (c) 2018-2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""URDF Exporter Kit extension registration and UI delegate."""

import gc

import omni.ext
import omni.kit.actions.core
import omni.ui as ui
import omni.usd
from isaacsim.gui.components.menu import MenuItemDescription
from omni.kit.menu.utils import add_menu_items, remove_menu_items
from omni.kit.window.file_exporter import ExportOptionsDelegate, get_file_exporter

from .exporter import UrdfExporter

EXTENSION_TITLE = "URDF Exporter"


class Extension(omni.ext.IExt):
    """Extension class for the isaacsim.asset.exporter.urdf extension.

    This extension provides URDF export functionality for Isaac Sim, allowing users to export USD scenes
    and assets to URDF (Unified Robot Description Format) files. The extension integrates with Isaac Sim's
    file export system and adds a "URDF Exporter" menu item to the File menu.

    The extension creates a file export dialog that supports .urdf file format and provides export-specific
    options through a custom UI. Users can select USD prims and convert them to URDF format with
    appropriate robot description syntax including joints, links, and material properties.
    """

    def on_startup(self, ext_id: str) -> None:
        """Register the export action and menu item.

        Args:
            ext_id: Unique identifier of the extension instance.
        """
        self._ext_name = omni.ext.get_extension_name(ext_id)
        self._export_options: UrdfExporterDelegate | None = None

        action_registry = omni.kit.actions.core.get_action_registry()
        action_registry.register_action(
            self._ext_name,
            "show_export_dialog",
            self._show_dialog,
            display_name=EXTENSION_TITLE,
            description="Show the URDF export dialog",
        )

        self._menu_items = [
            MenuItemDescription(name=EXTENSION_TITLE, onclick_action=(self._ext_name, "show_export_dialog"))
        ]
        add_menu_items(self._menu_items, "File")

    def _show_dialog(self) -> None:
        """Shows the URDF export dialog.

        Creates a UrdfExporterDelegate and displays the file exporter window with URDF format options.
        """
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

    def _hide_dialog(self) -> None:
        """Hides the URDF export dialog window."""
        file_exporter = get_file_exporter()
        if file_exporter:
            file_exporter.hide_window()

    def on_shutdown(self) -> None:
        """Cleans up resources when the extension is shut down.

        Cleans up the export options delegate, hides the dialog, removes menu items, and performs garbage collection.
        """
        if self._export_options:
            self._export_options.cleanup()
        self._hide_dialog()
        remove_menu_items(self._menu_items, "File")
        action_registry = omni.kit.actions.core.get_action_registry()
        action_registry.deregister_action(self._ext_name, "show_export_dialog")
        gc.collect()


class UrdfExporterDelegate(ExportOptionsDelegate):
    """Export options delegate for URDF file format.

    This delegate integrates with the Omniverse Kit file exporter system to provide URDF-specific export
    options and functionality. It creates a UI frame containing export configuration options and handles the
    export process when users select the URDF format in the file exporter dialog.

    The delegate manages the lifecycle of URDF export operations, including building the options UI,
    handling export requests, and cleaning up resources when no longer needed.
    """

    def __init__(self) -> None:
        # Initialize the delegate
        super().__init__(
            build_fn=self._build_ui_impl,
            destroy_fn=self._destroy_impl,
        )
        self._widget: ui.Frame | None = None
        self._exporter = UrdfExporter()

    def _build_ui_impl(self) -> None:
        """Builds the UI implementation for the URDF exporter options.

        Creates a UI frame widget and builds the exporter options interface within it.
        """
        self._widget = ui.Frame()
        with self._widget:
            self._exporter.build_exporter_options()

    def export(self, filename: str, dirname: str, extension: str = "", selections: list[str] | None = None) -> None:
        """Export the current stage to a URDF file.

        Args:
            filename: Base name for the exported file (without extension).
            dirname: Directory path where the URDF will be written.
            extension: File extension override (unused, kept for delegate API).
            selections: Optional list of selected prim paths to export.
        """
        result = self._exporter._on_export_button_clicked_fn(dirname, filename)
        if result:
            print(f"Export to URDF successful")
        else:
            print(f"Error: Failed to export to URDF")

    def _destroy_impl(self) -> None:
        """Destroys the UI implementation and cleans up the widget.

        Destroys the UI frame widget and resets the widget reference to None.
        """
        if self._widget:
            self._widget.destroy()
        self._widget = None

    def cleanup(self) -> None:
        """Performs cleanup operations for the URDF exporter delegate.

        Cleans up the exporter instance and destroys the UI implementation.
        """
        self._exporter.cleanup()
        self._destroy_impl()
