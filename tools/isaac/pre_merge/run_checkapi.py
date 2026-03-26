#!/usr/bin/env python3

# SPDX-FileCopyrightText: Copyright (c) 2025-2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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

"""Run checkapi (python_api.md generation) on specific extensions.

This script reuses the APIAnalyzer from repo_kit_tools but avoids the heavy
repo/packman bootstrap chain so it can run with any Python 3.11+ interpreter.

Usage:
    python tools/isaac/pre_merge/run_checkapi.py isaacsim.core.telemetry
    python tools/isaac/pre_merge/run_checkapi.py isaacsim.core.telemetry isaacsim.robot.poser
    python tools/isaac/pre_merge/run_checkapi.py isaacsim.core.telemetry --config debug
    python tools/isaac/pre_merge/run_checkapi.py --list
"""

import argparse
import difflib
import importlib.util
import logging
import os
import sys
from io import StringIO

# ---------------------------------------------------------------------------
# Resolve repo root and import api_analyzer directly (stdlib-only module).
# This avoids pulling in omni.repo.man / packman / rich.
# ---------------------------------------------------------------------------
REPO_ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))

_ANALYZER_PATH = os.path.join(
    REPO_ROOT, "_repo", "deps", "repo_kit_tools", "omni", "repo", "kit_tools", "checkapi", "api_analyzer.py"
)


def _import_api_analyzer() -> object:
    """Import api_analyzer.py directly by file path (it only uses stdlib)."""
    spec = importlib.util.spec_from_file_location("api_analyzer", _ANALYZER_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_analyzer_mod = _import_api_analyzer()
APIAnalyzer = _analyzer_mod.APIAnalyzer
SearchPath = _analyzer_mod.SearchPath

logger = logging.getLogger(__name__)

PLATFORM = "linux-x86_64"

# ---------------------------------------------------------------------------
# Use tomllib (3.11+) or tomli as fallback for TOML parsing.
# ---------------------------------------------------------------------------
try:
    import tomllib
except ModuleNotFoundError:
    try:
        import tomli as tomllib  # type: ignore[no-redef]
    except ModuleNotFoundError:
        tomllib = None  # type: ignore[assignment]


def _load_toml(path: str) -> dict:
    if tomllib is not None:
        with open(path, "rb") as f:
            return tomllib.load(f)
    # Last-resort: simple key=value parser for the fields we need.
    # Only used if neither tomllib nor tomli is available.
    import re

    with open(path) as f:
        text = f.read()
    # Try to extract [[python.module]] entries
    modules = []
    for m in re.finditer(r"\[\[python\.module\]\]\s*\n((?:\s*\w+\s*=.*\n?)+)", text):
        block = m.group(1)
        entry = {}
        for kv in re.finditer(r'(\w+)\s*=\s*"([^"]*)"', block):
            entry[kv.group(1)] = kv.group(2)
        if entry:
            modules.append(entry)
    return {"python": {"module": modules}} if modules else {}


# ---------------------------------------------------------------------------
# Lightweight Extension (mirrors checkapi.Extension but no repo.man dependency)
# ---------------------------------------------------------------------------
def _find_extension_config(path: str) -> str | None:
    for config_path in [
        f"{path}/config/extension.toml",
        f"{path}/extension.toml",
        f"{path}/config/docs/docs.toml",
    ]:
        if os.path.exists(config_path):
            return config_path
    return None


class Extension:
    """Lightweight extension wrapper (mirrors checkapi.Extension without repo.man dependency)."""

    def __init__(self, path: str, config_path: str, is_extra: bool = False) -> None:
        self.name = os.path.basename(path)
        self.config_path = config_path
        self.path = path
        self.is_extra = is_extra

        try:
            self.config = _load_toml(config_path)
        except Exception as e:
            logger.error(f"Failed to load {config_path}: {e}")
            self.config = {}

        self.modules: list[str] = []
        self.search_paths: set[str] = set()

        for module in self.config.get("python", {}).get("module", []):
            mod_path = module.get("path", ".")
            name = module.get("name", "")
            if not name:
                continue
            self.modules.append(name)
            self.search_paths.add(os.path.join(self.path, mod_path))

    def generate_public_api_doc(self, analyzer: "APIAnalyzer") -> bool:
        """Generate python_api.md. Returns True if the file was changed."""
        api_doc_path = os.path.dirname(self.config_path) + "/python_api.md"
        buf = StringIO()
        printed_modules: set = set()
        for i, module_name in enumerate(self.modules):
            module = analyzer.load_public_module(module_name)
            if not module:
                continue
            if i > 0:
                buf.write("\n")
            module.print_attributes(public_only=True, stream=buf, printed_modules=printed_modules)

        content = buf.getvalue()

        if os.path.exists(api_doc_path):
            with open(api_doc_path) as f:
                existing = f.read()
            if existing == content and content:
                return False
            # Show diff
            diff = difflib.unified_diff(
                existing.splitlines(), content.splitlines(), fromfile="original", tofile="new", lineterm=""
            )
            diff_str = "\n".join(f"  {line}" for line in diff)
            if diff_str:
                print(f"  Diff for {self.name}:")
                print(diff_str)

        if content:
            with open(api_doc_path, "w") as f:
                f.write(content)
        else:
            if os.path.exists(api_doc_path):
                print(f"  Removing empty python_api.md for {self.name}")
                os.remove(api_doc_path)
            else:
                return False

        return True


# ---------------------------------------------------------------------------
# Discovery helpers
# ---------------------------------------------------------------------------
def _build_dir(config: str) -> str:
    return os.path.join(REPO_ROOT, "_build", PLATFORM, config)


def _ext_folders(config: str) -> list[str]:
    base = _build_dir(config)
    return [
        os.path.join(base, "exts"),
        os.path.join(base, "extsInternal"),
        os.path.join(base, "extsDeprecated"),
    ]


def _discover_extensions(ext_folders: list[str]) -> list[Extension]:
    exts = []
    for folder in ext_folders:
        if not os.path.isdir(folder):
            continue
        # Check if folder itself is an extension
        cfg = _find_extension_config(folder)
        if cfg:
            exts.append(Extension(folder, cfg))
            continue
        # Otherwise iterate subdirs
        for entry in sorted(os.listdir(folder)):
            ext_path = os.path.join(folder, entry)
            cfg = _find_extension_config(ext_path)
            if cfg:
                exts.append(Extension(ext_path, cfg))
    return exts


# ---------------------------------------------------------------------------
# Main logic
# ---------------------------------------------------------------------------
def run(extension_names: list[str], config: str, check: bool, verbose: bool, list_exts: bool) -> int:
    """Run checkapi on the given extensions, optionally checking API usage."""
    if verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.WARNING)

    ext_folders = _ext_folders(config)

    # Check build exists
    existing = [f for f in ext_folders if os.path.isdir(f)]
    if not existing:
        print(f"Error: no build directories found for config '{config}'. Run ./build.sh --no-docker first.")
        return 1

    # Discover all extensions
    all_exts = _discover_extensions(ext_folders)
    if not all_exts:
        print(f"Error: no extensions found in build for config '{config}'.")
        return 1

    ext_by_name = {e.name: e for e in all_exts}

    # --list mode
    if list_exts:
        for name in sorted(ext_by_name):
            print(name)
        print(f"\n{len(ext_by_name)} extensions found.")
        return 0

    if not extension_names:
        print("Error: specify one or more extension names (or use --list).")
        return 1

    # Validate requested names
    targets = []
    for name in extension_names:
        if name not in ext_by_name:
            print(f"Error: extension '{name}' not found. Partial matches:")
            for n in sorted(ext_by_name):
                if name in n:
                    print(f"  {n}")
            return 1
        targets.append(ext_by_name[name])

    # Build search paths and public module set from ALL extensions
    search_paths = []
    public_modules: set[str] = set()
    for ext in all_exts:
        for sp in ext.search_paths:
            search_paths.append(SearchPath(os.path.normpath(sp), False, ext.name, ext.is_extra))
        public_modules.update(ext.modules)

    print(f"Initializing analyzer ({len(all_exts)} extensions, {len(public_modules)} modules)...")
    analyzer = APIAnalyzer(
        search_paths,
        public_modules=public_modules,
        skip_packages=[],
        skip_toplevel_packages=[],
        strict_mode=False,
    )

    # Optionally run API usage check
    if check:
        print("Checking API usage...")
        results = analyzer.check_api_usage(skip_exts=[])
        target_names = {t.name for t in targets}
        found_errors = False
        for ext_name, errors in results.errors.items():
            if ext_name not in target_names:
                continue
            found_errors = True
            print(f"\n  {len(errors)} API usage error(s) in {ext_name}:")
            for err in errors:
                loc = f"{err.module_path}:{err.module_lineno}" if err.module_lineno else err.module_path
                if err.attr_name:
                    print(
                        f"    {err.source_path}:{err.source_lineno}"
                        f" imports non-public {err.module_name}.{err.attr_name} ({loc})"
                    )
                else:
                    print(
                        f"    {err.source_path}:{err.source_lineno}"
                        f" imports non-public module {err.module_name} ({loc})"
                    )
        if not found_errors:
            print("  No API usage errors.")

    # Generate python_api.md for each target
    changed = []
    for ext in targets:
        print(f"Generating python_api.md for {ext.name}...")
        if ext.generate_public_api_doc(analyzer):
            changed.append(ext.name)
            print(f"  Updated: {os.path.dirname(ext.config_path)}/python_api.md")
        else:
            print(f"  Already up-to-date.")

    if changed:
        print(f"\n{len(changed)} extension(s) updated:")
        for name in changed:
            print(f"  {name}")
    else:
        print("\nAll targeted extensions are up-to-date.")

    return 0


def main() -> None:
    """CLI entry point for run_checkapi."""
    parser = argparse.ArgumentParser(
        description="Run checkapi on specific extensions instead of the entire repo.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Examples:\n"
        "  python tools/isaac/pre_merge/run_checkapi.py isaacsim.core.telemetry\n"
        "  python tools/isaac/pre_merge/run_checkapi.py isaacsim.core.telemetry isaacsim.robot.poser\n"
        "  python tools/isaac/pre_merge/run_checkapi.py --list\n",
    )
    parser.add_argument("extensions", nargs="*", help="Extension name(s) to check")
    parser.add_argument("-c", "--config", default="release", help="Build configuration (default: release)")
    parser.add_argument("--check", action="store_true", help="Also run API usage checks (not just generation)")
    parser.add_argument("--list", action="store_true", dest="list_exts", help="List all available extensions and exit")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose logging")

    args = parser.parse_args()
    sys.exit(run(args.extensions, args.config, args.check, args.verbose, args.list_exts))


if __name__ == "__main__":
    main()
