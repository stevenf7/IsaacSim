# Changelog

## [2.0.1] - 2026-06-09
### Fixed
- Fix linter errors and missing or incomplete docstrings, and update `python_api.md`.

## [2.0.0] - 2026-04-13
### Changed
- Refactored TelemetryManager to use Carbonite structured logging with generated schema headers
- Telemetry events are now emitted automatically by the extension rather than requiring direct calls from `isaacsim.app.setup` and `isaacsim.simulation_app`

### Added
- Structured telemetry schema with generated C header (`IsaacsimTelemetryCommon.gen.h`)
- JSON schema definitions for telemetry events (`isaacsim.telemetry.common.1.0.json`)
- Decorator-based telemetry: `@telemetry`, `@telemetry_usage`, `@telemetry_error`, and `@telemetry_extension`

## [1.0.0] - 2026-03-18
### Added
- Initial version of the Isaac Sim telemetry framework extension.
- TelemetryManager singleton for schema registration and event emission.
- Common telemetry schema with extensionActivated, featureUsed, and errorOccurred events.
- Typed helper functions: emit_extension_activated, emit_feature_used, emit_error.
