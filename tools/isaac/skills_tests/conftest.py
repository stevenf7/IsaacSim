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

"""Shared fixtures + path setup for the skills test-suite."""

from __future__ import annotations

import os
import socket
import sys

import pytest

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
if TESTS_DIR not in sys.path:
    sys.path.insert(0, TESTS_DIR)

ISAACSIM_HOST = os.environ.get("ISAACSIM_HOST", "127.0.0.1")
ISAACSIM_PORT = int(os.environ.get("ISAACSIM_PORT", "8226"))
ISAACSIM_STARTUP_TIMEOUT = float(os.environ.get("ISAACSIM_STARTUP_TIMEOUT", "300"))


def port_open(host: str, port: int, timeout: float = 1.0) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


@pytest.fixture(scope="session")
def sim_server():
    """(host, port) of the python_server, launching a local one when needed.

    If nothing is listening and autostart is enabled (default; disable with
    ISAACSIM_AUTOSTART=0), a headless Isaac Sim with
    ``isaacsim.code_editor.python_server`` is launched once for the session and
    torn down at the end. When a server is already reachable (e.g. CI or a
    manually launched instance) it is used as-is and left running. Reachability
    is still asserted per-test, so a genuinely missing prerequisite (no build)
    fails with remediation rather than silently skipping.
    """
    from _remote import ensure_server

    server = (ISAACSIM_HOST, ISAACSIM_PORT)
    handle = ensure_server(server, startup_timeout=ISAACSIM_STARTUP_TIMEOUT)
    try:
        yield server
    finally:
        if handle is not None:
            handle.stop()


@pytest.fixture(scope="session")
def send_module():
    """The isaacsim_send.py client module (pure stdlib; safe to import)."""
    from _util import load_module_from_path, skill_path

    return load_module_from_path(skill_path("isaac-sim-remote", "scripts", "isaacsim_send.py"))


@pytest.fixture(scope="session")
def isaac_python():
    """Path to a built Isaac Sim python launcher, or None if no build is present."""
    from _util import skill_path

    candidates = []
    if os.environ.get("ISAAC_SIM_DIR"):
        candidates.append(os.path.join(os.environ["ISAAC_SIM_DIR"], "python.sh"))
    candidates.append(skill_path("..", "_build", "linux-x86_64", "release", "python.sh"))
    candidates.append(skill_path("..", "_build", "windows-x86_64", "release", "python.bat"))
    return next((c for c in candidates if os.path.isfile(c)), None)
