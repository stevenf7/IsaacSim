# Changelog

## [0.1.1] - 2026-04-28
### Added
- `pose_backend` arg on `EpisodeRecorder` / `EpisodeReplayer` (`usd` / `usdrt` / `fabric`, default `usd`). Mid-session FSD toggle silently demotes to `usd` with a one-shot warning instead of crashing.
- `pose_batch_tier_count` / `pose_backend` properties; `PoseBackend` re-exported.

### Fixed
- Replay writes nested xforms / articulations in parents-first tiers, removing the one-frame-lag stutter on prims under a moving parent.
- Missing-xformOps recovery on replay scopes per tier, so later tiers hitting the same error still recover instead of aborting the run.

## [0.1.0] - 2026-04-22
### Added
- Initial release: `EpisodeRecorder` / `EpisodeReplayer` record simulation state to HDF5 via a pluggable `Recordable` protocol and replay it as pure USD writes onto an anonymous sublayer (no physics stepping, no stage mutation).
