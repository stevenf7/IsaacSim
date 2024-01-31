# Changelog


## [1.3.0] - 2024-01-30
### Added
- IsaacStartupTimeRecorder measures startup time, collected only during "startup" phase

## [1.2.0] - 2024-01-25
### Added
- OsmoKPIFile writer logs KPIs to console.

## [1.1.0] - 2024-01-19
### Added
- Adds new BaseIsaacBenchmark for non-async benchmarking
- Adds new standalone examples for non-async benchmarking
- Adds OsmoKPIFile writer to publish KPIs compatible with OSMO's Kratos backend

### Fixed
- Async benchmark stability on new stage open
- ROS2 bridge camera helper

### Changed
- Move BaseIsaacBenchmark -> BaseIsaacBenchmarkAsync, for (eg) async unit tests

## [1.0.0] - 2024-01-04
### Changed
- Remove depdencies and added classes needed to make benchmarks work independently
- Helpers specific to certain benchmarks were moved to benchmarks extension

## [0.2.0] - 2023-12-14
### Added
- Added ROS2 camera graph helper

## [0.1.1] - 2023-11-30
### Changed
- Use get_assets_root_path_async()

## [0.1.0] - 2023-11-14
### Changed
- Moved utils from omni.isaac.benchmark into omni.isaac.benchmark.services

### Added
- Quasi-initial version
