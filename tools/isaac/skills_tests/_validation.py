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

"""Static-validation helpers (syntax, snippet extraction, frontmatter, cross-refs).

Syntax-only. Never imports or executes Isaac Sim code: Python is checked with
compile() (top-level await permitted, since python_server payloads use it) and
shell with `bash -n` (angle-bracket <placeholders> tolerated).
"""

from __future__ import annotations

import ast
import re
import subprocess
from pathlib import Path

from _util import SKILLS_DIR

ROOT = Path(SKILLS_DIR)

FENCE_RE = re.compile(r"^([ \t]*)```([^\n`]*)$")
CLOSE_RE = re.compile(r"^[ \t]*```\s*$")
PLACEHOLDER_RE = re.compile(r"<[^<>\n]+>")

# Cross-references that intentionally do not resolve to a skill-local file:
#  - skill-distillation: inline prose examples of the one-level-deep rule
#  - urdf-mjcf: paths relative to $ISAAC_LAB_DIR (Isaac Lab tooling), not skill-local
CROSSREF_ALLOWLIST = {
    ("skill-distillation/SKILL.md", "scripts/foo.py"),
    ("skill-distillation/SKILL.md", "scripts/utils/foo.py"),
    ("urdf-mjcf-to-usd-conversion/SKILL.md", "scripts/tools/convert_urdf.py"),
    ("urdf-mjcf-to-usd-conversion/SKILL.md", "scripts/tools/convert_mjcf.py"),
}

# Genuine defects: references to files that are not shipped. Tracked as xfail so
# the suite stays green while the dangling pointer remains visible. Remove an
# entry (and add the file or fix the doc) to turn the xfail into a hard check.
KNOWN_BROKEN_REFS: set[tuple[str, str]] = set()

REF_RE = re.compile(r"(?<![\w./-])(\.?/?(?:scripts|references|examples)/[\w./-]+\.(?:py|sh|bat|md))")


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def iter_scripts():
    for p in sorted(ROOT.rglob("*.py")):
        yield p, "python"
    for p in sorted(ROOT.rglob("*.sh")):
        yield p, "bash"


def iter_markdown():
    return sorted(ROOT.rglob("*.md"))


def lang_of(info: str):
    info = (info or "").lower().strip()
    first = info.split()[0] if info else ""
    if first in ("python", "py", "python3"):
        return "python"
    if first in ("bash", "sh", "shell", "console", "shell-session", "zsh"):
        return "bash"
    return None


def extract_fenced_blocks(md_path: Path):
    """Yield (lang, start_line, code) for fenced code blocks with a known lang."""
    lines = md_path.read_text(encoding="utf-8", errors="replace").splitlines()
    i, n = 0, len(lines)
    while i < n:
        m = FENCE_RE.match(lines[i])
        if m:
            indent, info = m.group(1), m.group(2).strip()
            body, j, closed = [], i + 1, False
            while j < n:
                if CLOSE_RE.match(lines[j]):
                    closed = True
                    break
                body.append(lines[j])
                j += 1
            if indent:
                body = [ln[len(indent) :] if ln.startswith(indent) else ln for ln in body]
            lang = lang_of(info)
            if lang is not None and "\n".join(body).strip():
                yield lang, i + 2, "\n".join(body)
            i = j + 1 if closed else j
        else:
            i += 1


def check_python(src: str, label: str):
    """Return (ok, detail). Top-level await is accepted."""
    try:
        compile(src, label, "exec")
        return True, "ok"
    except SyntaxError:
        try:
            compile(src, label, "exec", flags=ast.PyCF_ALLOW_TOP_LEVEL_AWAIT)
            return True, "top-level-await"
        except SyntaxError as e:
            return False, f"{type(e).__name__}: {e.msg} (line {e.lineno})"


def _bash_n(src: str):
    p = subprocess.run(["bash", "-n"], input=src, text=True, capture_output=True, timeout=30)
    return p.returncode, p.stderr.strip()


def check_bash(src: str, label: str):
    """Return (ok, detail). <angle-bracket> placeholders are tolerated."""
    rc, err = _bash_n(src)
    if rc == 0:
        return True, "ok"
    if PLACEHOLDER_RE.search(src):
        rc2, _ = _bash_n(PLACEHOLDER_RE.sub("PLACEHOLDER", src))
        if rc2 == 0:
            return True, "placeholder"
    return False, (err or "bash -n failed").replace("/dev/stdin", label)


def has_frontmatter(text: str):
    """Return (ok, missing_keys). Validates a leading --- ... --- block with name+description."""
    if not text.startswith("---"):
        return False, ["<no frontmatter block>"]
    end = text.find("\n---", 3)
    if end == -1:
        return False, ["<unterminated frontmatter>"]
    fm = text[3:end]
    missing = [k for k in ("name", "description") if not re.search(rf"^{k}\s*:", fm, re.MULTILINE)]
    return (not missing), missing


def skill_root(md_path: Path) -> Path:
    """Directory of the owning skill (nearest ancestor containing SKILL.md)."""
    if (md_path.parent / "SKILL.md").exists():
        return md_path.parent
    for parent in md_path.parents:
        if (parent / "SKILL.md").exists():
            return parent
    return md_path.parent


def collect_refs():
    """Yield (md_rel, ref, line, status) for every scripts/references/examples ref.

    status: "ok" (resolves), "missing" (does not resolve). External/allowlisted
    refs are omitted. Resolution is relative to the owning skill root so sidecar
    files (references/*.md) can point at ../scripts/* with a bare scripts/ path.
    """
    for md in iter_markdown():
        text = md.read_text(encoding="utf-8", errors="replace")
        root = skill_root(md)
        md_rel = rel(md)
        for m in REF_RE.finditer(text):
            ref = m.group(1).lstrip("./")
            if (md_rel, ref) in CROSSREF_ALLOWLIST:
                continue
            line = text[: m.start()].count("\n") + 1
            status = "ok" if (root / ref).exists() else "missing"
            yield md_rel, ref, line, status
