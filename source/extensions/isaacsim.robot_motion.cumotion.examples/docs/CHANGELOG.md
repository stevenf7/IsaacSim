# Changelog

## [0.3.1] - 2026-04-14
### Fixed
- `graph_planner` and `trajectory_optimizer` example tests no longer hang: removed `timeline.play()` / frame-wait / `timeline.stop()` from `_load_scene_async`, which could block the Kit update thread (e.g. on CUDA initialisation failures) and prevent `next_update_async()` from ever resolving.
- `test_cspace_button_passes_slider_joint_values` is now significantly faster in both examples: robot config (`load_cumotion_supported_robot`) and slider setup are performed before the nucleus USD load, so the test predicate resolves without waiting for the network round-trip. Task-space tests retain the full wait via a new `_load_until_articulation_ready` helper.
- Reduced `wait_until` poll interval from 250 ms to 50 ms, cutting idle delay after a predicate becomes true.

## [0.3.0] - 2026-03-18
### Added
- Unittests for button presses, slider values, stateful behavior of all GUI components.
### Changed
- All functions for loading assets are async.
### Fixed
- We no longer force physics or rendering dt, which threw an uncapture `RuntimeError` because timeline could be playing.

## [0.2.1] - 2026-03-18
### Changed
- TrajectoryOptimizer example functional on Windows.

## [0.2.0] - 2026-03-05
### Changed
- Added Overview.md, python_api.md and updated docstrings

## [0.1.1] - 2026-03-02
### Changed
- Uses improved QOL motion generation APIs

## [0.1.0] - 2026-02-22
### Added
- Initial release
