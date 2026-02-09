# Changelog

## [1.0.0] - 2026-02-02

### Added
- Initial release
- `get_instance_handle()` function (forwards to Kit Python API)
- `get_session_handle()` function (forwards to Kit Python API)
- `get_stage_space_handle()` function (forwards to Kit Python API)
- `get_instance_proc_addr()` function (retrieves from OpenXR loader via C++)
- Automatic polyfilling of missing functions into `omni.kit.xr.system.openxr`
- Compatibility checks to only patch functions that don't already exist