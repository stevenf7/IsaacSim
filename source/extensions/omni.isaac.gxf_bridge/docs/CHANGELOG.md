# Changelog
## [0.12.8] - 2023-08-09
### Fixed
- Switch from ui.Window to ScrollingWindow wrapper for extension because scrolling was broken

## [0.12.7] - 2023-07-21
### Fixed
- Skips OgnGXFPublishTimestamp execution if timestamp does not change with
  app update. (Bug 4182191)

## [0.12.6] - 2023-07-10
### Fixed
- Updates RangeScan info field population due to redefinition. (Bug 4188093)
## [0.12.5] - 2023-06-23
### Fixed
- RangeScan message relative_time correctly populated. (Bug 4143606)
## [0.12.4] - 2023-06-23
### Changed
- Isaac SDK dependency promoted, including GXF v23.05.
- Updates tcp_server.yaml to use new asynchronous TCP implementation.

## [0.12.3] - 2023-06-23
### Fixed
- Camera message intrinsics correctly populated for all distortion types (Bug 4163354)

## [0.12.2] - 2023-06-12
### Changed
- Update to kit 105.1, update build system

## [0.12.1] - 2023-06-07
### Fixed
- Incorrect dimension assignment in gxf image publisher
- Incorrect extrinsic rotation matrix definition in gxf image publisher

## [0.12.0] - 2023-05-31
### Added
- Support for passing rational polynomial model to gxf image publisher

## [0.11.1] - 2023-03-26
### Fixed
- Error in gxf camera helper due to non existent class member

## [0.11.0] - 2023-03-22
### Changed
- Use writer backend for gxf publishers
- Add support for camera helper to reset time on stop for cameras

## [0.10.3] - 2023-03-22
### Fixed
- GXFPublishTimestamp directly sets GXF clock to avoid race condition with other publishing nodes.
### Changed
- GxfContext, GxfNode now explicitly expect SyntheticClock in GXF app rather than any Clock.
## [0.10.2] - 2023-03-17
### Fixed
- Increases tcp_server.yaml receiver capacity to 10 to avoid dropping timestamps on client side.
### Changed
- Updates Isaac Sim GXF Bridge OG node documentation.
### Removed
- OgnGXFConfigureTCPServer - OgnGXFYAML has taken its place

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

