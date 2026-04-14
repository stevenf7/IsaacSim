# Isaac Sim Telemetry Framework

## Overview

`isaacsim.core.telemetry` provides a centralized telemetry framework for Isaac Sim extensions, built on top of Carbonite's `omni.structuredlog` Python bindings. It offers:

- **Pre-registered common events** for extension activation tracking, feature usage, and error reporting — usable with a single function call.
- **Custom schema support** for extensions that need domain-specific telemetry events (e.g. URDF import failure diagnostics).
- **Centralized enable/disable** — all events no-op when structured logging is disabled.
- **Consistent error handling** — failures are logged via `carb.log_warn` instead of raising exceptions.

## Quick Start

Add `"isaacsim.core.telemetry" = {}` to your extension's `[dependencies]` in `extension.toml`, then use the common helpers:

```python
from isaacsim.core.telemetry import emit_extension_activated, emit_feature_used, emit_error

# Track extension lifecycle
emit_extension_activated(extension_id="isaacsim.my.extension", extension_version="1.0.0", action="enabled")

# Track feature usage
emit_feature_used(
    extension_id="isaacsim.my.extension",
    feature_name="create_sensor",
    feature_type="command",
    duration_ms=150,
)

# Track errors
emit_error(
    extension_id="isaacsim.my.extension",
    error_category="validation_error",
    error_type="invalid_sensor_config",
    operation="create_sensor",
)
```

No schema registration or setup is required for these common events.

### Decorator-based instrumentation

For functions where you want automatic timing and error tracking, use the decorator API:

```python
from isaacsim.core.telemetry import telemetry, telemetry_usage, telemetry_error

# Full instrumentation: featureUsed on success, errorOccurred on exception
@telemetry(extension_id="isaacsim.sensors.experimental.rtx", feature_name="create_lidar_sensor")
def create_lidar_sensor(prim_path, config):
    ...

# Usage tracking only (no error events)
@telemetry_usage(extension_id="isaacsim.sensors.experimental.rtx", feature_name="query_sensor")
def query_sensor(sensor_id):
    ...

# Error tracking only (no usage events)
@telemetry_error(extension_id="isaacsim.app.setup", feature_name="app_startup")
def initialize():
    ...
```

### Extension lifecycle instrumentation

Apply `@telemetry_extension` to an `IExt` subclass to automatically emit `extensionActivated` events on startup and shutdown. The extension name and version are parsed from the `ext_id` that Kit passes to `on_startup`:

```python
from isaacsim.core.telemetry import telemetry_extension

@telemetry_extension
class MyExtension(omni.ext.IExt):
    def on_startup(self, ext_id):
        ...

    def on_shutdown(self):
        ...
```

## Common Event Reference

### extensionActivated

Emitted when an Isaac Sim extension is enabled or disabled.

| Property           | Type   | Description                                       |
| ------------------ | ------ | ------------------------------------------------- |
| `extensionId`      | string | Extension identifier (e.g. `isaacsim.sensors.experimental.rtx`) |
| `extensionVersion` | string | Semantic version (e.g. `1.2.0`)                    |
| `action`           | string | `"enabled"` or `"disabled"`                        |

### featureUsed

Emitted when a user invokes a command, menu item, or significant API call.

| Property      | Type   | Description                                                |
| ------------- | ------ | ---------------------------------------------------------- |
| `extensionId` | string | Extension that owns the feature                             |
| `featureName` | string | Short identifier (e.g. `import_urdf`, `create_lidar_sensor`) |
| `featureType` | string | `"command"`, `"menu_item"`, or `"api_call"`                  |
| `durationMs`  | integer | Wall-clock duration in milliseconds, `0` if not measured   |

### errorOccurred

Emitted when an error occurs in an Isaac Sim extension.

| Property        | Type    | Description                                                                    |
| --------------- | ------- | ------------------------------------------------------------------------------ |
| `extensionId`   | string  | Extension where the error occurred                                              |
| `errorCategory` | string  | Broad classification (enum: `import_failure`, `validation_error`, `runtime_error`, `configuration_error`, `dependency_error`, `timeout`) |
| `errorType`     | string  | Extension-specific error code (e.g. `urdf_joint_parse`, `missing_scan_rate_param`) |
| `operation`     | string  | Feature/operation active when the error occurred (matches `featureName` in `featureUsed`) |
| `recoverable`   | boolean | `true` if the operation could continue, `false` if it aborted                    |

## Feature Type Guidance

Use the `featureType` parameter to classify how the user triggered the feature:

- **`"command"`** — Registered Kit commands (`omni.kit.commands.execute`).
- **`"menu_item"`** — Menu bar or context menu actions.
- **`"api_call"`** — Significant programmatic operations (e.g. `SimulationApp` startup, sensor creation via Python API).

## Error Telemetry Patterns

All error fields are structured identifiers — no free-form text is accepted, which
eliminates PII risk by design.

```python
from isaacsim.core.telemetry import emit_error

try:
    parse_urdf(file_path)
except URDFParseError as exc:
    emit_error(
        extension_id="isaacsim.asset.importer.urdf",
        error_category="import_failure",
        error_type="urdf_joint_parse",
        operation="import_urdf",
        recoverable=False,
    )
```

### `errorCategory` values

| errorCategory        | When to use                                                  |
| -------------------- | ------------------------------------------------------------ |
| `import_failure`     | Asset or file import/parse failures                          |
| `validation_error`   | Invalid configuration, parameters, or schema violations      |
| `runtime_error`      | Unexpected failures during normal operation                  |
| `configuration_error`| Missing or invalid settings/configuration                    |
| `dependency_error`   | Required extension, plugin, or library not available          |
| `timeout`            | Operations that exceeded expected duration                   |

### `errorType` guidelines

Use a short, descriptive code that identifies the specific failure within the extension.
It should be meaningful for drill-down analysis but never contain PII:

- `urdf_joint_parse` — URDF joint element could not be parsed
- `missing_scan_rate_param` — required sensor parameter was absent
- `physics_step_nan` — physics simulation produced NaN values
- `prim_not_found` — expected USD prim was missing from the stage

## Custom Schemas

For domain-specific events that don't fit the common schema, register a custom baked JSON schema:

```python
from isaacsim.core.telemetry import get_telemetry_manager

MY_SCHEMA = {
    "generated": "Custom schema for URDF importer diagnostics.",
    "anyOf": [{"$ref": "#/definitions/events/com.nvidia.isaacsim.urdf.importResult"}],
    "$schema": "http://json-schema.org/draft-07/schema#",
    "schemaMeta": {
        "clientName": "isaacsim.urdf.diagnostics",
        "schemaVersion": "1.0",
        "eventPrefix": "com.nvidia.isaacsim.urdf",
        "definitionVersion": "1.0",
        "omniverseFlags": ["fSchemaFlagAnonymizeEvents"],
        "description": "URDF importer telemetry events.",
    },
    "definitions": {
        "events": {
            "com.nvidia.isaacsim.urdf.importResult": {
                "eventMeta": {
                    "service": "telemetry",
                    "privacy": {"category": "usage", "description": "URDF import results"},
                    "omniverseFlags": [],
                },
                "type": "object",
                "additionalProperties": False,
                "required": ["filePath", "success", "jointCount"],
                "properties": {
                    "filePath": {"type": "string", "description": "Path to the URDF file"},
                    "success": {"type": "boolean", "description": "Whether the import succeeded"},
                    "jointCount": {"type": "integer", "description": "Number of joints parsed"},
                },
                "description": "Emitted after a URDF import attempt.",
            },
        },
    },
    "description": "URDF importer telemetry events.",
}


class UrdfImporterExtension(omni.ext.IExt):
    def on_startup(self, ext_id):
        manager = get_telemetry_manager()
        manager.register_schema(schema_name="isaacsim.urdf.diagnostics", schema=MY_SCHEMA)

    def on_shutdown(self):
        manager = get_telemetry_manager()
        manager.unregister_schema(schema_name="isaacsim.urdf.diagnostics")
```

Send custom events via the raw API:

```python
get_telemetry_manager().send_event(
    schema_name="isaacsim.urdf.diagnostics",
    event_name="importResult",
    data={"filePath": "/path/to/robot.urdf", "success": True, "jointCount": 12},
)
```

## Schema Versioning

Every baked JSON schema contains two version fields in `schemaMeta`:

| Field | Purpose |
| --- | --- |
| `schemaVersion` | Version of the schema as a registered entity. Used by the telemetry transmitter and data servers to validate events. Once approved and published, a version is immutable. |
| `definitionVersion` | Version of the event definitions block (`definitions/events`). Tracks changes to event structure independently. |

Both use `MAJOR.MINOR` format and are kept in sync.

- **Minor bump** (e.g. `1.0` → `1.1`) — non-breaking changes: adding a new event, adding an optional property, adding a privacy category.
- **Major bump** (e.g. `1.1` → `2.0`) — breaking changes: removing an event, removing/renaming a required property, changing a property's type.

Published schema versions are immutable. Older versions remain approved so that older Isaac Sim builds continue to function. Bump versions only when event definitions actually change, not on every extension release.

## Privacy and Configuration

Telemetry behavior is controlled by a layered hierarchy. `isaacsim.core.telemetry` checks only the top-level switch; the remaining layers are enforced by `omni.kit.telemetry` and the Carbonite transmitter.

### Control hierarchy

| Layer | Setting | Effect |
| --- | --- | --- |
| **1. Master switch** | `/structuredLog/enable` | When `false`, disables all structured logging — no local logs, no transmission. All `emit_*` and `send_event` calls return `False`. This is the only setting checked by `TelemetryManager.is_enabled()`. |
| **2. Transmission** | `/telemetry/enableAnonymousData` | When `false`, events are still logged locally (`~/.nvidia-omniverse/logs/`) but not transmitted to NVIDIA. Can also be disabled via the `OMNI_TELEMETRY_DISABLE_ANONYMOUS_DATA=1` environment variable (useful for containers). |
| **3. Mode** | `/telemetry/mode` (`prod` / `test` / `dev`) | Each mode applies different collection and transmission policies. **Headless mode disables telemetry by default** — pass `--/telemetry/mode=dev` to enable. |
| **4. Extension toggle** | Per-extension setting (e.g. `/exts/<ext>/telemetry_enabled`) | Individual extensions can define their own toggle in `extension.toml`. `isaacsim.core.telemetry` does not enforce these — the extension is responsible for checking before calling `emit_*`. |
| **5. Privacy consent** | `privacy.toml` via `/structuredLog/privacySettingsFile` | Per-category consent (`usage`, `performance`, `personalization`). Events whose category is not consented to are suppressed by the transmitter. Managed by the Omniverse Launcher or set programmatically. |

### Setting telemetry controls

**Command line:**

```bash
# Disable all structured logging
--/structuredLog/enable=false

# Disable transmission only (local logging continues)
--/telemetry/enableAnonymousData=false

# Enable telemetry in headless mode
--/telemetry/mode=dev
```

**Application `.kit` file:**

```toml
[settings.telemetry]
enableAnonymousData = true
```

**Runtime (Python):**

```python
import carb.settings

settings = carb.settings.get_settings()
settings.set("/structuredLog/enable", False)      # disable everything
settings.set("/telemetry/enableAnonymousData", False)  # disable transmission only
```

### Privacy categories

Carbonite defines three consent categories. Each event schema declares which category it belongs to; the transmitter only sends events whose category has user consent.

| Category | Description | Used by this extension? |
| --- | --- | --- |
| `usage` | App usage — startup, shutdown, feature adoption | Yes — `extensionActivated`, `featureUsed` |
| `performance` | App performance — hardware info, timing, errors | Yes — `errorOccurred` |
| `personalization` | App customization by the user | No — not currently collected in Omniverse apps |

Consent is set in `~/.nvidia-omniverse/config/privacy.toml`:

```toml
[privacy]
usage = true
performance = true
personalization = true
```

For containers, use environment variables instead: `OMNI_TELEMETRY_PRIVACY_USAGE`, `OMNI_TELEMETRY_PRIVACY_PERFORMANCE`, `OMNI_TELEMETRY_PRIVACY_PERSONALIZATION`. If a category is missing and no environment variable is set, consent is **denied** by default.

### Anonymization

- All common events use the `fSchemaFlagAnonymizeEvents` flag, which strips personally identifiable information before transmission.
- Error events use only structured identifiers (enums and codes) — no free-form text fields — eliminating PII risk by design.
- `omni.kit.telemetry` (a dependency of this extension) manages the structured log transmitter lifecycle.

## Complete Integration Example

A full extension combining common helpers and a custom schema:

```python
import time

import omni.ext
from isaacsim.core.telemetry import (
    emit_error,
    emit_extension_activated,
    emit_feature_used,
    get_telemetry_manager,
)

CUSTOM_SCHEMA = {
    # ... your baked JSON schema dict ...
}


class MyExtension(omni.ext.IExt):
    def on_startup(self, ext_id):
        ext_name = ext_id.split("-")[0]
        version = ext_id.split("-")[1] if "-" in ext_id else "0.0.0"

        # Track activation
        emit_extension_activated(extension_id=ext_name, extension_version=version, action="enabled")

        # Register domain-specific schema
        get_telemetry_manager().register_schema(schema_name="my.custom.schema", schema=CUSTOM_SCHEMA)

    def on_shutdown(self):
        get_telemetry_manager().unregister_schema(schema_name="my.custom.schema")

    def do_work(self):
        start = time.perf_counter()
        try:
            result = self._perform_operation()
            duration_ms = (time.perf_counter() - start) * 1000.0
            emit_feature_used(
                extension_id="isaacsim.my.extension",
                feature_name="do_work",
                feature_type="command",
                duration_ms=duration_ms,
            )

            # Send domain-specific event
            get_telemetry_manager().send_event(
                schema_name="my.custom.schema", event_name="operationResult", data={"success": True}
            )
        except Exception:
            emit_error(
                extension_id="isaacsim.my.extension",
                error_category="runtime_error",
                error_type="operation_failed",
                operation="do_work",
            )
```
