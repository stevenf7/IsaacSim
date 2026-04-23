# Changelog

## [1.1.0] - 2026-04-23
### Added
- `RtxCamera` authoring class for creating/wrapping USD Camera prims with OmniSensorAPI schema
- `CameraSensor` runtime class for single-camera annotator data retrieval with resolution-aware render products
- `TiledCameraSensor` runtime class for batched multi-camera rendering with shared annotators
- `SingleViewDepthCameraSensor` runtime class extending `CameraSensor` with stereoscopic depth post-processing
- `draw_annotator_data_to_image` utility for converting annotator output to images
- Camera-specific annotator spec registry (`_camera_common.py`)
- `register_annotator_spec`, `unregister_annotator_spec`, `register_writer_spec`, `unregister_writer_spec` for companion extension integration
- `aux_output_level` parameter to `Radar.create()` and `Acoustic.create()` (matching `Lidar.create()`)
- `aux_output_level` to `Radar` and `Acoustic` class docstrings

## [1.0.1] - 2026-04-22
### Fixed
- Mark extension as platform-specific (`writeTarget.platform = true`) so the registry publishes a separate artifact per platform. Without this, consumers on Linux would pull a Windows-built package containing `.pyd` instead of `.so` from `generic-model-output`/`sensor-checker` (or vice versa) and fail to load.

## [1.0.0] - 2026-04-06
### Added
- `Radar` authoring class for creating/wrapping OmniRadar prims via `omni.replicator.core.functional.create.omni_radar`
- `Acoustic` authoring class for creating/wrapping OmniAcoustic prims with auto-applied multi-instance schemas (sensorMount, rxGroup)
- `RadarSensor` runtime class for radar annotator data retrieval
- `AcousticSensor` runtime class for acoustic annotator data retrieval
- `tick_rate` parameter on all authoring constructors (`Lidar`, `Radar`, `Acoustic`) for setting `omni:sensor:tickRate`
- `omni.sensors.nv.acoustic` extension dependency

### Changed
- Split `LidarSensor` into separate `Lidar` (authoring) and `LidarSensor` (runtime) classes
- `Lidar` authoring class now uses `omni.replicator.core.functional.create.omni_lidar` for prim creation
- Renamed `RtxLidarSensor` to `LidarSensor`
- Extracted `_SensorAuthoring` and `_SensorRuntime` base classes to reduce code duplication
- `omni:sensor:tickRate` in attributes dict overrides the `tick_rate` parameter (with warning)

### Fixed
- `parse_generic_model_output_data` returning the `GenericModelOutput` class instead of an instance in fallback paths

## [0.1.0] - 2026-03-17
### Added
- Initial release
