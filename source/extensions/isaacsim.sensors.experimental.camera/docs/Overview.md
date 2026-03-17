```{csv-table}
**Extension**: {{ extension_version }},**Documentation Generated**: {sub-ref}`today`
```

# Overview

The isaacsim.sensors.experimental.camera extension provides high-level APIs for creating and operating camera sensors in Isaac Sim. This extension simplifies camera sensor setup and data collection by wrapping underlying rendering and annotation systems into user-friendly sensor classes that can capture various types of visual data including RGB images, depth maps, motion vectors, and other annotated sensor outputs.

## Key Components

### {class}`CameraSensor <isaacsim.sensors.experimental.camera.CameraSensor>`

The {class}`CameraSensor <isaacsim.sensors.experimental.camera.CameraSensor>` class provides a high-level interface for operating single camera sensors. It accepts a camera path or Camera object, configures the specified resolution and annotators, and provides methods to capture sensor data.

```python
from isaacsim.sensors.experimental.camera import CameraSensor

camera_sensor = CameraSensor(
    "/World/camera",
    resolution=(512, 512),
    annotators=["rgb", "distance_to_image_plane"],
)

# Capture RGB data
data, info = camera_sensor.get_data("rgb")
```

The sensor supports dynamic annotator management through `attach_annotators()` and `detach_annotators()` methods, allowing you to modify which data types are captured without recreating the sensor.

### {class}`TiledCameraSensor <isaacsim.sensors.experimental.camera.TiledCameraSensor>`

The {class}`TiledCameraSensor <isaacsim.sensors.experimental.camera.TiledCameraSensor>` enables efficient batch processing of multiple cameras by rendering them as a single tiled output. This is particularly useful for multi-camera setups or when processing large numbers of camera views simultaneously.

```python
from isaacsim.sensors.experimental.camera import TiledCameraSensor

# Create sensor for multiple cameras using regex pattern
tiled_sensor = TiledCameraSensor(
    "/World/camera_.*",
    resolution=(240, 320),
    annotators=["rgb", "normals"],
)

# Get data as individual frames or single tiled frame
batch_data, info = tiled_sensor.get_data("rgb", tiled=False)  # Shape: (N, height, width, channels)
tiled_data, info = tiled_sensor.get_data("rgb", tiled=True)   # Single combined image
```

### {class}`SingleViewDepthCameraSensor <isaacsim.sensors.experimental.camera.SingleViewDepthCameraSensor>`

The {class}`SingleViewDepthCameraSensor <isaacsim.sensors.experimental.camera.SingleViewDepthCameraSensor>` simulates depth cameras using a single camera view to compute disparity and depth information. It extends the base {class}`CameraSensor <isaacsim.sensors.experimental.camera.CameraSensor>` with specialized depth sensing parameters and post-processing controls.

```python
from isaacsim.sensors.experimental.camera import SingleViewDepthCameraSensor

depth_sensor = SingleViewDepthCameraSensor(
    "/World/depth_camera",
    resolution=(480, 640),
    annotators="depth_sensor_distance",
)

# Configure depth sensing parameters
depth_sensor.set_sensor_baseline(50.0)  # millimeters
depth_sensor.set_sensor_maximum_disparity(120.0)
depth_sensor.set_sensor_distance_cutoffs(minimum_distance=0.1, maximum_distance=1000.0)
```

The depth sensor provides extensive configuration options including baseline distance, disparity parameters, noise simulation, and debug visualization modes.

## Functionality

### Annotator System

All sensor classes support a flexible annotator system that determines what types of data are captured. Common annotators include RGB images, depth maps, surface normals, motion vectors, and point clouds. Annotators can be specified during sensor creation or attached/detached dynamically.

### Data Visualization

The {func}`draw_annotator_data_to_image <isaacsim.sensors.experimental.camera.draw_annotator_data_to_image>` function provides visualization capabilities for annotator data, particularly useful for debugging and analysis:

```python
from isaacsim.sensors.experimental.camera import draw_annotator_data_to_image

# Draw motion vectors on RGB background
frame, _ = camera_sensor.get_data("rgb")
motion_data, motion_info = camera_sensor.get_data("motion_vectors")

visualization = draw_annotator_data_to_image(
    annotator="motion_vectors",
    data=motion_data,
    info=motion_info,
    frame=frame,
)
```

### Memory Management

All sensor classes support pre-allocated output arrays through the `out` parameter in `get_data()` methods, enabling efficient memory usage in performance-critical applications.

## Integration

The extension integrates with isaacsim.core.experimental.objects for camera object management and **omni.replicator.core** for underlying rendering and annotation capabilities. This integration provides access to USD-based camera prims while abstracting the complexity of render product configuration and annotator setup.
