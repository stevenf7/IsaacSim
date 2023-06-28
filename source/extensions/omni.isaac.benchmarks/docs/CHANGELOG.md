# Changelog

## [0.10.0] - 2023-06-28

### Added
- Test for 10 robots with camera
- Test 10 robots with lidar and camera

## [0.9.0] - 2023-06-26

### Added
- Test for 100 PhysX Lidar sensors
- Tests for 1-50 robots with no sensor
## [0.8.2] - 2023-06-26

### Fixed
- Removed test loops, benchmark data was not exported because setUp and tearDown were not called for every test

### Changed
- SDG benchmark set default resolution to 720p
- SDG benchmark set writer to None for future replicator changes to cleanup

## [0.8.1] - 2023-06-21

### Fixed
- new (fixed) stage for SDG benchmark

## [0.8.0] - 2023-06-21

### Added
- rtx lidar benchmark

## [0.7.3] - 2023-06-21

### Fixed
- Scene generation crash on pre-existing prim transform attributes

## [0.7.2] - 2023-06-01

### Fixed
- Don't fail on error messages due to missing features on gpu

## [0.7.1] - 2023-05-25

### Changed
- SDG benchmark segment names

## [0.7.0] - 2023-05-18

### Changed
- Use camera class for camera scaling benchmark

### Removed
- PB metric from windows benchmarks

## [0.6.1] - 2023-05-16

### Added
- made SDG benchmark names more descriptive

## [0.6.0] - 2023-05-05

### Added
- phase label to cpu/memory metrics

## [0.5.0] - 2023-04-23

### Added
- Scene generation benchmark
- SDG generation benchmark

## [0.4.1] - 2022-11-17

### Fixed
- missing extensions


## [0.4.0] - 2022-11-16

### Added
- ROS camera benchmark tests
- RTX lidar benchmark tests

### Fixed
- deleting existing sensors/robots/cameras that's already on stage when new rounds of tests start


## [0.3.1] - 2022-10-28

### Changed
- Logging format


## [0.3.0] - 2022-10-24

### Added
- Multi-Robot, multi-robot with lidar, multi-robot with camera tests

## [0.2.0] - 2022-10-24

### Added
- Lidar Benchmark

### Fixed
- Camera Benchmark and logging bugs


## [0.1.0] - 2022-10-05

### Added
- Initial version
