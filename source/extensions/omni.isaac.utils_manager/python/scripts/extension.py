# Copyright (c) 2018-2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

import omni.ext
import omni.kit.commands
import omni.ui as ui
from omni.kit.menu.utils import add_menu_items, remove_menu_items, MenuItemDescription

import gc
import asyncio
import weakref

from .style import *
from pathlib import Path

from .toolbar_utils import *


EXTENSION_NAME = "Isaac Sim Utilities Manager"

# ---PHYSICS---
# Inspect Physics
# Physics Utils

# ---IMPORT---
# Step Importer
# URDF Importer

# ---Isaac SDK---
# Robot Engine Bridge

# ---MAPPING---
# Occupancy Map

# ---GEOMETRY---
# Mesh Merge Tool
# ShapeNet Loader


UTILITIES = {
    "Physics": ["Inspect Physics", "Physics Utilities"],
    "Import": ["URDF Importer", "Step Importer"],
    "Mapping": ["Occupancy Map"],
    "Isaac SDK": ["Robot Engine Bridge"],
    "Geometry": ["Mesh Merge Tool", "ShapeNet Loader"],
    # "Training": ["Synthetic Data Recorder"],
}

DEBUG_PRINT_ON = False


class Extension(omni.ext.IExt):
    def on_startup(self, ext_id: str):

        manager = omni.kit.app.get_app().get_extension_manager()
        extension_path = manager.get_extension_path(ext_id)

        self.icon_path = Path(extension_path).joinpath("data")
        self._visible = True
        self._toolbar = None
        self._task = None
        self.build_ui()
        self.enable_ui()

    def build_ui(self):
        # Grabbed this style AttributesEditor example
        self._style = get_window_style

        self._toolbar = ToolBarUtilities(self.icon_path, UTILITIES)

        async def dock_windows():
            await omni.kit.app.get_app().next_update_async()
            self.dock_toolbar()
            await omni.kit.app.get_app().next_update_async()
            self.dock_utilities()
            await omni.kit.app.get_app().next_update_async()
            self.hide_utilities()
            await omni.kit.app.get_app().next_update_async()

        self._task = asyncio.ensure_future(dock_windows())

    def dock_toolbar(self):
        """Docks the Utilities Toolbar along the right side of the window on start up."""
        if DEBUG_PRINT_ON:
            # print(ui.Workspace.get_windows())
            print("DOCKING TOOLBAR")
        tgt = ui.Workspace.get_window("Content")
        self.dock_window(tgt, "Isaac Utilities Toolbar", omni.ui.DockPosition.RIGHT, 0.9)
        # tgt = ui.Workspace.get_window("DockSpace") # <-- causes seg fault for some reason
        # self.dock_window(tgt, "Isaac Utilities Toolbar", omni.ui.DockPosition.RIGHT, .2)

    def dock_utilities(self):
        """Docks each Extension Utility in the  Utilities Toolbar on start up."""
        if DEBUG_PRINT_ON:
            print("DOCKING UTILITIES")
        # Dock the first of each group category on top of one another
        pos = 0.75
        prev_group = ""
        for group in UTILITIES:
            if prev_group == "":
                tgt = ui.Workspace.get_window("Content")
                self.dock_window(tgt, UTILITIES[group][0], omni.ui.DockPosition.SAME)
            # else:
            #     tgt = ui.Workspace.get_window(UTILITIES[prev_group][0])
            #     self.dock_window(tgt, UTILITIES[group][0], omni.ui.DockPosition.BOTTOM, pos)
            prev_group = group
        # Add multiples of any given group category
        for group in UTILITIES:
            # i = 0
            for ext in UTILITIES[group]:
                # if i > 0:
                # tgt = ui.Workspace.get_window(UTILITIES[group][0])
                tgt = ui.Workspace.get_window("Content")
                self.dock_window(tgt, ext, omni.ui.DockPosition.SAME)
            # i += 1

        # Move the Property panel so it gives our extension the full height
        # tgt = ui.Workspace.get_window("Stage")
        # self.dock_window(tgt, "Property", omni.ui.DockPosition.BOTTOM)

    def show_utilities(self):
        """Makes all Extension Utilities visible in the Toolbar"""
        if DEBUG_PRINT_ON:
            print("SHOWING UTILITIES")
        # Update the btn image url
        self._toolbar._models["visibility"].image_url = str(self.icon_path.joinpath("tray_close.png"))

        # Reset all the toolbar buttons to True
        for group in UTILITIES:
            self._toolbar._models[group].set_value(True)

        # Make each Utility visible & dock
        for group in UTILITIES:
            for ext in UTILITIES[group]:
                omni.ui.Workspace.get_window(ext).visible = True

    def hide_utilities(self):
        """Hides all Extension Utilities, and just leaves the Toolbar visible."""
        if DEBUG_PRINT_ON:
            print("HIDING UTILITIES")
        # Update the Toolbar's btn image url
        self._toolbar._models["visibility"].image_url = str(self.icon_path.joinpath("tray_open.png"))

        # Reset all the toolbar buttons to False
        for group in UTILITIES:
            self.hide_utility(group)

    def show_utility(self, name):
        """Makes one Utilities Group visible in the Toolbar"""
        if DEBUG_PRINT_ON:
            print("\tSelect: ", name)
        # Make each Extension in the group visible
        for ext in UTILITIES[name]:
            ui.Workspace.get_window(ext).visible = True

        # Dock the group next to the Content
        tgt = ui.Workspace.get_window("Content")
        window = ui.Workspace.get_window(UTILITIES[name][0])
        window.dock_in(tgt, omni.ui.DockPosition.SAME)

        i = 0
        for ext in UTILITIES[name]:
            if i > 0:
                # tgt = ui.Workspace.get_window(UTILITIES[name][0])
                tgt = ui.Workspace.get_window("Content")
                window = ui.Workspace.get_window(ext)
                window.dock_in(tgt, omni.ui.DockPosition.SAME)
            i += 1

    def hide_utility(self, name):
        """Hides one Utilities Group visible in the Toolbar"""
        if DEBUG_PRINT_ON:
            print("\tDeselect: ", name)

        # Deselect the Toolbar Button
        if self._toolbar is not None:
            self._toolbar._models[name].set_value(False)

        # Hide any GUI panels that are showing
        for ext in UTILITIES[name]:
            window = ui.Workspace.get_window(ext)
            if window:
                window.visible = False

    def enable_ui(self):
        # use weakrefs to self so the extension cleans up properly
        self._toolbar._models["visibility"].set_clicked_fn(
            lambda a=weakref.proxy(self): a.toggle_visibility_all(a._toolbar._models["visibility"])
        )

        for group in UTILITIES:
            self._toolbar._models[group].add_value_changed_fn(lambda m, g=group: self.toggle_visibility(g, m))

    # Dock windows if they exist
    def dock_window(self, space, name, location, pos=0.5):
        window = omni.ui.Workspace.get_window(name)
        if window and space:
            window.dock_in(space, location, pos)
        return window

    def toggle_visibility_all(self, button):
        # change visibility based on button press
        self._visible = not self._visible

        if DEBUG_PRINT_ON:
            print("Show ALL? ", self._visible)

        # If visbile, turn off the toolbar buttons, show all, and re-dock
        if self._visible:
            # Make Utilities visible
            self.show_utilities()
            # dock the toolbar to the right of the Stage
            self.dock_toolbar()
            # dock the utlities to the left of the Toolbar
            self.dock_utilities()

        # # Dock the toolbar all the way to the right of the screen
        else:
            self.hide_utilities()
            self.dock_toolbar()

            # # reposition the Property panel under the Stage
            # tgt = ui.Workspace.get_window("Stage")
            # self.dock_window(tgt, "Property", omni.ui.DockPosition.BOTTOM)

        if DEBUG_PRINT_ON:
            print()

    def toggle_visibility(self, group, model):
        msg = group + ": " + str(model.get_value_as_bool())
        if DEBUG_PRINT_ON:
            print("Button Press from ", msg)

        async def async_toggle():
            if model.get_value_as_bool():
                # Hide the other utilities
                # for g in UTILITIES:
                #     if g != group:
                #         await omni.kit.app.get_app().next_update_async()
                #         self.hide_utility(g)
                #         await omni.kit.app.get_app().next_update_async()
                # Show this utility
                await omni.kit.app.get_app().next_update_async()
                self.show_utility(group)
                await omni.kit.app.get_app().next_update_async()
                # self.dock_utilities()
                # await omni.kit.app.get_app().next_update_async()
            else:
                self.hide_utility(group)

        asyncio.ensure_future(async_toggle())

    def get_name(self):
        """Return the name of the extension"""
        return EXTENSION_NAME

    def on_shutdown(self):
        for g in UTILITIES:
            self.hide_utility(g)
        if self._toolbar is not None:
            self._toolbar.clean()
            self._toolbar = None
        gc.collect()
