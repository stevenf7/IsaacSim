# Changelog

## [0.10.1] - 2023-02-17
### Changed
- Changing default tcp_server.yaml to follow Isaac convention

## [0.10.0] - 2023-02-15
### Changed

- GXF bridge now publishes CameraMessage instead of CameraImageMessage for color frames
- Adding a new property to the helper / publisher to have stereo offset

## [0.9.0] - 2023-02-09
### Changed

- All publishing nodes now use context clock instead of timestamp input
- Some fixes in crashes for publishing components in case of missing frames
- Adding posetree publisher node

## [0.8.1] - 2023-02-05
### Fixed
- Missing GXF camera helper node

## [0.8.0] - 2023-01-31
### Changed
- Add clock and atlas as configurable entity/components to GxfContext node
- exec out to all nodes with an exect in so they can be triggered in user defined order


## [0.7.1] - 2023-01-25
### Fixed
- remove un-needed cpp ogn files from extension

## [0.7.0] - 2023-01-12

### Added
- GXF Context node for multiple application support
## [0.6.0] - 2023-01-11

### Added
- Node to store a GXF yaml config


## [0.5.1] - 2023-01-09

### Fixed
- pose tree frames were not using properly formatted c style strings

## [0.5.0] - 2023-01-01

### Added
- GXF node to set TCP server address/port
- Extension root folder to include paths in extension

### Changed
- Moves GxfNode.h to plugins/Core

## [0.4.2] - 2023-01-06
### Fixed
- onclick_fn warning when creating UI

## [0.4.1] - 2022-12-06

### Fixed
- Camera publisher intrinsics

## [0.4.0] - 2022-11-28

### Added
- GXF node for timestamp message

### Changed
- Added receivers and serializers for timestamp message to tcp_server.yaml
- Modified tcp_server.yaml scheduler + scheduling terms to guarantee sensor messages are sent only when timestamp message is ready

## [0.3.0] - 2022-11-16

### Changed
- Deprecated viewport input for camera helper
- Added renderProductPath input for camera helper


## [0.2.0] - 2022-09-30

### Added
- GXF nodes for IMU, Differential State and Range Scan

## [0.1.1] - 2022-03-16

### Changed
- Replaced find_nucleus_server() with get_assets_root_path()

## [0.1.0] - 2020-12-11

