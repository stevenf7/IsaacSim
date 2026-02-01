# Changelog

## [1.0.0] - 2026-01-31
### Added
- Additional control structures, in particular the `SequentialController` and `ParallelController`
### Changed
- `BaseController`, function `reset` now returns `True` if it is successful.
- `BaseController` function `forward` now returns an `Optional[RobotState]`. `None` indicates no valid output.
- `Trajectory` no longer has a (redundant) function for `get_joint_names`
- `Trajectory` returns an `Optional[RobotState]`. `None` indicates no valid output.
- `MinimalTimeTrajectory` is now named `MinimalTimeJointTrajectory`

### Removed
- `Action` type is no longer used, as `RobotState` is more general.

## [0.2.0] - 2026-01-27
### Added
- Introduces a full obstacle strategy and configurations. 
- Adds collision approximation utilities

## [0.1.1] - 2026-01-25
### Changed
- Update license headers

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-01-12
### Added
- Initial release
