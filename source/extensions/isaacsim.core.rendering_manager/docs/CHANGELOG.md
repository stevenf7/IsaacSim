# Changelog

## [0.3.1] - 2026-03-25
### Changed
- `ViewportManager.set_camera_view` now delegates look-at matrix computation to `look_at_matrix` from `isaacsim.core.experimental.utils.transform`

## [0.3.0] - 2026-03-04
### Changed
- Added Overview.md, python_api.md and updated docstrings

## [0.2.3] - 2025-12-20
### Changed
- Move import of kit loop runner to a try-except block to handle import exceptions if omni.kit.loop-isaac is not enabled

## [0.2.2] - 2025-11-28
### Fixed
- Fix camera view test case by comparing whether the quaternions represent the same orientation

## [0.2.1] - 2025-11-25
### Changed
- Handle Isaac Sim's loop runner import exceptions

## [0.2.0] - 2025-11-21
### Added
- Add method to set a camera view

### Changed
- Split the manager implementation into two: `RenderingManager` and `ViewportManager`

## [0.1.0] - 2025-11-11
### Added
- Initial release
