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

"""Unit tier: isaacsim_send.py client logic (pure stdlib, no Isaac Sim)."""

from __future__ import annotations

import asyncio
import json
import subprocess
import sys
import threading
import types

import pytest
from _util import load_module_from_path, skill_path

pytestmark = pytest.mark.unit

SEND_PY = skill_path("isaac-sim-remote", "scripts", "isaacsim_send.py")


@pytest.fixture(scope="module")
def mod():
    return load_module_from_path(SEND_PY)


# --------------------------------------------------------------------------- #
# arg injection / type inference
# --------------------------------------------------------------------------- #
def test_inject_args_typed(mod):
    out = mod._inject_args("print(x)", ["x=42"])
    assert out == "x = 42\nprint(x)"


def test_inject_args_string_fallback(mod):
    out = mod._inject_args("print(name)", ["name=hello"])
    assert out.startswith('name = "hello"\n')


def test_inject_args_empty_is_noop(mod):
    assert mod._inject_args("print(1)", []) == "print(1)"


def test_parse_args_kv_type_inference(mod):
    assert mod._parse_args_kv(["x=42", "y=foo", "z=[1, 2]"]) == {"x": 42, "y": "foo", "z": [1, 2]}


# --------------------------------------------------------------------------- #
# isolated-scope wrapper
# --------------------------------------------------------------------------- #
def test_wrap_isolated_structure(mod):
    wrapped = mod._wrap_isolated("await foo()\nprint(1)", ["n=3"])
    assert wrapped.startswith("async def _isolated_script():")
    assert "    n = 3" in wrapped
    assert "    await foo()" in wrapped
    assert wrapped.rstrip().endswith("await _isolated_script()")


def test_wrap_isolated_compiles_with_top_level_await(mod):
    import ast

    wrapped = mod._wrap_isolated("x = 1\nawait something()", [])
    # The wrapper ends with a top-level `await _isolated_script()`, so it is only
    # valid under the server's async-exec flag (PyCF_ALLOW_TOP_LEVEL_AWAIT).
    with pytest.raises(SyntaxError):
        compile(wrapped, "<wrapped>", "exec")
    compile(wrapped, "<wrapped>", "exec", flags=ast.PyCF_ALLOW_TOP_LEVEL_AWAIT)


# --------------------------------------------------------------------------- #
# envelope detection
# --------------------------------------------------------------------------- #
def _ns(**over):
    base = dict(
        json_envelope=False,
        context=None,
        fire_and_forget=False,
        execution_timeout=None,
        args_json=None,
        introspect=None,
    )
    base.update(over)
    return types.SimpleNamespace(**base)


def test_needs_envelope_false_by_default(mod):
    assert mod._needs_envelope(_ns()) is False


@pytest.mark.parametrize(
    "over",
    [
        {"context": "s"},
        {"fire_and_forget": True},
        {"execution_timeout": 0},
        {"args_json": "{}"},
        {"introspect": "status"},
        {"json_envelope": True},
    ],
)
def test_needs_envelope_true(mod, over):
    assert mod._needs_envelope(_ns(**over)) is True


# --------------------------------------------------------------------------- #
# wire protocol against an in-process mock server
# --------------------------------------------------------------------------- #
def test_send_and_receive_roundtrip(mod):
    async def run():
        async def handler(reader, writer):
            data = await reader.read()
            writer.write(json.dumps({"status": "ok", "echo": data.decode()}).encode())
            writer.write_eof()
            await writer.drain()
            writer.close()

        server = await asyncio.start_server(handler, "127.0.0.1", 0)
        port = server.sockets[0].getsockname()[1]
        async with server:
            return await mod.send_and_receive("127.0.0.1", port, "payload-123", timeout=5)

    resp = asyncio.run(run())
    assert resp["status"] == "ok"
    assert resp["echo"] == "payload-123"


# --------------------------------------------------------------------------- #
# full CLI against a threaded mock server
# --------------------------------------------------------------------------- #
@pytest.fixture
def mock_server():
    state = {"requests": [], "response": {"status": "ok", "output": "hi\n", "result": None}}
    holder = {}
    ready = threading.Event()

    def run():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        async def handler(reader, writer):
            data = await reader.read()
            state["requests"].append(data.decode())
            writer.write(json.dumps(state["response"]).encode())
            writer.write_eof()
            await writer.drain()
            writer.close()

        server = loop.run_until_complete(asyncio.start_server(handler, "127.0.0.1", 0))
        holder["port"] = server.sockets[0].getsockname()[1]
        holder["loop"] = loop
        ready.set()
        loop.run_forever()
        server.close()
        loop.run_until_complete(server.wait_closed())
        loop.close()

    t = threading.Thread(target=run, daemon=True)
    t.start()
    assert ready.wait(5), "mock server did not start"
    yield ("127.0.0.1", holder["port"], state)
    holder["loop"].call_soon_threadsafe(holder["loop"].stop)
    t.join(timeout=5)


def _run_cli(args, timeout=30):
    return subprocess.run([sys.executable, SEND_PY, *args], capture_output=True, text=True, timeout=timeout)


def test_cli_help_exit_zero():
    r = _run_cli(["--help"])
    assert r.returncode == 0
    assert "isaac" in (r.stdout + r.stderr).lower()


def test_cli_raw_python_ok(mock_server):
    host, port, state = mock_server
    r = _run_cli(["--host", host, "--port", str(port), 'print("hi")'])
    assert r.returncode == 0
    assert "hi" in r.stdout
    # raw code path => the request is the bare source, not a JSON envelope
    assert state["requests"][-1].strip() == 'print("hi")'


def test_cli_error_status_exit_one(mock_server):
    host, port, state = mock_server
    state["response"] = {"status": "error", "ename": "ValueError", "evalue": "boom", "traceback": []}
    r = _run_cli(["--host", host, "--port", str(port), "raise ValueError"])
    assert r.returncode == 1
    assert "boom" in r.stderr


def test_cli_context_builds_envelope(mock_server):
    host, port, state = mock_server
    r = _run_cli(["--host", host, "--port", str(port), "--context", "sess", "x = 1"])
    assert r.returncode == 0
    env = json.loads(state["requests"][-1])
    assert env["context"] == "sess"
    assert env["code"] == "x = 1"


def test_cli_introspect_builds_query(mock_server):
    host, port, state = mock_server
    state["response"] = {"status": "ok", "result": {"running": True}}
    r = _run_cli(["--host", host, "--port", str(port), "--introspect", "status"])
    assert r.returncode == 0
    assert json.loads(state["requests"][-1]) == {"introspect": "status"}


def test_cli_connection_refused_exit_one():
    # Bind then release a port to obtain one that is (almost certainly) closed.
    import socket

    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    r = _run_cli(["--host", "127.0.0.1", "--port", str(port), "print(1)"])
    assert r.returncode == 1
    assert "cannot connect" in r.stderr.lower()
