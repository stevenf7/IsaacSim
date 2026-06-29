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

"""Static tier: static validation of every shipped script and skill snippet.

Always runnable (no Isaac Sim, GPU, or network). Gates the other tiers.
"""

from __future__ import annotations

import pytest
from _discovery import all_script_paths, classify
from _discovery import rel as drel
from _discovery import scripts_of_kind
from _validation import (
    KNOWN_BROKEN_REFS,
    check_bash,
    check_python,
    collect_refs,
    extract_fenced_blocks,
    has_frontmatter,
    iter_markdown,
    iter_scripts,
    rel,
)

pytestmark = pytest.mark.static

# Kinds the generic executors handle, and the library_sim scripts that have a
# dedicated (non-generic) test. A new library_sim script will fail the coverage
# test until it is given a test and listed here.
HANDLED_KINDS = {"shell", "batch", "standalone", "client", "remote", "pure", "library_sim"}
COVERED_LIBRARY_SIM = {"isaac-sim-ros2-bridge/scripts/multi_robot_namespacing.py"}

_SCRIPTS = list(iter_scripts())
_MARKDOWN = list(iter_markdown())
_SKILLS = [m for m in _MARKDOWN if m.name == "SKILL.md"]
_BATCH = scripts_of_kind("batch")

# Pre-extract snippets so each becomes its own parametrized case.
_SNIPPETS = []
for _md in _MARKDOWN:
    for _lang, _line, _code in extract_fenced_blocks(_md):
        _SNIPPETS.append((_md, _lang, _line, _code))


@pytest.mark.parametrize("path,lang", _SCRIPTS, ids=[rel(p) for p, _ in _SCRIPTS])
def test_script_syntax(path, lang):
    src = path.read_text(encoding="utf-8", errors="replace")
    ok, detail = check_python(src, str(path)) if lang == "python" else check_bash(src, str(path))
    assert ok, f"{rel(path)}: {detail}"


@pytest.mark.parametrize(
    "md,lang,line,code",
    _SNIPPETS,
    ids=[f"{rel(md)}:{line}:{lang}" for md, lang, line, _ in _SNIPPETS],
)
def test_snippet_syntax(md, lang, line, code):
    label = f"{rel(md)}:{line}"
    ok, detail = check_python(code, label) if lang == "python" else check_bash(code, label)
    assert ok, f"{label} ({lang}): {detail}"


@pytest.mark.parametrize("md", _SKILLS, ids=[rel(p) for p in _SKILLS])
def test_skill_frontmatter(md):
    ok, missing = has_frontmatter(md.read_text(encoding="utf-8", errors="replace"))
    assert ok, f"{rel(md)}: frontmatter problem: {missing}"


_REFS = [(m, r, line, st) for (m, r, line, st) in collect_refs()]


@pytest.mark.parametrize(
    "md_rel,ref,line,status",
    _REFS,
    ids=[f"{m}:{line}->{r}" for m, r, line, _ in _REFS],
)
def test_cross_reference_resolves(md_rel, ref, line, status):
    if (md_rel, ref) in KNOWN_BROKEN_REFS:
        pytest.xfail(f"DEFECT: {md_rel}:{line} points at '{ref}', which is not shipped")
    assert status == "ok", f"{md_rel}:{line}: unresolved reference '{ref}'"


@pytest.mark.parametrize("relp", _BATCH, ids=[r.split("/")[-1] for r in _BATCH] or ["none"])
def test_batch_structure(relp):
    # Windows .bat cannot be executed/parsed on Linux; do a basic structural check.
    from _util import skill_path

    if not _BATCH:
        pytest.skip("no .bat scripts")
    text = open(skill_path(*relp.split("/")), encoding="utf-8", errors="replace").read()
    assert text.strip(), f"{relp} is empty"
    assert any(not ln.strip().startswith("::") and ln.strip() for ln in text.splitlines()), f"{relp} has no commands"


def test_every_script_is_covered():
    """Every shipped script must classify into a kind a generic executor handles."""
    unhandled = {drel(p): classify(p) for p in all_script_paths() if classify(p) not in HANDLED_KINDS}
    assert not unhandled, f"scripts with no handling: {unhandled}"
    # library_sim scripts need a dedicated test (generic executors can't run them).
    uncovered = set(scripts_of_kind("library_sim")) - COVERED_LIBRARY_SIM
    assert not uncovered, f"library_sim scripts lacking a dedicated test: {uncovered}"


def test_inventory_nonempty():
    # Guards against the collection globs silently matching nothing.
    assert len(_SCRIPTS) >= 20, f"expected >=20 scripts, found {len(_SCRIPTS)}"
    assert len(_SNIPPETS) >= 150, f"expected >=150 snippets, found {len(_SNIPPETS)}"
    assert len(_SKILLS) >= 25, f"expected >=25 SKILL.md, found {len(_SKILLS)}"
