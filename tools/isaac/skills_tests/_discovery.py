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

"""Auto-discovery + classification of skill scripts and snippets.

The test-suite is driven by this module: every script and every fenced snippet
under skills/ is found here and handed to a generic, kind-specific executor.
Adding a new script or snippet requires no new test code.

Script kinds
------------
- shell       : *.sh                              -> bash -n (+ optional run)
- batch       : *.bat                             -> structural check (no Linux exec)
- standalone  : has `SimulationApp(`              -> run via Isaac python launcher
- client      : isaacsim_send.py                  -> import + --help
- remote      : isaac-sim-remote/scripts/*.py     -> send to python_server
- library_sim : imports omni/pxr/... at top level -> needs stubbing (special test)
- pure        : everything else (stdlib/numpy)    -> import (+ --help)
"""

from __future__ import annotations

import re
from pathlib import Path

from _util import SKILLS_DIR

ROOT = Path(SKILLS_DIR)

_TOP_LEVEL_SIM_IMPORT = re.compile(r"^(?:import|from)\s+(omni|pxr|isaacsim|carb|usdrt|warp)\b", re.MULTILINE)


def rel(path: Path | str) -> str:
    return str(Path(path).relative_to(ROOT))


def all_script_paths() -> list[Path]:
    """Every shippable script under skills/ (.py, .sh, .bat), sorted."""
    paths: list[Path] = []
    for pattern in ("*.py", "*.sh", "*.bat"):
        paths.extend(ROOT.rglob(pattern))
    return sorted(paths)


def classify(path: Path) -> str:
    suffix = path.suffix
    if suffix == ".sh":
        return "shell"
    if suffix == ".bat":
        return "batch"
    text = path.read_text(encoding="utf-8", errors="replace")
    if "SimulationApp(" in text or "from isaacsim import SimulationApp" in text:
        return "standalone"
    if path.name == "isaacsim_send.py":
        return "client"
    if rel(path).startswith("isaac-sim-remote/scripts/"):
        return "remote"
    if _TOP_LEVEL_SIM_IMPORT.search(text):
        return "library_sim"
    return "pure"


def scripts_of_kind(*kinds: str) -> list[str]:
    """Relative paths of all scripts whose classification is in kinds."""
    wanted = set(kinds)
    return [rel(p) for p in all_script_paths() if classify(p) in wanted]


def classification_summary() -> dict[str, list[str]]:
    summary: dict[str, list[str]] = {}
    for p in all_script_paths():
        summary.setdefault(classify(p), []).append(rel(p))
    return summary
