# Public API for module omni.cuopt.examples.create_network:

## Classes

- class NetworkSimpleViz
  - def __init__(self)
  - def add_waypoint_material(self, stage: Any) -> Any
  - def add_node_to_scene(self, stage: Any, node_prim_path: Any, translation: Any) -> Any
  - def add_edge_to_scene(self, stage: Any, edge_prim_path: Any, point_from: Any, point_to: Any) -> Any
  - def get_route_material(self, stage: Any, i: Any) -> Any
  - def display_routes(self, stage: Any, graph: Any, waypoint_graph_edge_path: Any, routes: Any) -> Any

- class cuOptSampleExtension(omni.ext.IExt)
  - def on_startup(self, ext_id: Any) -> Any
  - def create_node(self) -> Any
  - def create_edge(self) -> Any
  - def on_shutdown(self) -> Any

## Functions

- def btn_builder(label: str = '', type: str = 'button', text: str = 'button', tooltip: str = '', on_clicked_fn: object = None) -> ui.Button
- def get_style() -> dict[str, Any]
- def setup_ui_headers(ext_id: str, file_path: str, title: str = 'My Custom Extension', doc_link: str = 'https://docs.isaacsim.omniverse.nvidia.com/latest/index.html', overview: str = '', info_collapsed: bool = True)

## Variables

- EXTENSION_NAME: str

# Public API for module omni.cuopt.examples.costmat:

## Classes

- class cuOptRunner
  - def __init__(self, cuopt_url: str)
  - def get_routes(self, cuopt_problem_data: Any) -> Any

- class cuOptSampleExtension(omni.ext.IExt)
  - def on_startup(self, ext_id: Any) -> Any
  - def clear_locations(self) -> Any
  - def update_location_position(self) -> Any
  - def problem_setup_validation(self, n_vehicles: Any, capacity_val: Any, n_locations: Any, time_limit: Any) -> Any
  - def create_problem_geometry(self) -> Any
  - def distance_matrix_from_point_list(self, point_list: Any, scale: Any) -> Any
  - def get_routes(self, raw_routes: Any) -> Any
  - def run_cuopt(self) -> Any
  - def draw_routes(self, routes: Any) -> Any
  - def on_shutdown(self) -> Any

## Functions

- def btn_builder(label: str = '', type: str = 'button', text: str = 'button', tooltip: str = '', on_clicked_fn: object = None) -> ui.Button
- def float_builder(label: str = '', type: str = 'floatfield', default_val: float = 0, tooltip: str = '', min: float = -inf, max: float = inf, step: float = 0.1, format: str = '%.2f') -> object
- def get_style() -> dict[str, Any]
- def int_builder(label: str = '', type: str = 'intfield', default_val: int = 0, tooltip: str = '', min: int = sys.maxsize * -1, max: int = sys.maxsize) -> ui.AbstractValueModel
- def setup_ui_headers(ext_id: str, file_path: str, title: str = 'My Custom Extension', doc_link: str = 'https://docs.isaacsim.omniverse.nvidia.com/latest/index.html', overview: str = '', info_collapsed: bool = True)
- def str_builder(label: str = '', type: str = 'stringfield', default_val: str = ' ', tooltip: str = '', on_clicked_fn: object = None, use_folder_picker: bool = False, read_only: bool = False, item_filter_fn: object = None, bookmark_label: str | None = None, bookmark_path: str | None = None, folder_dialog_title: str = 'Select Output Folder', folder_button_title: str = 'Select Folder', identifier: str | None = None, label_width: int | None = None) -> ui.AbstractValueModel
- def show_vehicle_routes(routes: Any) -> Any
- def test_connection_managed_service(auth: Any, function_name: Any, function_id: Any)
- def test_connection_microservice(ip: Any, port: Any)

## Variables

- EXTENSION_NAME: str

# Public API for module omni.cuopt.examples.wpgraph:

## Classes

- class cuOptRunner
  - def __init__(self, cuopt_url: str)
  - def get_routes(self, cuopt_problem_data: Any) -> Any

- class TransportOrders
  - def __init__(self)
  - def load_sample(self, orders_json: Any) -> Any

- class TransportVehicles
  - def __init__(self)
  - def load_sample(self, vehicles_json_path: Any) -> Any

- class WaypointGraphModel
  - def __init__(self)

- class cuOptMicroserviceExtension(omni.ext.IExt)
  - def on_startup(self, ext_id: Any) -> Any
  - def on_shutdown(self) -> Any

## Functions

- def btn_builder(label: str = '', type: str = 'button', text: str = 'button', tooltip: str = '', on_clicked_fn: object = None) -> ui.Button
- def get_style() -> dict[str, Any]
- def setup_ui_headers(ext_id: str, file_path: str, title: str = 'My Custom Extension', doc_link: str = 'https://docs.isaacsim.omniverse.nvidia.com/latest/index.html', overview: str = '', info_collapsed: bool = True)
- def str_builder(label: str = '', type: str = 'stringfield', default_val: str = ' ', tooltip: str = '', on_clicked_fn: object = None, use_folder_picker: bool = False, read_only: bool = False, item_filter_fn: object = None, bookmark_label: str | None = None, bookmark_path: str | None = None, folder_dialog_title: str = 'Select Output Folder', folder_button_title: str = 'Select Folder', identifier: str | None = None, label_width: int | None = None) -> ui.AbstractValueModel
- def show_vehicle_routes(routes: Any) -> Any
- def test_connection_managed_service(auth: Any, function_name: Any, function_id: Any)
- def test_connection_microservice(ip: Any, port: Any)
- def preprocess_cuopt_data(graph: Any, task: Any, fleet: Any) -> Any
- def load_waypoint_graph_from_file(stage: Any, waypoint_graph_json: Any) -> Any
- def visualize_order_locations(stage: Any, waypoint_graph_model: Any, transport_orders: Any) -> Any
- def load_waypoint_graph_from_scene(stage: Any, model: Any) -> Any
- def visualize_waypoint_graph(stage: Any, model: Any, waypoint_graph_node_path: Any, waypoint_graph_edge_path: Any) -> Any

## Variables

- EXTENSION_NAME: str

# Public API for module omni.cuopt.examples.warehouse_transport_demo:

## Classes

- class ViewportManager
  - class def wait_for_viewport(cls) -> tuple[bool, int]
  - class async def wait_for_viewport_async(cls) -> tuple[bool, int]
  - class def set_camera(cls, camera: str | Usd.Prim | UsdGeom.Camera)
  - class def get_camera(cls, render_product_or_viewport: str | Usd.Prim | UsdRender.Product | 'ViewportAPI' | None = None) -> UsdGeom.Camera
  - class def get_viewport_api(cls, render_product_or_viewport: str | Usd.Prim | UsdRender.Product | 'ViewportAPI' | None = None) -> 'ViewportAPI' | None
  - class def get_render_product(cls, render_product_or_viewport: str | Usd.Prim | UsdRender.Product | 'ViewportAPI' | None = None) -> UsdRender.Product | None
  - class def get_resolution(cls, render_product_or_viewport: str | Usd.Prim | UsdRender.Product | 'ViewportAPI' | None = None) -> tuple[int, int]
  - class def set_resolution(cls, resolution: tuple[int, int] | str)
  - class def create_viewport_window(cls) -> ViewportWindow
  - class def get_viewport_windows(cls) -> list
  - class def destroy_viewport_windows(cls) -> list[str]
  - class def set_camera_view(cls, camera: str | Usd.Prim | UsdGeom.Camera)

- class cuOptRunner
  - def __init__(self, cuopt_url: str)
  - def get_routes(self, cuopt_problem_data: Any) -> Any

- class TransportOrders
  - def __init__(self)
  - def load_sample(self, orders_json: Any) -> Any

- class TransportVehicles
  - def __init__(self)
  - def load_sample(self, vehicles_json_path: Any) -> Any

- class WaypointGraphModel
  - def __init__(self)

- class cuOptMicroserviceExtension(omni.ext.IExt)
  - def on_startup(self, ext_id: Any) -> Any
  - def on_shutdown(self) -> Any

## Functions

- def btn_builder(label: str = '', type: str = 'button', text: str = 'button', tooltip: str = '', on_clicked_fn: object = None) -> ui.Button
- def get_style() -> dict[str, Any]
- def setup_ui_headers(ext_id: str, file_path: str, title: str = 'My Custom Extension', doc_link: str = 'https://docs.isaacsim.omniverse.nvidia.com/latest/index.html', overview: str = '', info_collapsed: bool = True)
- def str_builder(label: str = '', type: str = 'stringfield', default_val: str = ' ', tooltip: str = '', on_clicked_fn: object = None, use_folder_picker: bool = False, read_only: bool = False, item_filter_fn: object = None, bookmark_label: str | None = None, bookmark_path: str | None = None, folder_dialog_title: str = 'Select Output Folder', folder_button_title: str = 'Select Folder', identifier: str | None = None, label_width: int | None = None) -> ui.AbstractValueModel
- def get_assets_root_path() -> str
- def show_vehicle_routes(routes: Any) -> Any
- def test_connection_managed_service(auth: Any, function_name: Any, function_id: Any)
- def test_connection_microservice(ip: Any, port: Any)
- def preprocess_cuopt_data(graph: Any, task: Any, fleet: Any) -> Any
- def load_waypoint_graph_from_file(stage: Any, waypoint_graph_json: Any) -> Any
- def check_build_base_path(stage: Any, semantic_path: Any, final_xform: Any = True) -> Any
- def visualize_order_locations(stage: Any, waypoint_graph_model: Any, transport_orders: Any) -> Any
- def generate_semantic_zones(stage: Any, semantic_prim_path: Any, semantics: Any, length: Any, width: Any) -> Any
- def generate_conveyor_assets(stage: Any, conveyor_prim_path: Any, conveyor_json_path: Any, conveyor_asset_path: Any) -> Any
- def generate_shelves_assets(stage: Any, shelves_prim_path: Any, shelves_json_path: Any, shelves_asset_path: Any) -> Any
- def generate_building_structure(stage: Any, building_prim_path: Any, building_json_path: Any, building_asset_path: Any) -> Any
- def update_weights(stage: Any, model: Any, semantics: Any) -> Any
- def visualize_waypoint_graph(stage: Any, model: Any, waypoint_graph_node_path: Any, waypoint_graph_edge_path: Any) -> Any

## Variables

- EXTENSION_NAME: str
