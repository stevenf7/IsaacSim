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

"""Unit tests for python_server port discovery (pure, fake-settings driven)."""

import omni.kit.test
from isaacsim.util.agent.impl.port_discovery import DEFAULT_PORT, PORT_SETTING, get_python_server_port


class _FakeSettings:
    def __init__(self, mapping: dict) -> None:
        self._mapping = mapping

    def get(self, key: str) -> object:
        return self._mapping.get(key)


class _RaisingSettings:
    def get(self, key: str) -> object:
        raise RuntimeError("settings backend down")


class TestPortDiscovery(omni.kit.test.AsyncTestCase):
    """Port resolution and fallback behavior."""

    async def test_configured_port(self) -> None:
        """An int setting is returned as-is."""
        self.assertEqual(get_python_server_port(_FakeSettings({PORT_SETTING: 8231})), 8231)

    async def test_configured_port_as_string(self) -> None:
        """A numeric string setting is coerced to int."""
        self.assertEqual(get_python_server_port(_FakeSettings({PORT_SETTING: "8240"})), 8240)

    async def test_missing_returns_default(self) -> None:
        """An unset setting falls back to the default port."""
        self.assertEqual(get_python_server_port(_FakeSettings({})), DEFAULT_PORT)

    async def test_none_returns_default(self) -> None:
        """A ``None`` setting falls back to the default port."""
        self.assertEqual(get_python_server_port(_FakeSettings({PORT_SETTING: None})), DEFAULT_PORT)

    async def test_non_int_returns_default(self) -> None:
        """A non-coercible setting falls back to the default port."""
        self.assertEqual(get_python_server_port(_FakeSettings({PORT_SETTING: "not-a-port"})), DEFAULT_PORT)

    async def test_raising_backend_returns_default(self) -> None:
        """A settings backend that raises falls back to the default port."""
        self.assertEqual(get_python_server_port(_RaisingSettings()), DEFAULT_PORT)
