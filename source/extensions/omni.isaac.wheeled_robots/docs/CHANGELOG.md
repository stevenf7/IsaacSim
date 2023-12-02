# Changelog

## [0.9.0] - 2023-11-28
### Changed
- OgnAckermannSteering node receives inputs in SI units.
- OgnAckermannSteering node now accepts speed and acceleration as desired forward motion inputs. 
- OgnAckermannSteering node uses front axel steering angle as input rather than curvature 

## [0.8.1] - 2023-11-27
### Fixed
- _wheeled_dof_indices vs _wheel_dof_indices typo

## [0.8.0] - 2023-11-13
### Changed
- Moved wheel base pose controller from motion generation extension

## [0.7.2] - 2023-10-11
### Fixed
- Differential controller will not ignore 0s as max speed inputs.

## [0.7.1] - 2023-10-06
### Changed
- wheeled robot class can now accept a relative path from the default prim to the robot prim when the robot is not the default prim
### Fixed
- Differential controller now resets on simulation Stop

## [0.7.0] - 2023-09-06
### Added
- Ackermann Steering OmniGraph node

## [0.6.5] - 2023-08-10
### Fixed
- Changed robot prim types from bundle to target in Omnigraph
## [0.6.4] - 2023-06-13

### Fixed
- Kit 105.1 update 
- use omni.usd instead of omni.usd.utils for get_world_transform_matrix

## [0.6.3] - 2023-03-10

### Fixed
- Error on stop for holonomic and differential controllers

## [0.6.2] - 2023-03-07

### Fixed
- Hardcoded stanley control parameters
- OGN wrapper node could not change stanley control parameters

## [0.6.1] - 2022-08-29

### Fixed
- Issue with targeting using coordinates instead of prim

### Changed
- Removed excessive db.inputs calls to improve efficiency/speed
- Removed path drawing (may add later as an option)


## [0.6.0] - 2022-08-22

### Added
- OgnQuinticPathPlanner
- OgnCheckGoal2D
- OgnStanleyControlPID

## [0.5.8] - 2022-08-08

### Fixed
- Issue with holonomic controller returning an error on reset


## [0.5.7] - 2022-07-22

### Changed
- pulled out the internal state classes for both holonomic and differential controller 

## [0.5.6] - 2022-07-19

### Added
- unit tests for nodes and controllers

## [0.5.5] - 2022-06-29

### Added
- doc strings for python files and comments for omnigraph nodes.

## [0.5.4] - 2022-06-01

### Changed
- OgnHolonomicController to use BaseResetNode class from core_nodes

## [0.5.3] - 2022-05-31

### Changed
- OgnDifferentialController to use BaseResetNode class from core_nodes

## [0.5.2] - 2022-05-11

### Changed
- Add Isaac sim category to holonomic robot setup node.

## [0.5.1] - 2022-05-11

### Changed
- holonomic_controller.py allows for flexible wheels rotation axis and stage-up axis

## [0.5.0] - 2022-05-11

### Changed
- holonomic_controller.py becomes robot agnostic

### Added
- OgnHolonomicController Node
- holonomic_robot_usd_setup.py to pull robot attributes from Usd
- OgnHolonomicRobotUsdSetup Node 

## [0.4.1] - 2022-05-10

### Fixed
- Minor fixes to OgnDifferentialController

## [0.4.0] - 2022-05-06

### Removed
- OgnGenericDifferentialRobotSetup node

### Changed
- OgnDifferentialController no longer uses bundle inputs

## [0.3.0] - 2022-05-03

### Added
- OgnGenericDifferentialRobotSetup
- wheeled_robot.py

### Changed
- OgnDifferentialController uses bundle inputs

### Fixed
- omnigraph dependency

## [0.2.0] - 2022-04-27

### Added
- OgnDifferentialController

## [0.1.2] - 2022-04-22

### Changed
- Using osqp to solve holonomic controller
- Remove unecessary dependencies

## [0.1.1] - 2022-04-16

### Changed
- Fixed dependency versions

## [0.1.0] - 2022-04-08

### Added
- Initial version
