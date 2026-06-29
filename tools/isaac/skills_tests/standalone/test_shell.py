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

"""Standalone tier (generic): every shell script, auto-discovered.

`bash -n` syntax for all shells lives in the static tier. Here we additionally
*run* the shells that declare a safe invocation in the manifest (e.g. usage /
guard paths). Shells that would launch a long-running app/server are marked
no_run and covered by the static syntax check only.
"""

from __future__ import annotations

import os
import subprocess

import pytest
from _discovery import scripts_of_kind
from _manifest import SHELL
from _util import skill_path

pytestmark = [pytest.mark.standalone]

_SHELL = scripts_of_kind("shell")


@pytest.mark.parametrize("relp", _SHELL, ids=[r.split("/")[-1] for r in _SHELL])
def test_shell_script(relp):
    spec = SHELL.get(relp)
    if spec is None:
        pytest.fail(
            f"{relp}: no execution spec.\n"
            f"  To enable this test, add a SHELL['{relp}'] entry with args/assertions, "
            "mark it static_only=True with a reason, or point it at a bespoke test.",
            pytrace=False,
        )
    if spec.get("bespoke"):
        pytest.skip(f"covered by a dedicated test ({spec['bespoke']})")
    if spec.get("static_only"):
        pytest.skip(spec.get("reason", "static-only (bash -n in the static tier)"))

    env = dict(os.environ)
    for key in spec.get("env_unset", []):
        env.pop(key, None)

    result = subprocess.run(
        ["bash", skill_path(*relp.split("/")), *spec.get("args", [])],
        capture_output=True,
        text=True,
        timeout=spec.get("timeout", 60),
        env=env,
    )
    combined = result.stdout + result.stderr
    if spec.get("exit_nonzero"):
        assert result.returncode != 0, combined
    if spec.get("exit_zero"):
        assert result.returncode == 0, combined
    if spec.get("contains"):
        assert spec["contains"] in combined, combined
