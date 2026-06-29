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

"""Thin wrappers around isaacsim_send.py for Remote tier integration tests.

Also owns the optional autostart path: when no python_server is reachable the
remote tier launches its own headless Isaac Sim (``isaacsim.code_editor.python_server``)
for the test session and tears it down afterwards. See :func:`ensure_server`.
"""

from __future__ import annotations

import asyncio
import contextlib
import functools
import os
import signal
import socket
import subprocess
import sys
import tempfile
import time

from _util import REPO_ROOT, load_module_from_path, skill_path

_IS_WINDOWS = sys.platform.startswith("win")

SERVER_REMEDIATION = (
    "Isaac Sim python_server not reachable at {host}:{port}.\n"
    "  The remote tier auto-launches a headless server when an Isaac Sim build is\n"
    "  present; this failure means no build was found or it did not come up in time.\n"
    "  Build the repo, or launch one manually and wait for 'app ready':\n"
    "    bash _build/linux-x86_64/release/isaac-sim.sh --no-window --no-ros-env \\\n"
    "         --enable isaacsim.code_editor.python_server\n"
    "  (TCP server listens on 127.0.0.1:8226; override with ISAACSIM_HOST / ISAACSIM_PORT;\n"
    "   disable autostart with ISAACSIM_AUTOSTART=0)."
)


@functools.lru_cache(maxsize=1)
def _send_mod():
    return load_module_from_path(skill_path("isaac-sim-remote", "scripts", "isaacsim_send.py"))


def server_reachable(server, timeout: float = 1.0) -> bool:
    host, port = server
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


_SCENE_READY: set = set()


def ensure_scene(server) -> None:
    """Idempotently set up the shared test scene (stage + cube + capture ext)."""
    if server in _SCENE_READY:
        return
    from _manifest import CUBE

    r = send_script(server, "isaac-sim-remote/scripts/open_stage.py", ["action=new"])
    assert r.get("status") == "ok", r
    code = (
        "import omni.usd\n"
        "from pxr import UsdGeom\n"
        "import omni.kit.app\n"
        "omni.kit.app.get_app().get_extension_manager()"
        ".set_extension_enabled_immediate('isaacsim.test.utils', True)\n"
        "stage = omni.usd.get_context().get_stage()\n"
        "UsdGeom.Xform.Define(stage, '/World')\n"
        f"UsdGeom.Cube.Define(stage, '{CUBE}')\n"
        f"print('SCENE_READY', stage.GetPrimAtPath('{CUBE}').IsValid())\n"
    )
    r = send_code(server, code)
    assert r.get("status") == "ok" and "SCENE_READY True" in r.get("output", ""), r
    _SCENE_READY.add(server)


def send_code(server, code: str, timeout: float = 60.0) -> dict:
    """Send raw Python to the python_server, return the parsed JSON response."""
    host, port = server
    mod = _send_mod()
    return asyncio.run(mod.send_and_receive(host, port, code, timeout))


def send_script(server, relpath: str, args=None, timeout: float = 180.0) -> dict:
    """Send a skill script file (wrapped in an isolated async scope) with injected args.

    relpath is relative to skills/, e.g. "isaac-sim-remote/scripts/health_check.py".
    args is a list of "key=value" strings, matching isaacsim_send.py --arg.
    """
    host, port = server
    mod = _send_mod()
    src = open(skill_path(*relpath.split("/")), encoding="utf-8").read()
    source = mod._wrap_isolated(src, list(args or []))
    return asyncio.run(mod.send_and_receive(host, port, source, timeout))


# ---------------------------------------------------------------------------
# Autostart: launch a headless python_server when none is reachable
# ---------------------------------------------------------------------------


def isaac_launcher() -> str | None:
    """Path to the built Isaac Sim app launcher (``isaac-sim.sh`` / ``isaac-sim.bat``), or None.

    Honors ``ISAAC_SIM_DIR`` first, then falls back to the in-repo build output.
    """
    candidates = []
    env_dir = os.environ.get("ISAAC_SIM_DIR")
    if env_dir:
        candidates += [os.path.join(env_dir, "isaac-sim.sh"), os.path.join(env_dir, "isaac-sim.bat")]
    candidates += [
        os.path.join(REPO_ROOT, "_build", "linux-x86_64", "release", "isaac-sim.sh"),
        os.path.join(REPO_ROOT, "_build", "windows-x86_64", "release", "isaac-sim.bat"),
    ]
    return next((c for c in candidates if os.path.isfile(c)), None)


def autostart_enabled() -> bool:
    """Whether the remote tier may launch its own server (default on; ISAACSIM_AUTOSTART=0 to disable)."""
    return os.environ.get("ISAACSIM_AUTOSTART", "1") != "0"


def _terminate(proc: subprocess.Popen, timeout: float = 20.0) -> None:
    """Terminate a launched process group (SIGTERM, then SIGKILL on timeout)."""
    if proc is None or proc.poll() is not None:
        return
    with contextlib.suppress(ProcessLookupError, OSError):
        if _IS_WINDOWS:
            proc.terminate()
        else:
            os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
    try:
        proc.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        with contextlib.suppress(ProcessLookupError, OSError):
            if _IS_WINDOWS:
                proc.kill()
            else:
                os.killpg(os.getpgid(proc.pid), signal.SIGKILL)


class LocalServerHandle:
    """Handle to a python_server subprocess started by the test-suite."""

    def __init__(self, proc: subprocess.Popen, log_path: str, log_fh=None) -> None:
        self.proc = proc
        self.log_path = log_path
        self._log_fh = log_fh

    def stop(self, timeout: float = 20.0) -> None:
        """Stop the launched server and close its log file."""
        _terminate(self.proc, timeout)
        if self._log_fh is not None:
            with contextlib.suppress(Exception):
                self._log_fh.close()


def _responsive(server, timeout: float = 5.0) -> bool:
    """True when the server accepts a connection and executes a trivial print."""
    try:
        resp = send_code(server, "print('AUTOSTART_PROBE')", timeout=timeout)
    except Exception:
        return False
    return resp.get("status") == "ok" and "AUTOSTART_PROBE" in resp.get("output", "")


def ensure_server(server, *, startup_timeout: float = 300.0) -> LocalServerHandle | None:
    """Make ``server`` reachable, launching a local headless python_server if needed.

    Returns a :class:`LocalServerHandle` (the caller must call ``.stop()`` at
    teardown) when a server was launched here. Returns ``None`` when nothing was
    started: the server was already reachable (e.g. CI or a manually launched
    instance -- left running), autostart is disabled (``ISAACSIM_AUTOSTART=0``),
    or no Isaac Sim build is present. If a process is launched but never becomes
    responsive within ``startup_timeout``, the handle is still returned (so it is
    cleaned up) and diagnostics are printed; the per-test reachability check then
    fails with remediation.

    Args:
        server: ``(host, port)`` of the target python_server.
        startup_timeout: Seconds to wait for the launched server to respond.

    Returns:
        A handle to the launched process, or None when nothing was started.
    """
    if server_reachable(server):
        return None
    if not autostart_enabled():
        return None
    launcher = isaac_launcher()
    if launcher is None:
        return None

    host, port = server
    log_path = os.path.join(tempfile.gettempdir(), f"skills_remote_python_server_{port}.log")
    cmd = (["bash", launcher] if launcher.endswith(".sh") else [launcher]) + [
        "--no-window",
        "--no-ros-env",
        "--enable",
        "isaacsim.code_editor.python_server",
        f"--/exts/isaacsim.code_editor.python_server/host={host}",
        f"--/exts/isaacsim.code_editor.python_server/port={port}",
    ]
    print(f"[remote] no server at {host}:{port}; launching headless Isaac Sim (log: {log_path})", flush=True)

    popen_kwargs: dict = {"cwd": os.path.dirname(launcher)}
    if _IS_WINDOWS:
        popen_kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP  # type: ignore[attr-defined]
    else:
        popen_kwargs["start_new_session"] = True

    log_fh = open(log_path, "w", encoding="utf-8")  # noqa: SIM115 -- closed by LocalServerHandle.stop()
    proc = subprocess.Popen(cmd, stdout=log_fh, stderr=subprocess.STDOUT, **popen_kwargs)
    handle = LocalServerHandle(proc, log_path, log_fh)

    deadline = time.time() + startup_timeout
    while time.time() < deadline:
        if proc.poll() is not None:
            print(f"[remote] Isaac Sim exited early (code {proc.returncode}); see {log_path}", flush=True)
            return handle
        if server_reachable(server, timeout=2.0) and _responsive(server):
            print(f"[remote] python_server ready at {host}:{port}", flush=True)
            return handle
        time.sleep(3.0)

    print(f"[remote] python_server not ready within {startup_timeout:.0f}s; see {log_path}", flush=True)
    return handle
