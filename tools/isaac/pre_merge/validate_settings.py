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

"""Validate extension settings docs against config/extension.toml.

Checks that each extension's `docs/SETTINGS.md` reflects the active settings
declared in the sibling `config/extension.toml` file. The validator reports one
failure per mismatch and optionally rewrites `SETTINGS.md` in place with `--fix`.

Validation rules:
  - Active settings in `extension.toml` must exist in `docs/SETTINGS.md`
  - Default values in `docs/SETTINGS.md` must match `extension.toml`
  - Descriptions are checked when `extension.toml` has a comment directly above
    the setting assignment
  - Entries in `docs/SETTINGS.md` that correspond only to commented-out TOML
    settings are treated as failures
  - Other docs pages are scanned for fenced `toml` settings snippets, and any
    copied values they contain must stay aligned with the live settings

Usage:
    python tools/isaac/pre_merge/validate_settings.py source/extensions/isaacsim.storage.native
    python tools/isaac/pre_merge/validate_settings.py --fix source/extensions/isaacsim.gui.content_browser
    python tools/isaac/pre_merge/validate_settings.py
"""

from __future__ import annotations

import argparse
import ast
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from repo_helpers import all_extensions
from term_helpers import log_fail, log_info, log_pass, log_warn

try:
    import tomllib as _toml_reader
except ImportError:
    try:
        import tomli as _toml_reader  # type: ignore[no-redef]
    except ImportError:
        _toml_reader = None

_SETTINGS_HEADER = [
    "```{csv-table}",
    "**Extension**: {{ extension_version }},**Documentation Generated**: {sub-ref}`today`",
    "```",
    "",
    "# Settings",
]

_TOML_FENCE_RE = re.compile(r"```toml\s*\n(.*?)\n```", re.DOTALL)
_SETTING_HEADING_RE = re.compile(r"^###\s+(.+?)\s*$")
_BULLET_INDENT_RE = re.compile(r"^(\s*)-\s+\*\*Default Value\*\*:")
_COMMENTED_SETTING_RE = re.compile(r"^#\s*([A-Za-z0-9_.\"-]+)\s*=")


@dataclass
class SettingSource:
    key: str
    value: Any
    rendered_value: str
    description: str


@dataclass
class SettingsDocEntry:
    key: str
    raw_value: str
    value: Any | None
    description: str


@dataclass
class SettingsDoc:
    path: Path
    header_lines: list[str]
    bullet_indent: str
    entries: list[SettingsDocEntry]

    @property
    def by_key(self) -> dict[str, SettingsDocEntry]:
        return {entry.key: entry for entry in self.entries}


@dataclass
class ParsedSettings:
    ordered: list[SettingSource]
    by_key: dict[str, SettingSource]
    commented_out_keys: set[str]
    conflicted_keys: set[str]


def _parse_toml_value(raw_value: str) -> Any:
    if _toml_reader is not None:
        return _toml_reader.loads(f"x = {raw_value}")["x"]

    cleaned_lines: list[str] = []
    for line in raw_value.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            continue
        cleaned_lines.append(line)
    fallback_value = "\n".join(cleaned_lines)
    fallback_value = re.sub(r"\btrue\b", "True", fallback_value)
    fallback_value = re.sub(r"\bfalse\b", "False", fallback_value)
    return ast.literal_eval(fallback_value)


def _render_scalar(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, str):
        escaped = value.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped}"'
    return str(value)


def _render_value(value: Any) -> str:
    if isinstance(value, list):
        items = [_render_scalar(item) for item in value]
        if not items:
            return "[]"
        lines = ["["]
        for index, item in enumerate(items):
            suffix = "," if index < len(items) - 1 else ""
            lines.append(f"    {item}{suffix}")
        lines.append("]")
        return "\n".join(lines)
    return _render_scalar(value)


def _render_value_lines(value: Any, bullet_indent: str) -> list[str]:
    if isinstance(value, list):
        lines = [f"{bullet_indent}- **Default Value**: ["]
        for index, item in enumerate(value):
            suffix = "," if index < len(value) - 1 else ""
            lines.append(f"{bullet_indent}  {_render_scalar(item)}{suffix}")
        lines.append(f"{bullet_indent}]")
        return lines
    return [f"{bullet_indent}- **Default Value**: {_render_scalar(value)}"]


def _collect_value_lines(lines: list[str], start_index: int, first_rhs: str) -> tuple[str, int]:
    raw_lines = [first_rhs.rstrip()]
    bracket_depth = first_rhs.count("[") - first_rhs.count("]")
    index = start_index
    while bracket_depth > 0 and index + 1 < len(lines):
        index += 1
        next_line = lines[index].rstrip()
        raw_lines.append(next_line)
        bracket_depth += next_line.count("[") - next_line.count("]")
    return "\n".join(raw_lines).strip(), index


def _parse_settings_sections(toml_path: Path) -> ParsedSettings:
    lines = toml_path.read_text(encoding="utf-8").splitlines()
    in_settings_section = False
    pending_comments: list[str] = []
    grouped_entries: dict[str, list[SettingSource]] = {}
    ordered_keys: list[str] = []
    commented_out_keys: set[str] = set()

    index = 0
    while index < len(lines):
        line = lines[index]
        stripped = line.strip()

        if not stripped:
            pending_comments = []
            index += 1
            continue

        if stripped.startswith("[") and stripped.endswith("]"):
            in_settings_section = stripped.startswith("[settings")
            pending_comments = []
            index += 1
            continue

        if not in_settings_section:
            index += 1
            continue

        commented_match = _COMMENTED_SETTING_RE.match(stripped)
        if commented_match:
            commented_out_keys.add(commented_match.group(1))
            pending_comments = []
            index += 1
            continue

        if stripped.startswith("#"):
            pending_comments.append(stripped[1:].strip())
            index += 1
            continue

        if "=" not in line:
            pending_comments = []
            index += 1
            continue

        key, rhs = line.split("=", 1)
        raw_value, index = _collect_value_lines(lines, index, rhs)
        description = " ".join(pending_comments).strip()
        pending_comments = []

        try:
            value = _parse_toml_value(raw_value)
        except Exception:
            index += 1
            continue

        key = key.strip()
        source = SettingSource(
            key=key,
            value=value,
            rendered_value=_render_value(value),
            description=description,
        )
        if key not in grouped_entries:
            grouped_entries[key] = []
            ordered_keys.append(key)
        grouped_entries[key].append(source)
        index += 1

    ordered: list[SettingSource] = []
    by_key: dict[str, SettingSource] = {}
    conflicted_keys: set[str] = set()
    for key in ordered_keys:
        entries = grouped_entries[key]
        distinct_values = {entry.rendered_value for entry in entries}
        if len(distinct_values) > 1:
            conflicted_keys.add(key)
            continue
        chosen = entries[0]
        descriptions = [entry.description for entry in entries if entry.description]
        if descriptions:
            chosen = SettingSource(
                key=chosen.key,
                value=chosen.value,
                rendered_value=chosen.rendered_value,
                description=descriptions[0],
            )
        ordered.append(chosen)
        by_key[key] = chosen

    return ParsedSettings(
        ordered=ordered,
        by_key=by_key,
        commented_out_keys=commented_out_keys,
        conflicted_keys=conflicted_keys,
    )


def _default_settings_header() -> list[str]:
    return list(_SETTINGS_HEADER)


def _parse_settings_md(settings_path: Path) -> SettingsDoc:
    if not settings_path.exists():
        return SettingsDoc(settings_path, _default_settings_header(), "", [])

    lines = settings_path.read_text(encoding="utf-8").splitlines()
    header_end = -1
    bullet_indent = ""
    entries: list[SettingsDocEntry] = []

    for idx, line in enumerate(lines):
        if line.strip() == "# Settings":
            header_end = idx
        if not bullet_indent:
            indent_match = _BULLET_INDENT_RE.match(line)
            if indent_match:
                bullet_indent = indent_match.group(1)

    header_lines = lines[: header_end + 1] if header_end >= 0 else _default_settings_header()

    index = header_end + 1 if header_end >= 0 else len(lines)
    while index < len(lines):
        heading_match = _SETTING_HEADING_RE.match(lines[index].strip())
        if not heading_match:
            index += 1
            continue

        key = heading_match.group(1)
        raw_value_lines: list[str] = []
        description = ""
        index += 1
        while index < len(lines):
            stripped = lines[index].strip()
            if _SETTING_HEADING_RE.match(stripped):
                break
            if stripped.startswith("- **Default Value**:"):
                remainder = stripped.split(":", 1)[1].strip()
                raw_value_lines = [remainder] if remainder else []
                index += 1
                while index < len(lines):
                    next_stripped = lines[index].strip()
                    if next_stripped.startswith("- **Description**:") or _SETTING_HEADING_RE.match(next_stripped):
                        break
                    raw_value_lines.append(next_stripped)
                    index += 1
                continue
            if stripped.startswith("- **Description**:"):
                description = stripped.split(":", 1)[1].strip()
            index += 1

        raw_value = "\n".join(line for line in raw_value_lines if line).strip()
        parsed_value: Any | None = None
        if raw_value:
            try:
                parsed_value = _parse_toml_value(raw_value)
            except Exception:
                parsed_value = None

        entries.append(
            SettingsDocEntry(
                key=key,
                raw_value=raw_value,
                value=parsed_value,
                description=description,
            )
        )

    return SettingsDoc(settings_path, header_lines, bullet_indent, entries)


def _settings_doc_failures(parsed: ParsedSettings, doc: SettingsDoc) -> list[str]:
    failures: list[str] = []
    doc_entries = doc.by_key

    for key in sorted(parsed.conflicted_keys):
        failures.append(f"{doc.path}: {key} has multiple active platform-specific defaults in extension.toml")

    for source in parsed.ordered:
        entry = doc_entries.get(source.key)
        if entry is None:
            failures.append(f"{doc.path}: missing setting `{source.key}`")
            continue

        if not _doc_entry_value_matches(entry, source):
            failures.append(
                f"{doc.path}: `{source.key}` default mismatch (docs: {entry.raw_value or '<missing>'}; toml: {source.rendered_value})"
            )

    for entry in doc.entries:
        if entry.key in parsed.by_key or entry.key in parsed.conflicted_keys:
            continue
        if entry.key in parsed.commented_out_keys:
            failures.append(f"{doc.path}: `{entry.key}` documents a commented-out setting without an active default")
        else:
            failures.append(f"{doc.path}: `{entry.key}` is not present in active extension.toml settings")

    return failures


def _doc_entry_value_matches(entry: SettingsDocEntry, source: SettingSource) -> bool:
    if entry.value == source.value:
        return True

    raw_value = entry.raw_value.strip()
    if not raw_value:
        return False

    return raw_value.startswith(source.rendered_value)


def _build_settings_md(parsed: ParsedSettings, existing_doc: SettingsDoc) -> str:
    header_lines = existing_doc.header_lines or _default_settings_header()
    while header_lines and header_lines[-1] == "":
        header_lines.pop()

    doc_by_key = existing_doc.by_key
    bullet_indent = existing_doc.bullet_indent
    output_lines = [*header_lines, ""]

    for index, source in enumerate(parsed.ordered):
        output_lines.append(f"### {source.key}")
        output_lines.extend(_render_value_lines(source.value, bullet_indent))

        existing_description = doc_by_key.get(source.key).description if source.key in doc_by_key else ""
        description = source.description or existing_description
        description_line = f"{bullet_indent}- **Description**:"
        if description:
            description_line += f" {description}"
        output_lines.append(description_line)

        if index < len(parsed.ordered) - 1:
            output_lines.append("")

    output_lines.append("")
    return "\n".join(output_lines)


def _fix_settings_md(parsed: ParsedSettings, doc: SettingsDoc) -> bool:
    new_content = _build_settings_md(parsed, doc)
    current_content = doc.path.read_text(encoding="utf-8") if doc.path.exists() else ""
    if current_content == new_content:
        return False
    doc.path.write_text(new_content, encoding="utf-8")
    return True


def _parse_doc_snippet_settings(block: str) -> list[tuple[str, Any]]:
    lines = block.splitlines()
    in_settings_section = False
    parsed: list[tuple[str, Any]] = []

    index = 0
    while index < len(lines):
        stripped = lines[index].strip()
        if not stripped or stripped.startswith("#"):
            index += 1
            continue
        if stripped.startswith("[") and stripped.endswith("]"):
            in_settings_section = stripped.startswith("[settings")
            index += 1
            continue
        if not in_settings_section or "=" not in lines[index]:
            index += 1
            continue

        key, rhs = lines[index].split("=", 1)
        raw_value, index = _collect_value_lines(lines, index, rhs)
        try:
            value = _parse_toml_value(raw_value)
        except Exception:
            index += 1
            continue
        parsed.append((key.strip(), value))
        index += 1

    return parsed


def _snippet_value_matches(doc_value: Any, source_value: Any) -> bool:
    if isinstance(doc_value, list) and isinstance(source_value, list):
        source_index = 0
        for item in doc_value:
            while source_index < len(source_value) and source_value[source_index] != item:
                source_index += 1
            if source_index == len(source_value):
                return False
            source_index += 1
        return True
    return doc_value == source_value


def _other_doc_failures(ext_path: Path, parsed: ParsedSettings) -> list[str]:
    docs_dir = ext_path / "docs"
    if not docs_dir.exists():
        return []

    failures: list[str] = []
    for doc_path in sorted(docs_dir.glob("*.md")):
        if doc_path.name == "SETTINGS.md":
            continue
        content = doc_path.read_text(encoding="utf-8")
        for block in _TOML_FENCE_RE.findall(content):
            if "[settings]" not in block:
                continue
            for key, doc_value in _parse_doc_snippet_settings(block):
                source = parsed.by_key.get(key)
                if source is None:
                    continue
                if not _snippet_value_matches(doc_value, source.value):
                    failures.append(f"{doc_path}: copied settings snippet for `{key}` is out of date")
    return failures


def validate_extension(ext_path: Path, fix: bool = False) -> int:
    ext_path = ext_path.resolve()
    toml_path = ext_path / "config" / "extension.toml"
    settings_path = ext_path / "docs" / "SETTINGS.md"

    if not toml_path.exists():
        log_fail(f"{ext_path.name}: missing config/extension.toml")
        return 1

    parsed = _parse_settings_sections(toml_path)
    if not parsed.ordered and not settings_path.exists():
        log_info(f"{ext_path.name}: no settings docs to validate.")
        return 0

    doc = _parse_settings_md(settings_path)
    failures = _settings_doc_failures(parsed, doc)

    if fix and failures:
        changed = _fix_settings_md(parsed, doc)
        if changed:
            log_info(f"{ext_path.name}: updated docs/SETTINGS.md")
        doc = _parse_settings_md(settings_path)
        failures = _settings_doc_failures(parsed, doc)

    failures.extend(_other_doc_failures(ext_path, parsed))

    if failures:
        for failure in failures:
            log_fail(failure)
        return 1

    log_pass(f"{ext_path.name}: settings docs OK.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate SETTINGS.md files and copied settings snippets against extension.toml defaults.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "extensions",
        nargs="*",
        type=Path,
        help="Extension directories to validate. Defaults to all repository extensions.",
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Rewrite docs/SETTINGS.md to match extension.toml for the selected extensions.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    extensions = args.extensions or all_extensions()
    if not extensions:
        log_warn("No extensions found.")
        return 0

    failures = 0
    for ext in extensions:
        failures += validate_extension(ext, fix=args.fix)

    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
