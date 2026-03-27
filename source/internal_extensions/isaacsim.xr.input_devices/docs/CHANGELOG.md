# Changelog

## [1.1.1] - 2026-03-26
### Changed
- Moved Python binding module to `bindings/` subdirectory

## [1.1.0] - 2025-12-17
### Changed
- Migrate extension implementation to core experimental API

## [1.0.4] - 2025-12-08
### Fixed
- Disable tests when pysurvive is not available

## [1.0.3] - 2025-10-28
### Added
- Add test dependency on `omni.isaac.ml_archive`

## [1.0.2] - 2025-10-16
### Fixed
- Remove pysurvive prebundle to avoid re-dist

## [1.0.1] - 2025-10-08
### Fixed
- Force publish the platform type for kit registery
- Increment version numbr for axis fix

## [1.0.0] - 2025-08-08
### Added
- Initial release of `isaacsim.xr.input_devices` extension
- Hand-tracker integration via pluggable C API, exposed through Python bindings
- Vive tracker integration via `pysurvive` (libsurvive)
- Unified Python API via `get_manus_vive_integration()`
- Per-device connection status structure
- Documentation and basic tests
- Orientation conventions: `[w, x, y, z]` (right handed)
- Set `ISAACSIM_HANDTRACKER_LIB` or `ISAACSIM_HANDTRACKER_NAME` to control the hand-tracker library loaded by the plugin
