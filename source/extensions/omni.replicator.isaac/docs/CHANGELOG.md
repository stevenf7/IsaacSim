# Changelog

## [1.2.3] - 2022-08-03
### Added
- Added documentation and example demo script
### Changed
- Changed articulation body mass and body intertia randomization to CPU pipeline only

## [1.2.2] - 2022-07-29
### Fixed
- Fixed an issue where distribution parameters in the write nodes are not updated when the distribution is modified

## [1.2.1] - 2022-07-29
### Added
- Added bucketing support for material properties to avoid exceeding 64k material limit

## [1.2.0] - 2022-07-27
### Added
- Added simulation context randomization such as gravity
### Changed
- Changed the behaviour of on_reset randomization such that on_interval modifies the values set at on_reset instead of initial values
### Fixed
- Fixed a bug regarding lower and upper dof limits where randomization would change initial values

## [1.1.2] - 2022-07-26
### Changed
- Changed articulation tendon properties write nodes to be sequential.
### Added
- Added articulation material properties randomization.

## [1.1.1] - 2022-07-25
### Fixed
- Fixed the tests by moving away from using omnigraph bundles and just doing static type resolution on the output of the distribution nodes 

## [1.1.0] - 2022-07-22
### Added
- Added mass, inertia, material properties, rest offset, and contact offset for rigid prim view randomization
- Added mass, inertia, and tendon properties for articulation view randomization
- Added additive and scaling operations for orientation randomization
- Added pytorch rgb writer with replicator API for isaac gym
- Added pytorch listener for provide direct access to batched pytorch tensors from gym simulations

## [1.0.1] - 2022-07-20
### Changed
- Changed rigid_body_view to rigid_prim_view

## [1.0.0] - 2022-07-07
### Added
- Added tensor API node that interface with omni.replicator.core for RL domain randomization