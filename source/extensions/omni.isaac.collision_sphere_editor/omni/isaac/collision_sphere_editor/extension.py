# Copyright (c) 2018-2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

import weakref
import asyncio
import gc
import carb
import omni
from pxr import Usd
from omni.kit.window.property.templates import LABEL_WIDTH
import omni.ui as ui
import omni.usd
import omni.timeline
from omni.kit.menu.utils import add_menu_items, remove_menu_items, MenuItemDescription
from omni.isaac.core.utils.prims import get_prim_object_type
from omni.isaac.core.articulations import Articulation
from .collision_sphere_editor import CollisionSphereEditor

from omni.isaac.ui.widgets import DynamicComboBoxModel

from omni.isaac.ui.ui_utils import (
    add_line_rect_flourish,
    btn_builder,
    float_builder,
    int_builder,
    xyz_builder,
    color_picker_builder,
    setup_ui_headers,
    get_style,
    str_builder,
)
import omni.physx as _physx
import numpy as np
import os

EXTENSION_NAME = "Collision Sphere Editor"

MAX_DOF_NUM = 100


def is_yaml_file(path: str):
    _, ext = os.path.splitext(path.lower())
    return ext in [".yaml", ".YAML"]


def on_filter_item(item) -> bool:
    if not item or item.is_folder:
        return not (item.name == "Omniverse" or item.path.startswith("omniverse:"))
    return is_yaml_file(item.path)


class Extension(omni.ext.IExt):
    def on_startup(self, ext_id: str):
        """Initialize extension and UI elements"""

        # Events
        self._usd_context = omni.usd.get_context()
        self._physxIFace = _physx.acquire_physx_interface()
        self._physx_subscription = None
        self._stage_event_sub = None
        self._timeline = omni.timeline.get_timeline_interface()

        # Build Window
        self._window = ui.Window(
            title=EXTENSION_NAME, width=600, height=500, visible=False, dockPreference=ui.DockPreference.LEFT_BOTTOM
        )
        self._window.set_visibility_changed_fn(self._on_window)

        # UI
        self._models = {}
        self._ext_id = ext_id
        self._menu_items = [
            MenuItemDescription(name=EXTENSION_NAME, onclick_fn=lambda a=weakref.proxy(self): a._menu_callback())
        ]
        # self._menu_items = [MenuItemDescription(name="Workflows", sub_menu=menu_items)]
        add_menu_items(self._menu_items, "Isaac Utils")

        # Selection
        self.new_selection = True
        self._selected_index = None
        self._selected_prim_path = None
        self._prev_art_prim_path = None

        # Articulation
        self.articulation = None
        self.num_dof = 0
        self.dof_names = []

        # Animation
        self._set_joint_positions_on_step = False

        self._collision_sphere_editor = CollisionSphereEditor()

    def on_shutdown(self):
        self._collision_sphere_editor.clear_spheres(store_op=False)
        self._usd_context = None
        self._stage_event_sub = None
        self._timeline_event_sub = None
        self._physx_subscription = None
        self._models = {}
        remove_menu_items(self._menu_items, "Isaac Utils")
        if self._window:
            self._window = None
        gc.collect()

    def _on_window(self, visible):
        if self._window.visible:
            # Subscribe to Stage and Timeline Events
            self._usd_context = omni.usd.get_context()
            events = self._usd_context.get_stage_event_stream()
            self._stage_event_sub = events.create_subscription_to_pop(self._on_stage_event)
            stream = self._timeline.get_timeline_event_stream()
            self._timeline_event_sub = stream.create_subscription_to_pop(self._on_timeline_event)

            self._build_ui()
        else:
            self._usd_context = None
            self._stage_event_sub = None
            self._timeline_event_sub = None

    def _menu_callback(self):
        self._window.visible = not self._window.visible
        # Update the Selection Box if the Timeline is already playing
        if self._timeline.is_playing():
            self._refresh_selection_combobox()

    def _build_ui(self):
        # if not self._window:
        with self._window.frame:
            with ui.VStack(spacing=5, height=0):

                self._build_info_ui()

                self._build_selection_ui()

                self._build_command_ui()

                self._build_editor_ui()

        async def dock_window():
            await omni.kit.app.get_app().next_update_async()

            def dock(space, name, location, pos=0.5):
                window = omni.ui.Workspace.get_window(name)
                if window and space:
                    window.dock_in(space, location, pos)
                return window

            tgt = ui.Workspace.get_window("Viewport")
            dock(tgt, EXTENSION_NAME, omni.ui.DockPosition.LEFT, 0.33)
            await omni.kit.app.get_app().next_update_async()

        self._task = asyncio.ensure_future(dock_window())

    def _on_selection(self, prim_path):
        """Creates an Articulation Object from the selected articulation prim path.
           Updates the UI with the Selected articulation.

        Args:
            prim_path (string): path to selected articulation
        """
        if prim_path == self._prev_art_prim_path:
            return
        else:
            self._prev_art_prim_path = prim_path

        self.new_selection = True

        if self.articulation_list and prim_path != "None":

            # Create and Initialize the Articulation
            self.articulation = Articulation(prim_path)
            if not self.articulation.handles_initialized:
                self.articulation.initialize()

            # Update the entire UI with the selected articulaiton
            self._refresh_ui(self.articulation)

            # start event subscriptions
            if not self._physx_subscription:
                self._physx_subscription = self._physxIFace.subscribe_physics_step_events(self._on_physics_step)

            # Enable Buttons / Layouts in GUI
            self._models["set_joint_positions"].enabled = True

        # Deselect and Reset
        else:
            if self.articulation is not None:
                self._reset_ui()
                self._refresh_selection_combobox()
            self.articulation = None
            # carb.log_warn("Resetting Articulation Inspector")

    def _on_combobox_selection(self, model, val):
        index = model.get_item_value_model().as_int
        if index >= 0 and index < len(self.articulation_list):
            self._selected_index = index
            item = self.articulation_list[index]
            self._selected_prim_path = item
            self._on_selection(item)

    def _refresh_selection_combobox(self):
        self.articulation_list = self.get_all_articulations()
        self._models["ar_selection_model"] = DynamicComboBoxModel(self.articulation_list)
        self._models["ar_selection_combobox"].model = self._models["ar_selection_model"]
        self._models["ar_selection_combobox"].model.add_item_changed_fn(self._on_combobox_selection)
        # If something was already selected, reselect after refresh
        if self._selected_index is not None and self._selected_prim_path is not None:
            # If the item is still in the articulation list
            if self._selected_prim_path in self.articulation_list:
                self._models["ar_selection_combobox"].model.set_item_value_model(
                    ui.SimpleIntModel(self._selected_index)
                )

    def _clear_selection_combobox(self):
        self._selected_index = None
        self._selected_prim_path = None
        self.articulation_list = []
        self._models["ar_selection_model"] = DynamicComboBoxModel(self.articulation_list)
        self._models["ar_selection_combobox"].model = self._models["ar_selection_model"]
        self._models["ar_selection_combobox"].model.add_item_changed_fn(self._on_combobox_selection)

    def get_all_articulations(self):
        """Get all the articulation objects from the Stage.

        Returns:
            list(str): list of prim_paths as strings
        """
        articulations = ["None"]
        stage = self._usd_context.get_stage()
        if stage:
            for prim in Usd.PrimRange(stage.GetPrimAtPath("/")):
                path = str(prim.GetPath())
                # Get prim type get_prim_object_type
                type = get_prim_object_type(path)
                # carb.log_warn(f"{path}:\t{type}")
                if type == "articulation":
                    articulations.append(path)
        # carb.log_warn(f"ALL ARTICULATIONS:\t{articulations}")
        return articulations

    def get_articulation_values(self, articulation):
        """Get and store the latest dof_properties from the articulation.
           Update the Properties UI.

        Args:
            articulation (Articulation): Selected Articulation
        """
        # Update static dof properties on new selection
        if self.new_selection:
            self.num_dof = articulation.num_dof
            self.dof_names = articulation.dof_names
            self.new_selection = False

            self._joint_positions = articulation.get_joint_positions()

    def _refresh_ui(self, articulation):
        """Updates the GUI with a new Articulation's properties.

        Args:
            articulation (Articulation): [description]
        """
        # Get the latest articulation values and update the Properties UI
        self.get_articulation_values(articulation)

        self._update_editor_ui()
        self._update_command_ui()

    def _reset_ui(self):
        """Reset / Hide UI Elements.
        """
        self._clear_selection_combobox()
        self._prev_art_prim_path = None

        # Reset & Disable Button
        self._models["set_joint_positions"].enabled = False

        self._models["frame_command_ui"].collapsed = True

        for i in range(MAX_DOF_NUM):
            self._models[f"joint_{i}_frame"].visible = False

        self._models["sphere_editor_ui"].collapsed = True

    ##################################
    # Callbacks
    ##################################

    def _on_stage_event(self, event):
        """Callback for Stage Events

        Args:
            event (omni.usd.StageEventType): Event Type
        """

        # On every stage event check if any articulations have been added/removed from the Stage
        self._refresh_selection_combobox()

        if event.type == int(omni.usd.StageEventType.SELECTION_CHANGED):
            # self._on_selection_changed()
            self._collision_sphere_editor.copy_all_sphere_data()
            pass

        elif event.type == int(omni.usd.StageEventType.OPENED) or event.type == int(omni.usd.StageEventType.CLOSED):
            # stage was opened or closed, cleanup
            self._physx_subscription = None

    def _on_physics_step(self, step):
        """Callback for Physics Step.
           
        Args:
            step ([type]): [description]
        """
        if self.articulation is not None:
            if not self.articulation.handles_initialized:
                self.articulation.initialize()
            # Get the latest values from the articulation
            self.get_articulation_values(self.articulation)

            # Handle animation
            if self._set_joint_positions_on_step:
                self._set_joint_positions(step)
        return

    def _on_timeline_event(self, e):
        """Callback for Timeline Events

        Args:
            event (omni.timeline.TimelineEventType): Event Type
        """

        if e.type == int(omni.timeline.TimelineEventType.PLAY):
            # BUG: get_all_articulations returns ['None'] after STOP/PLAY <-- articulations show up as xforms
            self._refresh_selection_combobox()
        elif e.type == int(omni.timeline.TimelineEventType.STOP):
            self._reset_ui()

    def _set_joint_positions(self, step):
        if self.articulation is not None:
            joint_velocities = np.zeros_like(self._joint_positions)
            self.articulation.set_joint_positions(self._joint_positions)
            self.articulation.set_joint_velocities(joint_velocities)
        self._set_joint_positions_on_step = False
        return

    ##################################
    # UI Builders
    ##################################

    def _build_info_ui(self):
        title = EXTENSION_NAME
        doc_link = "https://docs.omniverse.nvidia.com/app_isaacsim/app_isaacsim/overview.html"

        overview = "This utility is used to help generate and refine the collision sphere representation of a robot.  "
        overview += "Select the Articulation for which you would like to edit spheres from the dropdown menu."
        overview += "\n\nPress the 'Open in IDE' button to view the source code."

        setup_ui_headers(self._ext_id, __file__, title, doc_link, overview)

    def _build_selection_ui(self):
        frame = ui.CollapsableFrame(
            title="Selection Panel",
            height=0,
            collapsed=False,
            style=get_style(),
            style_type_name_override="CollapsableFrame",
            horizontal_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_AS_NEEDED,
            vertical_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_ALWAYS_ON,
        )
        with frame:
            with ui.VStack(style=get_style(), spacing=5, height=0):

                # Create a dynamic ComboBox for Articulation Selection
                self.articulation_list = []
                self._models["ar_selection_model"] = DynamicComboBoxModel(self.articulation_list)
                with ui.HStack():
                    ui.Label(
                        "Select Articulation",
                        width=LABEL_WIDTH,
                        alignment=ui.Alignment.LEFT_CENTER,
                        tooltip="Select Articulation",
                    )
                    self._models["ar_selection_combobox"] = ui.ComboBox(self._models["ar_selection_model"])
                    add_line_rect_flourish(False)
                self._models["ar_selection_combobox"].model.add_item_changed_fn(self._on_combobox_selection)

    def _build_command_ui(self):
        self._models["frame_command_ui"] = ui.CollapsableFrame(
            title="Command Panel",
            name="groupFrame",
            height=0,
            collapsed=True,
            style=get_style(),
            style_type_name_override="CollapsableFrame",
            horizontal_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_AS_NEEDED,
            vertical_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_ALWAYS_ON,
        )
        with self._models["frame_command_ui"]:
            with ui.VStack(style=get_style(), spacing=5, height=0):

                frame = ui.CollapsableFrame(
                    title="Set Joint Positions",
                    name="subFrame",
                    height=0,
                    collapsed=True,
                    style=get_style(),
                    style_type_name_override="CollapsableFrame",
                    horizontal_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_AS_NEEDED,
                    vertical_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_ALWAYS_ON,
                )
                with frame:
                    with ui.VStack(style=get_style(), spacing=5, height=0):
                        for i in range(MAX_DOF_NUM):
                            name = f"joint_{i}_frame"
                            frame = ui.CollapsableFrame(
                                title=name,
                                name="subFrame",
                                height=0,
                                collapsed=False,
                                style=get_style(),
                                style_type_name_override="CollapsableFrame",
                                horizontal_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_AS_NEEDED,
                                vertical_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_ALWAYS_ON,
                            )
                            if self.articulation is None:
                                frame.visible = False
                            self._models[f"joint_{i}_frame"] = frame

                            kwargs = {
                                "label": "Joint Position",
                                "default_val": 0,
                                "tooltip": f"Desired Position for Robot Joint: {i}",
                            }
                            with frame:
                                with ui.VStack(style=get_style(), spacing=5, height=0):
                                    self._models["joint_{}_position".format(i)] = float_builder(**kwargs)

                        def on_set_joint_positions():
                            # if self.dof_names is None:
                            #     return
                            for i, joint_name in enumerate(self.dof_names):
                                desired_position = self._models["joint_{}_position".format(i)].get_value_as_float()
                                self._joint_positions[i] = desired_position
                            self._set_joint_positions_on_step = True
                            return

                        kwargs = {
                            "label": "Set",
                            "text": "Set Joint Positions",
                            "tooltip": "Set robot joint positions to the desired values",
                            "on_clicked_fn": on_set_joint_positions,
                        }
                        self._models["set_joint_positions"] = btn_builder(**kwargs)
                        self._models["set_joint_positions"].enabled = False

    def _build_editor_ui(self):
        self._models["sphere_editor_ui"] = ui.CollapsableFrame(
            title="Sphere Editor",
            height=0,
            collapsed=True,
            style=get_style(),
            name="editorFrame",
            horizontal_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_AS_NEEDED,
            vertical_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_ALWAYS_ON,
        )
        with self._models["sphere_editor_ui"]:
            with ui.VStack(style=get_style(), spacing=5, height=0):
                ###################################################################
                #                          Generate Spheres
                ###################################################################

                # TODO: Add Sphere Generator Tool from Lula once it is complete.
                """
                frame = ui.CollapsableFrame(
                    title="Generate Spheres",
                    name="subFrame",
                    height=0,
                    collapsed=True,
                    style_type_name_override="CollapsableFrame",
                    horizontal_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_AS_NEEDED,
                    vertical_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_ALWAYS_ON,
                )
                """

                ###################################################################
                #                   Import Robot Description Spheres
                ###################################################################

                frame = ui.CollapsableFrame(
                    title="Load Spheres",
                    name="subFrame",
                    height=0,
                    collapsed=True,
                    style=get_style(),
                    style_type_name_override="CollapsableFrame",
                    horizontal_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_AS_NEEDED,
                    vertical_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_ALWAYS_ON,
                )

                with frame:
                    with ui.VStack(style=get_style(), spacing=5, height=0):

                        def check_file_type(model=None):
                            path = model.get_value_as_string()
                            if (
                                is_yaml_file(path)
                                and "omniverse:" not in path.lower()
                                and self.articulation is not None
                            ):
                                self._models["import_btn"].enabled = True
                            elif self.articulation is None:
                                self._models["import_btn"].enabled = False
                                carb.log_warn(
                                    "Robot Articulation must be selected in the Selection Panel in order to import spheres for a robot"
                                )
                            else:
                                self._models["import_btn"].enabled = False
                                carb.log_warn(f"Invalid path to Robot Desctiption YAML: {path}")

                        kwargs = {
                            "label": "Input File",
                            "default_val": "",
                            "tooltip": "Click the Folder Icon to Set Filepath",
                            "use_folder_picker": True,
                            "item_filter_fn": on_filter_item,
                            "bookmark_label": "Built In YAML Files",
                            "bookmark_path": "/home/arudich/Desktop/Denso/Cobotta_Pro_900_Assets/",
                            "folder_dialog_title": "Select Robot Description YAML file, clearing all spheres",
                            "folder_button_title": "Select YAML",
                        }
                        self._models["input_file"] = str_builder(**kwargs)
                        self._models["input_file"].add_value_changed_fn(check_file_type)

                        self._models["import_btn"] = btn_builder(
                            "Import", text="Import", on_clicked_fn=self._load_spheres_from_robot_description
                        )
                        self._models["import_btn"].enabled = False

                ###################################################################
                #                            Add Sphere
                ###################################################################

                frame = ui.CollapsableFrame(
                    title="Add Sphere",
                    name="subFrame",
                    height=0,
                    collapsed=True,
                    style=get_style(),
                    style_type_name_override="CollapsableFrame",
                    horizontal_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_AS_NEEDED,
                    vertical_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_ALWAYS_ON,
                )

                with frame:
                    with ui.VStack(style=get_style(), spacing=5, height=0):
                        kwargs = {
                            "label": "Parent Prim Path",
                            "default_val": "",
                            "tooltip": "Prim path to parent link for this sphere",
                        }
                        self._models["add_sphere_link_path"] = str_builder(**kwargs)

                        kwargs = {"label": "Radius", "default_val": 0.1, "min": 0.001, "tooltip": "Desired Radius"}
                        self._models["add_sphere_radius"] = float_builder(**kwargs)

                        kwargs = {
                            "label": "Relative Translation",
                            "tooltip": "Relative translation of sphere in the local frame of the selected Prim path.",
                            "axis_count": 3,
                            "default_val": [0.0, 0.0, 0.0],
                        }

                        val_models = xyz_builder(**kwargs)
                        self._models["add_sphere_translation_x"] = val_models[0]
                        self._models["add_sphere_translation_y"] = val_models[1]
                        self._models["add_sphere_translation_z"] = val_models[2]

                        def on_add_sphere():
                            radius = self._models["add_sphere_radius"].get_value_as_float()
                            translation = np.zeros(3)
                            translation[0] = self._models["add_sphere_translation_x"].get_value_as_float()
                            translation[1] = self._models["add_sphere_translation_y"].get_value_as_float()
                            translation[2] = self._models["add_sphere_translation_z"].get_value_as_float()
                            link_path = self._models["add_sphere_link_path"].get_value_as_string()

                            self._collision_sphere_editor.add_sphere(link_path, translation, radius)

                        self._models["add_sphere_btn"] = btn_builder(
                            "Add Sphere", text="Add Sphere", on_clicked_fn=on_add_sphere
                        )

                ###################################################################
                #                           Connect Spheres
                ###################################################################
                frame = ui.CollapsableFrame(
                    title="Connect Spheres",
                    name="subFrame",
                    height=0,
                    collapsed=True,
                    style=get_style(),
                    style_type_name_override="CollapsableFrame",
                    horizontal_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_AS_NEEDED,
                    vertical_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_ALWAYS_ON,
                )

                with frame:
                    with ui.VStack(style=get_style(), spacing=5, height=0):

                        kwargs = {"label": "Prim Path To Sphere", "default_val": "", "tooltip": "Prim path to sphere"}
                        self._models["connect_sphere_path_1"] = str_builder(**kwargs)

                        kwargs = {"label": "Prim Path To Sphere", "default_val": "", "tooltip": "Prim path to sphere"}
                        self._models["connect_sphere_path_2"] = str_builder(**kwargs)

                        kwargs = {
                            "label": "Number of Interpolated Spheres",
                            "default_val": 0,
                            "tooltip": "Create the specified number of spheres interpolated between the selected spheres",
                        }
                        self._models["connect_sphere_num"] = int_builder(**kwargs)

                        def on_connect_spheres():
                            path_1 = self._models["connect_sphere_path_1"].get_value_as_string()
                            path_2 = self._models["connect_sphere_path_2"].get_value_as_string()
                            num = self._models["connect_sphere_num"].get_value_as_int()

                            self._collision_sphere_editor.interpolate_spheres(path_1, path_2, num)

                        self._models["connect_sphere_btn"] = btn_builder(
                            "Connect Spheres", text="Connect Spheres", on_clicked_fn=on_connect_spheres
                        )
                        self._models["connect_sphere_btn"].enabled = True

                ###################################################################
                #                           Scale Spheres
                ###################################################################
                frame = ui.CollapsableFrame(
                    title="Scale Spheres",
                    name="subFrame",
                    height=0,
                    collapsed=True,
                    style=get_style(),
                    style_type_name_override="CollapsableFrame",
                    horizontal_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_AS_NEEDED,
                    vertical_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_ALWAYS_ON,
                )

                with frame:
                    with ui.VStack(style=get_style(), spacing=5, height=0):

                        kwargs = {
                            "label": "Prim Path Root",
                            "default_val": "",
                            "tooltip": "Scale the radii of all spheres whose prim paths start with this argument.",
                        }
                        self._models["scale_spheres_path"] = str_builder(**kwargs)

                        kwargs = {
                            "label": "Scaling Factor",
                            "default_val": 1.0,
                            "min": 0.001,
                            "tooltip": "Scaling factor for the radii of the specified spheres",
                        }
                        self._models["scale_spheres_factor"] = float_builder(**kwargs)

                        def on_scale_spheres():
                            path = self._models["scale_spheres_path"].get_value_as_string()
                            factor = self._models["scale_spheres_factor"].get_value_as_float()

                            self._collision_sphere_editor.scale_spheres(path, factor)

                        self._models["scale_sphere_btn"] = btn_builder(
                            "Scale Spheres", text="Scale Spheres", on_clicked_fn=on_scale_spheres
                        )
                        self._models["scale_sphere_btn"].enabled = True

                ###################################################################
                #                            Save to File
                ###################################################################
                frame = ui.CollapsableFrame(
                    title="Save Spheres",
                    name="subFrame",
                    height=0,
                    collapsed=True,
                    style=get_style(),
                    style_type_name_override="CollapsableFrame",
                    horizontal_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_AS_NEEDED,
                    vertical_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_ALWAYS_ON,
                )

                with frame:
                    with ui.VStack(style=get_style(), spacing=5, height=0):

                        def check_file_type(model=None):
                            path = model.get_value_as_string()
                            if is_yaml_file(path) and "omniverse:" not in path.lower():
                                self._models["export_btn"].enabled = True
                            else:
                                self._models["export_btn"].enabled = False
                                carb.log_warn(f"Invalid path to Robot Desctiption YAML: {path}")

                        kwargs = {
                            "label": "Output File",
                            "default_val": "",
                            "tooltip": "Click the Folder Icon to Set Filepath",
                            "use_folder_picker": True,
                            "item_filter_fn": on_filter_item,
                            "folder_dialog_title": "Write all sphere to a YAML file",
                            "folder_button_title": "Select YAML",
                        }
                        self._models["output_file"] = str_builder(**kwargs)
                        self._models["output_file"].add_value_changed_fn(check_file_type)

                        self._models["export_btn"] = btn_builder("Save", text="Save", on_clicked_fn=self._save_spheres)
                        self._models["export_btn"].enabled = False

                ###################################################################
                #                            Editor Tools
                ###################################################################
                frame = ui.CollapsableFrame(
                    title="Editor Tools",
                    name="subFrame",
                    height=0,
                    collapsed=True,
                    style=get_style(),
                    style_type_name_override="CollapsableFrame",
                    horizontal_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_AS_NEEDED,
                    vertical_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_ALWAYS_ON,
                )

                with frame:
                    with ui.VStack(style=get_style(), spacing=5, height=0):

                        self._models["undo_btn"] = btn_builder(
                            "Undo", text="Undo", on_clicked_fn=self._collision_sphere_editor.undo
                        )
                        self._models["undo_btn"].enabled = True

                        self._models["redo_btn"] = btn_builder(
                            "Redo", text="Redo", on_clicked_fn=self._collision_sphere_editor.redo
                        )
                        self._models["redo_btn"].enabled = True

                        def on_color_change(a1, a2):
                            sphere_color = []
                            for item in self._models["color_picker"].get_item_children():
                                val = self._models["color_picker"].get_item_value_model(item).get_value_as_float()
                                sphere_color.append(val)
                            sphere_color = np.array(sphere_color[:3])
                            self._collision_sphere_editor.set_sphere_colors(sphere_color)

                        kwargs = {
                            "label": "Sphere Color",
                            "default_val": self._collision_sphere_editor.sphere_color,
                            "tooltip": "Set the color of all collision spheres",
                        }
                        self._models["color_picker"] = color_picker_builder(**kwargs)
                        self._models["color_picker"].add_end_edit_fn(on_color_change)

                        kwargs = {
                            "label": "Robot Opacity",
                            "default_val": 0.5,
                            "min": 0.0,
                            "max": 1.0,
                            "tooltip": "Opacity of the robot ranging from 0 (invisible) to 1 (opaque).",
                        }
                        # TODO: fill in self._set_robot_opacity() function to allow the robot to be made transparent via a slider
                        # self._models["art_opacity"] = float_builder(**kwargs)
                        # self._models["art_opacity"].add_value_changed_fn(self._set_robot_opacity)

                        """
                        Create a "Quickstart" button for debugging.  quickstart() function can be filled in to simulate a series of inputs to
                        the UI such as loading spheres from a file, then adding a sphere

                        def quickstart():
                            self._collision_sphere_editor.load_spheres(
                                self.articulation,
                                "/home/arudich/Desktop/Denso/Cobotta_Pro_900_Assets/robot_descriptor_final.yaml",
                            )
                            self._collision_sphere_editor.add_sphere(
                                "/cobotta_pro_900/J1", np.array([0.0, 0.0, 0.0]), 0.2
                            )

                        self._models["quickstart"] = btn_builder(
                            "Quickstart", text="Quickstart", on_clicked_fn=quickstart
                        )
                        self._models["quickstart"].enabled = True
                        """

                        self._models["clear_btn"] = btn_builder(
                            "Clear All Spheres", text="Clear", on_clicked_fn=self._collision_sphere_editor.clear_spheres
                        )
                        self._models["clear_btn"].enabled = True

    def _update_editor_ui(self):
        self._models["connect_sphere_path_1"].set_value(self.articulation.prim_path + "/")
        self._models["connect_sphere_path_2"].set_value(self.articulation.prim_path + "/")
        self._models["add_sphere_link_path"].set_value(self.articulation.prim_path + "/")
        self._models["scale_spheres_path"].set_value(self.articulation.prim_path + "/")

        if is_yaml_file(self._models["input_file"].get_value_as_string()):
            self._models["import_btn"].enabled = True

    def _update_command_ui(self):
        if self.articulation is None:
            return

        # self._models["frame_command_ui"].visible=True

        for i, joint_name in enumerate(self.dof_names):
            self._models[f"joint_{i}_frame"].title = joint_name
            self._models[f"joint_{i}_frame"].visible = True

            self._models[f"joint_{i}_position"].set_value(self._joint_positions[i])

    def _set_robot_opacity(self, model=None):
        if self.articulation is None:
            return
        opacity = self._models["art_opacity"].get_value_as_float()

    def _save_spheres(self, path=None):
        path = self._models["output_file"].get_value_as_string()
        if path:
            self._collision_sphere_editor.save_spheres(self.articulation, path)

    def _load_spheres_from_robot_description(self, path=None):
        path = self._models["input_file"].get_value_as_string()
        if path:
            self._collision_sphere_editor.load_spheres(self.articulation, path)
