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

"""Unit tier (generic): every pure / client script, auto-discovered.

Imports each discovered pure-Python script (proving it loads with no Isaac Sim
runtime) and runs `--help` for those that expose an argparse CLI. Deep behavioral
assertions for specific modules live alongside in test_spatial / test_compare_*
/ test_isaacsim_send.
"""

from __future__ import annotations

import subprocess
import sys

import pytest
from _discovery import scripts_of_kind
from _manifest import PURE_HELP
from _util import load_module_from_path, skill_path

pytestmark = [pytest.mark.unit]

_PURE = scripts_of_kind("pure", "client")


@pytest.mark.parametrize("relp", _PURE, ids=[r.split("/")[-1] for r in _PURE])
def test_pure_script_imports(relp):
    path = skill_path(*relp.split("/"))
    try:
        load_module_from_path(path)
    except ModuleNotFoundError as exc:
        pytest.fail(
            f"{relp}: import failed -- missing dependency '{exc.name}'.\n  To enable this test: pip install {exc.name}",
            pytrace=False,
        )


@pytest.mark.parametrize("relp", [r for r in _PURE if PURE_HELP.get(r)], ids=lambda r: r.split("/")[-1])
def test_pure_script_help(relp):
    result = subprocess.run(
        [sys.executable, skill_path(*relp.split("/")), "--help"],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
