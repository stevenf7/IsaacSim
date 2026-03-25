# Changelog

## [1.0.0] - 2026-03-18
### Added
- Initial version of the Isaac Sim telemetry framework extension.
- TelemetryManager singleton for schema registration and event emission.
- Common telemetry schema with extensionActivated, featureUsed, and errorOccurred events.
- Typed helper functions: emit_extension_activated, emit_feature_used, emit_error.
