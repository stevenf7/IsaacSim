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

"""Standalone tier: isaac-sim-validator/validate_sim.sh levels 1-2 (deterministic, headless).

Level 3 runtime execution of a real SimulationApp script is covered generically
by standalone/test_standalone.py running scripts through the Isaac python launcher.
"""

from __future__ import annotations

import subprocess

import pytest
from _util import skill_path

pytestmark = pytest.mark.standalone

VALIDATE = skill_path("isaac-sim-validator", "scripts", "validate_sim.sh")

GOOD = (
    "from isaacsim import SimulationApp\n"
    'simulation_app = SimulationApp({"headless": True})\n'
    "import isaacsim.core.experimental.utils.stage as stage_utils\n"
    "stage_utils.create_new_stage()\n"
    "simulation_app.close()\n"
)
WRONG_ORDER = (
    "from isaacsim import SimulationApp\n"
    "import isaacsim.core.experimental.utils.stage as s\n"
    'simulation_app = SimulationApp({"headless": True})\n'
    "simulation_app.close()\n"
)


def _run(*args, timeout=60):
    return subprocess.run(["bash", VALIDATE, *args], capture_output=True, text=True, timeout=timeout)


def test_usage_without_script():
    r = _run()
    assert r.returncode != 0
    assert "Usage" in (r.stdout + r.stderr)


def test_level1_passes_good_script(tmp_path):
    p = tmp_path / "good.py"
    p.write_text(GOOD)
    r = _run("--level", "1", str(p))
    assert r.returncode == 0, r.stdout + r.stderr
    assert "Errors: 0" in r.stdout


def test_level1_flags_syntax_error(tmp_path):
    p = tmp_path / "bad.py"
    p.write_text("def f(:\n    pass\n")
    r = _run("--level", "1", str(p))
    assert r.returncode != 0
    assert "Python syntax errors" in r.stdout


def test_level1_flags_missing_simulationapp(tmp_path):
    p = tmp_path / "plain.py"
    p.write_text("print('hi')\n")
    r = _run("--level", "1", str(p))
    assert r.returncode != 0
    assert "Missing 'from isaacsim import SimulationApp'" in r.stdout


def test_level2_passes_good_script(tmp_path):
    p = tmp_path / "good.py"
    p.write_text(GOOD)
    r = _run("--level", "2", str(p))
    assert r.returncode == 0, r.stdout + r.stderr
    assert "Errors: 0" in r.stdout


def test_level2_flags_wrong_import_order(tmp_path):
    p = tmp_path / "order.py"
    p.write_text(WRONG_ORDER)
    r = _run("--level", "2", str(p))
    assert r.returncode != 0
    assert "BEFORE" in r.stdout
