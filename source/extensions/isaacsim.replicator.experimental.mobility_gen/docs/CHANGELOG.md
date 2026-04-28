# Changelog

## [0.2.1] - 2026-04-27
### Fixed
- Kit test runner failures: converted test classes from `unittest.TestCase` to `omni.kit.test.AsyncTestCase` so tests are awaitable
- `test_migrate_recording.py`: fixed `FileNotFoundError` by walking upward to locate `standalone_examples/` rather than using a hardcoded `parents[4]` offset that diverges between source and build layouts
- Suppressed expected `parse_sensor_entries` log errors in `stdoutFailPatterns.exclude` so intentional invalid-input tests don't trip the runner

## [0.2.0] - 2026-04-22
### Added
- `MobilityGenMultiSensorRobot` and `MobilityGenSensorRig` for YAML-driven multi-sensor robots; camera rendering is supported, other sensor types (lidar, IMU, radar) are discovered but not yet rendered
- `sensor_overrides.py` module with `save_sensor_overrides`, `apply_sensor_overrides`, and `log_camera_properties`
- Camera calibration overrides (intrinsics, distortion, extrinsics) made in the UI are persisted to `sensor_overrides.usda` at recording time and re-applied during replay
- `generate_sensor_rigs.py` script to discover sensor prims in a robot USD and scaffold `sensor_rig:` YAML blocks
- Added Overview, sensor_rig, module, and adding_a_robot documentation
### Changed
- `state/common/` steps now saved as `.npz` (named arrays) instead of `.npy` (pickled dict); use `migrate_recordings.py` to convert older recordings

## [0.1.1] - 2026-04-18
### Changed
- Added return type annotations, `from __future__ import annotations`, and imperative-mood docstrings

## [0.1.0] - 2026-02-25
### Added
- Initial version of MobilityGen extension migrated to use `isaacsim.core.experimental` API
- Replace `isaacsim.core.prims` with `isaacsim.core.experimental.prims` (`XformPrim`, `Articulation`)
- Replace `isaacsim.core.utils` stage/prim helpers with `isaacsim.core.experimental.utils` equivalents
