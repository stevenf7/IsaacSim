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

"""Validate SKILL.md files against the Anthropic skill spec.

Rules enforced:

  1. Body ≤ 500 lines.
  2. ``description`` field in YAML frontmatter ≤ 1024 chars.
  3. No inline ``\`\`\`python`` code block with ≥ 20 lines
     (must be extracted to a ``scripts/`` sidecar).
  4. No hardcoded ``/home/<user>/`` or ``/Users/<user>/`` paths.
  5. No hardcoded non-loopback IP addresses.

Rules 4 and 5 skip markdown table rows (lines starting with ``|``) to
allow spec documents that show counter-examples.

Usage:
    # Validate specific skill directories
    python tools/isaac/pre_merge/validate_skills.py skills/usd-pipeline skills/mobility-gen

    # Validate all skills under skills/
    python tools/isaac/pre_merge/validate_skills.py --all
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import yaml

# Ensure this script's directory is on sys.path so repo_helpers / term_helpers can be imported
_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

from repo_helpers import REPO_ROOT  # noqa: E402
from term_helpers import log_fail, log_info, log_pass  # noqa: E402

_LOOPBACK = re.compile(r"^127\.|^0\.0\.0\.0$|^::1$")


def validate_skill(skill_dir: Path) -> list[str]:
    """Run all spec rules against one skill directory and return a list of violation strings.

    Args:
        skill_dir: Path to the skill directory (must contain ``SKILL.md``).

    Returns:
        List of human-readable violation strings (empty when the skill is clean).
    """
    skill_md = skill_dir / "SKILL.md"
    text = skill_md.read_text(encoding="utf-8")
    lines = text.splitlines()
    issues: list[str] = []

    # Rule 1: body ≤ 500 lines
    if len(lines) > 500:
        issues.append(f"body is {len(lines)} lines (max 500)")

    # Rule 2: description ≤ 1024 chars (from YAML frontmatter)
    fm_match = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
    if fm_match:
        try:
            fm = yaml.safe_load(fm_match.group(1)) or {}
            desc = fm.get("description", "")
            if isinstance(desc, str) and len(desc) > 1024:
                issues.append(f"description is {len(desc)} chars (max 1024)")
        except Exception:
            issues.append("could not parse YAML frontmatter")

    # Rule 3: no inline ```python block ≥ 20 lines.
    # Track ALL fenced blocks so a closing fence never accidentally opens a new one.
    in_any_block = False
    is_python_block = False
    block_start = 0
    block_count = 0
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped.startswith("```"):
            if not in_any_block:
                lang = stripped[3:].strip().lower()
                in_any_block = True
                is_python_block = lang in ("python", "py")
                if is_python_block:
                    block_start = i
                    block_count = 0
            else:
                if is_python_block and block_count >= 20:
                    issues.append(
                        f"inline Python block at line {block_start} has {block_count} lines"
                        " (≥20 must be extracted to scripts/)"
                    )
                in_any_block = False
                is_python_block = False
        elif in_any_block and is_python_block:
            block_count += 1

    # Rules 4 & 5: no hardcoded home paths or non-loopback IPs.
    # Table rows (lines starting with |) are exempt — they often show counter-examples.
    for lineno, line in enumerate(lines, 1):
        if line.strip().startswith("|"):
            continue
        if re.search(r"/home/[a-zA-Z0-9_]+/", line):
            issues.append(f"line {lineno}: hardcoded /home/<user>/ path")
            break
    for lineno, line in enumerate(lines, 1):
        if line.strip().startswith("|"):
            continue
        if re.search(r"/Users/[a-zA-Z0-9_]+/", line):
            issues.append(f"line {lineno}: hardcoded /Users/<user>/ path")
            break
    for lineno, line in enumerate(lines, 1):
        if line.strip().startswith("|"):
            continue
        m = re.search(r"\b(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})\b", line)
        if m and all(int(g) <= 255 for g in m.groups()) and not _LOOPBACK.match(m.group()):
            issues.append(f"line {lineno}: possible hardcoded IP address ({m.group()})")
            break

    return issues


def validate_skills(skill_dirs: list[Path]) -> int:
    """Validate a list of skill directories and print per-skill pass/fail results.

    Args:
        skill_dirs: Skill directories to validate (each must contain ``SKILL.md``).

    Returns:
        Number of skills with validation errors.
    """
    errors = 0
    for skill_dir in skill_dirs:
        issues = validate_skill(skill_dir)
        if issues:
            for issue in issues:
                print(f"    {issue}", flush=True)
            log_fail(f"{skill_dir.name}: SKILL.md validation failed.")
            errors += 1
        else:
            log_pass(f"{skill_dir.name}: SKILL.md OK.")
    return errors


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser.

    Returns:
        Configured ArgumentParser.
    """
    parser = argparse.ArgumentParser(
        description="Validate SKILL.md files against the Anthropic skill spec.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "skill_dirs",
        nargs="*",
        type=Path,
        metavar="SKILL_DIR",
        help="One or more skill directories to validate (e.g. skills/usd-pipeline).",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        dest="all_skills",
        help="Validate every skill directory under skills/ in the repo root.",
    )
    return parser


def main() -> int:
    """Parse arguments and run validation.

    Returns:
        Exit code (0 if all clean, 1 if any violations found).
    """
    parser = build_parser()
    args = parser.parse_args()

    skills_root = REPO_ROOT / "skills"

    if args.all_skills:
        if not skills_root.exists():
            log_info("No skills/ directory found.")
            return 0
        skill_dirs = sorted(d for d in skills_root.iterdir() if d.is_dir() and (d / "SKILL.md").exists())
    elif args.skill_dirs:
        skill_dirs = []
        for p in args.skill_dirs:
            resolved = p if p.is_absolute() else REPO_ROOT / p
            if not (resolved / "SKILL.md").exists():
                log_fail(f"{resolved}: no SKILL.md found.")
                return 1
            skill_dirs.append(resolved)
    else:
        parser.print_help()
        return 0

    errors = validate_skills(skill_dirs)
    return 1 if errors > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
