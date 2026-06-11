# Changelog

## [1.1.3] - 2026-06-09
### Fixed
- Fix linter errors and missing or incomplete docstrings, and update `python_api.md`.

## [1.1.2] - 2026-04-28
### Changed
- Added writeTarget.platform to extension.toml

## [1.1.1] - 2026-03-26
### Changed
- Moved Python binding module to `bindings/` subdirectory

## [1.1.0] - 2026-02-23
### Added
- Configurable OpenXR required extension settings via carb settings:
  - `exts."isaacsim.kit.xr.teleop.bridge".openxr.requiredExtensions.set`
  - `exts."isaacsim.kit.xr.teleop.bridge".openxr.requiredExtensions.add`
  - `exts."isaacsim.kit.xr.teleop.bridge".openxr.requiredExtensions.remove`
- Extension resolution flow to support replace (`set`), additive (`add`), and removal (`remove`) behaviors from `.toml`/`.kit` files
- Runtime required-extension callback subscription API:
  - C++: `ITeleopBridge::subscribeRequiredExtensions(...)`
  - Python: `subscribe_required_extensions(...)`
- RAII subscription handle support for automatic unsubscription when the handle is released
- Lifetime-safe subscription backing via weak registry-state references (avoids raw interface pointer teardown hazards)
- Documentation updates in `docs/README.md` with runtime callback usage examples

## [1.0.0] - 2026-02-02
### Added
- Initial release
- `get_instance_handle()` function (forwards to Kit Python API)
- `get_session_handle()` function (forwards to Kit Python API)
- `get_stage_space_handle()` function (forwards to Kit Python API)
- `get_instance_proc_addr()` function (retrieves from OpenXR loader via C++)
- Automatic polyfilling of missing functions into `omni.kit.xr.system.openxr`
- Compatibility checks to only patch functions that don't already exist
