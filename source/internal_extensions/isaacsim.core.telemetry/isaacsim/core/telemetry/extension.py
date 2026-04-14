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

import asyncio
import functools
import inspect
import re
import time
from collections.abc import Callable
from typing import Any, TypeVar

import carb
import omni.structuredlog

from .schema import COMMON_SCHEMA_NAME, ISAACSIM_COMMON_SCHEMA

_T = TypeVar("_T")


def _to_snake_case(name: str) -> str:
    """Convert a PascalCase or camelCase name to snake_case."""
    s = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", name)
    s = re.sub(r"([a-z\d])([A-Z])", r"\1_\2", s)
    return s.lower()


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

            events = get_telemetry_manager().register_schema(schema_name="my.schema", schema=my_schema_dict)
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
                schema_name="my.schema", event_name="myEvent", data={"key": "value"}
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
        self.register_schema(schema_name=COMMON_SCHEMA_NAME, schema=ISAACSIM_COMMON_SCHEMA)


def get_telemetry_manager() -> TelemetryManager:
    """Return the global :class:`TelemetryManager` singleton.

    Returns:
        The shared `TelemetryManager` instance.

    Example:

    .. code-block:: python

        from isaacsim.core.telemetry import get_telemetry_manager

        manager = get_telemetry_manager()
            manager.send_event(schema_name="my.schema", event_name="myEvent", data={"key": "value"})
    """
    return TelemetryManager.get_instance()


# ---------------------------------------------------------------------------
# Typed helper functions for the common Isaac Sim telemetry schema
# ---------------------------------------------------------------------------


def emit_extension_activated(extension_id: str, extension_version: str, action: str) -> bool:
    """Emit an ``extensionActivated`` event.

    Args:
        extension_id: Extension identifier (e.g. ``"isaacsim.sensors.experimental.rtx"``).
        extension_version: Semantic version string (e.g. ``"1.2.0"``).
        action: ``"enabled"`` or ``"disabled"``.

    Returns:
        True if the event was sent successfully.

    Example:

    .. code-block:: python

        from isaacsim.core.telemetry import emit_extension_activated

        emit_extension_activated(
            extension_id="isaacsim.sensors.experimental.rtx", extension_version="1.2.0", action="enabled"
        )
    """
    return get_telemetry_manager().send_event(
        schema_name=COMMON_SCHEMA_NAME,
        event_name="extensionActivated",
        data={
            "extensionId": extension_id,
            "extensionVersion": extension_version,
            "action": action,
        },
    )


def emit_feature_used(
    extension_id: str,
    feature_name: str,
    feature_type: str,
    duration_ms: int = 0,
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

        emit_feature_used(
            extension_id="isaacsim.asset.importer.urdf",
            feature_name="import_urdf",
            feature_type="command",
            duration_ms=1234,
        )
    """
    return get_telemetry_manager().send_event(
        schema_name=COMMON_SCHEMA_NAME,
        event_name="featureUsed",
        data={
            "extensionId": extension_id,
            "featureName": feature_name,
            "featureType": feature_type,
            "durationMs": int(duration_ms),
        },
    )


def emit_error(
    extension_id: str,
    error_category: str,
    error_type: str,
    operation: str,
    recoverable: bool = True,
) -> bool:
    """Emit an ``errorOccurred`` event.

    All parameters are structured identifiers — no free-form text is accepted,
    which eliminates PII risk by design.

    Args:
        extension_id: Extension where the error occurred.
        error_category: Broad classification.  Must be one of
            ``"import_failure"``, ``"validation_error"``,
            ``"runtime_error"``, ``"configuration_error"``,
            ``"dependency_error"``, or ``"timeout"``.
        error_type: Extension-specific error code for drill-down
            (e.g. ``"urdf_joint_parse"``).
        operation: The feature/operation active when the error happened.
            Should match ``featureName`` values used in ``featureUsed`` events.
        recoverable: ``True`` if the operation could continue or degrade
            gracefully, ``False`` if it aborted.

    Returns:
        True if the event was sent successfully.

    Example:

    .. code-block:: python

        from isaacsim.core.telemetry import emit_error

        emit_error(
            "isaacsim.asset.importer.urdf",
            "import_failure",
            "urdf_joint_parse",
            "import_urdf",
            recoverable=False,
        )
    """
    return get_telemetry_manager().send_event(
        schema_name=COMMON_SCHEMA_NAME,
        event_name="errorOccurred",
        data={
            "extensionId": extension_id,
            "errorCategory": error_category,
            "errorType": error_type,
            "operation": operation,
            "recoverable": recoverable,
        },
    )


# ---------------------------------------------------------------------------
# Decorators
# ---------------------------------------------------------------------------


def _wrap_sync_and_async(
    func: Callable[..., Any],
    on_success: Callable[[int], None] | None,
    on_exception: Callable[[Exception], None] | None,
) -> Callable[..., Any]:
    """Build a sync or async wrapper that calls *on_success* / *on_exception*."""
    if asyncio.iscoroutinefunction(func):

        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            start = time.perf_counter()
            try:
                result = await func(*args, **kwargs)
            except Exception as exc:
                if on_exception is not None:
                    on_exception(exc)
                raise
            elapsed_ms = int((time.perf_counter() - start) * 1000)
            if on_success is not None:
                on_success(elapsed_ms)
            return result

        return async_wrapper

    @functools.wraps(func)
    def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
        start = time.perf_counter()
        try:
            result = func(*args, **kwargs)
        except Exception as exc:
            if on_exception is not None:
                on_exception(exc)
            raise
        elapsed_ms = int((time.perf_counter() - start) * 1000)
        if on_success is not None:
            on_success(elapsed_ms)
        return result

    return sync_wrapper


def telemetry(
    extension_id: str,
    feature_name: str,
    feature_type: str = "api_call",
    error_category: str = "runtime_error",
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator that instruments a function with full telemetry.

    On successful return a ``featureUsed`` event is emitted with the
    wall-clock duration.  If the function raises, an ``errorOccurred``
    event is emitted instead and the exception is re-raised unchanged.

    Works with both regular and ``async`` functions.

    Args:
        extension_id: Extension that owns the feature.
        feature_name: Short identifier (e.g. ``"import_urdf"``).
        feature_type: One of ``"command"``, ``"menu_item"``, or
            ``"api_call"``.
        error_category: Category used in the ``errorOccurred`` event if the
            function raises.

    Returns:
        A decorator that wraps the target function.

    Example:

    .. code-block:: python

        from isaacsim.core.telemetry import telemetry

        @telemetry(extension_id="isaacsim.sensors.experimental.rtx", feature_name="create_lidar_sensor")
        def create_lidar_sensor(prim_path, config):
            ...

        @telemetry(extension_id="isaacsim.asset.importer.urdf", feature_name="import_urdf", feature_type="command")
        async def import_urdf(file_path):
            ...
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        def on_success(elapsed_ms: int) -> None:
            emit_feature_used(
                extension_id=extension_id,
                feature_name=feature_name,
                feature_type=feature_type,
                duration_ms=elapsed_ms,
            )

        def on_exception(exc: Exception) -> None:
            error_type = _to_snake_case(type(exc).__name__)
            emit_error(
                extension_id=extension_id,
                error_category=error_category,
                error_type=error_type,
                operation=feature_name,
                recoverable=False,
            )

        return _wrap_sync_and_async(func=func, on_success=on_success, on_exception=on_exception)

    return decorator


def telemetry_usage(
    extension_id: str,
    feature_name: str,
    feature_type: str = "api_call",
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator that emits a ``featureUsed`` event on successful return.

    Exceptions are ignored (no ``errorOccurred`` event).  Use this for
    functions where errors are expected or handled elsewhere.

    Works with both regular and ``async`` functions.

    Args:
        extension_id: Extension that owns the feature.
        feature_name: Short identifier (e.g. ``"query_sensor"``).
        feature_type: One of ``"command"``, ``"menu_item"``, or
            ``"api_call"``.

    Returns:
        A decorator that wraps the target function.

    Example:

    .. code-block:: python

        from isaacsim.core.telemetry import telemetry_usage

        @telemetry_usage(extension_id="isaacsim.sensors.experimental.rtx", feature_name="query_sensor")
        def query_sensor(sensor_id):
            ...
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        def on_success(elapsed_ms: int) -> None:
            emit_feature_used(
                extension_id=extension_id,
                feature_name=feature_name,
                feature_type=feature_type,
                duration_ms=elapsed_ms,
            )

        return _wrap_sync_and_async(func=func, on_success=on_success, on_exception=None)

    return decorator


def telemetry_error(
    extension_id: str,
    feature_name: str,
    error_category: str = "runtime_error",
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator that emits an ``errorOccurred`` event when the function raises.

    No ``featureUsed`` event is emitted on success.  Use this for functions
    where you only care about failure tracking.

    Works with both regular and ``async`` functions.

    Args:
        extension_id: Extension where the error would occur.
        feature_name: Operation name used as the ``operation`` field in the
            error event.
        error_category: Broad error classification.

    Returns:
        A decorator that wraps the target function.

    Example:

    .. code-block:: python

        from isaacsim.core.telemetry import telemetry_error

        @telemetry_error(extension_id="isaacsim.app.setup", feature_name="app_startup")
        def initialize():
            ...
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        def on_exception(exc: Exception) -> None:
            error_type = _to_snake_case(type(exc).__name__)
            emit_error(
                extension_id=extension_id,
                error_category=error_category,
                error_type=error_type,
                operation=feature_name,
                recoverable=False,
            )

        return _wrap_sync_and_async(func=func, on_success=None, on_exception=on_exception)

    return decorator


def telemetry_extension(cls: type[_T]) -> type[_T]:
    """Class decorator that instruments an ``omni.ext.IExt`` subclass with lifecycle telemetry.

    Wraps ``on_startup`` and ``on_shutdown`` to automatically emit
    ``extensionActivated`` events with ``action="enabled"`` / ``"disabled"``.
    The extension name and version are parsed from the ``ext_id`` argument
    that Kit passes to ``on_startup`` (format ``"ext.name-X.Y.Z"``).

    Handles both ``on_startup(self, ext_id)`` and ``on_startup(self)``
    signatures — Kit inspects the method signature to decide whether to
    pass ``ext_id``.

    Args:
        cls: The ``IExt`` subclass to decorate.

    Returns:
        The same class with wrapped ``on_startup`` / ``on_shutdown``.

    Example:

    .. code-block:: python

        from isaacsim.core.telemetry import telemetry_extension

        @telemetry_extension
        class MyExtension(omni.ext.IExt):
            def on_startup(self, ext_id):
                ...

            def on_shutdown(self):
                ...
    """
    original_startup = getattr(cls, "on_startup", None)
    original_shutdown = getattr(cls, "on_shutdown", None)

    if original_startup is not None:
        sig = inspect.signature(original_startup)
        takes_ext_id = len(sig.parameters) > 1  # self + ext_id

        if takes_ext_id:

            @functools.wraps(original_startup)
            def wrapped_startup(self: Any, ext_id: str, *args: Any, **kwargs: Any) -> Any:
                result = original_startup(self, ext_id, *args, **kwargs)
                name, _, version = ext_id.partition("-")
                self._telemetry_ext_name = name
                self._telemetry_ext_version = version or "0.0.0"
                emit_extension_activated(
                    extension_id=name,
                    extension_version=self._telemetry_ext_version,
                    action="enabled",
                )
                return result

        else:

            @functools.wraps(original_startup)
            def wrapped_startup(self: Any) -> Any:
                result = original_startup(self)
                self._telemetry_ext_name = cls.__module__.split(".")[0] if cls.__module__ else "unknown"
                self._telemetry_ext_version = "0.0.0"
                emit_extension_activated(
                    extension_id=self._telemetry_ext_name,
                    extension_version=self._telemetry_ext_version,
                    action="enabled",
                )
                return result

        cls.on_startup = wrapped_startup

    if original_shutdown is not None:

        @functools.wraps(original_shutdown)
        def wrapped_shutdown(self: Any) -> None:
            name = getattr(self, "_telemetry_ext_name", "unknown")
            version = getattr(self, "_telemetry_ext_version", "0.0.0")
            emit_extension_activated(extension_id=name, extension_version=version, action="disabled")
            original_shutdown(self)

        cls.on_shutdown = wrapped_shutdown

    return cls
