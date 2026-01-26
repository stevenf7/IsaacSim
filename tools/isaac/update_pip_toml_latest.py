#!/usr/bin/env python3
"""Update pip*.toml package versions to latest available on PyPI."""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from typing import Dict, List, Optional, Tuple
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

PACKAGE_RE = re.compile(r'"([^"]+)"')
VERSION_RE = re.compile(r"^([^=<>!~\s]+(?:\[[^\]]+\])?)==([^=<>!~\s]+)$")


def fetch_latest_version(package_name: str, timeout: int = 10) -> Optional[str]:
    """Fetch latest version for a package from PyPI."""
    url = f"https://pypi.org/pypi/{package_name}/json"
    request = Request(url, headers={"User-Agent": "isaac-pip-toml-updater/1.0"})
    try:
        with urlopen(request, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
        return payload.get("info", {}).get("version")
    except (HTTPError, URLError, json.JSONDecodeError) as exc:
        print(f"Warning: failed to fetch {package_name} from PyPI ({exc})", file=sys.stderr)
        return None


def update_package_line(
    line: str,
    latest_versions: Dict[str, str],
    cache: Dict[str, Optional[str]],
    sleep_seconds: float,
) -> Tuple[str, Optional[Tuple[str, str, str]]]:
    """Update a single package line; return updated line and change tuple."""
    match = PACKAGE_RE.search(line)
    if not match:
        return line, None

    spec = match.group(1)
    version_match = VERSION_RE.match(spec)
    if not version_match:
        return line, None

    name_part, old_version = version_match.groups()
    base_name = name_part.split("[", 1)[0].lower()

    if base_name in cache:
        latest = cache[base_name]
    else:
        latest = fetch_latest_version(base_name)
        cache[base_name] = latest
        if sleep_seconds > 0:
            time.sleep(sleep_seconds)

    if not latest or latest == old_version:
        return line, None

    latest_versions[base_name] = latest
    new_spec = f"{name_part}=={latest}"
    updated_line = line.replace(f'"{spec}"', f'"{new_spec}"', 1)
    return updated_line, (spec, new_spec, base_name)


def update_pip_toml(path: str, sleep_seconds: float) -> List[Tuple[str, str, str]]:
    """Update all package versions in a pip.toml-style file."""
    with open(path, "r") as file:
        lines = file.readlines()

    updated_lines: List[str] = []
    changes: List[Tuple[str, str, str]] = []
    cache: Dict[str, Optional[str]] = {}
    latest_versions: Dict[str, str] = {}

    in_dependency_section = False
    in_packages_block = False

    for line in lines:
        if "[[dependency]]" in line:
            in_dependency_section = True
            in_packages_block = False
            updated_lines.append(line)
            continue

        if in_dependency_section and "packages = [" in line:
            in_packages_block = True
            updated_lines.append(line)
            continue

        if in_packages_block and "]" in line and not line.strip().startswith("#"):
            in_packages_block = False
            updated_lines.append(line)
            continue

        if in_packages_block and line.strip() and not line.strip().startswith("#"):
            updated_line, change = update_package_line(line, latest_versions, cache, sleep_seconds)
            updated_lines.append(updated_line)
            if change:
                changes.append(change)
            continue

        updated_lines.append(line)

        if in_dependency_section and not line.strip() and not in_packages_block:
            in_dependency_section = False

    with open(path, "w") as file:
        file.writelines(updated_lines)

    return changes


def main() -> None:
    parser = argparse.ArgumentParser(description="Update packages in a pip*.toml file to latest PyPI versions.")
    parser.add_argument("toml_file", help="Path to pip.toml-style file to update.")
    parser.add_argument(
        "--sleep",
        type=float,
        default=0.0,
        help="Seconds to sleep between PyPI requests.",
    )
    args = parser.parse_args()

    changes = update_pip_toml(args.toml_file, args.sleep)
    if changes:
        print("Updated packages:")
        for old_spec, new_spec, base_name in changes:
            print(f"  {base_name}: {old_spec} -> {new_spec}")
    else:
        print("No packages updated.")


if __name__ == "__main__":
    main()
