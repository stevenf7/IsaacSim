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
import omni.ui as ui
import omni.usd
from omni.kit.menu.utils import add_menu_items, remove_menu_items, MenuItemDescription
from omni.isaac.core.utils.stage import get_stage_units
from omni.isaac.core.utils.prims import get_prim_object_type
from omni.isaac.core.articulations import Articulation

from omni.isaac.articulation_inspector.widgets import ListItemModel, ListItemDelegate
from omni.isaac.ui.ui_utils import (
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
        self._window = None
        self._physxIFace = _physx.acquire_physx_interface()
        self._physx_subscription = None
        self._timeline = omni.timeline.get_timeline_interface()

        # Create Selection parameters
        self._usd_context = omni.usd.get_context()
        self._selection = None
        self._events = None

        self._ext_id = ext_id
        menu_items = [
            MenuItemDescription(name=EXTENSION_NAME, onclick_fn=lambda a=weakref.proxy(self): a._menu_callback())
        ]
        self._menu_items = menu_items
        add_menu_items(self._menu_items, "Isaac Utils")

        self.articulation = None
        self._models = {}
        self.current_dof = 0
        self.speeds = None
        self.num_dof = None
        self._animate_pos = False
        self._animate_vel = False
        self.animation_state = ANIM_SEEK_LOWER

    def _menu_callback(self):
        # start/stop physics sim once on load
        # if not self._timeline.is_playing():
        #     self._timeline.play()
        #     self._timeline.stop()

        self._build_ui()

    def _build_ui(self):
        if not self._window:

            self._usd_context = omni.usd.get_context()
            self._selection = self._usd_context.get_selection()
            self._events = self._usd_context.get_stage_event_stream()
            self._stage_event_sub = self._events.create_subscription_to_pop(
                self._on_stage_event, name="Articulation Selection Watch"
            )

            self._window = ui.Window(
                title=EXTENSION_NAME, width=500, height=500, visible=True, dockPreference=ui.DockPreference.LEFT_BOTTOM
            )
            with self._window.frame:
                with ui.VStack(spacing=5, height=0):
                    title = "Articulation Inspector"
                    doc_link = "https://docs.omniverse.nvidia.com/app_isaacsim/app_isaacsim/overview.html"

                    overview = "This utility is used to inspect and verify the Dynamic Control Properties of an articulation.  "
                    overview += "Select the Articulation you would like to inspect from the Stage."
                    overview += "\n\nPress the 'Open in IDE' button to view the source code."

                    setup_ui_headers(self._ext_id, __file__, title, doc_link, overview)

                    frame = ui.CollapsableFrame(
                        title="Command Panel",
                        height=0,
                        collapsed=False,
                        style=get_style(),
                        style_type_name_override="CollapsableFrame",
                        horizontal_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_AS_NEEDED,
                        vertical_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_ALWAYS_ON,
                    )
                    with frame:
                        with ui.VStack(style=get_style(), spacing=5, height=0):

                            kwargs = {
                                "label": "Articulation Root",
                                "default_val": "",
                                "tooltip": "The Prim Path of the Articulation Root",
                            }
                            self._models["ar_prim_path"] = str_builder(**kwargs)

                            kwargs = {
                                "label": "Animate Joint Positions",
                                "a_text": "START",
                                "b_text": "STOP",
                                "tooltip": "Sequentially Animate Each Joint",
                                "on_clicked_fn": self._on_animate_joint_pos,
                            }
                            self._models["animate_pos_btn"] = state_btn_builder(**kwargs)
                            self._models["animate_pos_btn"].enabled = False

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
                            self._models["animate_vel_btn"] = state_btn_builder(**kwargs)
                            self._models["animate_vel_btn"].enabled = False

                            kwargs = {
                                "label": "Velocity Speed Scalar",
                                "default_val": "1",
                                "min": 0.1,
                                "max": 100,
                                "step": 0.01,
                                "tooltip": ["Speed Scalar", ""],
                            }
                            self._models["speed_vel"] = combo_floatfield_slider_builder(**kwargs)

                    self._models["frame_articulation"] = ui.CollapsableFrame(
                        title="Articulation Inspector",
                        height=0,
                        collapsed=True,
                        style=get_style(),
                        name="groupFrame",
                        horizontal_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_AS_NEEDED,
                        vertical_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_ALWAYS_ON,
                    )
                    with self._models["frame_articulation"]:
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
                                    self._models["dof_props_num_dof"] = str_builder(**kwargs)

                                    kwargs = {
                                        "label": "DOF Types",
                                        "default_val": "",
                                        "tooltip": "0 = DOF_NONE, 1 = DOF_ROTATION, 2 = DOF_TRANSLATION",
                                        "read_only": True,
                                    }
                                    self._models["dof_props_types"] = str_builder(**kwargs)

                                    kwargs = {
                                        "label": "Positions",
                                        "default_val": "",
                                        "tooltip": "Positions",
                                        "read_only": True,
                                    }
                                    self._models["dof_props_positions"] = str_builder(**kwargs)

                                    kwargs = {
                                        "label": "Velocities",
                                        "default_val": "",
                                        "tooltip": "Velocities",
                                        "read_only": True,
                                    }
                                    self._models["dof_props_velocities"] = str_builder(**kwargs)

                                    kwargs = {
                                        "label": "Efforts",
                                        "default_val": "",
                                        "tooltip": "Efforts",
                                        "read_only": True,
                                    }
                                    self._models["dof_props_efforts"] = str_builder(**kwargs)

                                    kwargs = {
                                        "label": "Stiffness",
                                        "default_val": "",
                                        "tooltip": "Gains (kp)",
                                        "read_only": True,
                                    }
                                    self._models["dof_props_gains_kp"] = str_builder(**kwargs)

                                    kwargs = {
                                        "label": "Damping",
                                        "default_val": "",
                                        "tooltip": "Gains (kd)",
                                        "read_only": True,
                                    }
                                    self._models["dof_props_gains_kd"] = str_builder(**kwargs)

                                    kwargs = {
                                        "label": "Joint Limits",
                                        "default_val": "",
                                        "tooltip": "Joint Limits",
                                        "read_only": True,
                                    }
                                    self._models["dof_props_joint_limits"] = str_builder(**kwargs)

                            frame = ui.CollapsableFrame(
                                title="DOF Tuning",
                                height=0,
                                collapsed=True,
                                style=get_style(),
                                name="groupFrame",
                                horizontal_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_AS_NEEDED,
                                vertical_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_ALWAYS_ON,
                            )
                            with frame:
                                with ui.VStack(style=get_style(), spacing=5, height=0):
                                    self.dof_prop_frames = []
                                    for i in range(MAX_DOF_NUM):
                                        frame = ui.CollapsableFrame(
                                            title=f"DOF {i}",
                                            height=0,
                                            collapsed=True,
                                            style=get_style(),
                                            name="subFrame",
                                            horizontal_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_AS_NEEDED,
                                            vertical_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_ALWAYS_ON,
                                        )
                                        frame.visible = False
                                        self.dof_prop_frames.append(frame)

                                        with frame:
                                            with ui.VStack(style=get_style(), spacing=5, height=0):

                                                self.dof_prop_names = ["pos", "vels", "gains_kp", "gains_kd", "efforts"]
                                                self.dof_prop_labels = [
                                                    "Position",
                                                    "Velocity",
                                                    "Stiffness (kp)",
                                                    "Damping (kd)",
                                                    "Effort",
                                                ]

                                                for j in range(len(self.dof_prop_names)):
                                                    name = self.dof_prop_names[j]
                                                    label = self.dof_prop_labels[j]

                                                    kwargs = {
                                                        "label": label,
                                                        "step": 0.001,
                                                        "tooltip": ["DOF " + label, ""],
                                                    }
                                                    self._models["dof_" + name + f"_{i}_field"], self._models[
                                                        "dof_" + name + f"_{i}_slider"
                                                    ] = combo_floatfield_slider_builder(**kwargs)

                    self._models["frame_joint"] = ui.CollapsableFrame(
                        title="Joint Controllers",
                        height=0,
                        collapsed=True,
                        style=get_style(),
                        name="groupFrame",
                        horizontal_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_AS_NEEDED,
                        vertical_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_ALWAYS_ON,
                    )
                    with self._models["frame_joint"]:
                        with ui.VStack(style=get_style(), spacing=5, height=0):

                            frame = ui.CollapsableFrame(
                                title="Joint Positions",
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

                            frame = ui.CollapsableFrame(
                                title="Joint Velocities",
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

                            frame = ui.CollapsableFrame(
                                title="Joint Efforts",
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

    def on_shutdown(self):
        self._sub_stage_event = None
        self._physx_subscription = None
        self._models = {}
        self._usd_context = None
        self._selection = None
        self._events = None
        remove_menu_items(self._menu_items, "Isaac Utils")
        self._window = None

    def update_articulation_properties_gui(self):
        self._models["dof_props_num_dof"].set_value(f"{self.num_dof}")
        val = "[" + ", ".join(map(str, self.types)) + "]"
        self._models["dof_props_types"].set_value(f"{val}")

        val = "[ "
        for i in range(self.num_dof):
            val += f"[{self.lower_limits[i]:.4f}, {self.upper_limits[i]:.4f}], "
        val += "]"
        self._models["dof_props_joint_limits"].set_value(f"{val}")

    def update_joint_states_gui(self):
        val = "[" + ", ".join(map(str, self.positions)) + "]"
        self._models["dof_props_positions"].set_value(f"{val}")
        val = "[" + ", ".join(map(str, self.velocities)) + "]"
        self._models["dof_props_velocities"].set_value(f"{val}")
        val = "[" + ", ".join(map(str, self.efforts)) + "]"
        self._models["dof_props_efforts"].set_value(f"{val}")

        val = "[" + ", ".join(map(str, self.stiffness)) + "]"
        self._models["dof_props_gains_kp"].set_value(f"{val}")
        val = "[" + ", ".join(map(str, self.damping)) + "]"
        self._models["dof_props_gains_kd"].set_value(f"{val}")

    def update_articulation_values(self, articulation):
        self.num_dof = articulation.num_dof
        # self.names = articulation.dof_properties["names"]
        # for name in self.names:
        #     carb.log_warn(f"{name}")
        self.types = articulation.dof_properties["type"]
        self.stiffness = articulation.dof_properties["stiffness"]
        self.damping = articulation.dof_properties["damping"]
        self.lower_limits = articulation.dof_properties["lower"]
        self.upper_limits = articulation.dof_properties["upper"]
        self.max_efforts = articulation.dof_properties["maxEffort"]
        self.update_articulation_properties_gui()

        self.positions = articulation.get_joint_positions()
        self.velocities = articulation.get_joint_velocities()
        self.efforts = articulation.get_joint_efforts()
        self.update_joint_states_gui()

    def _refresh_gui(self, articulation):
        """Updates the GUI with a new Articulation's properties.

        Args:
            articulation (Articulation): [description]
        """

        self.update_articulation_values(articulation)

        # Set defaults to the mid-point
        self.defaults = np.zeros(self.num_dof)
        for i in range(self.num_dof):
            self.defaults[i] = (self.upper_limits[i] + self.lower_limits[i]) / 2

        self.speeds = np.full(self.num_dof, 1.0, dtype=float)
        self.max_velocities = np.full(self.num_dof, 10.0, dtype=float)

        # Initalize sliders

        # Clear the sliders in case the selected articulation has a different
        # number of joints
        for i in range(MAX_DOF_NUM):
            self.dof_prop_frames[i].visible = False

        # Initialize the correct number of DOF sliders
        pos_list = []
        vel_list = []
        efforts_list = []
        units = get_stage_units()
        for i in range(self.num_dof):

            label = f"Joint Position {i}"
            tooltip = label
            if self.types[i] == 1:  # _dynamic_control.DOF_ROTATION:
                tooltip = "Angle (rad)"
            elif self.types[i] == 2:  # _dynamic_control.DOF_TRANSLATION:
                tooltip = "Distance"
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
                # "on_value_changed_fn": lambda a,b,c,d=weakref.proxy(self): d._on_joint_value_changed(a,b,c),
                "on_value_changed_fn": self._on_joint_value_changed,
                "tooltip": tooltip,
            }
            pos_list.append(kwargs)

            label = f"Joint Velocity {i}"
            tooltip = label
            kwargs = {
                "label": label,
                "id": i,
                "min": self.max_velocities[i] * -1,
                "max": self.max_velocities[i],
                "default_val": self.velocities[i],
                # "on_value_changed_fn": lambda a,b,c,d=weakref.proxy(self): d._on_joint_value_changed(a,b,c),
                "on_value_changed_fn": self._on_joint_value_changed,
                "tooltip": tooltip,
            }
            vel_list.append(kwargs)

            label = f"Joint Efforts {i}"
            tooltip = label
            kwargs = {
                "label": label,
                "id": i,
                "min": 0,
                "max": self.max_efforts[i],
                "default_val": self.efforts[i],
                # "on_value_changed_fn": lambda a,b,c,d=weakref.proxy(self): d._on_joint_value_changed(a,b,c),
                "on_value_changed_fn": self._on_joint_value_changed,
                "tooltip": tooltip,
            }
            efforts_list.append(kwargs)

        self.joint_pos_model = ListItemModel(*pos_list)
        self.joint_pos_tree.model = self.joint_pos_model

        self.joint_vel_model = ListItemModel(*vel_list)
        self.joint_vel_tree.model = self.joint_vel_model

        self.joint_efforts_model = ListItemModel(*efforts_list)
        self.joint_efforts_tree.model = self.joint_efforts_model

        for i in range(self.num_dof):
            self.dof_prop_frames[i].visible = True
            for name in self.dof_prop_names:
                key = "dof_" + name + f"_{i}"
                if name == "pos":
                    self._models[key + "_field"].set_value(self.positions[i])
                    self._models[key + "_slider"].min = self.lower_limits[i]
                    self._models[key + "_slider"].max = self.upper_limits[i]
                elif name == "vels":
                    self._models[key + "_field"].set_value(self.positions[i])
                    self._models[key + "_slider"].min = self.max_velocities[i] * -1.0
                    self._models[key + "_slider"].max = self.max_velocities[i]
                elif name == "efforts":
                    self._models[key + "_field"].set_value(self.efforts[i])
                    self._models[key + "_slider"].min = 0
                    self._models[key + "_slider"].max = self.max_efforts[i]
                elif name == "gains_kp":
                    self._models[key + "_field"].set_value(self.stiffness[i])
                    self._models[key + "_slider"].min = 0
                    self._models[key + "_slider"].max = 100000
                elif name == "gains_kd":
                    self._models[key + "_field"].set_value(self.damping[i])
                    self._models[key + "_slider"].min = 0
                    self._models[key + "_slider"].max = 10000

        # Turn on slider callbacks
        if self.num_dof is not None:
            self._toggle_edit_joints(True)

    def _on_selection_changed(self):
        """Checks if selection is an Articulation and updates UI
        accordingly.

        Returns:
            [type]: [description]
        """
        # When TC runs tests, it's possible that stage is None
        selection = self._selection.get_selected_prim_paths()
        stage = self._usd_context.get_stage()
        if selection and stage:

            ar_prim_path = selection[0]
            self._models["ar_prim_path"].set_value(ar_prim_path)

            # Get prim type get_prim_object_type
            type = get_prim_object_type(ar_prim_path)
            if type == "articulation":
                self.articulation = Articulation(ar_prim_path)
                if not self.articulation.handles_initialized:
                    self.articulation.initialize()

                # update GUI with new articulation
                self._refresh_gui(self.articulation)

                self._physx_subscription = self._physxIFace.subscribe_physics_step_events(self._on_physics_step)
                self._sub_stage_event = (
                    omni.usd.get_context().get_stage_event_stream().create_subscription_to_pop(self._on_stage_event)
                )
                self._models["animate_pos_btn"].enabled = True
                self._models["animate_vel_btn"].enabled = True
                self._models["frame_articulation"].collapsed = False
                self._models["frame_joint"].collapsed = False
            else:
                if self.articulation is not None:
                    self._reset_gui()
                self.articulation = None
                if self.num_dof is not None:
                    self._toggle_edit_joints(False)
                msg = "Either the Selection is not an Articulation, or the simulation has never been started."
                msg += " Please select an Articulation Root or toggle the simulation to begin."
                carb.log_warn(msg)
            return True

        return False

    def _reset_gui(self):
        """Reset / Hide UI Elements.
        """
        # Reset & Disable MOVE Button
        self._animate_pos = False
        self._models["animate_pos_btn"].text = "START"
        self._models["animate_pos_btn"].enabled = False

        self._animate_vel = False
        self._models["animate_vel_btn"].text = "START"
        self._models["animate_vel_btn"].enabled = False

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
            self.dof_prop_frames[i].visible = False

        self._models["frame_articulation"].collapsed = True
        self._models["frame_joint"].collapsed = True

        # Clear Articulation Properties
        self._models["dof_props_num_dof"].set_value("")
        self._models["dof_props_types"].set_value("")
        self._models["dof_props_gains_kp"].set_value("")
        self._models["dof_props_gains_kd"].set_value("")
        self._models["dof_props_positions"].set_value("")
        self._models["dof_props_velocities"].set_value("")
        self._models["dof_props_efforts"].set_value("")
        self._models["dof_props_joint_limits"].set_value("")

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

    def update_dof_properties_frame(self):
        """Update the UI for the DOF Properties Frame.
        """
        val = "[" + ", ".join(map(str, self.positions)) + "]"
        self._models["dof_props_positions"].set_value(f"{val}")
        val = "[" + ", ".join(map(str, self.velocities)) + "]"
        self._models["dof_props_velocities"].set_value(f"{val}")
        val = "[" + ", ".join(map(str, self.efforts)) + "]"
        self._models["dof_props_efforts"].set_value(f"{val}")
        val = "[" + ", ".join(map(str, self.stiffness)) + "]"
        self._models["dof_props_gains_kp"].set_value(f"{val}")
        val = "[" + ", ".join(map(str, self.damping)) + "]"
        self._models["dof_props_gains_kd"].set_value(f"{val}")

    def _on_joint_value_changed(self, name, model, id):
        """Callback for when Joint Controller Slider is modified.

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
                    name = "gains_kp"
                    self.stiffness[id] = val
                elif "kd" in name.lower():
                    name = "gains_kd"
                    self.damping[id] = val

                # Update the DOF GUI panel
                key = "dof_" + name + f"_{id}_field"
                self._models[key].set_value(val)

                if self.articulation is not None:
                    if name == "pos":
                        self.articulation.set_joint_positions(self.positions)
                    elif name == "vels":
                        self.articulation.set_joint_velocities(self.velocities)
                    elif name == "efforts":
                        self.articulation.set_joint_efforts(self.efforts)
                    elif name == "gains_kp" or name == "gains_kd":
                        self.articulation.get_articulation_controller().set_gains(self.stiffness, self.damping)

                    self.update_dof_properties_frame()
                else:
                    carb.log_warn("Invalid Articulation.")
            else:
                carb.log_warn(f"Incoming slider id [ {id} ] is out of range (0, {self.num_dof}).")

    def _on_dof_property_changed(self, name, model, id):
        """Callback for when DOF Tuning Slider is modified.

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

                self.update_dof_properties_frame()

            else:
                carb.log_warn("Invalid Articulation.")
        else:
            carb.log_warn(f"Incoming slider id [ {id} ] is out of range (0, {self.num_dof}).")

        pass

    def _toggle_edit_joints(self, val):
        """Adds / Removes value_changed_fn to sliders.

        Args:
            val (bool): Toggle flag
        """
        for i in range(self.num_dof):
            for name in self.dof_prop_names:
                dof_key = "dof_" + name + f"_{i}"
                if val:
                    self._models[dof_key + "_fn"] = self._models[dof_key + "_field"].add_value_changed_fn(
                        lambda m, n=name, id=i: self._on_dof_property_changed(n, m, id)
                    )
                else:
                    self._models[dof_key + "_field"].remove_value_changed_fn(self._models[dof_key + "_fn"])

    def _on_stage_event(self, event):

        if event.type == int(omni.usd.StageEventType.SELECTION_CHANGED):
            self._on_selection_changed()

        elif event.type == int(omni.usd.StageEventType.OPENED) or event.type == int(omni.usd.StageEventType.CLOSED):
            # stage was opened or closed, cleanup
            self._physx_subscription = None
            # self.ar = _dynamic_control.INVALID_HANDLE

    def _on_physics_step(self, step):
        if self.articulation is not None:
            if self._animate_pos:
                self._animate_joints(step)
            elif self._animate_vel:
                self._animate_joint_velocities(step)

            # Update GUI
            self.update_articulation_values(self.articulation)

        return

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
            if val <= self.defaults[i]:
                val = self.defaults[i]
                self.animation_state = ANIM_FINISHED
        elif self.animation_state == ANIM_FINISHED:
            val = self.defaults[i]
            self.current_dof = (i + 1) % self.num_dof
            self.animation_state = ANIM_SEEK_LOWER

        # Update the joint position
        self.positions[i] = val

        # Update the slider to update the articulation
        name = f"dof_pos_{i}_field"
        self._models[name].set_value(float(self.positions[i]))  # need to cast to float for some reason (?)
