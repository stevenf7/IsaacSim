# Changelog

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
