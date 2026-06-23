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

"""Discover the python_server loopback port.

Tells the embedded agent the *actual* port the
``isaacsim.code_editor.python_server`` socket listens on rather than assuming
the 8226 default (a co-resident Kit instance may have moved it). Pure module:
takes a settings-like object exposing ``get(path)`` so it can be unit-tested
with a fake.
"""

from __future__ import annotations

from typing import Protocol

PORT_SETTING = "/exts/isaacsim.code_editor.python_server/port"
DEFAULT_PORT = 8226


class _SettingsLike(Protocol):
    # Duck-typed view of the carb settings store; keeps this module Kit-free and
    # lets tests pass a fake. Underscore-private so it is not part of the API.
    def get(self, path: str) -> object: ...


def get_python_server_port(settings: _SettingsLike) -> int:
    """Return the configured python_server port, or :data:`DEFAULT_PORT`.

    Falls back to the default when the setting is unset, ``None``, or not
    coercible to ``int``.

    Args:
        settings: A settings-like object exposing ``get(path)`` (e.g. the carb
            settings store, or a fake in tests).

    Returns:
        The configured port, or :data:`DEFAULT_PORT` on any failure.
    """
    try:
        value = settings.get(PORT_SETTING)
    except Exception:  # noqa: BLE001 - a misbehaving settings backend must not break startup
        return DEFAULT_PORT
    if value is None:
        return DEFAULT_PORT
    try:
        return int(value)
    except (TypeError, ValueError):
        return DEFAULT_PORT
