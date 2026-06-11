# Public API for module isaacsim.core.telemetry:

## Classes

- class TelemetryManager
  - def __init__(self)
  - class def get_instance(cls) -> TelemetryManager
  - def is_enabled(self) -> bool
  - def register_schema(self, schema_name: str, schema: dict) -> dict | None
  - def send_event(self, schema_name: str, event_name: str, data: dict) -> bool
  - def unregister_schema(self, schema_name: str)

## Functions

- def emit_error(extension_id: str, error_category: str, error_type: str, operation: str, recoverable: bool = True) -> bool
- def emit_extension_activated(extension_id: str, extension_version: str, action: str) -> bool
- def emit_feature_used(extension_id: str, feature_name: str, feature_type: str, duration_ms: int = 0) -> bool
- def get_telemetry_manager() -> TelemetryManager
- def telemetry(extension_id: str, feature_name: str, feature_type: str = 'api_call', error_category: str = 'runtime_error') -> Callable[[Callable[..., Any]], Callable[Ellipsis, Any]]
- def telemetry_error(extension_id: str, feature_name: str, error_category: str = 'runtime_error') -> Callable[[Callable[..., Any]], Callable[Ellipsis, Any]]
- def telemetry_extension(cls: type[_T]) -> type[_T]
- def telemetry_usage(extension_id: str, feature_name: str, feature_type: str = 'api_call') -> Callable[[Callable[..., Any]], Callable[Ellipsis, Any]]
