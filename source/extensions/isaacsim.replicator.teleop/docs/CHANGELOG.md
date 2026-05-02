# Changelog

## [0.3.1] - 2026-04-28
### Added
- `pose_backend` arg on `build_teleop_recorder` (forwarded to `EpisodeRecorder`).

### Fixed
- Custom XR anchor actually moves the headset.
- Disconnect returns the headset to its pre-Connect pose.

## [0.3.0] - 2026-04-22
### Added
- Teleop-side `Recordable` plugins, a `build_teleop_recorder(...)` factory, and a `VRRecordingButton` that toggles recording from a VR button — all built on `isaacsim.replicator.episode_recorder`.

### Changed
- Recorder / replayer code moved out to `isaacsim.replicator.episode_recorder`; the teleop extension now only contributes teleop-specific channels.

## [0.2.1] - 2026-04-18
### Changed
- Added return type annotations, `from __future__ import annotations`, imperative-mood docstrings, and `__all__` definitions

## [0.2.0] - 2026-04-16
### Added
- Added FSD backend option

### Changed
- Switced to numpy arrays for most operations

## [0.1.0] - 2026-04-09
### Added
- Initial version of the Teleop extension
