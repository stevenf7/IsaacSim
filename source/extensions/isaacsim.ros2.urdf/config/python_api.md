# Public API for module isaacsim.ros2.urdf:

## Classes

- class RobotDefinitionReader
  - def __init__(self)
  - def on_description_received(self, _: str)
  - def service_call(self, node: typing.Any)
  - def start_get_robot_description(self, node_name: str)

- class URDFImportFromROS2Node(omni.kit.commands.Command)
  - def __init__(self, ros2_node_name: str = 'robot_state_publisher', import_config: URDFImporterConfig = URDFImporterConfig(), dest_path: str = '', get_articulation_root: bool = False)
  - def on_app_update(self, event: typing.Any)
  - def on_description_received(self, urdf_description: str)
  - def import_robot(self, urdf_path: str)
  - def do(self) -> Result

- class RobotDescription
  - def __init__(self)
  - def shutdown(self)
  - def show_window(self)

- class Extension(omni.ext.IExt)
  - def menu_click(self, menu: typing.Any, value: bool)
  - def on_startup(self, ext_id: str)
  - def deregister_actions(self)
  - def on_shutdown(self)

- class Ros2UrdfOptionWidget
  - def __init__(self, models: dict[str, typing.Any], config: URDFImporterConfig, on_node_changed: typing.Callable[[ui.AbstractValueModel], None] | None = None, on_import_clicked: typing.Callable[[], None] | None = None)
  - [property] def models(self) -> dict[str, typing.Any]
  - [property] def config(self) -> URDFImporterConfig
  - def build_options(self)
  - def set_refresh_enabled(self, enabled: bool)
  - def get_ros2_node(self) -> str
  - def set_status(self, text: str, color: int = 4284266588)
  - def set_import_enabled(self, enabled: bool)

## Functions

- def package_path_to_system_path(package_name: str, relative_path: str = '') -> str
- def replace_package_urls_with_paths(input_string: str) -> tuple[str, bool]
- def singleton(class_: type) -> typing.Callable

## Variables

- Singleton: singleton
