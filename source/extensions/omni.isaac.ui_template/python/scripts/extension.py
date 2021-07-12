# Copyright (c) 2020-2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

import omni.ext
import omni.appwindow
import omni.ui as ui
import weakref
import omni.kit.settings
import gc
from omni.kit.menu.utils import add_menu_items, remove_menu_items, MenuItemDescription

from omni.isaac.utils.scripts.ui_utils import *


EXTENSION_NAME = "Example UI"

PRINT_DEBUG = True


class Extension(omni.ext.IExt):
    def on_startup(self, ext_id):
        """Initialize extension and UI elements"""
        manager = omni.kit.app.get_app().get_extension_manager()
        self._extension_path = manager.get_extension_path(ext_id)

        # Keep a Reference to the Usd Context, Stage, & Viewport
        self._usd_context = omni.usd.get_context()
        self._stage = self._usd_context.get_stage()
        self._viewport = omni.kit.viewport.get_default_viewport_window()

        # Intialize the UI Window
        self._window = None

        # Keep a Reference to interactive GUI elements
        self._models = {}

        # Add EXTENSION_NAME to a Drop Down Menu
        # The UI for EXTENSION_NAME is created once selected from the Menu.
        menu_items = [
            MenuItemDescription(name=EXTENSION_NAME, onclick_fn=lambda a=weakref.proxy(self): a._menu_callback())
        ]
        self._menu_items = [
            MenuItemDescription(name="Misc", sub_menu=[MenuItemDescription(name="Templates", sub_menu=menu_items)])
        ]
        add_menu_items(self._menu_items, "Isaac Examples")
        self._build_ui()

    def on_shutdown(self):
        """Cleanup objects on extension shutdown"""
        self._app_event_subscription = None
        remove_menu_items(self._menu_items, "Isaac Examples")
        self._window = None
        self._models = {}
        gc.collect()

    def _menu_callback(self):
        """Call the UI builder once selected from the drop down menu"""
        self._build_ui()

    def _build_ui(self):
        """Builds the UI for EXTENSION_NAME"""
        if not self._window:
            self._window = ui.Window(
                title=EXTENSION_NAME, width=400, height=600, visible=True, dockPreference=ui.DockPreference.LEFT_BOTTOM
            )

            with self._window.frame:
                with ui.VStack(spacing=5, height=0):

                    title = "Isaac Sim Example UI"
                    doc_link = "https://docs.omniverse.nvidia.com/app_isaacsim/app_isaacsim/overview.html"
                    build_header(title, doc_link)

                    overview = "The Example UI teaches you how to structure your own GUI-based extension in Isaac Sim."
                    overview += "\n\nUse this as a template when creating a UI for a new project or extension."
                    overview += "\n\nPress the 'Open in IDE' button to view the source code."
                    author = "Isaac Sim Team"
                    date = "07/01/2021"
                    build_info_frame(overview, author, date)

                    log_filename = EXTENSION_NAME.lower()
                    log_filename = log_filename.replace(" ", "_") + ".log"
                    build_settings_frame(log_filename)

                    self.build_custom_ui()

                    self.build_example_gui_grid()
                    self.build_search_frame()
                    self.build_file_browser_frame()

    def build_search_frame(self):
        self._search_frame = ui.CollapsableFrame(
            title="Example: Search",
            height=0,
            collapsed=False,
            style=get_style(),
            style_type_name_override="CollapsableFrame",
            horizontal_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_AS_NEEDED,
            vertical_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_ALWAYS_ON,
        )

    def build_file_browser_frame(self):
        self._file_browser = ui.CollapsableFrame(
            title="Example: File Browser",
            height=0,
            collapsed=False,
            style=get_style(),
            style_type_name_override="CollapsableFrame",
            horizontal_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_AS_NEEDED,
            vertical_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_ALWAYS_ON,
        )

    def build_example_gui_grid(self):

        test_gui = {
            "Test_0": {
                "label": "CB_0",
                "type": "checkbox",
                "default_val": False,
                "tooltip": "Add Tooltip Here",
                "on_clicked_fn": self._on_dummy_callable_0,
            },
            "Test_1": {
                "label": "CB_1",
                "type": "checkbox",
                "default_val": True,
                "tooltip": "Add Tooltip Here",
                "on_clicked_fn": self._on_dummy_callable_1,
            },
            "Test_2": {
                "label": "CB_2",
                "type": "checkbox",
                "default_val": True,
                "tooltip": "Add Tooltip Here",
                "on_clicked_fn": self._on_dummy_callable_2,
            },
            "Test_4": {
                "label": "BTN_0",
                "type": "button",
                "text": "PRESS ME",
                "tooltip": "Add Tooltip Here",
                "on_clicked_fn": self._on_dummy_callable_1,
            },
            "Test_5": {
                "label": "BTN_GROUP_0",
                "count": 2,
                "type": "multi_button",
                "text": ["PRESS ME", "no...PReSs mE"],
                "tooltip": ["This is the Label Tooltip", "Tooltip 0", "Tooltip 1"],
                "on_clicked_fn": [self._on_dummy_callable_0, self._on_dummy_callable_2],
            },
            "Test_6": {
                "label": "BTN_GROUP_1",
                "count": 3,
                "type": "multi_button",
                "text": ["PRESS ME", "NO, PRESS ME", "NO...PRESs ME!"],
                "tooltip": ["This group has button tooltips", "Tooltip 0", "Tooltip 1", "Tooltip 2"],
                "on_clicked_fn": [self._on_dummy_callable_0, self._on_dummy_callable_2, self._on_dummy_callable_1],
            },
            "Test_6.5": {
                "label": "BTN_GROUP_2",
                "count": 3,
                "type": "multi_button",
                "text": ["PRESS ME", "NO, PRESS ME", "NO, PRESS ME!"],
                "tooltip": ["This group doesn't have button tooltips", "", "", ""],
                "on_clicked_fn": [self._on_dummy_callable_0, self._on_dummy_callable_2, self._on_dummy_callable_1],
            },
            "Test_7": {
                "label": "CB_GROUP_0",
                "count": 3,
                "type": "multi_checkbox",
                "default_val": [False, True, False, True],
                "text": ["Label 0", "Label 1", "Label 2"],
                "tooltip": ["This is the Label Tooltip", "Tooltip 0", "Tooltip 1", "Tooltip 2"],
                "on_clicked_fn": [self._on_dummy_callable_0, self._on_dummy_callable_2, self._on_dummy_callable_1],
            },
            "Test_8": {
                "label": "CB_GROUP_1",
                "count": 4,
                "type": "multi_checkbox",
                "default_val": [False, True, False, True],
                "text": ["Label 0", "Label 1", "Label 2", "Label 3"],
                "tooltip": ["This is the Label Tooltip", "Tooltip 0", "Tooltip 1", "Tooltip 2", "Tooltip 3"],
                "on_clicked_fn": [
                    self._on_dummy_callable_0,
                    self._on_dummy_callable_2,
                    self._on_dummy_callable_1,
                    self._on_dummy_callable_1,
                ],
            },
            "Test_9": {
                "label": "FF_COMBO_0",
                "type": "combo_floatfield_slider",
                "default_val": 0,
                "min": -1,
                "max": 1,
                "step": 0.001,
                "tooltip": ["This is the Label Tooltip", "FF Tooltip"],
            },
            "Test_10": {
                "label": "FF_COMBO_1",
                "type": "combo_floatfield_slider",
                "default_val": 0,
                "min": 0,
                "max": 20,
                "step": 2,
                "tooltip": ["This is the Label Tooltip", "FF Tooltip"],
            },
            "Test_11": {
                "label": "DROPDOWN",
                "type": "dropdown",
                "default_val": 2,
                "tooltip": "This is the Label Tooltip",
                "items": ["Config 1", "Config 2", "Config 3"],
                "on_clicked_fn": self._on_dummy_callable_3,
            },
            "Test_13": {
                "label": "DROPDOWN_GROUP",
                "type": "multi_dropdown",
                "count": 3,
                "default_val": [0, 1, 0],
                "tooltip": "This is the Label Tooltip",
                "items": [
                    ["Option 1", "Option 2", "Option 3"],
                    ["Option A", "Option B", "Option C"],
                    ["Option X", "Option Y"],
                ],
                "on_clicked_fn": [self._on_dummy_callable_3, self._on_dummy_callable_3, self._on_dummy_callable_3],
            },
            "Test_12": {
                "label": "ENABLE_DROPDN",
                "type": "checkbox_dropdown",
                "default_val": [False, 1],
                "tooltip": "This is the Label Tooltip",
                "items": ["Config 1", "Config 2", "Config 3"],
                "on_clicked_fn": [self._on_dummy_callable_0, self._on_dummy_callable_3],
            },
            "Test_3": {
                "label": "ENABLE_STR",
                "type": "checkbox_stringfield",
                "default_val": [False, "default"],
                "tooltip": "This is the Label Tooltip",
                "on_clicked_fn": self._on_dummy_callable_0,
            },
            "Test_14": {
                "label": "ENABLE_STREAM",
                "type": "checkbox_scrolling_frame",
                "default_val": [False, "No Data"],
                "tooltip": "This is the Label Tooltip",
                "on_clicked_fn": self._on_dummy_callable_0,
            },
        }

        self._grid = ui.CollapsableFrame(
            title="Example: GUI Grid",
            height=0,
            collapsed=False,
            style=get_style(),
            style_type_name_override="CollapsableFrame",
            horizontal_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_AS_NEEDED,
            vertical_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_ALWAYS_ON,
        )
        with self._grid:
            with ui.VStack(spacing=5, height=0):

                # You can also build a UI with a dictionary
                for key, value in test_gui.items():
                    # Button
                    if value["type"] == "button":
                        self._models["btn_" + value["label"]] = btn_builder(**value)
                    # Checkbox
                    elif value["type"] == "checkbox":
                        self._models["cb_" + value["label"]] = cb_builder(**value)
                    # Multiple Buttons
                    elif value["type"] == "multi_button":
                        elems = multi_btn_builder(**value)
                        for i in range(len(elems)):
                            self._models["btn_" + value["label"]] = elems[i]
                    # Multiple Checkboxes
                    elif value["type"] == "multi_checkbox":
                        elems = multi_cb_builder(**value)
                        for i in range(len(elems)):
                            self._models["cb_" + value["label"]] = elems[i]
                    # Float Field + Slider
                    elif value["type"] == "combo_floatfield_slider":
                        elems = combo_floatfield_slider_builder(**value)
                        self._models["ff_" + value["label"]] = elems[0]
                        self._models["str_field_" + value["label"]] = elems[1]
                    # Dropdown ComboBox
                    elif value["type"] == "dropdown":
                        self._models["dropdown_" + value["label"]] = dropdown_builder(**value).model
                    # Mulitple Dropdown ComboBoxes
                    elif value["type"] == "multi_dropdown":
                        elems = multi_dropdown_builder(**value)
                        for i in range(len(elems)):
                            self._models["dropdown_" + value["label"]] = elems[i].model
                    # Checkbox + Stringfield
                    elif value["type"] == "checkbox_stringfield":
                        elems = combo_cb_str_builder(**value)
                        self._models["cb_" + value["label"]] = elems[0]
                        self._models["stringfield_" + value["label"]] = elems[1]
                    # Checkbox + Dropdown ComboBox
                    elif value["type"] == "checkbox_dropdown":
                        elems = combo_cb_dropdown_builder(**value)
                        self._models["cb_" + value["label"]] = elems[0]
                        self._models["str_field_" + value["label"]] = elems[1]
                    elif value["type"] == "checkbox_scrolling_frame":
                        elems = combo_cb_scrolling_frame_builder(**value)
                        self._models["cb_" + value["label"]] = elems[0]
                        self._models["info_label_" + value["label"]] = elems[1]

                # Test building with default values
                ui.Spacer(height=LABEL_HEIGHT)
                ui.Label("Testing Default UI Elements")
                btn_builder()
                cb_builder()
                multi_btn_builder()
                multi_cb_builder()
                dropdown_builder()
                scrolling_frame_builder()
                multi_dropdown_builder()
                combo_cb_dropdown_builder()
                combo_cb_str_builder()
                btn_builder()
                combo_cb_scrolling_frame_builder()
                ui.Spacer()

    def build_custom_ui(self):
        """
        This is where the User creates their main GUI. 
        Use a Group Frame to help visually differente user-generated vs core Isaac UI elements
        """
        self._my_ui = ui.CollapsableFrame(
            title="My Custom UI",
            height=0,
            collapsed=False,
            style=get_style(),
            name="groupFrame",
            horizontal_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_AS_NEEDED,
            vertical_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_ALWAYS_ON,
        )
        with self._my_ui:
            with ui.VStack(spacing=VERTICAL_SPACING):
                ui.CollapsableFrame(
                    title="Parameter Group 1",
                    height=0,
                    collapsed=False,
                    style=get_style(),
                    name="subFrame",
                    horizontal_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_AS_NEEDED,
                    vertical_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_ALWAYS_ON,
                )
                ui.CollapsableFrame(
                    title="Parameter Group 2",
                    height=0,
                    collapsed=False,
                    style=get_style(),
                    name="subFrame",
                    horizontal_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_AS_NEEDED,
                    vertical_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_ALWAYS_ON,
                )
                ui.CollapsableFrame(
                    title="Parameter Group 3",
                    height=0,
                    collapsed=False,
                    style=get_style(),
                    name="subFrame",
                    horizontal_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_AS_NEEDED,
                    vertical_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_ALWAYS_ON,
                )

    def _on_dummy_callable_0(self, val=None):
        """Dummy Callable for testing the GUI"""
        if PRINT_DEBUG:
            print("You've cliked DUMMY CALLABLE 0:", val)

    def _on_dummy_callable_1(self, val=None):
        """Dummy Callable for testing the GUI"""
        if PRINT_DEBUG:
            print("You've cliked DUMMY CALLABLE 1:", val)

    def _on_dummy_callable_2(self, val=None):
        """Dummy Callable for testing the GUI"""
        if PRINT_DEBUG:
            print("You've cliked DUMMY CALLABLE 2:", val)

    def _on_dummy_callable_3(self, val=None):
        """Dummy Callable for testing the GUI"""
        if PRINT_DEBUG:
            print("You've cliked DUMMY CALLABLE 3. Item Selected: ", val)
