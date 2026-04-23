# Public API for module isaacsim.sensors.experimental.physics:

## Classes

- class IsaacSensorExperimentalCreatePrim(omni.kit.commands.Command)
  - def __init__(self, path: str = '', parent: str = '', translation: Gf.Vec3d = Gf.Vec3d(0, 0, 0), orientation: Gf.Quatd = Gf.Quatd(1, 0, 0, 0), schema_type: type = IsaacSensorSchema.IsaacBaseSensor)
  - def do(self) -> object | None
  - def undo(self)

- class IsaacSensorExperimentalCreateContactSensor(omni.kit.commands.Command)
  - def __init__(self, path: str = '/Contact_Sensor', parent: str | None = None, min_threshold: float = 0, max_threshold: float = 100000, color: Gf.Vec4f = Gf.Vec4f(1, 1, 1, 1), radius: float = -1, translation: Gf.Vec3d = Gf.Vec3d(0, 0, 0))
  - def do(self) -> object | None
  - def undo(self)

- class IsaacSensorExperimentalCreateImuSensor(omni.kit.commands.Command)
  - def __init__(self, path: str = '/Imu_Sensor', parent: str | None = None, translation: Gf.Vec3d = Gf.Vec3d(0, 0, 0), orientation: Gf.Quatd = Gf.Quatd(1, 0, 0, 0), linear_acceleration_filter_size: int = 1, angular_velocity_filter_size: int = 1, orientation_filter_size: int = 1)
  - def do(self) -> object | None
  - def undo(self)

- class IsaacSensorExperimentalCreateRaycastSensor(omni.kit.commands.Command)
  - def __init__(self, path: str = '/Raycast_Sensor', parent: str | None = None, min_range: float = 0.4, max_range: float = 100.0, ray_origins: list | np.ndarray | None = None, ray_directions: list | np.ndarray | None = None, ray_time_offsets: list | np.ndarray | None = None, output_frame: str = 'SENSOR', report_hit_prim_paths: bool = False, translation: Gf.Vec3d = Gf.Vec3d(0, 0, 0), orientation: Gf.Quatd = Gf.Quatd(1, 0, 0, 0))
  - def do(self) -> object | None
  - def undo(self)

- class ContactSensorReading
  - value: float
  - time: float
  - is_valid: bool
  - [property] def in_contact(self) -> bool
  - [in_contact.setter] def in_contact(self, value: bool)

- class IMURawData
  - time: float
  - dt: float
  - linear_velocity_x: float
  - linear_velocity_y: float
  - linear_velocity_z: float
  - angular_velocity_x: float
  - angular_velocity_y: float
  - angular_velocity_z: float
  - orientation_w: float
  - orientation_x: float
  - orientation_y: float
  - orientation_z: float

- class IMUSensorReading
  - linear_acceleration_x: float
  - linear_acceleration_y: float
  - linear_acceleration_z: float
  - angular_velocity_x: float
  - angular_velocity_y: float
  - angular_velocity_z: float
  - orientation: Quaternion
  - time: float
  - is_valid: bool

- class ContactSensor(XformPrim)
  - def __init__(self, prim_path: str, name: str | None = 'contact_sensor', translation: np.ndarray | None = None, position: np.ndarray | None = None, min_threshold: float | None = None, max_threshold: float | None = None, radius: float | None = None)
  - [property] def prim_path(self) -> str
  - def initialize(self, physics_sim_view: Any = None)
  - def get_current_frame(self) -> dict
  - def add_raw_contact_data_to_frame(self)
  - def remove_raw_contact_data_from_frame(self)
  - def get_radius(self) -> float
  - def set_radius(self, value: float)
  - def get_min_threshold(self) -> float | None
  - def set_min_threshold(self, value: float)
  - def get_max_threshold(self) -> float | None
  - def set_max_threshold(self, value: float)

- class ContactSensorBackend(_PhysicsSensorBase)
  - def __init__(self, prim_path: str)
  - def on_physics_step(self, step_dt: float)
  - def on_timeline_stop(self)
  - def get_sensor_reading(self) -> ContactSensorReading
  - def get_raw_data(self) -> list[dict[str, object]]
  - [property] def parent_token(self) -> int | None

- class EffortSensor
  - def __init__(self, prim_path: str, enabled: bool = True)
  - def get_sensor_reading(self) -> EffortSensorReading
  - def update_dof_name(self, dof_name: str)
  - def change_buffer_size(self, new_buffer_size: int)

- class EffortSensorReading
  - def __init__(self, is_valid: bool = False, time: float = 0, value: float = 0)

- class EffortSensorBackend
  - def __init__(self, joint_prim_path: str)
  - def get_sensor_reading(self) -> object
  - def on_timeline_stop(self)
  - def reset(self)

- class Extension(omni.ext.IExt)
  - def on_startup(self, ext_id: str)
  - def on_shutdown(self)

- class IMUSensor(XformPrim)
  - def __init__(self, prim_path: str, name: str | None = 'imu_sensor', translation: np.ndarray | None = None, position: np.ndarray | None = None, orientation: np.ndarray | None = None, linear_acceleration_filter_size: int | None = 1, angular_velocity_filter_size: int | None = 1, orientation_filter_size: int | None = 1)
  - [property] def prim_path(self) -> str
  - def initialize(self, physics_sim_view: Any = None)
  - def get_current_frame(self, read_gravity: bool = True) -> dict

- class ImuSensorBackend(_PhysicsSensorBase)
  - def __init__(self, prim_path: str)
  - def get_sensor_reading(self, read_gravity: bool = True) -> object
  - def on_physics_step(self, step_dt: float)
  - def on_timeline_stop(self)
  - def reset(self)

- class JointStateSensor
  - def __init__(self, prim_path: str, enabled: bool = True)
  - def get_sensor_reading(self) -> JointStateSensorReading

- class JointStateSensorReading
  - def __init__(self, is_valid: bool = False, time: float = 0.0, dof_names: list[str] | None = None, positions: np.ndarray | None = None, velocities: np.ndarray | None = None, efforts: np.ndarray | None = None, dof_types: np.ndarray | None = None, stage_meters_per_unit: float = 0.0)

- class JointStateSensorBackend
  - def __init__(self, articulation_prim_path: str)
  - def get_sensor_reading(self) -> object
  - def on_timeline_stop(self)
  - def reset(self)

- class RaycastSensor(XformPrim)
  - def __init__(self, prim_path: str, name: str | None = 'raycast_sensor', translation: np.ndarray | None = None, position: np.ndarray | None = None, orientation: np.ndarray | None = None, min_range: float | None = None, max_range: float | None = None, ray_origins: np.ndarray | list | None = None, ray_directions: np.ndarray | list | None = None, ray_time_offsets: np.ndarray | list | None = None, output_frame: str | None = None, report_hit_prim_paths: bool | None = None)
  - [property] def prim_path(self) -> str
  - def initialize(self, physics_sim_view: Any = None)
  - def get_current_frame(self) -> dict
  - def get_sensor_reading(self) -> object

- class RaycastSensorBackend(_PhysicsSensorBase)
  - def __init__(self, prim_path: str)
  - def get_sensor_reading(self) -> object
  - def on_physics_step(self, step_dt: float)
  - def on_timeline_stop(self)
  - def reset(self)

## Functions

- def get_imu_sensor_interface() -> object | None
- def get_contact_sensor_interface() -> object | None
- def get_effort_sensor_interface() -> object | None
- def get_joint_state_sensor_interface() -> object | None
- def get_raycast_sensor_interface() -> object | None
