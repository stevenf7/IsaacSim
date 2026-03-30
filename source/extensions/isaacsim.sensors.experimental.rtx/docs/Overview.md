# Overview

The isaacsim.sensors.experimental.rtx extension provides experimental Python APIs for RTX-based lidar simulation in Isaac Sim. It wraps OmniLidar prims and Replicator annotators so workflows can configure a sensor, run simulation, and retrieve structured range returns and stable-ID semantics. The extension metadata also covers related RTX sensor stack pieces (for example shared NV lidar and radar renderer options); the primary documented Python surface today is RTX lidar.

## Key Components

### {class}`RtxLidarSensor <isaacsim.sensors.experimental.rtx.RtxLidarSensor>`

**High-level OmniLidar wrapper.** The class resolves or creates a single `OmniLidar` prim, attaches selected annotators, and exposes `get_data()` after the timeline advances. Supported annotator names include `generic-model-output` and `stable-id-map`.

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

```python
from isaacsim.sensors.experimental.rtx import RtxLidarSensor, parse_generic_model_output_data
import isaacsim.core.experimental.utils.app as app_utils

sensor = RtxLidarSensor(
    "/World/lidar",
    annotators=["generic-model-output"],
)
app_utils.play(commit=True)

data, _ = sensor.get_data("generic-model-output")
gmo = parse_generic_model_output_data(data)
```

## Integration

Dependencies include **isaacsim.core.experimental.prims** (transform and prim utilities), **omni.replicator.core** (annotators and writers), **omni.sensors.nv.lidar**, **omni.sensors.nv.radar**, **omni.sensors.nv.common**, **omni.sensors.nv.ids**, **omni.usd.schema.omni_sensors**, and **isaacsim.storage.native** for asset paths. Enable the extension from **Window > Extensions** and turn on `isaacsim.sensors.experimental.rtx`. Annotator names and buffer layouts are summarized in `docs/usage.rst` for published docs builds.
