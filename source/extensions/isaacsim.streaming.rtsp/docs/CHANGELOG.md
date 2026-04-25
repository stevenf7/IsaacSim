# Changelog

## [0.1.2] - 2026-04-24

### Fixed
- Materialize the `RenderVar` child required by SRTX under the render product before attaching `RTSPStreamWriter`, and author the matching `srtx:compression:type` for raw and H.264 streaming.

## [0.1.1] - 2026-04-21

### Fixed
- Pass simulation time as `start_time_ns`/`ended_time_ns` to the RTSP server so streamed frame timestamps reflect sim time.

## [0.1.0] - 2026-03-31

### Added
- `RTSPStreamWriter` Replicator writer with H.264 pre-encoded and raw CUDA streaming modes.
- Per-frame SEI metadata injection (simulation time, wall-clock timestamp, frame number).
- `RTSPCameraHelper` OmniGraph node for graph-based streaming setup.
