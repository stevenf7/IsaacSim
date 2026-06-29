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

"""Standalone tier (generic): every standalone SimulationApp script, auto-discovered.

Each discovered script is run end-to-end through the built Isaac python launcher
(args from the manifest; unlisted scripts run with no args). Skips when no build
is available, or with SKIP_HEAVY=1.
"""

from __future__ import annotations

import glob
import os
import subprocess

import pytest
from _discovery import scripts_of_kind
from _manifest import BUILD_REMEDIATION, STANDALONE
from _util import skill_path

pytestmark = [pytest.mark.standalone, pytest.mark.gpu]

_STANDALONE = scripts_of_kind("standalone")


@pytest.mark.parametrize("relp", _STANDALONE, ids=[r.split("/")[-1] for r in _STANDALONE])
def test_standalone_script(isaac_python, tmp_path, relp):
    if not isaac_python:
        pytest.fail(BUILD_REMEDIATION, pytrace=False)
    if os.environ.get("SKIP_HEAVY") == "1":
        pytest.skip("SKIP_HEAVY=1 (explicit opt-out of heavy GPU renders)")
    spec = STANDALONE.get(relp, {})
    script = skill_path(*relp.split("/"))
    out_dir = str(tmp_path / "out")
    run_args = [a.format(out=out_dir) for a in spec.get("run_args", [])]

    result = subprocess.run(
        [isaac_python, script, *run_args],
        capture_output=True,
        text=True,
        timeout=spec.get("timeout", 600),
    )
    combined = result.stdout + result.stderr
    assert "Traceback (most recent call last)" not in combined, combined[-3000:]
    assert "Item indexing is not supported" not in combined, combined[-3000:]
    assert result.returncode == 0, combined[-3000:]
    if spec.get("expect_glob"):
        hits = glob.glob(os.path.join(out_dir, "**", spec["expect_glob"]), recursive=True)
        assert hits, f"{relp}: no files matching {spec['expect_glob']} under {out_dir}"
