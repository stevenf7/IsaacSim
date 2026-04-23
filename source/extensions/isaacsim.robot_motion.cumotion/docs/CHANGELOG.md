# Changelog
## [1.1.2] - 2026-04-23
### Added
- `RmpFlowController` contains `maximum_substep_size` for sub-stepping when more stable integration is required.

## [1.1.1] - 2026-03-16
### Fixed
- TrajectoryOptimizer now functional on Windows.

## [1.1.0] - 2026-03-05
### Changed
- Added Overview.md, python_api.md and updated docstrings

## [1.0.1] - 2026-03-04
### Fixed
- Fixed type annotation errors by adding `from __future__ import annotations` to files using union type syntax.

## [1.0.0] - 2026-03-03
### Changed
- `CumotionWorldInterface.add_oriented_bounding_boxes` now accepts quaternions (w, x, y, z) instead of rotation matrices for the `rotations` parameter.
- `CumotionWorldInterface.add_oriented_bounding_boxes` now accepts warp arrays directly for `centers`, `rotations`, and `half_side_lengths` instead of lists of warp arrays.

## [0.2.1] - 2026-02-27
### Changed
- Graph planner does not use CUDA on windows

### Fixed
- Patches missing dll path on windows for python wheel

### Removed
- TrajectoryOptimizer support on windows

## [0.2.0] - 2026-02-21
### Added
- Initial integration to experimental motion generation API.

## [0.1.0] - 2026-02-21
### Added
- Cumotion pip prebundle
