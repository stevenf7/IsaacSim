# Changelog

## [0.1.2] - 2022-12-08

### Fixed
- Changed CortexControlRos to reset the entire cortex pipeline when
  synchronizing with a sim/physical robot rather than just the commanders.

## [0.1.1] - 2022-10-28

### Changed
- Modularize `cortex_{ros,sim}` into simple objects wrapping robots rather than extensions.
- Improvements/bugfixes to cortex control (including low-level controller) to handle pausing/stopping
  and restarting the simulator with the controller running.


## [0.1.0] - 2022-10-24

### Added
- Initial version of `cortex_sync`. Pulled ROS components from `omni.isaac.cortex`.
