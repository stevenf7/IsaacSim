# Changelog
## [1.0.0] - 2025-05-16
### Changed
- Add time acquisition related features to this extension
- getSystemTime, getSimulationTimeMonotonic
- getSimulationTimeAtTime, getSimulationTimeMonotonicAtTime, getSystemTimeAtTime
- Add python bindings for new APIs

## [0.4.5] - 2025-05-16
### Changed
- Remove timeline commit from physx callback

## [0.4.4] - 2025-05-11
### Changed
- Enable FSD in test settings

## [0.4.3] - 2025-05-10
### Changed
- Remove internal build time dependency

## [0.4.2] - 2025-05-07
### Changed
- switch to omni.physics interface

## [0.4.1] - 2025-04-30
### Changed
- Update event subscriptions to Event 2.0 system

## [0.4.0] - 2025-04-13
### Added
- Added get_simulation_time, get_num_physics_steps, step, set_physics_dt, enable_ccd and is_ccd_enabled in SimulationManager
- Added order and name args to SimulationMangager.register_callback
- Added POST_PHYSICS_STEP and PRE_PHYSICS_STEP to IsaacEvents
- Added is_simulating and is_paused apis to SimulationManager

### Removed
- Removed PHYSICS_STEP from IsaacEvents

## [0.3.13] - 2025-04-07
### Added
- Instantiate an internal physics simulation view (Warp frontend) for the experimental implementations

## [0.3.12] - 2025-04-04
### Changed
- Version bump to fix extension publishing issues

## [0.3.11] - 2025-03-26
### Changed
- Cleanup and standardize extension.toml, update code formatting for all code

## [0.3.10] - 2025-03-26
### Changed
- CCD is not supported when using a cuda device, CCD is now automatically disabled if a cuda device is requested.

## [0.3.9] - 2025-03-24
### Changed
- Migrate to Events 2.0

## [0.3.8] - 2025-03-20
### Changed
- Improve doxygen docstrings

## [0.3.7] - 2025-03-05
### Changed
- Update extension codebase to adhere to isaac sim extension structure and file naming  guidelines

## [0.3.6] - 2025-03-04
### Changed
- Update to kit 107.1 and fix build issues

## [0.3.5] - 2025-02-21
### Changed
- Update style format and naming conventions in c++ code, add doxygen docstrings

## [0.3.4] - 2025-01-28
### Fixed
- Windows signing issue

## [0.3.3] - 2025-01-21
### Changed
- Update extension description and add extension specific test settings

## [0.3.2] - 2024-12-04
### Fixed
- Fixed access to invalid Fabric cache Id

## [0.3.1] - 2024-11-25
### Added
- SimulationManager.enable_fabric_usd_notice_handler method to enable/disable fabric USD notice handler.
- SimulationManager.is_fabric_usd_notice_handler_enabled method to query whether fabric USD notice handler is enabled.

## [0.3.0] - 2024-11-15
### Added
- SimulationManager.assets_loading method to query if textures finished loading.

### Changed
- SimulationManager's default backend with gpu pipelines to torch.

## [0.2.1] - 2024-11-08
### Changed
- Changed testing init file

## [0.2.0] - 2024-11-07
### Added
- Changed C++ plugin to follow the naming guidelines.

## [0.1.0] - 2024-10-31
### Added
- Initial release
