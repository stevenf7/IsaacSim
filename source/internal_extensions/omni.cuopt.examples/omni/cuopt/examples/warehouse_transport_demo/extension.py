# SPDX-FileCopyrightText: Copyright (c) 2021-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: LicenseRef-NvidiaProprietary
#
# NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
# property and proprietary rights in and to this material, related
# documentation and any modifications thereto. Any use, reproduction,
# disclosure or distribution of this material and related documentation
# without an express license agreement from NVIDIA CORPORATION or
# its affiliates is strictly prohibited.
"""Intra-warehouse transport demo UI for building a scene and solving cuOpt routes."""

import gc
import weakref
from typing import Any

import carb.eventdispatcher
import omni.ext
import omni.ui as ui
import omni.usd
from isaacsim.core.rendering_manager import ViewportManager
from isaacsim.gui.components.ui_utils import btn_builder, get_style, setup_ui_headers, str_builder
from isaacsim.storage.native import get_assets_root_path
from omni.cuopt.service.common import show_vehicle_routes, test_connection_managed_service, test_connection_microservice
from omni.cuopt.service.cuopt_data_proc import preprocess_cuopt_data
from omni.cuopt.service.cuopt_microservice_manager import cuOptRunner
from omni.cuopt.service.transport_orders import TransportOrders
from omni.cuopt.service.transport_vehicles import TransportVehicles
from omni.cuopt.service.waypoint_graph_model import WaypointGraphModel, load_waypoint_graph_from_file
from omni.cuopt.visualization.common import check_build_base_path
from omni.cuopt.visualization.generate_orders import visualize_order_locations
from omni.cuopt.visualization.generate_semantics import generate_semantic_zones
from omni.cuopt.visualization.generate_warehouse_assets import generate_conveyor_assets, generate_shelves_assets
from omni.cuopt.visualization.generate_warehouse_building import generate_building_structure
from omni.cuopt.visualization.generate_waypoint_graph import update_weights, visualize_waypoint_graph
from omni.kit.menu.utils import MenuItemDescription, add_menu_items, remove_menu_items
from pxr import UsdGeom, UsdLux

# Any class derived from `omni.ext.IExt` in top level module (defined in `python.modules` of `extension.toml`) will be
# instantiated when extension gets enabled and `on_startup(ext_id)` will be called. Later when extension gets disabled
# on_shutdown() is called.

EXTENSION_NAME = "Intra-warehouse Transport Demo"


class cuOptMicroserviceExtension(omni.ext.IExt):
    """Build warehouse assets, load routing inputs, and visualize solved transport routes."""

    # ext_id is current extension id. It can be used with extension manager to query additional information, like where
    # this extension is located on filesystem.
    def on_startup(self, ext_id: Any) -> Any:
        """Register the demo menu item, resolve assets/sample data, and initialize route state.

        Args:
            ext_id: Extension identifier passed by Kit.

        Returns:
            None.
        """
        self._ext_id = ext_id

        ext_manager = omni.kit.app.get_app().get_extension_manager()
        self._extension_path = ext_manager.get_extension_path(ext_id)
        self._extension_data_path = (
            f"{self._extension_path}/omni/cuopt/examples/warehouse_transport_demo/extension_data/"
        )

        self._window = None
        self._usd_context = omni.usd.get_context()

        self._cuopt_ip_prompt = "Enter IP"
        self._cuopt_port_prompt = "Enter Port"
        self._cuopt_sak_prompt = "Enter SAK"
        self._function_name_prompt = ""
        self._function_id_prompt = ""
        self._cuopt_ip = "Enter IP"
        self._cuopt_port = "Enter Port"
        self._cuopt_sak = "Enter SAK"
        self._function_name = ""
        self._function_id = ""
        self.client = None

        self._semantic = {}

        base_isaac_path = get_assets_root_path()

        self._base_isaac_asset_path = base_isaac_path + "/Isaac/"
        self._base_nvidia_asset_path = base_isaac_path + "/NVIDIA/Assets/"
        self._nvidia_digital_twin_path = self._base_nvidia_asset_path + "DigitalTwin/Assets/Warehouse/"

        self.waypoint_graph_node_path = "/World/Warehouse/Transportation/WaypointGraph/Nodes"
        self.waypoint_graph_edge_path = "/World/Warehouse/Transportation/WaypointGraph/Edges"

        self.warehouse_building_config = "warehouse_building_data.json"
        self.warehouse_shelves_config = "warehouse_shelves_data.json"
        self.warehouse_conveyors_config = "warehouse_conveyors_data.json"
        self.waypoint_graph_config = "waypoint_graph.json"
        self.semantic_config = "semantics_data.json"
        self.orders_config = "orders_data.json"
        self.vehicles_config = "vehicle_data.json"

        self._waypoint_graph_model = WaypointGraphModel()
        self._orders_obj = TransportOrders()
        self._vehicles_obj = TransportVehicles()
        self._semantics = []

        self._menu_items = [
            MenuItemDescription(
                name=EXTENSION_NAME,
                onclick_fn=lambda a=weakref.proxy(self): a._menu_callback(),
            )
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
                observer_name="cuopt_warehouse_transport._on_stage_event",
            )
        else:
            self._sub_stage_event = None

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

                overview = "This example demonstrates use of the NVIDIA cuOpt microservice "
                overview += "to perform routing optimization in an intra-warehouse transport context."
                overview += "\n\nPress the 'Open Source Code' button to view the source code."

                setup_ui_headers(self._ext_id, __file__, title, doc_link, overview)

                # Setting up the UI to connect to cuOpt Managed Service
                connect_cuOpt_frame = ui.CollapsableFrame(
                    title="Connect to cuOpt Managed Service",
                    height=0,
                    collapsed=False,
                    style=get_style(),
                    style_type_name_override="CollapsableFrame",
                    horizontal_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_AS_NEEDED,
                    vertical_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_ALWAYS_ON,
                )

                with connect_cuOpt_frame:

                    with ui.VStack(style=get_style(), spacing=5, height=0):

                        kwargs = {
                            "label": "cuOpt SAK",
                            "type": "stringfield",
                            "default_val": self._cuopt_sak_prompt,
                            "tooltip": "SAK for cuOpt managed service",
                            "on_clicked_fn": None,
                            "use_folder_picker": False,
                            "read_only": False,
                        }
                        self._cuopt_sak = str_builder(**kwargs)

                        kwargs = {
                            "label": "Function Name",
                            "type": "stringfield",
                            "default_val": self._function_name_prompt,
                            "tooltip": "Function name for cuOpt managed service",
                            "on_clicked_fn": None,
                            "use_folder_picker": False,
                            "read_only": False,
                        }
                        self._function_name = str_builder(**kwargs)

                        kwargs = {
                            "label": "Function Id",
                            "type": "stringfield",
                            "default_val": self._function_id_prompt,
                            "tooltip": "Function id for cuOpt managed service",
                            "on_clicked_fn": None,
                            "use_folder_picker": False,
                            "read_only": False,
                        }
                        self._function_id = str_builder(**kwargs)

                        kwargs = {
                            "label": "Test cuOpt Connection ",
                            "type": "button",
                            "text": "Test",
                            "tooltip": "Test to verify cuOpt managed service is reachable",
                            "on_clicked_fn": self._test_cuopt_connection_managed_service,
                        }
                        btn_builder(**kwargs)

                # Setting up the UI to connect to cuOpt Microservice
                connect_cuOpt_frame = ui.CollapsableFrame(
                    title="Connect to cuOpt Microservice",
                    height=0,
                    collapsed=False,
                    style=get_style(),
                    style_type_name_override="CollapsableFrame",
                    horizontal_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_AS_NEEDED,
                    vertical_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_ALWAYS_ON,
                )
                with connect_cuOpt_frame:

                    with ui.VStack(style=get_style(), spacing=5, height=0):

                        kwargs = {
                            "label": "cuOpt IP",
                            "type": "stringfield",
                            "default_val": self._cuopt_ip_prompt,
                            "tooltip": "IP for cuOpt microservice",
                            "on_clicked_fn": None,
                            "use_folder_picker": False,
                            "read_only": False,
                        }
                        self._cuopt_ip = str_builder(**kwargs)

                        kwargs = {
                            "label": "cuOpt Port",
                            "type": "stringfield",
                            "default_val": self._cuopt_port_prompt,
                            "tooltip": "Port for cuOpt microservice",
                            "on_clicked_fn": None,
                            "use_folder_picker": False,
                            "read_only": False,
                        }
                        self._cuopt_port = str_builder(**kwargs)

                        kwargs = {
                            "label": "Test cuOpt Connection ",
                            "type": "button",
                            "text": "Test",
                            "tooltip": "Test to verify cuOpt microservice is reachable",
                            "on_clicked_fn": self._test_cuopt_connection_microservice,
                        }
                        btn_builder(**kwargs)

                self._cuopt_status_info = ui.Label(" ")

                # Setting up the UI setup the optimization problem
                setup_frame = ui.CollapsableFrame(
                    title="Optimization Problem Setup",
                    height=0,
                    collapsed=False,
                    style=get_style(),
                    style_type_name_override="CollapsableFrame",
                    horizontal_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_AS_NEEDED,
                    vertical_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_ALWAYS_ON,
                )
                with setup_frame:
                    with ui.VStack(style=get_style(), spacing=5, height=0):

                        ui_data_style = {
                            "font_size": 14,
                            "color": 0x88888888,
                            "alignment": ui.Alignment.LEFT,
                        }

                        kwargs = {
                            "label": "Load Sample Warehouse ",
                            "type": "button",
                            "text": "Load",
                            "tooltip": "Loads an example warehouse environment",
                            "on_clicked_fn": self._build_warehouse_environment,
                        }
                        btn_builder(**kwargs)
                        self._warehouse_ui_data = ui.Label(
                            "No Warehouse Loaded",
                            width=350,
                            word_wrap=True,
                            style=ui_data_style,
                        )

                        kwargs = {
                            "label": "Load Waypoint Graph ",
                            "type": "button",
                            "text": "Load",
                            "tooltip": "Loads a waypoint graph for the sample environment",
                            "on_clicked_fn": self._load_waypoint_graph,
                        }
                        btn_builder(**kwargs)
                        self._network_ui_data = ui.Label(
                            "No Waypoint Graph network Loaded",
                            width=350,
                            word_wrap=True,
                            style=ui_data_style,
                        )

                        kwargs = {
                            "label": "Load Orders ",
                            "type": "button",
                            "text": "Load",
                            "tooltip": "Loads sample orders",
                            "on_clicked_fn": self._load_orders,
                        }
                        btn_builder(**kwargs)
                        self._orders_ui_data = ui.Label(
                            "No Orders Loaded",
                            width=350,
                            word_wrap=True,
                            style=ui_data_style,
                        )

                        kwargs = {
                            "label": "Load Vehicles ",
                            "type": "button",
                            "text": "Load",
                            "tooltip": "Loads sample vehicle data",
                            "on_clicked_fn": self._load_vehicles,
                        }
                        btn_builder(**kwargs)
                        self._vehicle_ui_data = ui.Label(
                            "No Vehicles Loaded",
                            width=350,
                            word_wrap=True,
                            style=ui_data_style,
                        )

                        kwargs = {
                            "label": "Generate Semantic Zone ",
                            "type": "button",
                            "text": "Generate",
                            "tooltip": "Generates a sample semantics zone",
                            "on_clicked_fn": self._load_semantic_zone,
                        }
                        btn_builder(**kwargs)
                        self._semantic_ui_data = ui.Label(
                            "No Semantic Zones Loaded",
                            width=350,
                            word_wrap=True,
                            style=ui_data_style,
                        )

                        with ui.VStack(style=get_style(), spacing=5, height=0):

                            kwargs = {
                                "label": "length",
                                "type": "integer",
                                "default_val": 2.0,
                                "tooltip": "Length for semantic",
                                "on_clicked_fn": None,
                                "use_folder_picker": False,
                                "read_only": False,
                            }
                            self._semantic["length"] = str_builder(**kwargs)

                            kwargs = {
                                "label": "width",
                                "type": "integer",
                                "default_val": 2.0,
                                "tooltip": "Width for semantic",
                                "on_clicked_fn": None,
                                "use_folder_picker": False,
                                "read_only": False,
                            }
                            self._semantic["width"] = str_builder(**kwargs)

                # Setting up the UI setup the optimization problem
                run_frame = ui.CollapsableFrame(
                    title="Update/Run cuOpt",
                    height=0,
                    collapsed=False,
                    style=get_style(),
                    style_type_name_override="CollapsableFrame",
                    horizontal_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_AS_NEEDED,
                    vertical_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_ALWAYS_ON,
                )
                with run_frame:
                    with ui.VStack(style=get_style(), spacing=5, height=0):

                        ui_data_style = {
                            "font_size": 14,
                            "color": 0xBBBBBBBB,
                            "alignment": ui.Alignment.LEFT,
                        }

                        kwargs = {
                            "label": "Update Weights ",
                            "type": "button",
                            "text": "Update",
                            "tooltip": "Update the waypoint graph weights",
                            "on_clicked_fn": self._update_weights,
                        }
                        btn_builder(**kwargs)

                        kwargs = {
                            "label": "Run cuOpt ",
                            "type": "button",
                            "text": "Solve",
                            "tooltip": "Run the cuOpt solver based on current data",
                            "on_clicked_fn": self._run_cuopt,
                        }
                        btn_builder(**kwargs)
                        self._routes_ui_message = ui.Label(
                            "Run cuOpt for solution",
                            width=350,
                            word_wrap=True,
                            style=ui_data_style,
                        )

    def _on_stage_event(self, event: Any) -> Any:
        """Clear generated semantic-zone tracking after the watched stage closes.

        Args:
            event: Stage event payload from the event dispatcher.

        Returns:
            None.

        Note: With Events 2.0, this is called only for CLOSED events.
        """
        self._semantics = []

    def _form_cuopt_url(self) -> Any:
        cuopt_ip = self._cuopt_ip.get_value_as_string()
        cuopt_port = self._cuopt_port.get_value_as_string()
        cuopt_url = f"http://{cuopt_ip}:{cuopt_port}/cuopt/"
        return cuopt_url

    # Test if cuopt microservice is up and running
    def _test_cuopt_connection_microservice(self) -> Any:

        cuopt_ip = self._cuopt_ip.get_value_as_string()
        cuopt_port = self._cuopt_port.get_value_as_string()

        if (cuopt_ip == self._cuopt_ip_prompt) or (cuopt_port == self._cuopt_port_prompt):
            self._cuopt_status_info.text = "FAILURE: Please set both an IP and Port"
            return
        self.client = None
        self._cuopt_status_info.text = test_connection_microservice(cuopt_ip, cuopt_port)

    # Test if cuopt managed service is up and running
    def _test_cuopt_connection_managed_service(self) -> Any:

        cuopt_sak = self._cuopt_sak.get_value_as_string()
        function_name = self._function_name.get_value_as_string()
        function_id = self._function_id.get_value_as_string()

        if cuopt_sak == self._cuopt_sak_prompt:
            self._cuopt_status_info.text = "FAILURE: Please set SAK"
            return

        self._cuopt_status_info.text, self.client = test_connection_managed_service(
            cuopt_sak, function_name, function_id
        )

    def _build_warehouse_environment(self) -> Any:
        print("building environment")

        building_json_path = f"{self._extension_data_path}{self.warehouse_building_config}"
        shelves_json_path = f"{self._extension_data_path}{self.warehouse_shelves_config}"
        conveyors_json_path = f"{self._extension_data_path}{self.warehouse_conveyors_config}"

        self._stage = self._usd_context.get_stage()

        building_prim_path = "/World/Warehouse/Building"
        check_build_base_path(self._stage, building_prim_path, final_xform=True)

        generate_building_structure(
            self._stage,
            building_prim_path,
            building_json_path,
            self._base_isaac_asset_path,
        )

        shelves_prim_path = "/World/Warehouse/Assets/Shelves"
        check_build_base_path(self._stage, shelves_prim_path, final_xform=True)

        generate_shelves_assets(
            self._stage,
            shelves_prim_path,
            shelves_json_path,
            self._base_nvidia_asset_path,
        )

        conveyor_prim_path = "/World/Warehouse/Assets/Conveyors"
        check_build_base_path(self._stage, conveyor_prim_path, final_xform=True)

        generate_conveyor_assets(
            self._stage,
            conveyor_prim_path,
            conveyors_json_path,
            self._nvidia_digital_twin_path,
        )

        # Add outdoor lighting via hdr
        sky_light_stage_path = "/World/ExteriorHDR"

        hdr_path = self._base_nvidia_asset_path + "Skies/Clear/noon_grass_4k.hdr"

        omni.kit.commands.execute(
            "CreatePrim",
            prim_path=sky_light_stage_path,
            prim_type="DomeLight",
            select_new_prim=False,
            attributes={
                UsdLux.Tokens.inputsIntensity: 1000,
                UsdLux.Tokens.inputsSpecular: 1,
                UsdLux.Tokens.inputsTextureFile: hdr_path,
                UsdLux.Tokens.inputsTextureFormat: UsdLux.Tokens.latlong,
                UsdGeom.Tokens.visibility: "inherited",
            },
            create_default_xform=True,
        )
        self._warehouse_ui_data.text = f"Warehouse loaded"

        ViewportManager.set_camera_view("/OmniverseKit_Persp", eye=[2.0, 7.0, 8.0], target=[26.0, 60.0, 0.0])

    def _load_waypoint_graph(self) -> Any:
        print("loading waypoint graph")
        self._stage = self._usd_context.get_stage()
        waypoint_graph_data_path = f"{self._extension_data_path}{self.waypoint_graph_config}"
        self._waypoint_graph_model = load_waypoint_graph_from_file(self._stage, waypoint_graph_data_path)
        visualize_waypoint_graph(
            self._stage,
            self._waypoint_graph_model,
            self.waypoint_graph_node_path,
            self.waypoint_graph_edge_path,
        )
        self._network_ui_data.text = f"Waypoint Graph Network Loaded: {len(self._waypoint_graph_model.nodes)} nodes, {len(self._waypoint_graph_model.edges)} edges"

    def _load_orders(self) -> Any:
        print("Loading Orders")
        orders_path = f"{self._extension_data_path}{self.orders_config}"
        self._orders_obj.load_sample(orders_path)
        visualize_order_locations(self._stage, self._waypoint_graph_model, self._orders_obj)
        self._orders_ui_data.text = (
            f"Orders Loaded: {len(self._orders_obj.graph_locations)} tasks at nodes {self._orders_obj.graph_locations}"
        )

    def _load_vehicles(self) -> Any:
        print("Loading Vehicles")
        vehicle_data_path = f"{self._extension_data_path}{self.vehicles_config}"
        self._vehicles_obj.load_sample(vehicle_data_path)
        start_locs = [locs[0] for locs in self._vehicles_obj.graph_locations]
        self._vehicle_ui_data.text = (
            f"Vehicles Loaded: {len(self._vehicles_obj.graph_locations)} vehicles at nodes {start_locs}"
        )

    def _load_semantic_zone(self) -> Any:
        length = self._semantic["length"].get_value_as_float()
        width = self._semantic["width"].get_value_as_float()
        semantic_prim_path = "/World/Warehouse/Semantics"
        check_build_base_path(self._stage, semantic_prim_path, final_xform=True)

        self._semantics = generate_semantic_zones(self._stage, semantic_prim_path, self._semantics, length, width)
        self._semantic_ui_data.text = f"Semantic Zones loaded"

    # Update the network edge weights based on semantics
    def _update_weights(self) -> Any:
        print("updating weights")
        self._stage = self._usd_context.get_stage()
        update_weights(self._stage, self._waypoint_graph_model, self._semantics)

    def _run_cuopt(self) -> Any:
        print("Running cuOpt")

        self._stage = self._usd_context.get_stage()

        # Solver Settings
        solver_config = {
            "time_limit": 0.01,
        }

        # Preprocess network, fleet and task data
        waypoint_graph_data, fleet_data, task_data = preprocess_cuopt_data(
            self._waypoint_graph_model, self._orders_obj, self._vehicles_obj
        )

        # Initialize server data and call for solve
        environment_data = {
            "cost_waypoint_graph_data": waypoint_graph_data,
            "fleet_data": fleet_data,
            "task_data": task_data,
            "solver_config": solver_config,
        }

        if self.client is None:
            cuopt_url = self._form_cuopt_url()
            cuopt_server = cuOptRunner(cuopt_url)

            cuopt_solution = cuopt_server.get_routes(environment_data)
            routes = cuopt_solution

        else:
            res = self.client.get_optimized_routes(environment_data)
            routes = res["response"]["solver_response"]

        # Visualize the optimized routes
        self._waypoint_graph_model.visualization.display_routes(
            self._stage,
            self._waypoint_graph_model,
            self.waypoint_graph_edge_path,
            routes,
        )

        # Display the routes on UI
        self._routes_ui_message.text = show_vehicle_routes(routes)

    def on_shutdown(self) -> Any:
        """Remove the cuOpt menu entry, release the UI window, and collect extension objects.

        Returns:
            None.
        """
        remove_menu_items(self._menu_items, "cuOpt")
        self._window = None
        gc.collect()
