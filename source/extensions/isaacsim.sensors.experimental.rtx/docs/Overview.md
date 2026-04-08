# Overview

The isaacsim.sensors.experimental.rtx extension provides experimental Python APIs for RTX-based sensor simulation in Isaac Sim, covering lidar, radar, and acoustic (ultrasonic) sensors. Each sensor type is split into an **authoring** class for USD prim creation and configuration, and a **runtime sensor** class for attaching annotators and retrieving data at simulation time.

## Key Components

### Authoring classes

Authoring classes inherit from `XformPrim` and manage the underlying USD sensor prim. They handle prim creation (or wrapping existing prims), schema application, attribute setting, and transform operations.

- {class}`Lidar <isaacsim.sensors.experimental.rtx.Lidar>` — Creates or wraps `OmniLidar` prims using `omni.replicator.core.functional.create.omni_lidar`. Supports creating from known configurations via {data}`SUPPORTED_LIDAR_CONFIGS <isaacsim.sensors.experimental.rtx.SUPPORTED_LIDAR_CONFIGS>`.
- {class}`Radar <isaacsim.sensors.experimental.rtx.Radar>` — Creates or wraps `OmniRadar` prims using `omni.replicator.core.functional.create.omni_radar`. Requires Motion BVH to be enabled (`/renderer/raytracingMotion/enabled`).
- {class}`Acoustic <isaacsim.sensors.experimental.rtx.Acoustic>` — Creates or wraps `OmniAcoustic` prims directly. Automatically applies multi-instance schemas (`OmniSensorWpmAcousticSensorMountAPI`, `OmniSensorWpmAcousticRxGroupAPI`) when attributes with matching prefixes are provided.

All authoring classes accept a `tick_rate` parameter (default `0` for autotrigger) that sets `omni:sensor:tickRate` on the prim.

### Runtime sensor classes

Runtime sensor classes wrap an authoring object, create a Replicator render product, and manage annotator attachment and data retrieval. Supported annotator names include `generic-model-output` and `stable-id-map`.

- {class}`LidarSensor <isaacsim.sensors.experimental.rtx.LidarSensor>` — Wraps a `Lidar` object (or creates one from a path).
- {class}`RadarSensor <isaacsim.sensors.experimental.rtx.RadarSensor>` — Wraps a `Radar` object (or creates one from a path).
- {class}`AcousticSensor <isaacsim.sensors.experimental.rtx.AcousticSensor>` — Wraps an `Acoustic` object (or creates one from a path).

### Lidar configuration registry

**Supported USD lidar assets and variants.** The package exports {data}`SUPPORTED_LIDAR_CONFIGS <isaacsim.sensors.experimental.rtx.SUPPORTED_LIDAR_CONFIGS>` (paths to known Isaac Sim lidar assets mapped to optional variant names) and {data}`SUPPORTED_LIDAR_VARIANT_SET_NAME <isaacsim.sensors.experimental.rtx.SUPPORTED_LIDAR_VARIANT_SET_NAME>` (expected variant set name on those prims).

### Parser utilities

- {func}`parse_generic_model_output_data <isaacsim.sensors.experimental.rtx.parse_generic_model_output_data>` — Decodes `generic-model-output` annotator data into a `GenericModelOutput` structure provided by the bundled `isaacsim.sensors.experimental.rtx.generic_model_output` module.
- {func}`parse_stable_id_map_data <isaacsim.sensors.experimental.rtx.parse_stable_id_map_data>` — Decodes `stable-id-map` data into a mapping from stable object IDs to prim paths.

### Auxiliary modules

The extension ships {mod}`isaacsim.sensors.experimental.rtx.generic_model_output` and {mod}`isaacsim.sensors.experimental.rtx.sensor_checker` alongside the main package. The former defines the binary layout used by `parse_generic_model_output_data`; the latter provides helpers such as `SensorCheckerUtil` and `ModelInfo` for working with supported sensor assets (see extension tests for typical usage).

### Settings

**Kit settings contributed by this extension.** Defaults and inline comments live in `config/extension.toml` under `[settings]`. The keys cover GPU-resident lidar and radar return buffers (`app.sensors.nv.lidar.outputBufferOnGPU`, `app.sensors.nv.radar.outputBufferOnGPU`), optional non-visual material semantics from USD (`rtx.materialDb.nonVisualMaterialCSV.enabled`, `rtx.materialDb.nonVisualMaterialSemantics.prefix`), and Hydra timeline use for RTX sensor models (`rtx.rtxsensor.useHydraTimeAlways`).

## Code examples

### Lidar

```python
from isaacsim.sensors.experimental.rtx import Lidar, LidarSensor, parse_generic_model_output_data
import isaacsim.core.experimental.utils.app as app_utils

# authoring: create a lidar prim from a known config
lidar = Lidar.create(path="/World/lidar", config="OS1", variant="OS1_REV6_32ch20hz512res")

# runtime: attach annotators and retrieve data
sensor = LidarSensor(lidar, annotators=["generic-model-output"])
app_utils.play(commit=True)

data, _ = sensor.get_data("generic-model-output")
gmo = parse_generic_model_output_data(data)
```

### Radar

```python
from isaacsim.sensors.experimental.rtx import Radar, RadarSensor

radar = Radar("/World/radar", tick_rate=20.0)
sensor = RadarSensor(radar, annotators=["generic-model-output"])
```

### Acoustic

```python
from isaacsim.sensors.experimental.rtx import Acoustic, AcousticSensor

acoustic = Acoustic(
    "/World/acoustic",
    tick_rate=30.0,
    attributes={
        "omni:sensor:WpmAcoustic:centerFrequency": 51200.0,
        "omni:sensor:WpmAcoustic:sensorMount:m001:position": (0.0, 0.0, 0.0),
    },
)
sensor = AcousticSensor(acoustic, annotators=["generic-model-output"])
```

## Integration

Dependencies include **isaacsim.core.experimental.prims** (transform and prim utilities), **omni.replicator.core** (annotators and writers), **omni.sensors.nv.lidar**, **omni.sensors.nv.radar**, **omni.sensors.nv.acoustic**, **omni.sensors.nv.common**, **omni.sensors.nv.ids**, **omni.usd.schema.omni_sensors**, and **isaacsim.storage.native** for asset paths. Enable the extension from **Window > Extensions** and turn on `isaacsim.sensors.experimental.rtx`.
