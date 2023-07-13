# Changelog

## [0.16.1] - 2023-07-13

### Changed
- Cleaned up benchmark code - unused imports, formatting, etc.

## [0.16.0] - 2023-07-03

### Added
- Test mode for TeamCity, which runs each benchmark for 1 frame instead of 600 frames, just to check if there are no bugs. To enable test mode, set environment variable ISAAC_TEST_MODE to 1.

## [0.15.0] - 2023-07-06

### Changed
- use sync stage load function to get better behavior
- reuse viewport rp for first camera. 

## [0.14.0] - 2023-07-04

### Added
- added sync load parameters to setUp in base isaac benchmark class

### Changed
- Update ROS camera test to use render products
- Start ROSCore when running benchmarks

## [0.13.2] - 2023-07-04

### Added
- runtime and frametime recorder to sdg benchmark phase

## [0.13.1] - 2023-07-03

### Added
- moved wait_until_stage_is_fully_loaded_async to helper.py

### Fixed
- unrolled scene generation benchmark loops
- sdg using step_async loop + wait_until_complete_async to make sure data is written to disk in the benchmark phase 

## [0.13.0] - 2023-06-30

### Added
- Real Time Factor (RTF) measurement to frametime recorder and benchmark specificially for RTF, used to compare time in simulator vs real time

## [0.12.0] - 2023-06-29

### Added
- ROS 1 camera benchmarks only appear when running Isaac Sim on Linux

## [0.11.0] - 2023-06-29

### Added
- Runtime metric for benchmarks, used to measure total load time in place of framerate data

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
