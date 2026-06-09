# SPDX-FileCopyrightText: Copyright (c) 2021-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: LicenseRef-NvidiaProprietary
#
# NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
# property and proprietary rights in and to this material, related
# documentation and any modifications thereto. Any use, reproduction,
# disclosure or distribution of this material and related documentation
# without an express license agreement from NVIDIA CORPORATION or
# its affiliates is strictly prohibited.
"""Create-network example UI for authoring a waypoint graph directly in the stage."""

import gc
import weakref
from typing import Any

import carb.eventdispatcher
import omni.ext
import omni.ui as ui
import omni.usd
from isaacsim.gui.components.ui_utils import btn_builder, get_style, setup_ui_headers
from omni.cuopt.visualization.generate_waypoint_graph import NetworkSimpleViz
from omni.kit.menu.utils import MenuItemDescription, add_menu_items, remove_menu_items
from pxr import Gf

EXTENSION_NAME = "Create Network"


# Any class derived from `omni.ext.IExt` in top level module (defined in `python.modules` of `extension.toml`) will be
# instantiated when extension gets enabled and `on_startup(ext_id)` will be called. Later when extension gets disabled
# on_shutdown() is called.
class cuOptSampleExtension(omni.ext.IExt):
    """Expose menu actions that add waypoint node and edge prims to the USD stage."""

    # ext_id is current extension id. It can be used with extension manager to query additional information, like where
    # this extension is located on filesystem.
    def on_startup(self, ext_id: Any) -> Any:
        """Register the example menu item and prepare an empty waypoint-graph visualizer.

        Args:
            ext_id: Extension identifier passed by Kit.

        Returns:
            None.
        """
        self._ext_id = ext_id

        self._window = None
        self._usd_context = omni.usd.get_context()
        self._stage = self._usd_context.get_stage()
        self._num_nodes = 0
        self._num_edges = 0
        self.waypoint_graph_node_path = "/World/WaypointGraph/Nodes"
        self.waypoint_graph_edge_path = "/World/WaypointGraph/Edges"

        self._network = NetworkSimpleViz()

        self._menu_items = [
            MenuItemDescription(header="Examples"),
            MenuItemDescription(
                name=EXTENSION_NAME,
                onclick_fn=lambda a=weakref.proxy(self): a._menu_callback(),
            ),
        ]

        add_menu_items(self._menu_items, "cuOpt")

        self._build_ui()

    def _menu_callback(self) -> Any:
        self._window.visible = not self._window.visible

    def _on_window(self, visible: Any) -> Any:
        if self._window.visible:
            self._sub_stage_event = carb.eventdispatcher.get_eventdispatcher().observe_event(
                event_name=self._usd_context.stage_event_name(omni.usd.StageEventType.CLOSED),
                on_event=self._on_stage_event,
                observer_name="cuopt_create_network._on_stage_event",
            )
        else:
            self._sub_stage_event = None

    def _on_stage_event(self, event: Any) -> Any:
        """Receive stage-close notifications while the example window is visible.

        Args:
            event: Stage event payload from the event dispatcher.

        Returns:
            None.

        Note: With Events 2.0, this is called only for CLOSED events.
        """

    def _build_ui(self) -> Any:
        if not self._window:
            self._window = ui.Window(
                title=EXTENSION_NAME,
                width=0,
                height=0,
                visible=False,
                dockPreference=ui.DockPreference.LEFT_BOTTOM,
            )
            self._window.set_visibility_changed_fn(self._on_window)

        with self._window.frame:
            with ui.VStack(spacing=5, height=0):
                title = "cuOpt Extension Code and Docs"
                doc_link = "https://docs.nvidia.com/cuopt/"

                overview = "This example demonstrates the creation of a route network"
                overview += "\n\nPress the 'Open Source Code' button to view the source code."

                setup_ui_headers(self._ext_id, __file__, title, doc_link, overview)

                # Setting up the UI setup the optimization problem
                create_frame = ui.CollapsableFrame(
                    title="Create Network",
                    height=0,
                    collapsed=False,
                    style=get_style(),
                    style_type_name_override="CollapsableFrame",
                    horizontal_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_AS_NEEDED,
                    vertical_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_ALWAYS_ON,
                )
                with create_frame:
                    with ui.VStack(style=get_style(), spacing=5, height=0):

                        ui_data_style = {
                            "font_size": 14,
                            "color": 0xBBBBBBBB,
                            "alignment": ui.Alignment.LEFT,
                        }

                        args = {
                            "label": "Create Node",
                            "type": "button",
                            "text": "Create Node",
                            "tooltip": "Create a Network Node",
                            "on_clicked_fn": self.create_node,
                        }
                        self.create_node_btn = btn_builder(**args)

                        self._node_ui_data = ui.Label(
                            "",
                            width=350,
                            word_wrap=True,
                            style=ui_data_style,
                        )

                        args = {
                            "label": "Create Edge",
                            "type": "button",
                            "text": "Create Edge",
                            "tooltip": "Create an Edge between two Nodes",
                            "on_clicked_fn": self.create_edge,
                        }
                        self.create_edge_btn = btn_builder(**args)

                        self._edge_ui_data = ui.Label(
                            "",
                            width=350,
                            word_wrap=True,
                            style=ui_data_style,
                        )

    def create_node(self) -> Any:
        """Add a new waypoint node sphere under the graph node root.

        Returns:
            None.
        """
        stage = self._usd_context.get_stage()
        node_name = "Node_" + str(self._num_nodes)
        node_prim_path = self.waypoint_graph_node_path + "/" + node_name

        self._network.add_node_to_scene(stage, node_prim_path, [0, 0, 0])
        self._node_ui_data.text = "Created node: " + node_name
        self._num_nodes += 1

    def create_edge(self) -> Any:
        """Create a directed waypoint edge cylinder between the two selected node prims.

        Returns:
            None.
        """
        stage = self._usd_context.get_stage()
        selection = self._usd_context.get_selection().get_selected_prim_paths()
        if len(selection) == 2:
            Node_from = stage.GetPrimAtPath(selection[0])
            Node_to = stage.GetPrimAtPath(selection[1])
            node_from_coord = list(Node_from.GetAttribute("xformOp:translate").Get())
            node_to_coord = list(Node_to.GetAttribute("xformOp:translate").Get())
        else:
            self._edge_ui_data.text = "Please select exactly two nodes"
            return

        point_from = Gf.Vec3d(node_from_coord)
        point_to = Gf.Vec3d(node_to_coord)

        from_to_node = Node_from.GetName().split("_")[-1] + "_" + Node_to.GetName().split("_")[-1]
        edge_name = "Edge_" + from_to_node
        edge_prim_path = self.waypoint_graph_edge_path + "/" + edge_name
        self._network.add_edge_to_scene(stage, edge_prim_path, point_from, point_to)

        self._edge_ui_data.text = "Created edge: " + edge_name
        self._num_edges += 1

    def on_shutdown(self) -> Any:
        """Remove the example menu item, release the window, and collect extension objects.

        Returns:
            None.
        """
        self._editor_event_subscription = None
        remove_menu_items(self._menu_items, "cuOpt")
        self._window = None
        gc.collect()
