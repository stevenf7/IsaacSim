# SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Centralized telemetry framework for Isaac Sim extensions.

Provides :class:`TelemetryManager` for registering custom structured-log schemas
and emitting events, plus module-level convenience helpers for the common Isaac Sim
telemetry events (extension activation, feature usage, errors).
"""

from __future__ import annotations

import carb
import omni.structuredlog

from .schema import COMMON_SCHEMA_NAME, ISAACSIM_COMMON_SCHEMA


class TelemetryManager:
    """Singleton that manages structured-log schema registration and event emission.

    On first access the common Isaac Sim schema is automatically registered so
    that the typed helper functions (:func:`emit_extension_activated`,
    :func:`emit_feature_used`, :func:`emit_error`) work without any setup.

    Extensions that need domain-specific telemetry can register additional schemas
    via :meth:`register_schema` and emit events via :meth:`send_event`.
    """

    _instance: TelemetryManager | None = None
    #: Singleton instance.

    _schemas: dict[str, dict]
    #: Mapping of schema name to event-handle dict returned by ``omni.structuredlog``.

    def __init__(self) -> None:
        self._schemas = {}
        self._register_common_schema()

    @classmethod
    def get_instance(cls) -> TelemetryManager:
        """Return the singleton instance, creating it on first call.

        Returns:
            The global `TelemetryManager` instance.

        Example:

        .. code-block:: python

            from isaacsim.core.telemetry import TelemetryManager

            manager = TelemetryManager.get_instance()
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def is_enabled(self) -> bool:
        """Check whether structured logging is enabled.

        Returns:
            True if the ``/structuredLog/enable`` carb setting is truthy.

        Example:

        .. code-block:: python

            manager = TelemetryManager.get_instance()
            if manager.is_enabled():
                print("Telemetry is active")
        """
        settings = carb.settings.get_settings()
        return bool(settings.get("/structuredLog/enable"))

    def register_schema(self, schema_name: str, schema: dict) -> dict | None:
        """Register a baked JSON schema with the structured-log system.

        The *schema* dict must follow the Carbonite baked JSON Schema draft-07
        format (with ``schemaMeta``, ``definitions/events``, ``$schema``,
        ``anyOf``).  See the Carbonite structured-log walkthrough for details.

        Args:
            schema_name: Unique key for later lookups (e.g. the schema's
                ``clientName``).
            schema: Baked JSON schema dict passed directly to
                ``omni.structuredlog.register_schema()``.

        Returns:
            Dict mapping short event names to event handles, or None if
            registration failed or telemetry is disabled.

        Example:

        .. code-block:: python

            from isaacsim.core.telemetry import get_telemetry_manager

            events = get_telemetry_manager().register_schema("my.schema", my_schema_dict)
        """
        if not self.is_enabled():
            carb.log_info(f"Telemetry disabled; skipping schema registration for {schema_name}")
            return None
        if schema_name in self._schemas:
            carb.log_info(f"Schema {schema_name} already registered")
            return self._schemas[schema_name]
        try:
            events = omni.structuredlog.register_schema(schema)
            self._schemas[schema_name] = events
            carb.log_info(f"Registered telemetry schema {schema_name} with events: {list(events.keys())}")
            return events
        except Exception as exc:
            carb.log_warn(f"Failed to register telemetry schema {schema_name}: {exc}")
            return None

    def send_event(self, schema_name: str, event_name: str, data: dict) -> bool:
        """Emit a structured-log event.

        Args:
            schema_name: Key used during :meth:`register_schema`.
            event_name: Short event name within the schema.
            data: Dict of event properties matching the schema definition.

        Returns:
            True if the event was sent, False otherwise.

        Example:

        .. code-block:: python

            from isaacsim.core.telemetry import get_telemetry_manager

            get_telemetry_manager().send_event(
                "my.schema", "myEvent", {"key": "value"}
            )
        """
        if not self.is_enabled():
            return False
        events = self._schemas.get(schema_name)
        if events is None:
            carb.log_warn(f"Schema {schema_name} is not registered; cannot send event {event_name}")
            return False
        event_handle = events.get(event_name)
        if event_handle is None:
            carb.log_warn(f"Event {event_name} not found in schema {schema_name}")
            return False
        try:
            omni.structuredlog.send_event(event_handle, data)
            return True
        except Exception as exc:
            carb.log_warn(f"Failed to send telemetry event {schema_name}/{event_name}: {exc}")
            return False

    def unregister_schema(self, schema_name: str) -> None:
        """Remove a previously registered schema from tracking.

        This does not unregister the schema from the Carbonite structured-log
        system (schemas remain registered for the process lifetime), but it
        prevents further events from being sent through this manager for the
        given *schema_name*.

        Args:
            schema_name: Key used during :meth:`register_schema`.

        Example:

        .. code-block:: python

            from isaacsim.core.telemetry import get_telemetry_manager

            get_telemetry_manager().unregister_schema("my.schema")
        """
        if self._schemas.pop(schema_name, None) is not None:
            carb.log_info(f"Unregistered telemetry schema {schema_name}")

    def _register_common_schema(self) -> None:
        """Register the built-in Isaac Sim common telemetry schema."""
        self.register_schema(COMMON_SCHEMA_NAME, ISAACSIM_COMMON_SCHEMA)


def get_telemetry_manager() -> TelemetryManager:
    """Return the global :class:`TelemetryManager` singleton.

    Returns:
        The shared `TelemetryManager` instance.

    Example:

    .. code-block:: python

        from isaacsim.core.telemetry import get_telemetry_manager

        manager = get_telemetry_manager()
        manager.send_event("my.schema", "myEvent", {"key": "value"})
    """
    return TelemetryManager.get_instance()


# ---------------------------------------------------------------------------
# Typed helper functions for the common Isaac Sim telemetry schema
# ---------------------------------------------------------------------------


def emit_extension_activated(extension_id: str, extension_version: str, action: str) -> bool:
    """Emit an ``extensionActivated`` event.

    Args:
        extension_id: Extension identifier (e.g. ``"isaacsim.sensors.rtx"``).
        extension_version: Semantic version string (e.g. ``"1.2.0"``).
        action: ``"enabled"`` or ``"disabled"``.

    Returns:
        True if the event was sent successfully.

    Example:

    .. code-block:: python

        from isaacsim.core.telemetry import emit_extension_activated

        emit_extension_activated("isaacsim.sensors.rtx", "1.2.0", "enabled")
    """
    return get_telemetry_manager().send_event(
        COMMON_SCHEMA_NAME,
        "extensionActivated",
        {
            "extensionId": extension_id,
            "extensionVersion": extension_version,
            "action": action,
        },
    )


def emit_feature_used(
    extension_id: str,
    feature_name: str,
    feature_type: str,
    duration_ms: float = 0.0,
) -> bool:
    """Emit a ``featureUsed`` event.

    Args:
        extension_id: Extension that owns the feature.
        feature_name: Short identifier (e.g. ``"import_urdf"``).
        feature_type: One of ``"command"``, ``"menu_item"``, or ``"api_call"``.
        duration_ms: Wall-clock duration in milliseconds.

    Returns:
        True if the event was sent successfully.

    Example:

    .. code-block:: python

        from isaacsim.core.telemetry import emit_feature_used

        emit_feature_used("isaacsim.asset.importer.urdf", "import_urdf", "command", duration_ms=1234.5)
    """
    return get_telemetry_manager().send_event(
        COMMON_SCHEMA_NAME,
        "featureUsed",
        {
            "extensionId": extension_id,
            "featureName": feature_name,
            "featureType": feature_type,
            "durationMs": duration_ms,
        },
    )


def emit_error(
    extension_id: str,
    error_type: str,
    error_message: str,
    context: str = "",
) -> bool:
    """Emit an ``errorOccurred`` event.

    Args:
        extension_id: Extension where the error occurred.
        error_type: Classification (e.g. ``"import_failure"``).
        error_message: Human-readable description.
        context: Optional JSON-encoded extra detail for diagnostics.

    Returns:
        True if the event was sent successfully.

    Example:

    .. code-block:: python

        from isaacsim.core.telemetry import emit_error

        emit_error(
            "isaacsim.asset.importer.urdf",
            "import_failure",
            "Joint parsing failed",
            '{"file": "robot.urdf", "stage": "joint_parsing"}',
        )
    """
    return get_telemetry_manager().send_event(
        COMMON_SCHEMA_NAME,
        "errorOccurred",
        {
            "extensionId": extension_id,
            "errorType": error_type,
            "errorMessage": error_message,
            "context": context,
        },
    )
