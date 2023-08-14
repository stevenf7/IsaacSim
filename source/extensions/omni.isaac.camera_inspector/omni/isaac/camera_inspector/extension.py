# Copyright (c) 2018-2023, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

import asyncio
import gc
import weakref

import carb
import omni
import omni.kit.commands
import omni.timeline
import omni.ui as ui
import omni.usd
from omni.isaac.core.utils.viewports import create_viewport_for_camera
from omni.isaac.sensor import get_all_camera_objects
from omni.isaac.ui.element_wrappers import TextBlock
from omni.isaac.ui.menu import make_menu_item_description
from omni.isaac.ui.ui_utils import btn_builder, get_style, setup_ui_headers
from omni.kit.menu.utils import MenuItemDescription, add_menu_items, remove_menu_items
from omni.kit.viewport.window import get_viewport_window_instances
from omni.kit.window.property.templates import LABEL_WIDTH

from . import gui_utils

EXTENSION_NAME = "Camera Inspector"
SUPPORTED_AXES = ["world", "usd", "ros"]


class Extension(omni.ext.IExt):
    def on_startup(self, ext_id: str):
        """Initialize extension and UI elements"""

        # Events
        self._usd_context = omni.usd.get_context()

        # Build Window
        self._window = ui.Window(
            title=EXTENSION_NAME, width=500, height=500, visible=False, dockPreference=ui.DockPreference.LEFT_BOTTOM
        )
        self._window.set_visibility_changed_fn(self._on_window)

        # UI
        self._task_ui_elements = dict()

        self._ext_id = ext_id
        menu_items = [
            make_menu_item_description(ext_id, EXTENSION_NAME, lambda a=weakref.proxy(self): a._menu_callback())
        ]
        self._menu_items = [MenuItemDescription(name="Workflows", sub_menu=menu_items)]
        add_menu_items(self._menu_items, "Isaac Utils")
        self._all_cameras = []
        self._all_viewports = []

        # Selection
        self._selected_axis_world = SUPPORTED_AXES[0]
        self._selected_axis_local = SUPPORTED_AXES[0]
        self._selected_camera = None
        self._selected_viewport = None

        self._camera_state_subscriber = None

    def on_shutdown(self):
        self._usd_context = None
        remove_menu_items(self._menu_items, "Isaac Utils")
        if self._window:
            self._window = None
        gc.collect()

    def _on_window(self, visible):
        if self._window.visible:
            # Subscribe to Stage and Timeline Events
            self._usd_context = omni.usd.get_context()

            self._build_ui()
        else:
            self._usd_context = None

    def _menu_callback(self):
        self._window.visible = not self._window.visible

    def _build_ui(self):
        # if not self._window:
        with self._window.frame:
            with ui.VStack(spacing=5, height=0):

                self._build_info_ui()

                self._build_camera_pane()

                self._on_refresh()

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

    ##################################
    # Callbacks
    ##################################

    def _on_refresh(self):
        """Get all cameras in the scene and add them to the camera manager."""
        self._all_cameras = get_all_camera_objects()
        self._all_viewports = list(get_viewport_window_instances())

        self._update_camera_dropdown()
        self._update_viewport_dropdown()

        if self._all_cameras:
            if self._selected_camera is None:
                self._selected_camera = self._all_cameras[0]

            if self._camera_state_subscriber is None:
                self._camera_state_subscriber = (
                    omni.kit.app.get_app()
                    .get_update_event_stream()
                    .create_subscription_to_pop(self._update_camera_stats_ui)
                )

    def _on_camera_changed_event(self, option):
        option = self._task_ui_elements["Camera Names"].get_item_value_model().as_int
        if option < len(self._all_cameras):
            self._selected_camera = self._all_cameras[option]
        else:
            err = f"Selected option {option} not available; available cameras: {[camera.name for camera in self._all_cameras]}"
            raise ValueError(err)

        self._update_camera_stats_ui()

    def _on_viewport_changed_event(self, option):
        option = self._task_ui_elements["Viewport Names"].get_item_value_model().as_int
        if option < len(self._all_viewports):
            self._selected_viewport = self._all_viewports[option]
        else:
            err = f"Selected option {option} not available; available cameras: {[viewport.name for viewport in self._all_viewports]}"
            raise ValueError(err)

    def _on_axis_changed_event(self, option):
        option = self._task_ui_elements["World Camera Axis"].get_item_value_model().as_int
        self._selected_axis_world = SUPPORTED_AXES[option]

        option = self._task_ui_elements["Local Camera Axis"].get_item_value_model().as_int
        self._selected_axis_local = SUPPORTED_AXES[option]

        self._update_camera_stats_ui()

    def _on_create_viewport(self):
        """Create a viewport for the current camera."""
        if self._selected_camera is not None:
            create_viewport_for_camera(
                viewport_name=self._selected_camera.prim_path, camera_prim_path=self._selected_camera.prim_path
            )

            self._on_refresh()
        else:
            carb.log_warn("No camera selected. Cannot create viewport.")

    def _on_assign_camera(self):
        if self._selected_camera is not None and self._selected_viewport is not None:
            omni.kit.commands.execute(
                "SetViewportCamera",
                camera_path=self._selected_camera.prim_path,
                viewport_api=self._selected_viewport.viewport_api,
            )
        else:
            carb.log_warn("No camera or viewport selected. Cannot assign camera to viewport.")

    ##################################
    # UI Builders
    ##################################

    def _build_info_ui(self):
        title = EXTENSION_NAME
        doc_link = "https://docs.omniverse.nvidia.com/app_isaacsim/app_isaacsim/overview.html"

        overview = "This utility is used to inspect cameras in the scene.  "
        overview += "\n\nPress the 'Open in IDE' button to view the source code."

        setup_ui_headers(self._ext_id, __file__, title, doc_link, overview)

    def _build_camera_pane(self):
        frame = ui.CollapsableFrame(
            title="Cameras",
            width=ui.Fraction(1),
            height=0,
            collapsed=False,
            style=get_style(),
            horizontal_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_AS_NEEDED,
            vertical_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_ALWAYS_ON,
        )
        with frame:
            with ui.VStack(style=get_style(), spacing=5, height=0):
                dict = {
                    "label": "Get all cameras in the scene",
                    "type": "button",
                    "text": "Refresh",
                    "tooltip": "Finds all cameras in the scene and adds them to the camera manager.",
                    "on_clicked_fn": self._on_refresh,
                }
                self._task_ui_elements["refresh_btn"] = btn_builder(**dict)
                self._task_ui_elements["refresh_btn"].enabled = True
                frame.visible = True
                label_width = LABEL_WIDTH - 80

                self._task_ui_elements["CameraTextField"] = TextBlock(
                    "Camera State",
                    num_lines=3,
                    tooltip="Prints camera state to this field",
                    include_copy_button=True,
                )
                with ui.HStack():

                    # Add a button for human input source
                    self._camera_names_builder_config = {
                        "label": "Camera",
                        "default_val": 0,
                        "items": self._all_cameras,
                        "tooltip": "Select the camera",
                        "on_clicked_fn": self._on_camera_changed_event,
                        "add_line": False,
                        "label_width": label_width,
                        "width": ui.Fraction(100),
                    }
                    self._task_ui_elements["Camera Names"] = gui_utils.customized_dropdown_builder(
                        **self._camera_names_builder_config
                    )

                    self._open_viewport_btn_config = {
                        "type": "button",
                        "text": "Create Viewport",
                        "tooltip": "Create Viewport for Current Camera",
                        "on_clicked_fn": self._on_create_viewport,
                    }

                    self._task_ui_elements["Create Viewport button"] = btn_builder(**self._open_viewport_btn_config)
                    self._task_ui_elements["Create Viewport button"].enabled = True

                with ui.HStack():
                    # Add a button for human input source
                    self._viewport_names_builder_config = {
                        "label": "Viewport",
                        "default_val": 0,
                        "items": self._all_viewports,
                        "tooltip": "Select the viewport",
                        "on_clicked_fn": self._on_viewport_changed_event,
                        "add_line": False,
                        "label_width": label_width,
                        "width": ui.Fraction(100),
                    }
                    self._task_ui_elements["Viewport Names"] = gui_utils.customized_dropdown_builder(
                        **self._viewport_names_builder_config
                    )

                    # change this to display current camera more clearly
                    self._open_viewport_btn_config = {
                        "type": "button",
                        "text": "Assign Camera to Viewport",
                        "tooltip": "Assign the current camera to the viewport",
                        "on_clicked_fn": self._on_assign_camera,
                    }

                    self._task_ui_elements["Assign camera button"] = btn_builder(**self._open_viewport_btn_config)
                    self._task_ui_elements["Assign camera button"].enabled = True

                self._camera_axes_builder_config = {
                    "label": "World Camera Axis",
                    "default_val": 0,
                    "items": SUPPORTED_AXES,
                    "tooltip": "Select the axis to use",
                    "on_clicked_fn": self._on_axis_changed_event,
                    "add_line": False,
                    "label_width": label_width + 40,
                    "width": ui.Fraction(100),
                }
                self._task_ui_elements["World Camera Axis"] = gui_utils.customized_dropdown_builder(
                    **self._camera_axes_builder_config
                )

                world_transform_models = gui_utils.custom_pos_quat_builder(label_width=label_width, label="World")
                self._task_ui_elements["World Camera Position"] = world_transform_models[0:3]
                self._task_ui_elements["World Camera Orientation"] = world_transform_models[3:7]

                self._camera_axes_builder_config["label"] = "Local Camera Axis"
                self._task_ui_elements["Local Camera Axis"] = gui_utils.customized_dropdown_builder(
                    **self._camera_axes_builder_config
                )

                local_transform_models = gui_utils.custom_pos_quat_builder(label_width=label_width, label="Local")
                self._task_ui_elements["Local Camera Position"] = local_transform_models[0:3]
                self._task_ui_elements["Local Camera Orientation"] = local_transform_models[3:7]

    ##################################
    # UI Updaters
    ##################################
    def _update_camera_dropdown(self):
        # Remove all old camera names
        for child in self._task_ui_elements["Camera Names"].get_item_children():
            self._task_ui_elements["Camera Names"].remove_item(child)

        # add all cameras to the dropdown
        for camera in self._all_cameras:
            self._task_ui_elements["Camera Names"].append_child_item(None, ui.SimpleStringModel(camera.name))

    def _update_viewport_dropdown(self):
        # Remove all old viewport names
        for child in self._task_ui_elements["Viewport Names"].get_item_children():
            self._task_ui_elements["Viewport Names"].remove_item(child)

        # add all viewports to the dropdown
        for viewport in self._all_viewports:
            self._task_ui_elements["Viewport Names"].append_child_item(None, ui.SimpleStringModel(viewport.name))

    def _update_camera_stats_ui(self, e: carb.events.IEvent = None):
        # Update the camera translation and rotation
        if self._selected_camera is not None:
            world_pos, world_quat = self._selected_camera.get_world_pose(camera_axes=self._selected_axis_world)
            local_pos, local_quat = self._selected_camera.get_local_pose(camera_axes=self._selected_axis_local)

            for i in range(3):
                self._task_ui_elements["World Camera Position"][i].set_value(float(world_pos[i]))
                self._task_ui_elements["Local Camera Position"][i].set_value(float(local_pos[i]))

            for i in range(4):
                self._task_ui_elements["World Camera Orientation"][i].set_value(float(world_quat[i]))
                self._task_ui_elements["Local Camera Orientation"][i].set_value(float(local_quat[i]))

            status = f"# World Axis: {self._selected_axis_world}\nworld_position={world_pos.tolist()}\nworld_quat_wxyz={world_quat.tolist()}\n# Local Axis: {self._selected_axis_local}\nlocal_position={local_pos.tolist()}\nlocal_quat_wxyz={local_quat.tolist()}"

            self._task_ui_elements["CameraTextField"].set_text(status)
        else:
            # set all values to zero
            for i in range(3):
                self._task_ui_elements["World Camera Position"][i].set_value(float(0.0))
                self._task_ui_elements["Local Camera Position"][i].set_value(float(0.0))
            for i in range(4):
                self._task_ui_elements["World Camera Orientation"][i].set_value(float(0.0))
                self._task_ui_elements["Local Camera Orientation"][i].set_value(float(0.0))
