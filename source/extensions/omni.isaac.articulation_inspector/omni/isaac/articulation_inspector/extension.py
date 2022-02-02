# Copyright (c) 2018-2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

import weakref
import carb
import omni
from pxr import Usd
from omni.kit.window.property.templates import LABEL_WIDTH
import omni.ui as ui
import omni.usd
import omni.timeline
from omni.kit.menu.utils import add_menu_items, remove_menu_items, MenuItemDescription
from omni.isaac.core.utils.stage import get_stage_units
from omni.isaac.core.utils.prims import get_prim_object_type
from omni.isaac.core.articulations import Articulation

from omni.isaac.articulation_inspector.widgets import ListItemModel, ListItemDelegate, ComboBoxModel
from omni.isaac.ui.ui_utils import (
    add_separator,
    add_line_rect_flourish,
    btn_builder,
    float_builder,
    setup_ui_headers,
    get_style,
    state_btn_builder,
    str_builder,
    combo_floatfield_slider_builder,
)
import omni.physx as _physx
import numpy as np

# joint animation states
ANIM_SEEK_LOWER = 1
ANIM_SEEK_UPPER = 2
ANIM_SEEK_DEFAULT = 3
ANIM_FINISHED = 4

EXTENSION_NAME = "Articulation Inspector"

MAX_DOF_NUM = 100


class Extension(omni.ext.IExt):
    def on_startup(self, ext_id: str):
        """Initialize extension and UI elements"""

        # Events
        self._usd_context = omni.usd.get_context()
        self._physxIFace = _physx.acquire_physx_interface()
        self._physx_subscription = None
        self._stage_event_sub = None
        self._timeline = omni.timeline.get_timeline_interface()

        # UI
        self._window = None
        self._models = {}
        self._ext_id = ext_id
        menu_items = [
            MenuItemDescription(name=EXTENSION_NAME, onclick_fn=lambda a=weakref.proxy(self): a._menu_callback())
        ]
        self._menu_items = menu_items
        add_menu_items(self._menu_items, "Isaac Utils")

        # Selection
        self.new_selection = True
        self._selected_index = None
        self._selected_prim_path = None

        # Articulation
        self.articulation = None
        self.num_dof = None
        self.dof_names = None

        # Animation
        self.current_dof = 0
        self.speeds = None
        self._animate_pos = False
        self._animate_vel = False
        self.animation_state = ANIM_SEEK_LOWER

    def on_shutdown(self):
        self._usd_context = None
        self._stage_event_sub = None
        self._timeline_event_sub = None
        self._physx_subscription = None
        self._models = {}
        remove_menu_items(self._menu_items, "Isaac Utils")
        self._window = None

    def _menu_callback(self):
        # Create the UI
        self._build_ui()
        # Update the Selection Box if the Timeline is already playing
        if self._timeline.is_playing():
            self._refresh_selection_combobox()

    def _build_ui(self):
        if not self._window:

            # Subscribe to Stage and Timeline Events
            self._usd_context = omni.usd.get_context()
            events = self._usd_context.get_stage_event_stream()
            self._stage_event_sub = events.create_subscription_to_pop(self._on_stage_event)
            stream = self._timeline.get_timeline_event_stream()
            self._timeline_event_sub = stream.create_subscription_to_pop(self._on_timeline_event)

            # Build Window
            self._window = ui.Window(
                title=EXTENSION_NAME, width=500, height=500, visible=True, dockPreference=ui.DockPreference.LEFT_BOTTOM
            )
            with self._window.frame:
                with ui.VStack(spacing=5, height=0):

                    self._build_info_ui()

                    self._build_selection_ui()

                    self._build_animation_ui()

                    self._build_inspector_ui()

                    self._build_controllers_ui()

    def _on_selection(self, prim_path):
        """Creates an Articulation Object from the selected articulation prim path.
           Updates the UI with the Selected articulation.

        Args:
            prim_path (string): path to selected articulation
        """
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
            self._models["btn_animate_pos"].enabled = True
            self._models["btn_animate_vel"].enabled = True
            self._models["frame_inspector"].collapsed = False
            self._models["frame_controllers"].collapsed = False

        # Deselect and Reset
        else:
            if self.articulation is not None:
                self._reset_ui()
                self._refresh_selection_combobox()
            self.articulation = None
            if self.num_dof is not None:
                self._toggle_dof_and_gains_callbacks(False)
            # carb.log_warn("Resetting Articulation Inspector")

    def _on_combobox_selection(self, model, val):
        index = model.get_item_value_model().as_int
        if index >= 0 and index < len(self.articulation_list):
            self._selected_index = index
            item = self.articulation_list[index]
            self._selected_prim_path = item
            carb.log_warn(f"Selected Item: {item}")
            self._on_selection(item)

    def _refresh_selection_combobox(self):
        self.articulation_list = self.get_all_articulations()
        self._models["ar_selection_model"] = ComboBoxModel(self.articulation_list)
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
        self._models["ar_selection_model"] = ComboBoxModel(self.articulation_list)
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
        carb.log_warn(f"ALL ARTICULATIONS:\t{articulations}")
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
            self.types = articulation.dof_properties["type"]
            self.lower_limits = articulation.dof_properties["lower"]
            self.upper_limits = articulation.dof_properties["upper"]
            self.max_efforts = articulation.dof_properties["maxEffort"]
            self.stiffness = articulation.dof_properties["stiffness"]
            self.damping = articulation.dof_properties["damping"]
            self.new_selection = False

            self.update_properties_ui_static()

            # Update defaults for joint/vel animation
            # FIXME: these are just arbitrary numbers
            self._joint_pos_defaults = np.zeros(self.num_dof)
            for i in range(self.num_dof):
                self._joint_pos_defaults[i] = (self.upper_limits[i] + self.lower_limits[i]) / 2
            self.speeds = np.full(self.num_dof, 1.0, dtype=float)
            self.max_velocities = np.full(self.num_dof, 10.0, dtype=float)
        else:
            # Use gains from UI after initial update
            self.articulation.get_articulation_controller().set_gains(self.stiffness, self.damping)

        # Update dynamic properties every time
        self.positions = articulation.get_joint_positions()
        self.velocities = articulation.get_joint_velocities()
        self.efforts = articulation.get_joint_efforts()
        self.update_properties_ui_dynamic()

    def _refresh_ui(self, articulation):
        """Updates the GUI with a new Articulation's properties.

        Args:
            articulation (Articulation): [description]
        """
        # Get the latest articulation values and update the Properties UI
        self.get_articulation_values(articulation)

        # Hide the dof and gains frames in case the selected articulation
        # has a different number of joints
        for i in range(MAX_DOF_NUM):
            self.dof_frames[i].visible = False
            self.gains_frames[i].visible = False

        self._update_controllers_ui()
        self._update_dof_and_gains_ui()

        # Turn controller ui callbacks back on
        self._toggle_dof_and_gains_callbacks(True)

    def _reset_ui(self):
        """Reset / Hide UI Elements.
        """
        self._clear_selection_combobox()

        # Reset & Disable MOVE Button
        self._animate_pos = False
        self._models["btn_animate_pos"].text = "START"
        self._models["btn_animate_pos"].enabled = False

        self._animate_vel = False
        self._models["btn_animate_vel"].text = "START"
        self._models["btn_animate_vel"].enabled = False

        # Clear Sliders / TreeViews
        # NOTE: The GUI retains the same amount of space, unfortunately
        pos_list = []
        vel_list = []
        efforts_list = []

        self.joint_pos_model = ListItemModel(*pos_list)
        self.joint_pos_tree.model = self.joint_pos_model

        self.joint_vel_model = ListItemModel(*vel_list)
        self.joint_vel_tree.model = self.joint_vel_model

        self.joint_efforts_model = ListItemModel(*efforts_list)
        self.joint_efforts_tree.model = self.joint_efforts_model

        for i in range(MAX_DOF_NUM):
            self.dof_frames[i].visible = False
            self.gains_frames[i].visible = False

        self._models["frame_inspector"].collapsed = True
        self._models["frame_controllers"].collapsed = True

        # Clear Articulation Properties
        self._models["dof_property_num_dof"].set_value("")
        self._models["dof_property_types"].set_value("")
        self._models["dof_property_gains_kp"].set_value("")
        self._models["dof_property_gains_kd"].set_value("")
        self._models["dof_property_positions"].set_value("")
        self._models["dof_property_velocities"].set_value("")
        self._models["dof_property_efforts"].set_value("")
        self._models["dof_property_joint_limits"].set_value("")

    ##################################
    # Callbacks
    ##################################

    def _on_gains_value_changed(self, name, model, id):
        """Callback for when Gains Slider is modified.

        Args:
            name (string): ui.Label.text
            model (ui.AbstractValueModel): ui.FloatField model
            id (int): Index of DOF
        """
        if self.num_dof is not None:
            if id > -1 and id < self.num_dof:
                val = model.get_value_as_float()
                if "kp" in name.lower():
                    name = "kp"
                    self.stiffness[id] = val
                elif "kd" in name.lower():
                    name = "kd"
                    self.damping[id] = val
                else:
                    carb.log_warn(f"VALUE FROM UNKNOWN INPUT: {name}, {id}, {val}")

                # Update the Joint Value panel
                key = f"dof_{id}_" + name + "_field"
                self._models[key].set_value(val)

                # Update the Articulation
                if self.articulation is not None:
                    self.articulation.get_articulation_controller().set_gains(self.stiffness, self.damping)
                    self.update_properties_ui_dynamic()
                else:
                    carb.log_warn("Invalid Articulation.")

    def _on_controller_value_changed(self, name, model, id):
        """Callback for when a Joint Controller Slider is modified.

        Args:
            name (string): ui.Label.text
            model (ui.AbstractValueModel): ui.FloatField model
            id (int): Index of DOF
        """
        # carb.log_warn(f"{name}, {id}, {model.get_value_as_float()}")
        if self.num_dof is not None:
            if id > -1 and id < self.num_dof:
                val = model.get_value_as_float()

                if "pos" in name.lower():
                    name = "pos"
                    self.positions[id] = val
                elif "vel" in name.lower():
                    name = "vels"
                    self.velocities[id] = val
                elif "efforts" in name.lower():
                    name = "efforts"
                    self.efforts[id] = val
                elif "kp" in name.lower():
                    name = "kp"
                    self.stiffness[id] = val
                elif "kd" in name.lower():
                    name = "kd"
                    self.damping[id] = val

                # Update the DOF and Gains UI
                self._update_dof_and_gains_ui()

                # Update the selected articulation
                if self.articulation is not None:
                    if name == "pos":
                        self.articulation.set_joint_positions(self.positions)
                    elif name == "vels":
                        self.articulation.set_joint_velocities(self.velocities)
                    elif name == "efforts":
                        self.articulation.set_joint_efforts(self.efforts)
                    elif name == "gains_kp" or name == "gains_kd":
                        self.articulation.get_articulation_controller().set_gains(self.stiffness, self.damping)

                    # Update the Properties UI
                    self.update_properties_ui_dynamic()
                else:
                    carb.log_warn("Invalid Articulation.")
            else:
                carb.log_warn(f"Incoming slider id [ {id} ] is out of range (0, {self.num_dof}).")

    def _on_dof_property_changed(self, name, model, id):
        """for when a DOF UI Slider is modified.

        Args:
            name (string): ui.Label.text
            model (ui.AbstractValueModel): ui.FloatField model
            id (int): Index of DOF
        """
        if id > -1 and id < self.num_dof:

            val = model.get_value_as_float()

            if name == "pos":
                self.positions[id] = val
            elif name == "vels":
                self.velocities[id] = val
            elif name == "efforts":
                self.efforts[id] = val
            elif name == "gains_kp":
                self.stiffness[id] = val
            elif name == "gains_kd":
                self.damping[id] = val

            # Update the Gains GUI panels
            if name == "gains_kp" or name == "gains_kd":
                key = f"gains_{id}_" + name + f"_field"
                self._models[key].set_value(val)

            # Update the Joint Controller panels
            if self.joint_pos_model is not None and name == "pos":
                self.joint_pos_model.set_item_value(id, val)
            if self.joint_vel_model is not None and name == "vels":
                self.joint_vel_model.set_item_value(id, val)
            if self.joint_efforts_model is not None and name == "efforts":
                self.joint_efforts_model.set_item_value(id, val)

            if self.articulation is not None:
                if name == "pos":
                    self.articulation.set_joint_positions(self.positions)
                elif name == "vels":
                    self.articulation.set_joint_velocities(self.velocities)
                elif name == "efforts":
                    self.articulation.set_joint_efforts(self.efforts)
                elif name == "gains_kp" or name == "gains_kd":
                    self.articulation.get_articulation_controller().set_gains(self.stiffness, self.damping)

                self.update_properties_ui_dynamic()

            else:
                carb.log_warn("Invalid Articulation.")
        else:
            carb.log_warn(f"Incoming slider id [ {id} ] is out of range (0, {self.num_dof}).")

    def _toggle_dof_and_gains_callbacks(self, val):
        """Add / Remove callbacks from DOF and Gains UI

        Args:
            val (bool): Toggle flag
        """
        for i in range(self.num_dof):
            # Add / Remove callbacks from DOF UI
            for name in self.dof_property_keys:
                key = f"dof_{i}_" + name
                if val:
                    self._models[key + "_fn"] = self._models[key + "_field"].add_value_changed_fn(
                        lambda m, n=name, id=i: self._on_dof_property_changed(n, m, id)
                    )
                else:
                    self._models[key + "_field"].remove_value_changed_fn(self._models[key + "_fn"])
            # Add / Remove callbacks from Gains UI
            for name in self._gains_keys:
                key = f"gains_{i}_" + name
                if val:
                    self._models[key + "_fn"] = self._models[key + "_field"].add_value_changed_fn(
                        lambda m, n=name, id=i: self._on_gains_value_changed(n, m, id)
                    )
                else:
                    self._models[key + "_field"].remove_value_changed_fn(self._models[key + "_fn"])

    def _on_stage_event(self, event):
        """Callback for Stage Events

        Args:
            event (omni.usd.StageEventType): Event Type
        """

        # On every stage event check if any articulations have been added/removed from the Stage
        self._refresh_selection_combobox()

        if event.type == int(omni.usd.StageEventType.SELECTION_CHANGED):
            # self._on_selection_changed()
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

            # Get the latest values from the articulation
            self.get_articulation_values(self.articulation)

            # Handle animation
            if self._animate_pos:
                self._animate_joints(step)
            elif self._animate_vel:
                self._animate_joint_velocities(step)
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

    def _on_animate_joint_pos(self, val):
        """Toggles Animate Joints ON/OFF.

        Args:
            val (bool): Start / Stop. Defaults to False.
        """
        # Toggle Animation ON / OFF
        self._animate_pos = val

    def _on_animate_joint_velocities(self, val):
        """Toggles Animate Joint Velocities ON/OFF.

        Args:
            val (bool): Start / Stop. Defaults to False.
        """
        # Toggle Animation ON / OFF
        self._animate_vel = val

    def _animate_joint_velocities(self, step):
        """Sequentially animates each DOF's velocity between its min/max value.

        Args:
            step (float): simulation step
        """
        i = self.current_dof
        ff, fs = self._models["speed_vel"]
        speed_scalar = ff.get_value_as_float()
        speed = 1.0 * speed_scalar

        val = self.velocities[i]
        if self.animation_state == ANIM_SEEK_LOWER:
            val -= speed * step
            if val <= self.max_velocities[i] * -1:
                val = self.max_velocities[i] * -1
                self.animation_state = ANIM_SEEK_UPPER
        elif self.animation_state == ANIM_SEEK_UPPER:
            val += speed * step
            if val >= self.max_velocities[i]:
                val = self.max_velocities[i]
                self.animation_state = ANIM_SEEK_DEFAULT
        if self.animation_state == ANIM_SEEK_DEFAULT:
            val -= speed * step
            if val <= 0:
                val = 0
                self.animation_state = ANIM_FINISHED
        elif self.animation_state == ANIM_FINISHED:
            val = 0
            self.current_dof = (i + 1) % self.num_dof
            self.animation_state = ANIM_SEEK_LOWER

        # Update the joint velocity
        self.velocities[i] = val

        # Update the slider to update the articulation
        name = f"dof_vels_{i}_field"
        self._models[name].set_value(float(self.velocities[i]))  # need to cast to float for some reason (?)

        pass

    def _animate_joints(self, step):
        """Sequentially animates each DOF's position between its min/max value.

        Args:
            step (float): simulation step
        """
        i = self.current_dof
        ff, fs = self._models["speed_pos"]
        speed_scalar = ff.get_value_as_float()
        speed = self.speeds[i] * speed_scalar

        val = self.positions[i]
        if self.animation_state == ANIM_SEEK_LOWER:
            val -= speed * step
            if val <= self.lower_limits[i]:
                val = self.lower_limits[i]
                self.animation_state = ANIM_SEEK_UPPER
        elif self.animation_state == ANIM_SEEK_UPPER:
            val += speed * step
            if val >= self.upper_limits[i]:
                val = self.upper_limits[i]
                self.animation_state = ANIM_SEEK_DEFAULT
        if self.animation_state == ANIM_SEEK_DEFAULT:
            val -= speed * step
            if val <= self._joint_pos_defaults[i]:
                val = self._joint_pos_defaults[i]
                self.animation_state = ANIM_FINISHED
        elif self.animation_state == ANIM_FINISHED:
            val = self._joint_pos_defaults[i]
            self.current_dof = (i + 1) % self.num_dof
            self.animation_state = ANIM_SEEK_LOWER

        # Update the joint position
        self.positions[i] = val

        # Update the slider to update the articulation
        name = f"dof_{i}_pos_field"
        self._models[name].set_value(float(self.positions[i]))  # need to cast to float for some reason (?)

    ##################################
    # UI Builders
    ##################################

    def _build_info_ui(self):
        title = EXTENSION_NAME
        doc_link = "https://docs.omniverse.nvidia.com/app_isaacsim/app_isaacsim/overview.html"

        overview = "This utility is used to inspect and verify the Dynamic Control Properties of an articulation.  "
        overview += "Select the Articulation you would like to inspect from the Stage."
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
                self._models["ar_selection_model"] = ComboBoxModel(self.articulation_list)
                with ui.HStack():
                    ui.Label(
                        "Select Articulation",
                        width=LABEL_WIDTH,
                        alignment=ui.Alignment.LEFT_CENTER,
                        tooltip="Select Articulation to Inspect",
                    )
                    self._models["ar_selection_combobox"] = ui.ComboBox(self._models["ar_selection_model"])
                    add_line_rect_flourish(False)
                self._models["ar_selection_combobox"].model.add_item_changed_fn(self._on_combobox_selection)

    def _build_animation_ui(self):
        frame = ui.CollapsableFrame(
            title="Animation Controls",
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
                    "label": "Animate Joint Positions",
                    "a_text": "START",
                    "b_text": "STOP",
                    "tooltip": "Sequentially Animate Each Joint",
                    "on_clicked_fn": self._on_animate_joint_pos,
                }
                self._models["btn_animate_pos"] = state_btn_builder(**kwargs)
                self._models["btn_animate_pos"].enabled = False

                kwargs = {
                    "label": "Position Speed Scalar",
                    "default_val": "1",
                    "min": 0.1,
                    "max": 100,
                    "step": 0.01,
                    "tooltip": ["Speed Scalar", ""],
                }
                self._models["speed_pos"] = combo_floatfield_slider_builder(**kwargs)

                kwargs = {
                    "label": "Animate Joint Velocities",
                    "a_text": "START",
                    "b_text": "STOP",
                    "tooltip": "Sequentially Animate Each Joint Velocities",
                    "on_clicked_fn": self._on_animate_joint_velocities,
                }
                self._models["btn_animate_vel"] = state_btn_builder(**kwargs)
                self._models["btn_animate_vel"].enabled = False

                kwargs = {
                    "label": "Velocity Speed Scalar",
                    "default_val": "1",
                    "min": 0.1,
                    "max": 100,
                    "step": 0.01,
                    "tooltip": ["Speed Scalar", ""],
                }
                self._models["speed_vel"] = combo_floatfield_slider_builder(**kwargs)

    def _build_inspector_ui(self):

        self._models["frame_inspector"] = ui.CollapsableFrame(
            title="Inspector",
            height=0,
            collapsed=True,
            style=get_style(),
            name="groupFrame",
            horizontal_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_AS_NEEDED,
            vertical_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_ALWAYS_ON,
        )
        with self._models["frame_inspector"]:
            with ui.VStack(style=get_style(), spacing=5, height=0):
                frame = ui.CollapsableFrame(
                    title="Properties",
                    height=0,
                    collapsed=False,
                    style=get_style(),
                    name="subFrame",
                    horizontal_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_AS_NEEDED,
                    vertical_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_ALWAYS_ON,
                )
                with frame:
                    with ui.VStack(style=get_style(), spacing=5, height=0):

                        kwargs = {
                            "label": "Number of DOF",
                            "default_val": "",
                            "tooltip": "Number of Degrees of Freedom",
                            "read_only": True,
                        }
                        self._models["dof_property_num_dof"] = str_builder(**kwargs)

                        kwargs = {
                            "label": "DOF Types",
                            "default_val": "",
                            "tooltip": "0 = DOF_NONE, 1 = DOF_ROTATION, 2 = DOF_TRANSLATION",
                            "read_only": True,
                        }
                        self._models["dof_property_types"] = str_builder(**kwargs)

                        kwargs = {"label": "Positions", "default_val": "", "tooltip": "Positions", "read_only": True}
                        self._models["dof_property_positions"] = str_builder(**kwargs)

                        kwargs = {"label": "Velocities", "default_val": "", "tooltip": "Velocities", "read_only": True}
                        self._models["dof_property_velocities"] = str_builder(**kwargs)

                        kwargs = {"label": "Efforts", "default_val": "", "tooltip": "Efforts", "read_only": True}
                        self._models["dof_property_efforts"] = str_builder(**kwargs)

                        kwargs = {"label": "Stiffness", "default_val": "", "tooltip": "Gains (kp)", "read_only": True}
                        self._models["dof_property_gains_kp"] = str_builder(**kwargs)

                        kwargs = {"label": "Damping", "default_val": "", "tooltip": "Gains (kd)", "read_only": True}
                        self._models["dof_property_gains_kd"] = str_builder(**kwargs)

                        kwargs = {
                            "label": "Joint Limits",
                            "default_val": "",
                            "tooltip": "Joint Limits",
                            "read_only": True,
                        }
                        self._models["dof_property_joint_limits"] = str_builder(**kwargs)

                self._build_dof_ui()

                self._build_gains_ui()

    def _build_gains_ui(self):
        frame = ui.CollapsableFrame(
            title="Gain Tuning",
            height=0,
            collapsed=True,
            style=get_style(),
            name="subFrame",
            horizontal_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_AS_NEEDED,
            vertical_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_ALWAYS_ON,
        )
        with frame:
            with ui.VStack(style=get_style(), spacing=5, height=0):

                def on_zero_all_gains():
                    for i in range(self.num_dof):
                        self._models[f"gains_{i}_kp_field"].set_value(0.001)
                        self._models[f"gains_{i}_kd_field"].set_value(0.0001)

                kwargs = {
                    "label": "Zero All Gains",
                    "text": "Zero",
                    "tooltip": "Zero all joint gains for tuning",
                    "on_clicked_fn": on_zero_all_gains,
                }
                self._models["dof_tuning_zero_all_btn"] = btn_builder(**kwargs)

                kwargs = {"label": "Gain Multiplier", "default_val": 10, "tooltip": "Multiplier for Scaling Gains"}
                self._models["gains_scalar"] = float_builder(**kwargs)

                def on_scale_gains():
                    scalar = self._models["gains_scalar"].get_value_as_float()
                    for i in range(self.num_dof):
                        val = self._models[f"gains_{i}_kp_field"].get_value_as_float()
                        self._models[f"gains_{i}_kp_field"].set_value(val * scalar)
                        val = self._models[f"gains_{i}_kd_field"].get_value_as_float()
                        self._models[f"gains_{i}_kd_field"].set_value(val * scalar)
                    pass

                kwargs = {
                    "label": "Scale Gains",
                    "text": "Scale",
                    "tooltip": "Scale All Gains by the Gain Multiplier",
                    "on_clicked_fn": on_scale_gains,
                }
                self._models["gains_scale_btn"] = btn_builder(**kwargs)

                add_separator()

                self.gains_frames = []
                # Add the Gain Pairs per joint
                for i in range(MAX_DOF_NUM):
                    name = f"DOF {i}"
                    frame = ui.CollapsableFrame(
                        title=name,
                        height=0,
                        collapsed=False,
                        style=get_style(),
                        name="subFrame",
                        horizontal_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_AS_NEEDED,
                        vertical_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_ALWAYS_ON,
                    )
                    frame.visible = False
                    self.gains_frames.append(frame)

                    with frame:
                        with ui.VStack(style=get_style(), spacing=5, height=0):

                            self._gains_keys = ["kp", "kd"]
                            gains_labels = ["Stiffness (kp)", "Damping (kd)"]

                            for j in range(len(self._gains_keys)):
                                name = self._gains_keys[j]
                                label = gains_labels[j]

                                kwargs = {"label": label, "step": 0.001, "tooltip": ["DOF " + label, ""]}
                                self._models[f"gains_{i}_" + name + "_field"], self._models[
                                    f"gains_{i}_" + name + "_slider"
                                ] = combo_floatfield_slider_builder(**kwargs)

    def _build_dof_ui(self):
        """Creates an interactive UI where DOF properties are grouped together per DOF.
        """
        frame = ui.CollapsableFrame(
            title="DOF View",
            height=0,
            collapsed=True,
            style=get_style(),
            name="subFrame",
            horizontal_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_AS_NEEDED,
            vertical_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_ALWAYS_ON,
        )
        with frame:
            with ui.VStack(style=get_style(), spacing=5, height=0):

                self.dof_frames = []
                for i in range(MAX_DOF_NUM):
                    frame = ui.CollapsableFrame(
                        title=f"DOF {i}",
                        height=0,
                        collapsed=False,
                        style=get_style(),
                        name="subFrame",
                        horizontal_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_AS_NEEDED,
                        vertical_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_ALWAYS_ON,
                    )
                    frame.visible = False
                    self.dof_frames.append(frame)

                    with frame:
                        with ui.VStack(style=get_style(), spacing=5, height=0):

                            self.dof_property_keys = ["pos", "vels", "kp", "kd", "efforts"]
                            dof_property_labels = ["Position", "Velocity", "Stiffness (kp)", "Damping (kd)", "Effort"]

                            for j in range(len(self.dof_property_keys)):
                                name = self.dof_property_keys[j]
                                label = dof_property_labels[j]

                                kwargs = {"label": label, "step": 0.001, "tooltip": ["DOF " + label, ""]}
                                self._models[f"dof_{i}_" + name + "_field"], self._models[
                                    f"dof_{i}_" + name + "_slider"
                                ] = combo_floatfield_slider_builder(**kwargs)

    def _build_position_controller_ui(self):
        frame = ui.CollapsableFrame(
            title="Position Controller",
            height=0,
            collapsed=False,
            style=get_style(),
            style_type_name_override="CollapsableFrame",
            horizontal_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_AS_NEEDED,
            vertical_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_ALWAYS_ON,
        )
        with frame:
            with ui.VStack(style=get_style(), spacing=5, height=0):
                list = []
                self.joint_pos_model = ListItemModel(*list)
                self.joint_pos_delegate = ListItemDelegate()
                self.joint_pos_tree = ui.TreeView(
                    self.joint_pos_model,
                    height=0,
                    delegate=self.joint_pos_delegate,
                    root_visible=False,
                    header_visible=False,
                    style_type_name_override="CollapsableFrame",
                )

    def _build_velocity_controller_ui(self):
        frame = ui.CollapsableFrame(
            title="Velocity Controller",
            height=0,
            collapsed=False,
            style=get_style(),
            style_type_name_override="CollapsableFrame",
            horizontal_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_AS_NEEDED,
            vertical_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_ALWAYS_ON,
        )
        with frame:
            with ui.VStack(style=get_style(), spacing=5, height=0):
                list = []
                self.joint_vel_model = ListItemModel(*list)
                self.joint_vel_delegate = ListItemDelegate()
                self.joint_vel_tree = ui.TreeView(
                    self.joint_vel_model,
                    height=0,
                    delegate=self.joint_vel_delegate,
                    root_visible=False,
                    header_visible=False,
                    style_type_name_override="CollapsableFrame",
                )

    def _build_efforts_controller_ui(self):
        frame = ui.CollapsableFrame(
            title="Efforts Controller",
            height=0,
            collapsed=False,
            style=get_style(),
            style_type_name_override="CollapsableFrame",
            horizontal_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_AS_NEEDED,
            vertical_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_ALWAYS_ON,
        )
        with frame:
            with ui.VStack(style=get_style(), spacing=5, height=0):
                list = []
                self.joint_efforts_model = ListItemModel(*list)
                self.joint_efforts_delegate = ListItemDelegate()
                self.joint_efforts_tree = ui.TreeView(
                    self.joint_efforts_model,
                    height=0,
                    delegate=self.joint_efforts_delegate,
                    root_visible=False,
                    header_visible=False,
                    style_type_name_override="CollapsableFrame",
                )

    def _build_controllers_ui(self):
        self._models["frame_controllers"] = ui.CollapsableFrame(
            title="Joint Controllers",
            height=0,
            collapsed=True,
            style=get_style(),
            name="groupFrame",
            horizontal_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_AS_NEEDED,
            vertical_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_ALWAYS_ON,
        )
        with self._models["frame_controllers"]:
            with ui.VStack(style=get_style(), spacing=5, height=0):

                frame = ui.CollapsableFrame(
                    title="Update Controllers",
                    height=0,
                    # collapsed=False,
                    style=get_style(),
                    name="subFrame",
                    # style_override="CollapsableFrame",
                    horizontal_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_AS_NEEDED,
                    vertical_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_ALWAYS_ON,
                )
                with frame:
                    with ui.VStack(style=get_style(), spacing=5, height=0):

                        def on_get_current_joint_values():
                            """Updates the Joint Controller Sliders with the current values
                               the articulation.
                               Triggers the `_on_controller_value_changed` callback, which updates other
                               UI elements.
                            """
                            if self.articulation is not None and self.num_dof is not None:
                                for i in range(self.num_dof):
                                    name = f"dof_{i}_pos_field"
                                    self._models[name].set_value(float(self.positions[i]))
                                    name = f"dof_{i}_vels_field"
                                    self._models[name].set_value(float(self.velocities[i]))
                                    name = f"dof_{i}_efforts_field"
                                    self._models[name].set_value(float(self.efforts[i]))

                        kwargs = {
                            "label": "Get Current Values",
                            "text": "REFRESH",
                            "tooltip": "Updates Controllers with Current Joint Values",
                            "on_clicked_fn": on_get_current_joint_values,
                        }
                        self._models["update_controllers_btn"] = btn_builder(**kwargs)

                self._build_position_controller_ui()
                self._build_velocity_controller_ui()
                self._build_efforts_controller_ui()

    ##################################
    # UI Updaters
    ##################################

    def _update_controllers_ui(self):
        """Updates the Position, Velocity, Efforts UI with updated lists.
        """
        pos_list = []
        vel_list = []
        efforts_list = []
        units = get_stage_units()
        for i in range(self.num_dof):

            label = f"{self.dof_names[i]}"
            tooltip = f"DOF {i} Position:"
            if self.types[i] == 1:  # _dynamic_control.DOF_ROTATION:
                tooltip += " Angle (rad)"
            elif self.types[i] == 2:  # _dynamic_control.DOF_TRANSLATION:
                tooltip += " Distance"
                if units < 1.0 and units > 0.005:
                    tooltip += " (cm)"
                elif units < 0.005:
                    tooltip += " (mm)"
                else:
                    tooltip += " (m)"

            # label, id, min=0, max=1, default_val=0, on_value_changed_fn=None, tooltip=""
            kwargs = {
                "label": label,
                "id": i,
                "min": self.lower_limits[i],
                "max": self.upper_limits[i],
                "default_val": self.positions[i],
                "on_value_changed_fn": self._on_controller_value_changed,
                "tooltip": tooltip,
            }
            pos_list.append(kwargs)

            label = f"{self.dof_names[i]}"
            tooltip = f"DOF {i} Velocity"
            kwargs = {
                "label": label,
                "id": i,
                "min": self.max_velocities[i] * -1,
                "max": self.max_velocities[i],
                "default_val": self.velocities[i],
                # "on_value_changed_fn": lambda a,b,c,d=weakref.proxy(self): d._on_controller_value_changed(a,b,c),
                "on_value_changed_fn": self._on_controller_value_changed,
                "tooltip": tooltip,
            }
            vel_list.append(kwargs)

            label = f"{self.dof_names[i]}"
            tooltip = f"DOF {i} Effort"
            kwargs = {
                "label": label,
                "id": i,
                "min": 0,
                "max": self.max_efforts[i],
                "default_val": self.efforts[i],
                # "on_value_changed_fn": lambda a,b,c,d=weakref.proxy(self): d._on_controller_value_changed(a,b,c),
                "on_value_changed_fn": self._on_controller_value_changed,
                "tooltip": tooltip,
            }
            efforts_list.append(kwargs)

        self.joint_pos_model = ListItemModel(*pos_list)
        self.joint_pos_tree.model = self.joint_pos_model

        self.joint_vel_model = ListItemModel(*vel_list)
        self.joint_vel_tree.model = self.joint_vel_model

        self.joint_efforts_model = ListItemModel(*efforts_list)
        self.joint_efforts_tree.model = self.joint_efforts_model

    def update_properties_ui_static(self):
        """Update the static DOF Properties in the Properties Frame: num_dof, types, joint_limits
        """
        self._models["dof_property_num_dof"].set_value(f"{self.num_dof}")
        val = "[" + ", ".join(map(str, self.types)) + "]"
        self._models["dof_property_types"].set_value(f"{val}")

        val = "[ "
        for i in range(self.num_dof):
            val += f"[{self.lower_limits[i]:.4f}, {self.upper_limits[i]:.4f}], "
        val += "]"
        self._models["dof_property_joint_limits"].set_value(f"{val}")

    def update_properties_ui_dynamic(self):
        """Update the dynamic DOF Properties in the Properties Frame: positions, velocities, efforts, gains
        """
        val = "[" + ", ".join(map(str, self.positions)) + "]"
        self._models["dof_property_positions"].set_value(f"{val}")
        val = "[" + ", ".join(map(str, self.velocities)) + "]"
        self._models["dof_property_velocities"].set_value(f"{val}")
        val = "[" + ", ".join(map(str, self.efforts)) + "]"
        self._models["dof_property_efforts"].set_value(f"{val}")
        val = "[" + ", ".join(map(str, self.stiffness)) + "]"
        self._models["dof_property_gains_kp"].set_value(f"{val}")
        val = "[" + ", ".join(map(str, self.damping)) + "]"
        self._models["dof_property_gains_kd"].set_value(f"{val}")

    def _update_dof_and_gains_ui(self):
        """Updates the DOF and Gains UI with updated values.
        """
        for i in range(self.num_dof):
            self.dof_frames[i].visible = True
            self.dof_frames[i].title = f"DOF {i}: {self.dof_names[i]}"
            self.gains_frames[i].visible = True
            self.gains_frames[i].title = f"DOF {i}: {self.dof_names[i]}"
            for name in self.dof_property_keys:
                key = f"dof_{i}_" + name
                key_gains = f"gains_{i}_" + name
                if name == "pos":
                    self._models[key + "_field"].set_value(float(self.positions[i]))
                    self._models[key + "_slider"].min = self.lower_limits[i]
                    self._models[key + "_slider"].max = self.upper_limits[i]
                elif name == "vels":
                    self._models[key + "_field"].set_value(float(self.velocities[i]))
                    self._models[key + "_slider"].min = self.max_velocities[i] * -1.0
                    self._models[key + "_slider"].max = self.max_velocities[i]
                elif name == "efforts":
                    self._models[key + "_field"].set_value(float(self.efforts[i]))
                    self._models[key + "_slider"].min = 0
                    self._models[key + "_slider"].max = self.max_efforts[i]
                elif name == "kp":
                    self._models[key + "_field"].set_value(float(self.stiffness[i]))
                    self._models[key + "_slider"].min = 0
                    self._models[key + "_slider"].max = float(999999999)
                    self._models[key_gains + "_field"].set_value(float(self.stiffness[i]))
                    self._models[key_gains + "_slider"].min = 0
                    self._models[key_gains + "_slider"].max = float(999999999)
                elif name == "kd":
                    self._models[key + "_field"].set_value(float(self.damping[i]))
                    self._models[key + "_slider"].min = 0
                    self._models[key + "_slider"].max = float(999999999)
                    self._models[key_gains + "_field"].set_value(float(self.damping[i]))
                    self._models[key_gains + "_slider"].min = 0
                    self._models[key_gains + "_slider"].max = float(999999999)
