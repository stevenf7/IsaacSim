# Changelog

## [3.2.3] - 2026-06-09
### Fixed
- Fix linter errors and missing or incomplete docstrings, and update `python_api.md`.

## [3.2.2] - 2026-03-26
### Changed
- Moved Python binding module to `bindings/` subdirectory

## [3.2.1] - 2026-02-02
### Changed
- Update to Kit 110.0

## [3.2.0] - 2025-11-19
### Changed
- Refactor PrimitiveDrawingHelper to use size_t for loops
- Use enum class for RenderingMode
- Update to use new debug draw plugin interface
- Add docstrings to python code
- Update unit tests to have beetter coverage

## [3.1.1] - 2025-11-03
### Changed
- Fix missing static library from published extension

## [3.1.0] - 2025-06-24
### Added
- Added CUDA support to OgnDebugDrawPointCloud

## [3.0.1] - 2025-05-13
### Fixed
- Missing static library

## [3.0.0] - 2025-05-10
### Changed
- Removed interfaces that required internal dependencies

## [2.0.9] - 2025-05-02
### Changed
- Remove all Dynamic control compile time dependencies

## [2.0.8] - 2025-04-04
### Changed
- Version bump to fix extension publishing issues

## [2.0.7] - 2025-03-26
### Changed
- Cleanup and standardize extension.toml, update code formatting for all code

## [2.0.6] - 2025-03-05
### Changed
- Update extension codebase to adhere to isaac sim extension structure and file naming  guidelines

## [2.0.5] - 2025-03-04
### Changed
- Update to kit 107.1 and fix build issues

## [2.0.4] - 2025-02-21
### Changed
- Update style format and naming conventions in c++ code, add doxygen docstrings

## [2.0.3] - 2025-01-28
### Fixed
- Windows signing issue

## [2.0.2] - 2025-01-21
### Changed
- Update extension description and add extension specific test settings

## [2.0.1] - 2024-10-24
### Changed
- Updated dependencies and imports after renaming

## [2.0.0] - 2024-09-27
### Changed
- Renamed extension to isaacsim.util.debug_draw

## [1.1.0] - 2024-07-08
### Removed
- Deprecated and unused omni.debugdraw dependency

## [1.0.0] - 2024-06-13
### Added
- Added DebugDrawRayCast node to visualize arrays of raycasts

## [0.7.1] - 2024-04-16
### Fixed
- Update IStageUpdate usage to fix deprecation error

## [0.7.0] - 2024-01-08
### Changed
- Moved header files to extension

## [0.6.2] - 2023-12-12
### Changed
- In DebugDrawPointCloud compute, set pointer to debug draw helper if it's missing.
- In DebugDrawPointCloud compute, only clear when needed.

## [0.6.1] - 2023-11-17
### Added
- Check for valid prim path, so the debug drawing nodes will issue an error instead of crash with invalid path

## [0.6.0] - 2023-08-30
### Added
- doTransform to DebugDrawPointCloud node, set to false it ignores the input transform

## [0.5.1] - 2023-08-25
### Changed
- Added stdout fail pattern for the expected no prim found edge case for the ogn test

## [0.5.0] - 2023-08-22
### Changed
- Added testMode and removed depthTest (it did nothing) from DebugDrawPointCloud node.

## [0.4.1] - 2023-08-15
### Changed
- Changed prim input type from bundle to target for xPrim Axis and Radius visualizer

## [0.4.0] - 2023-08-15
### Changed
- Rename width to size for point cloud debug node to prevent auto connection when using in replicator pipelines

## [0.3.0] - 2023-08-01
### Added
- xPrim Axis Visualzier node
- xPrim Radius Visualizer node

### Changed
- Pass width vector by reference.
- Simplified DebugDrawPointCloud internals.
- DebugDrawPointCloud Node updated to work with dataPtr/bufferSize inputs.
- DebugDrawPointCloud Node updated to auto connect with synthetic data/replicator nodes.

## [0.2.3] - 2023-01-19
### Fixed
- Crash when trying to draw without a valid renderer

## [0.2.2] - 2022-12-14
### Fixed
- Crash when deleting

## [0.2.1] - 2022-10-18
### Changed
- Debug Draw Point Cloud takes transform
- PrimitiveDrawingHelper::setVertices with poistion only

## [0.2.0] - 2022-10-06
### Added
- Debug Draw Point Cloud node
- PrimitiveDrawingHelper::setVertices with constant color and width

### Changed
- antialiasingWidth to 1 in PrimitiveDrawingHelper::draw()

## [0.1.4] - 2022-10-02
### Fixed
- Crash when stage was not ready

## [0.1.3] - 2022-09-07
### Fixed
- Fixes for kit 103.5

## [0.1.2] - 2022-03-07
### Added
- Added flag to disable depth check

## [0.1.1] - 2021-08-20
### Added
- World space flag to specify if width value is in world coordinates.

## [0.1.0] - 2021-07-27
### Added
- Initial version of extension
