# Changelog
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.1.0] - 2026-02-05
### Added
- `WorldBinding`, `WorldInterface` and basic utility function for scaling validation of ancestor prims.

## [2.0.0] - 2026-02-04
### Changed
- All `wp.vec3` and `wp.quat` types were changed to `wp.array`.
- `JointState`, `BodyState` and `RootState` can all now have entries which are `None`, meaning they are not defined (for example, `JointState.velocity=None` indicating velocity is not known).
- The `combine_robot_states` function is more flexible.

## [1.1.0] - 2026-02-02
### Added
- `SceneQuery` and `TrackableApi`, for querying objects within an AABB for those with a certain API.

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

## [0.1.0] - 2026-01-12
### Added
- Initial release
