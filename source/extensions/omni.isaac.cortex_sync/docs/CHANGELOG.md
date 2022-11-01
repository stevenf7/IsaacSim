# Changelog

## [0.1.1] - 2022-10-28

### Changed
- Modularize `cortex_{ros,sim}` into simple objects wrapping robots rather than extensions.
- Improvements/bugfixes to cortex control (including low-level controller) to handle pausing/stopping
  and restarting the simulator with the controller running.


## [0.1.0] - 2022-10-24

### Added
- Initial version of `cortex_sync`. Pulled ROS components from `omni.isaac.cortex`.
