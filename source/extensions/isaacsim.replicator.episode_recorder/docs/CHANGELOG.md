# Changelog

## [0.1.0] - 2026-04-22
### Added
- Initial release: `EpisodeRecorder` / `EpisodeReplayer` record simulation
  state to HDF5 via a pluggable `Recordable` protocol and replay it as pure
  USD writes onto an anonymous sublayer (no physics stepping, no stage
  mutation).
