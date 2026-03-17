# Public API for module isaacsim.sensors.experimental.camera:

## Classes

- class CameraSensor
  - def __init__(self, path: str | Camera)
  - [property] def annotators(self) -> list[str]
  - [property] def camera(self) -> Camera
  - [property] def resolution(self) -> tuple[int, int]
  - [property] def render_product(self) -> UsdRender.Product
  - def attach_annotators(self, annotators: str | list[str])
  - def detach_annotators(self, annotators: str | list[str])
  - def get_data(self, annotator: str) -> tuple[wp.array | None, dict[str, Any]]

- class SingleViewDepthCameraSensor(CameraSensor)
  - def __init__(self, path: str | Camera)
  - def set_sensor_baseline(self, baseline: float)
  - def get_sensor_baseline(self) -> float
  - def set_sensor_disparity_confidence(self, confidence_threshold: float)
  - def get_sensor_disparity_confidence(self) -> float
  - def set_sensor_maximum_disparity(self, maximum_disparity: float)
  - def get_sensor_maximum_disparity(self) -> float
  - def set_enabled_post_processing(self, enabled: bool)
  - def get_enabled_post_processing(self) -> bool
  - def set_sensor_focal_length(self, focal_length: float)
  - def get_sensor_focal_length(self) -> float
  - def set_sensor_distance_cutoffs(self, minimum_distance: float = None, maximum_distance: float = None)
  - def get_sensor_distance_cutoffs(self) -> tuple[float, float]
  - def set_sensor_disparity_noise_downscale(self, downscale: float)
  - def get_sensor_disparity_noise_downscale(self) -> float
  - def set_sensor_noise_parameters(self, noise_mean: float = None, noise_sigma: float = None)
  - def get_sensor_noise_parameters(self) -> tuple[float, float]
  - def set_enabled_outlier_removal(self, enabled: bool)
  - def get_enabled_outlier_removal(self) -> bool
  - def set_sensor_output_mode(self, mode: int)
  - def get_sensor_output_mode(self) -> int
  - def set_sensor_size(self, size: float)
  - def get_sensor_size(self) -> float

- class TiledCameraSensor
  - def __init__(self, paths: str | list[str] | Camera)
  - [property] def annotators(self) -> list[str]
  - [property] def camera(self) -> Camera
  - [property] def resolution(self) -> tuple[int, int]
  - [property] def tiled_resolution(self) -> tuple[int, int]
  - [property] def render_product(self) -> UsdRender.Product
  - def attach_annotators(self, annotators: str | list[str])
  - def detach_annotators(self, annotators: str | list[str])
  - def get_data(self, annotator: str) -> tuple[wp.array | None, dict[str, Any]]

## Functions

- def draw_annotator_data_to_image() -> np.ndarray
