# Changelog

## [0.2.9] - 2025-01-26
### Changed
- Update test settings

## [0.2.8] - 2025-01-21
### Changed
- Update extension description and add extension specific test settings

## [0.2.7] - 2025-01-14
### Fixed
- Issues when output device did not match the device annotated data was acquired on

## [0.2.6] - 2025-01-06
### Fixed
- use indexed cuda:{idx} input for warp kernels in camera view class
- use indexed cuda device to pre-allocate out buffers

## [0.2.5] - 2024-12-31
### Fixed
- Camera sensor tests no longer needs OMPE-28827 WAR

## [0.2.4] - 2024-12-03
### Changed
- Isaac Util menu to Tools->Robotics menu

## [0.2.4] - 2024-11-26
### Fixed
- camera view sensor test warp.types.int32 -> warp.types.uint32
- decreased image comparison threshold with 0.95->0.94

## [0.2.3] - 2024-11-26
### Fixed
- Camera sensor tests fix for colorize param

## [0.2.2] - 2024-11-18
### Fixed
- Fixed camera sensor custom parameter output test

## [0.2.1] - 2024-11-07
### Added
- Added init_params to camera sensor parameters

## [0.2.0] - 2024-11-01
### Added
- Add a tiled camera method to get tiled and batched data from the different annotators/sensors

## [0.1.1] - 2024-10-24
### Changed
- Updated dependencies and imports after renaming

## [0.1.0] - 2024-09-24
### Added
- Initial version of isaacsim.sensors.camera
