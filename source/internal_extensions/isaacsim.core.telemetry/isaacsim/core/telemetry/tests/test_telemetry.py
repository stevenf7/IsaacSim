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

"""Tests for the isaacsim.core.telemetry extension."""

from __future__ import annotations

import omni.ext
import omni.kit.test
from isaacsim.core.telemetry import (
    TelemetryManager,
    emit_error,
    emit_extension_activated,
    emit_feature_used,
    get_telemetry_manager,
    telemetry,
    telemetry_error,
    telemetry_extension,
    telemetry_usage,
)
from isaacsim.core.telemetry.schema import COMMON_SCHEMA_NAME


class TestTelemetryManager(omni.kit.test.AsyncTestCase):
    """Test suite for TelemetryManager singleton and event emission."""

    async def setUp(self) -> None:
        """Set up test fixtures."""
        self.manager = get_telemetry_manager()

    async def tearDown(self) -> None:
        """Tear down test fixtures."""

    async def test_singleton_access(self) -> None:
        """Verify that get_telemetry_manager and get_instance return the same object."""
        manager_a = get_telemetry_manager()
        manager_b = TelemetryManager.get_instance()
        self.assertIs(manager_a, manager_b)

    async def test_is_enabled(self) -> None:
        """Verify that is_enabled returns a boolean."""
        result = self.manager.is_enabled()
        self.assertIsInstance(result, bool)

    async def test_common_schema_auto_registered(self) -> None:
        """Verify that the common schema is automatically registered."""
        self.assertIn(COMMON_SCHEMA_NAME, self.manager._schemas)

    async def test_emit_extension_activated(self) -> None:
        """Verify emit_extension_activated returns True when enabled, False otherwise."""
        result = emit_extension_activated(
            extension_id="isaacsim.test.extension", extension_version="1.0.0", action="enabled"
        )
        if self.manager.is_enabled():
            self.assertTrue(result)
        else:
            self.assertFalse(result)

    async def test_emit_feature_used_without_duration(self) -> None:
        """Verify emit_feature_used works without duration_ms."""
        result = emit_feature_used(
            extension_id="isaacsim.test.extension", feature_name="test_feature", feature_type="command"
        )
        if self.manager.is_enabled():
            self.assertTrue(result)
        else:
            self.assertFalse(result)

    async def test_emit_feature_used_with_duration(self) -> None:
        """Verify emit_feature_used works with duration_ms."""
        result = emit_feature_used(
            extension_id="isaacsim.test.extension",
            feature_name="test_feature",
            feature_type="api_call",
            duration_ms=42,
        )
        if self.manager.is_enabled():
            self.assertTrue(result)
        else:
            self.assertFalse(result)

    async def test_emit_error(self) -> None:
        """Verify emit_error sends an errorOccurred event."""
        result = emit_error(
            extension_id="isaacsim.test.extension",
            error_category="runtime_error",
            error_type="sensor_init_failed",
            operation="create_lidar_sensor",
            recoverable=True,
        )
        if self.manager.is_enabled():
            self.assertTrue(result)
        else:
            self.assertFalse(result)

    async def test_emit_error_non_recoverable(self) -> None:
        """Verify emit_error works with recoverable=False."""
        result = emit_error(
            extension_id="isaacsim.test.extension",
            error_category="import_failure",
            error_type="urdf_joint_parse",
            operation="import_urdf",
            recoverable=False,
        )
        if self.manager.is_enabled():
            self.assertTrue(result)
        else:
            self.assertFalse(result)

    async def test_send_event_unregistered_schema(self) -> None:
        """Verify send_event returns False for an unregistered schema."""
        result = self.manager.send_event(
            schema_name="nonexistent.schema", event_name="someEvent", data={"key": "value"}
        )
        self.assertFalse(result)

    async def test_register_custom_schema(self) -> None:
        """Verify registering a custom schema and sending events through it."""
        custom_schema = {
            "generated": "Test custom schema",
            "anyOf": [{"$ref": "#/definitions/events/com.nvidia.test.customEvent"}],
            "$schema": "http://json-schema.org/draft-07/schema#",
            "schemaMeta": {
                "clientName": "test.custom.schema",
                "schemaVersion": "1.0",
                "eventPrefix": "com.nvidia.test",
                "definitionVersion": "1.0",
                "omniverseFlags": ["fSchemaFlagAnonymizeEvents"],
                "description": "Test schema for unit tests.",
            },
            "definitions": {
                "events": {
                    "com.nvidia.test.customEvent": {
                        "eventMeta": {
                            "service": "telemetry",
                            "privacy": {"category": "usage", "description": "Test event"},
                            "omniverseFlags": [],
                        },
                        "type": "object",
                        "additionalProperties": False,
                        "required": ["testKey"],
                        "properties": {
                            "testKey": {"type": "string", "description": "A test property"},
                        },
                        "description": "A custom test event.",
                    },
                },
            },
            "description": "Test custom schema.",
        }

        schema_name = "test.custom.schema"
        events = self.manager.register_schema(schema_name=schema_name, schema=custom_schema)

        if self.manager.is_enabled():
            self.assertIsNotNone(events)
            self.assertIn("customEvent", events)

            result = self.manager.send_event(
                schema_name=schema_name, event_name="customEvent", data={"testKey": "hello"}
            )
            self.assertTrue(result)
        else:
            self.assertIsNone(events)

        self.manager.unregister_schema(schema_name=schema_name)

    async def test_unregister_schema(self) -> None:
        """Verify unregistering a schema removes it from the manager."""
        schema_name = "test.unregister.schema"
        self.manager._schemas[schema_name] = {"fakeEvent": 12345}
        self.assertIn(schema_name, self.manager._schemas)

        self.manager.unregister_schema(schema_name=schema_name)
        self.assertNotIn(schema_name, self.manager._schemas)

    async def test_unregister_nonexistent_schema(self) -> None:
        """Verify unregistering a nonexistent schema does not raise."""
        self.manager.unregister_schema(schema_name="does.not.exist")


class TestTelemetryDecorator(omni.kit.test.AsyncTestCase):
    """Test suite for the @telemetry decorator."""

    async def setUp(self) -> None:
        """Set up test fixtures."""
        self.manager = get_telemetry_manager()

    async def test_telemetry_sync_success(self) -> None:
        """Verify @telemetry decorated sync function runs and returns normally."""

        @telemetry(extension_id="isaacsim.test.extension", feature_name="test_op")
        def add(a: int, b: int) -> int:
            return a + b

        result = add(2, 3)
        self.assertEqual(result, 5)

    async def test_telemetry_sync_exception_reraises(self) -> None:
        """Verify @telemetry decorated sync function re-raises exceptions."""

        @telemetry(extension_id="isaacsim.test.extension", feature_name="test_op")
        def fail() -> None:
            raise ValueError("boom")

        with self.assertRaises(ValueError):
            fail()

    async def test_telemetry_async_success(self) -> None:
        """Verify @telemetry decorated async function runs and returns normally."""

        @telemetry(extension_id="isaacsim.test.extension", feature_name="test_async_op")
        async def async_add(a: int, b: int) -> int:
            return a + b

        result = await async_add(2, 3)
        self.assertEqual(result, 5)

    async def test_telemetry_async_exception_reraises(self) -> None:
        """Verify @telemetry decorated async function re-raises exceptions."""

        @telemetry(extension_id="isaacsim.test.extension", feature_name="test_async_op")
        async def async_fail() -> None:
            raise RuntimeError("boom")

        with self.assertRaises(RuntimeError):
            await async_fail()

    async def test_telemetry_preserves_function_name(self) -> None:
        """Verify functools.wraps preserves the original function metadata."""

        @telemetry(extension_id="isaacsim.test.extension", feature_name="test_op")
        def my_function() -> None:
            pass

        self.assertEqual(my_function.__name__, "my_function")


class TestTelemetryUsageDecorator(omni.kit.test.AsyncTestCase):
    """Test suite for the @telemetry_usage decorator."""

    async def test_usage_sync_success(self) -> None:
        """Verify @telemetry_usage decorated sync function returns normally."""

        @telemetry_usage(extension_id="isaacsim.test.extension", feature_name="test_op")
        def add(a: int, b: int) -> int:
            return a + b

        result = add(2, 3)
        self.assertEqual(result, 5)

    async def test_usage_sync_exception_reraises(self) -> None:
        """Verify @telemetry_usage still re-raises exceptions (no error event)."""

        @telemetry_usage(extension_id="isaacsim.test.extension", feature_name="test_op")
        def fail() -> None:
            raise ValueError("boom")

        with self.assertRaises(ValueError):
            fail()

    async def test_usage_async_success(self) -> None:
        """Verify @telemetry_usage decorated async function returns normally."""

        @telemetry_usage(extension_id="isaacsim.test.extension", feature_name="test_async_op")
        async def async_add(a: int, b: int) -> int:
            return a + b

        result = await async_add(2, 3)
        self.assertEqual(result, 5)

    async def test_usage_preserves_function_name(self) -> None:
        """Verify functools.wraps preserves the original function metadata."""

        @telemetry_usage(extension_id="isaacsim.test.extension", feature_name="test_op")
        def my_function() -> None:
            pass

        self.assertEqual(my_function.__name__, "my_function")


class TestTelemetryErrorDecorator(omni.kit.test.AsyncTestCase):
    """Test suite for the @telemetry_error decorator."""

    async def test_error_sync_success(self) -> None:
        """Verify @telemetry_error decorated sync function returns normally (no event)."""

        @telemetry_error(extension_id="isaacsim.test.extension", feature_name="test_op")
        def add(a: int, b: int) -> int:
            return a + b

        result = add(2, 3)
        self.assertEqual(result, 5)

    async def test_error_sync_exception_reraises(self) -> None:
        """Verify @telemetry_error re-raises exceptions after emitting error event."""

        @telemetry_error(extension_id="isaacsim.test.extension", feature_name="test_op")
        def fail() -> None:
            raise ValueError("boom")

        with self.assertRaises(ValueError):
            fail()

    async def test_error_async_exception_reraises(self) -> None:
        """Verify @telemetry_error re-raises async exceptions after emitting error event."""

        @telemetry_error(extension_id="isaacsim.test.extension", feature_name="test_async_op")
        async def async_fail() -> None:
            raise RuntimeError("boom")

        with self.assertRaises(RuntimeError):
            await async_fail()

    async def test_error_preserves_function_name(self) -> None:
        """Verify functools.wraps preserves the original function metadata."""

        @telemetry_error(extension_id="isaacsim.test.extension", feature_name="test_op")
        def my_function() -> None:
            pass

        self.assertEqual(my_function.__name__, "my_function")


class TestTelemetryExtensionDecorator(omni.kit.test.AsyncTestCase):
    """Test suite for the @telemetry_extension class decorator."""

    async def test_wraps_on_startup_with_ext_id(self) -> None:
        """Verify @telemetry_extension wraps on_startup that accepts ext_id."""

        @telemetry_extension
        class FakeExt(omni.ext.IExt):
            def on_startup(self, ext_id: str) -> None:
                self.started = True

            def on_shutdown(self) -> None:
                self.stopped = True

        ext = FakeExt()
        ext.on_startup("isaacsim.test.extension-2.3.4")
        self.assertTrue(ext.started)
        self.assertEqual(ext._telemetry_ext_name, "isaacsim.test.extension")
        self.assertEqual(ext._telemetry_ext_version, "2.3.4")

    async def test_wraps_on_startup_without_ext_id(self) -> None:
        """Verify @telemetry_extension wraps on_startup without ext_id."""

        @telemetry_extension
        class FakeExt(omni.ext.IExt):
            def on_startup(self) -> None:
                self.started = True

            def on_shutdown(self) -> None:
                self.stopped = True

        ext = FakeExt()
        ext.on_startup()
        self.assertTrue(ext.started)

    async def test_wraps_on_shutdown(self) -> None:
        """Verify @telemetry_extension wraps on_shutdown."""

        @telemetry_extension
        class FakeExt(omni.ext.IExt):
            def on_startup(self, ext_id: str) -> None:
                self.started = True

            def on_shutdown(self) -> None:
                self.stopped = True

        ext = FakeExt()
        ext.on_startup("isaacsim.test.extension-1.0.0")
        ext.on_shutdown()
        self.assertTrue(ext.stopped)

    async def test_ext_id_without_version(self) -> None:
        """Verify fallback version when ext_id has no dash."""

        @telemetry_extension
        class FakeExt(omni.ext.IExt):
            def on_startup(self, ext_id: str) -> None:
                pass

            def on_shutdown(self) -> None:
                pass

        ext = FakeExt()
        ext.on_startup("isaacsim.test.extension")
        self.assertEqual(ext._telemetry_ext_name, "isaacsim.test.extension")
        self.assertEqual(ext._telemetry_ext_version, "0.0.0")

    async def test_preserves_class_name(self) -> None:
        """Verify the decorator returns the same class."""

        @telemetry_extension
        class FakeExt(omni.ext.IExt):
            def on_startup(self, ext_id: str) -> None:
                pass

            def on_shutdown(self) -> None:
                pass

        self.assertEqual(FakeExt.__name__, "FakeExt")
