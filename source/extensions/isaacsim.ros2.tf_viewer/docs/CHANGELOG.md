# Changelog

## [2.0.0] - 2024-11-18
### Removed
- Removed ROS Foxy distro support

## [1.2.0] - 2024-11-11
### Added
- Add the root frame transform if it is not in the list to be rendered (configurable via carb settings)

### Changed
- Unify ROS 2 backend implementations
- Update source code to follow the Isaac Sim's Coding Style Guidelines for C++

## [1.1.0] - 2024-11-04
### Changed
- Updated tf viewer OG node replacing spinOnce function with new initialize ROS2 Node functions

## [1.0.2] - 2024-10-28
### Changed
- Remove test imports from runtime

## [1.0.1] - 2024-10-24
### Changed
- Updated dependencies and imports after renaming

## [1.0.0] - 2024-09-25
### Changed
- Extension renamed to isaacsim.ros2.tf_viewer

## [0.1.1] - 2024-08-26
### Fixed
- Fix the checked status of the menu when the window is closed by using omni.kit.menu helper

## [0.1.0] - 2024-04-12
### Added
- Initial release
