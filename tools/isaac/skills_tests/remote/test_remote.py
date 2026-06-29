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

"""Remote tier (generic): every isaac-sim-remote payload script, auto-discovered.

One parametrized test sends each discovered remote script to the python_server
(args come from the data manifest; unlisted scripts are smoke-tested with no
args). Adding a new remote script needs no test code -- only a manifest entry if
it requires args/scene/render.

The ``sim_server`` fixture (see conftest) makes the tier self-contained: when no
python_server is reachable it launches a headless Isaac Sim for the session and
tears it down afterwards (requires a build; disable with ISAACSIM_AUTOSTART=0).
"""

from __future__ import annotations

import os
import struct

import pytest
from _discovery import scripts_of_kind
from _manifest import REMOTE
from _remote import SERVER_REMEDIATION, ensure_scene, send_script, server_reachable

pytestmark = [pytest.mark.remote, pytest.mark.integration]

_REMOTE_SCRIPTS = scripts_of_kind("remote")


def _params():
    params = []
    for relp in _REMOTE_SCRIPTS:
        spec = REMOTE.get(relp, {})
        marks = [pytest.mark.gpu] if spec.get("render") else []
        params.append(pytest.param(relp, spec, marks=marks, id=relp.split("/")[-1]))
    return params


def _assert_png(path):
    assert os.path.exists(path), f"{path} was not written"
    data = open(path, "rb").read()
    assert data[:8] == b"\x89PNG\r\n\x1a\n", f"{path} is not a valid PNG"
    assert len(data) >= 1000, f"{path} suspiciously small ({len(data)} bytes)"
    assert data[12:16] == b"IHDR", f"{path} missing IHDR chunk"
    width, height = struct.unpack(">II", data[16:24])
    assert width > 0 and height > 0, f"{path} has invalid dimensions {width}x{height}"


def test_discovered_remote_scripts_nonempty():
    assert len(_REMOTE_SCRIPTS) >= 14, f"expected to discover the remote scripts, found {_REMOTE_SCRIPTS}"


@pytest.mark.parametrize("relp,spec", _params())
def test_remote_script(sim_server, relp, spec):
    if not server_reachable(sim_server):
        pytest.fail(SERVER_REMEDIATION.format(host=sim_server[0], port=sim_server[1]), pytrace=False)
    ensure_scene(sim_server)

    for artifact in (spec.get("png"), spec.get("file")):
        if artifact and os.path.exists(artifact):
            os.remove(artifact)

    resp = send_script(sim_server, relp, spec.get("args", []), timeout=spec.get("timeout", 180.0))
    assert (
        resp.get("status") == "ok"
    ), f"{relp}: server error {resp.get('ename')}: {resp.get('evalue')}\n{resp.get('output', '')}"
    output = resp.get("output", "")

    if spec.get("expect"):
        assert spec["expect"].lower() in output.lower(), f"{relp}: expected {spec['expect']!r} in:\n{output}"
    if spec.get("png"):
        _assert_png(spec["png"])
    if spec.get("file"):
        assert os.path.exists(spec["file"]) and os.path.getsize(spec["file"]) > 0, f"{relp}: {spec['file']} missing"
