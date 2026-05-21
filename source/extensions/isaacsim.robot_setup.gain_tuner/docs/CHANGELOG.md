# Changelog
## [3.5.2] - 2026-05-12
### Changed
- Menu entry is under Tools > Robotics > Asset Editors > Gain Tuner (matches `isaacsim.gui.menu` layout and user docs).

### Fixed
- Menu and `CreateUIExtension:Gain Tuner` show and focus the panel instead of toggling visibility, so a second open does not hide it.
- Visibility callback branches on the `visible` argument so the hide path runs when the window is closed (not only when `self._window.visible` was already false).

## [3.5.1] - 2026-05-07
### Fixed
- Fixed first column collapsing on small window sizes

## [3.5.0] - 2026-04-23
### Added
- `Snap to Limits` test mode with per-joint pass/blocked/fail results
- `Stress Test` mode with Random Walk and Adversarial sub-modes
- Pluggable `RobotTest` registry on `GainTuner`
- Disable self-collisions and disable velocity limits toggles
- `get_test_result_metrics()` API

### Changed
- Default test mode is now `Snap to Limits`
- Per-mode duration controls replace shared `Test Duration` field

### Fixed
- Bulk edit preserves multi-selection across widget clicks
- Self-collision restore auto-restarts timeline for re-cook
- Stale test metrics cleared on new run
- Creep vs blocked classification uses error variance check

## [3.4.2] - 2026-03-06
### Fixed
- Clear physics, render, and assets-loaded subscriptions when window is hidden to avoid per-frame callbacks running while the panel is not visible

## [3.4.1] - 2026-03-04
### Fixed
- Fix api errors
- Fixed incorrect type annotations

## [3.4.0] - 2026-03-04
### Changed
- Added Overview.md, python_api.md and updated docstrings

## [3.3.1] - 2026-02-27
### Fixed
- Hang on test exit

## [3.3.0] - 2026-02-26
### Changed
- Migrate mass property queries from PhysX property query interface to Articulation tensor API (`isaacsim.core.experimental.prims.Articulation`).
- Remove `omni.physics.physx` dependency; mass, COM, and inertia are now queried via `get_link_masses()`, `get_link_coms()`, and `get_link_inertias()`.

## [3.2.1] - 2026-02-26
### Fixed
- Fix Vec3f/Vec3d type mismatch in inertia accumulation caused by robot schema double-precision change
- Fixed hanging shutdown on tests

## [3.2.0] - 2026-02-25
### Added
- Added unit tests for equivalent inertia computation

## [3.1.5] - 2025-12-16
### Changed
- Fixed Natural Frequency calculation:
    - Convert computed unit from Radians to Degree when storing the Stiffness
    - Properly handle Fixed robot chains
    - Properly use only the proper axis inertia when Revolute Joint, or directly use mass when prismatic.

## [3.1.4] - 2025-12-16
### Changed
- Consume Asset Changed events

## [3.1.3] - 2025-12-15
### Fixed
- Fixed consumption of events downstream on UI builder

## [3.1.2] - 2025-12-05
### Changed
- Migrate to Events 2.0.

## [3.1.1] - 2025-10-27
### Removed
- Remove unused import statement and commented code

## [3.1.0] - 2025-10-17
### Changed
- Migrate PhysX subscription and simulation control interfaces to Omni Physics

## [3.0.6] - 2025-08-04
### Fixed
- Natural Frequency and Damping Ratio computations
- Unresponsive UI when bulk editing min step value

## [3.0.5] - 2025-07-02
### Changed
- Fixed refresh when robot changes on stage
- Fixed batch editing when tuning gains
- Removed "strength" and use stiffness/damping
- Pop up a warning asking for confirmation when save Gains to Physics Layer
- Make frames and table resizable and add scroll bar

## [3.0.4] - 2025-05-19
### Changed
- Update copyright and license to apache v2.0

## [3.0.3] - 2025-05-16
### Changed
- Make extension target a specific kit version

## [3.0.2] - 2025-05-14
### Changed
- Fix deregiter of action when extension is shutdown without version number

## [3.0.1] - 2025-05-12
### Changed
- Register action without version number

## [3.0.0] - 2025-05-09
### Changed
- Update extension to use new Core Prim API and Robot Schema
- Redesigned the UI to be more user friendly and intuitive

### Added
- Added a new "Save Gains to Physics Layer" button to the UI
- Added new Sequential mode to the gains test
- Added Natural Frequency and Damping Ratio fields to the gains tuning mode.
- Added automatic selection between Position and Velocity command based on the joint gains
- Added switching between Acceleration and Force modes for the joint setting.

## [2.0.7] - 2025-05-07
### Changed
- Switch to omni.physics interface

## [2.0.6] - 2025-04-04
### Changed
- Version bump to fix extension publishing issues

## [2.0.5] - 2025-03-26
### Changed
- Cleanup and standardize extension.toml, update code formatting for all code

## [2.0.4] - 2025-03-24
### Changed
- Migrate to Events 2.0

## [2.0.3] - 2025-01-21
### Changed
- Update extension description and add extension specific test settings

## [2.0.2] - 2024-12-03
### Changed
- Isaac Util menu to Tools->Robotics menu

## [2.0.1] - 2024-10-24
### Changed
- Updated dependencies and imports after renaming

## [2.0.0] - 2024-10-01
### Changed
- Extension renamed to isaacsim.robot_setup.gain_tuner.

## [1.1.2] - 2024-06-13
### Fixed
- Fixed bug where robot with zero-gains causes a math error in trying to take log(0).

## [1.1.1] - 2024-04-23
### Fixed
- Fixed post-test behavior where an Articulation is left with a non-zero velocity command.

## [1.1.0] - 2024-04-16
### Fixed
- Fixed bug where Gains Test Settings Panel had multiple ways of accumulating or forgetting state between tests when switching robots or toggling STOP/PLAY

### Added
- Added fields to add position and velocity impulses to the start of the robot trajectory.

## [1.0.1] - 2024-03-14
### Fixed
- Fixed logic around selecting Articulation on STOP/PLAY given new behavior in Core get_prim_object_type() function.

### Added
- Added helper text telling the user to click the play button to get started.
- Added more text clarifying Gains Test settings.

## [1.0.0] - 2024-03-08
### Added
- Initial version of Gain Tuner Extension
