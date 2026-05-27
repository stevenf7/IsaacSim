# SPDX-FileCopyrightText: Copyright (c) 2025-2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
"""Third-party OSS baseline generator and MR gate.

Scans a built release tree for Python ``.dist-info`` packages, classifies
each by license against ``license_policy.toml``, and either writes a fresh
``baseline.csv`` (``generate``) or diffs the current snapshot against the
committed baseline and fails if a new restricted-licensed package landed
without an OSRB exception (``check``). See ``README_INTERNAL.md`` for the
OSRB workflow.
"""

from __future__ import annotations

import argparse
import csv
import email.parser
import json
import logging
import os
import re
import sys
from collections.abc import Callable
from fnmatch import fnmatch
from pathlib import Path

try:
    import tomllib  # type: ignore[import-not-found]
except ModuleNotFoundError:
    import tomli as tomllib  # type: ignore[no-redef]


_THIS_DIR = Path(__file__).resolve().parent
REPO_ROOT = _THIS_DIR.parent.parent.parent
DEFAULT_RELEASE_DIR = "_build/linux-x86_64/release"
DEFAULT_BASELINE = _THIS_DIR / "baseline.csv"
DEFAULT_POLICY = _THIS_DIR / "license_policy.toml"
DEFAULT_OUTPUT_DIR = REPO_ROOT
CURRENT_SNAPSHOT_FILENAME = "oss_baseline_current.csv"
DIFF_REPORT_FILENAME = "oss_baseline_diff.json"

CSV_FIELDS = [
    "name",
    "version",
    "license",
    "license_normalized",
    "location",
    "classification",
    "osrb_ticket",  # populated on classification=exception, empty otherwise
]

CLASSIFICATION_ALLOWED = "allowed"
CLASSIFICATION_RESTRICTED = "restricted"
CLASSIFICATION_EXCEPTION = "exception"
CLASSIFICATION_UNKNOWN = "unknown"

REGRESSION_RESTRICTED = "restricted_no_exception"
REGRESSION_UNKNOWN = "unknown_license_blocked_by_policy"

# Every [[exceptions]] entry must point at an OSRB nvbug. Pattern is intentionally
# strict (NVIDIA-internal hostname only) so a copy-pasted Jira / Confluence link
# is rejected at load time rather than silently accepted.
NVBUG_URL_PATTERN = re.compile(r"^https?://(?:www\.)?nvbugspro\.nvidia\.com/bug/\d+/?$")

logger = logging.getLogger("oss_baseline")


# ---------------------------------------------------------------------------
# License normalization
# ---------------------------------------------------------------------------

# Order matters: most-specific patterns first. The first matching rule wins.
# Patterns match against the *upper-cased* raw license text. They aim to map
# the messy strings produced by extract_license_from_metadata into SPDX-ish
# identifiers that the policy file can reason about.
_NORMALIZATION_RULES: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\bAGPL[\s\-]?V?3"), "AGPL-3.0"),
    (re.compile(r"\bAFFERO\b.*\b3"), "AGPL-3.0"),
    (re.compile(r"\bLGPL[\s\-]?V?3"), "LGPL-3.0"),
    # LGPL-2.x: the trailing "1" must be required so bare "LGPLv2" / "LGPL-2.0"
    # do not collapse into LGPL-2.1 (a distinct license).
    (re.compile(r"\bLGPL[\s\-]?V?2[\.\-]?1\b"), "LGPL-2.1"),
    (re.compile(r"\bLGPL[\s\-]?V?2(?:[\.\-]?0)?\b"), "LGPL-2.0"),
    (re.compile(r"\bLESSER GENERAL PUBLIC LICENSE\b.*V?3"), "LGPL-3.0"),
    (re.compile(r"\bLESSER GENERAL PUBLIC LICENSE\b.*V?2[\.\-]?1\b"), "LGPL-2.1"),
    (re.compile(r"\bLESSER GENERAL PUBLIC LICENSE\b.*V?2(?:[\.\-]?0)?\b"), "LGPL-2.0"),
    # Bare "Lesser General Public License" (no version) -> LGPL-2.1: most
    # common modern flavor and UNKNOWN would slip past unknown_policy=warn.
    (re.compile(r"\bLESSER GENERAL PUBLIC LICENSE\b"), "LGPL-2.1"),
    (re.compile(r"\bGPL[\s\-]?V?3"), "GPL-3.0"),
    (re.compile(r"\bGPL[\s\-]?V?2"), "GPL-2.0"),
    (re.compile(r"\bGENERAL PUBLIC LICENSE\b.*V?3"), "GPL-3.0"),
    (re.compile(r"\bGENERAL PUBLIC LICENSE\b.*V?2"), "GPL-2.0"),
    (re.compile(r"\bGPL\b"), "GPL-2.0"),
    (re.compile(r"\bAPACHE\b.*2"), "Apache-2.0"),
    (re.compile(r"\bAPACHE\b"), "Apache"),
    (re.compile(r"\bMIT\b"), "MIT"),
    (re.compile(r"\bEXPAT\b"), "MIT"),
    (re.compile(r"\bBSD[\s\-]?3[\s\-]?CLAUSE"), "BSD-3-Clause"),
    (re.compile(r"\bBSD[\s\-]?2[\s\-]?CLAUSE"), "BSD-2-Clause"),
    (re.compile(r"\bNEW BSD\b"), "BSD-3-Clause"),
    (re.compile(r"\bSIMPLIFIED BSD\b"), "BSD-2-Clause"),
    (re.compile(r"\bBSD\b"), "BSD"),
    (re.compile(r"\bMOZILLA PUBLIC LICENSE\b.*2"), "MPL-2.0"),
    (re.compile(r"\bMPL[\s\-]?2"), "MPL-2.0"),
    (re.compile(r"\bISC\b"), "ISC"),
    (re.compile(r"\bZLIB\b"), "Zlib"),
    (re.compile(r"\bUNLICENSE\b"), "Unlicense"),
    (re.compile(r"\bCC0\b"), "CC0-1.0"),
    (re.compile(r"\bPUBLIC DOMAIN\b"), "CC0-1.0"),
    (re.compile(r"\bPYTHON SOFTWARE FOUNDATION\b"), "PSF-2.0"),
    (re.compile(r"\bPSF\b"), "PSF-2.0"),
    (re.compile(r"\bPYTHON LICENSE\b"), "Python-2.0"),
    (re.compile(r"\bPYTHON-2\.0\b"), "Python-2.0"),
    (re.compile(r"\bSSPL\b"), "SSPL-1.0"),
    (re.compile(r"\bSERVER SIDE PUBLIC LICENSE\b"), "SSPL-1.0"),
    (re.compile(r"\bBUSL\b"), "BUSL-1.1"),
    (re.compile(r"\bBUSINESS SOURCE LICENSE\b"), "BUSL-1.1"),
    (re.compile(r"\bCC[\s\-]?BY[\s\-]?NC\b"), "CC-BY-NC-4.0"),
    (re.compile(r"\bCC[\s\-]?BY\b"), "CC-BY-4.0"),
    (re.compile(r"\bPROPRIETARY\b"), "Proprietary"),
    (re.compile(r"\bNVIDIA\b"), "NVIDIA-Proprietary"),
]


def normalize_license(raw_license: str) -> str:
    """Map a raw license string to an SPDX-ish identifier or "UNKNOWN".

    The input comes from ``extract_license_from_metadata`` and may be a
    classifier ("License :: OSI Approved :: MIT License"), a free-form License
    field ("BSD-3-Clause"), a fallback ("See LICENSE file"), or "Unknown".
    """
    if not raw_license:
        return "UNKNOWN"
    text = raw_license.strip()
    if text.lower() in ("unknown", "see license file", "see metadata license field", ""):
        return "UNKNOWN"
    upper = text.upper()
    for pattern, normalized in _NORMALIZATION_RULES:
        if pattern.search(upper):
            return normalized
    return "UNKNOWN"


# ---------------------------------------------------------------------------
# Policy
# ---------------------------------------------------------------------------


def _validate_exceptions(
    exceptions: list,
    restricted_licenses: set,
    policy_path: Path,
) -> None:
    """Enforce that every ``[[exceptions]]`` entry that can shield a restricted
    license is OSRB-traceable.

    Policy:

        * ``package`` is always required (non-empty string, fnmatch glob OK).
        * ``osrb_ticket`` (matching ``NVBUG_URL_PATTERN``) is required iff the
          entry can match a package carrying a *restricted* license. That is
          true when either:
            - ``license`` is set and is in ``restricted_licenses``, or
            - ``license`` is unset, since an unset license filter matches any
              license -- including restricted ones -- so the entry could
              silently clear a future restricted regression.
        * For exceptions whose ``license`` is allowed (e.g. ``MIT``) or simply
          not in ``restricted_licenses``, ``osrb_ticket`` is optional. If it
          *is* set, its format is still validated.

    Raises ``ValueError`` listing every offending entry; intentionally fails
    loudly at policy-load time so a malformed exception cannot be silently
    relied on by the MR gate.
    """
    errors: list[str] = []
    for i, entry in enumerate(exceptions):
        loc = f"{policy_path}: [[exceptions]][{i}]"
        if not isinstance(entry, dict):
            errors.append(f"{loc}: entry must be a TOML table")
            continue

        package = entry.get("package")
        if not isinstance(package, str) or not package.strip():
            errors.append(f"{loc}: 'package' is required and must be a non-empty string")

        license_field = entry.get("license")
        license_is_str = isinstance(license_field, str)
        if license_field is not None and not license_is_str:
            errors.append(f"{loc}: 'license' must be a string if set")

        # Decide whether this entry could clear a restricted regression.
        if license_is_str:
            shields_restricted = license_field in restricted_licenses
        else:
            # license unset or invalid -> entry would match any license, so
            # treat as if it could shield a restricted package.
            shields_restricted = True

        osrb_ticket = entry.get("osrb_ticket")
        ticket_present = isinstance(osrb_ticket, str) and osrb_ticket.strip() != ""

        if shields_restricted and not ticket_present:
            if license_is_str:
                why = f"because license={license_field!r} is in restricted_licenses"
            else:
                why = (
                    "because no 'license' is set, so this entry would match any " "license -- including restricted ones"
                )
            errors.append(
                f"{loc}: 'osrb_ticket' is required {why}. Clone the template at "
                "https://nvbugspro.nvidia.com/bug/2885977 and use the resulting URL."
            )

        if ticket_present and not NVBUG_URL_PATTERN.match(osrb_ticket.strip()):
            errors.append(
                f"{loc}: 'osrb_ticket' must be an nvbug URL of the form "
                f"https://nvbugspro.nvidia.com/bug/<id>; got {osrb_ticket!r}"
            )

        for optional_key in ("version_pattern", "comment"):
            if optional_key in entry and not isinstance(entry[optional_key], str):
                errors.append(f"{loc}: '{optional_key}' must be a string if set")

    if errors:
        bullets = "\n  - ".join(errors)
        raise ValueError(
            f"Invalid exception entries in {policy_path}:\n  - {bullets}\n"
            "See tools/isaac/oss_baseline/README_INTERNAL.md for the workflow."
        )


class LicensePolicy:
    """Parsed view of ``license_policy.toml``."""

    def __init__(
        self,
        allowed: set[str],
        restricted: set[str],
        exceptions: list[dict],
        unknown_policy: str,
        path: Path,
        excluded_locations: list[str] | None = None,
    ) -> None:
        self.allowed = set(allowed)
        self.restricted = set(restricted)
        self.exceptions = exceptions
        self.unknown_policy = unknown_policy
        self.path = path
        self.excluded_locations: list[str] = list(excluded_locations or [])

    @classmethod
    def load(cls, path: Path) -> "LicensePolicy":
        with open(path, "rb") as f:
            data = tomllib.load(f)
        unknown_policy = str(data.get("unknown_policy", "warn")).lower()
        if unknown_policy not in ("warn", "fail"):
            raise ValueError(f"{path}: unknown_policy must be 'warn' or 'fail', got {unknown_policy!r}")
        exceptions = list(data.get("exceptions", []))
        restricted = set(data.get("restricted_licenses", []))
        _validate_exceptions(exceptions, restricted, path)
        excluded_locations = data.get("excluded_locations", []) or []
        if not isinstance(excluded_locations, list) or not all(
            isinstance(s, str) and s.strip() for s in excluded_locations
        ):
            raise ValueError(f"{path}: 'excluded_locations' must be a list of non-empty strings")
        return cls(
            allowed=set(data.get("allowed_licenses", [])),
            restricted=restricted,
            exceptions=exceptions,
            unknown_policy=unknown_policy,
            path=path,
            excluded_locations=[s.strip("/") for s in excluded_locations],
        )

    def is_excluded_location(self, location: str) -> bool:
        """Return True if the package's release-tree location is under an
        excluded top-level directory.

        Match semantics: each ``excluded_locations`` entry is treated as a
        top-level directory name. A package is excluded iff its ``location``
        equals that name or starts with ``"<name>/"``. This intentionally
        does not use fnmatch globs -- the policy file should stay readable
        as a list of plain directory names.
        """
        if not location:
            return False
        for excl in self.excluded_locations:
            if location == excl or location.startswith(excl + "/"):
                return True
        return False

    def _find_matching_exception(self, name: str, version: str, license_normalized: str) -> dict | None:
        for entry in self.exceptions:
            pkg = entry.get("package", "")
            ver_pat = entry.get("version_pattern", "*")
            lic = entry.get("license")
            if not fnmatch(name, pkg):
                continue
            if not fnmatch(version, ver_pat):
                continue
            if lic and lic != license_normalized:
                continue
            return entry
        return None

    def classify(self, name: str, version: str, license_normalized: str) -> tuple[str, str]:
        """Return ``(classification, osrb_ticket)`` for a single package.

        ``osrb_ticket`` is non-empty only when the package matches an
        ``[[exceptions]]`` entry that has a ticket URL set. ``allowed``
        matches first by design -- a package that happens to match both an
        allowed license and an exception entry is still allowed (and gets
        no ticket attribution, since the exception isn't what cleared it).
        """
        if license_normalized in self.allowed:
            return CLASSIFICATION_ALLOWED, ""
        match = self._find_matching_exception(name, version, license_normalized)
        if match is not None:
            return CLASSIFICATION_EXCEPTION, str(match.get("osrb_ticket", "") or "")
        if license_normalized in self.restricted:
            return CLASSIFICATION_RESTRICTED, ""
        return CLASSIFICATION_UNKNOWN, ""


# ---------------------------------------------------------------------------
# Dist-info scanning
# ---------------------------------------------------------------------------


def find_dist_info_dirs(root_path: Path, follow_symlinks: bool = True) -> list[tuple[Path, str]]:
    """Find all .dist-info directories which indicate installed Python packages.

    Returns list of tuples: (directory_path, package_name-version).
    """
    dist_info_dirs = []
    for dirpath, dirnames, _filenames in os.walk(root_path, followlinks=follow_symlinks):
        for dirname in dirnames:
            if dirname.endswith(".dist-info"):
                full_path = Path(dirpath) / dirname
                dist_info_dirs.append((full_path, dirname.replace(".dist-info", "")))
    return dist_info_dirs


def parse_package_name_version(package_identifier: str) -> tuple[str, str]:
    """Parse package name and version from a 'name-version' identifier.

    Splits at the first dash/underscore followed by a digit-and-dot
    (PEP 440-ish version pattern). Returns (name, "unknown") if no match.
    """
    match = re.match(r"^(.+?)[-_](\d+\..*)$", package_identifier)
    if match:
        return match.group(1), match.group(2)
    return package_identifier, "unknown"


def _identify_license_from_text(text: str) -> str | None:
    """Identify a common license type by pattern-matching raw text."""
    upper = text.upper()
    if "MIT LICENSE" in upper:
        return "MIT License"
    if "APACHE LICENSE" in upper:
        if "2.0" in upper:
            return "Apache License 2.0"
        return "Apache License"
    if "BSD LICENSE" in upper:
        if "3-CLAUSE" in upper:
            return "BSD 3-Clause License"
        if "2-CLAUSE" in upper:
            return "BSD 2-Clause License"
        return "BSD License"
    if "GPL" in upper:
        return "GPL License"
    return None


def extract_license_from_metadata(dist_info_path: Path) -> str:
    """Extract license info from a .dist-info directory's METADATA file.

    Tries the Classifier ``License ::`` line first (most reliable), then the
    raw ``License`` field, then a sibling LICENSE/COPYING file. Returns
    ``"Unknown"`` if nothing usable is found.
    """
    metadata_file = dist_info_path / "METADATA"
    if metadata_file.exists():
        try:
            with open(metadata_file, encoding="utf-8", errors="ignore") as f:
                parser = email.parser.Parser()
                metadata = parser.parse(f)

                classifiers = metadata.get_all("Classifier", [])
                if classifiers:
                    for classifier in classifiers:
                        if classifier.startswith("License ::"):
                            license_name = classifier.split("::")[-1].strip()
                            return license_name

                license_text = metadata.get("License", "").strip()
                if license_text and license_text not in ["", "UNKNOWN", "Unknown"]:
                    if len(license_text) > 100:
                        first_line = license_text.split("\n")[0].strip()
                        if len(first_line) < 100 and first_line:
                            return first_line
                        identified = _identify_license_from_text(license_text[:500])
                        if identified:
                            return identified
                        return "See METADATA License field"
                    return license_text
        except Exception:
            pass

    license_files = list(dist_info_path.glob("LICENSE*")) + list(dist_info_path.glob("COPYING*"))
    if license_files:
        try:
            with open(license_files[0], encoding="utf-8", errors="ignore") as f:
                content = f.read(500)
                identified = _identify_license_from_text(content)
                if identified:
                    return identified
                return "See LICENSE file"
        except Exception:
            return "See LICENSE file"

    return "Unknown"


def get_parent_directory_type(package_path: Path, release_root: Path) -> str:
    """Categorize the kind of directory a package lives under.

    Returns labels like 'pip_prebundle (...)', 'site-packages (...)',
    'python_packages (...)', or 'other (...)'.
    """
    try:
        relative_path = package_path.relative_to(release_root)
        parts = relative_path.parts
        if "pip_prebundle" in parts:
            idx = parts.index("pip_prebundle")
            return f"pip_prebundle ({'/'.join(parts[:idx])})"
        if "site-packages" in parts:
            idx = parts.index("site-packages")
            return f"site-packages ({'/'.join(parts[:idx])})"
        if "python_packages" in parts:
            return f"python_packages ({'/'.join(parts[:1])})"
        return f"other ({'/'.join(parts[:min(3, len(parts))])})"
    except ValueError:
        return "unknown"


def get_package_details(dist_info_path: Path, package_identifier: str, release_root: Path) -> dict[str, str]:
    """Extract name, version, license, location for a single .dist-info dir."""
    name, version = parse_package_name_version(package_identifier)
    license_info = extract_license_from_metadata(dist_info_path)
    try:
        relative_path = str(dist_info_path.parent.relative_to(release_root))
    except ValueError:
        relative_path = str(dist_info_path.parent)
    location_type = get_parent_directory_type(dist_info_path.parent, release_root)
    return {
        "name": name,
        "version": version,
        "license": license_info,
        "location": relative_path,
        "location_type": location_type,
    }


def clean_location_path(location: str) -> str:
    """Strip versioned suffixes from extension directory names in a path.

    Removes patterns like ``-0.18.1+109.0.0.lx64.cp312`` so paths that point
    at the same logical extension across versions collapse to a single key.
    """
    parts = location.split("/")
    cleaned_parts = []
    for part in parts:
        match = re.match(r"^([a-zA-Z_][\w.]*)-(\d+.*)$", part)
        if match:
            cleaned_parts.append(match.group(1))
        else:
            cleaned_parts.append(part)
    return "/".join(cleaned_parts)


# ---------------------------------------------------------------------------
# Snapshot generation
# ---------------------------------------------------------------------------


def collect_packages(release_dir: Path) -> list[dict[str, str]]:
    """Scan ``release_dir`` and return one row per unique (name, version) package.

    Rows are sorted by (name, version). De-duplicates packages reachable via
    symlinks by keeping the entry with the shortest path.
    """
    if not release_dir.exists():
        raise FileNotFoundError(f"Release directory not found: {release_dir}")

    dist_info_dirs = find_dist_info_dirs(release_dir, follow_symlinks=True)

    # Tuple key (matching diff_snapshots) so dedup is by exact (name, version).
    packages_map: dict[tuple[str, str], dict[str, str]] = {}
    for dist_info_path, package_identifier in dist_info_dirs:
        details = get_package_details(dist_info_path, package_identifier, release_dir)
        details["location"] = clean_location_path(details["location"])
        details.pop("location_type", None)

        key = (details["name"], details["version"])
        if key in packages_map:
            existing = packages_map[key]["location"]
            if len(details["location"]) < len(existing):
                packages_map[key] = details
        else:
            packages_map[key] = details

    rows: list[dict[str, str]] = []
    for pkg in packages_map.values():
        rows.append(
            {
                "name": pkg["name"],
                "version": pkg["version"],
                "license": pkg.get("license", "Unknown"),
                "location": pkg.get("location", ""),
            }
        )
    rows.sort(key=lambda r: (r["name"].lower(), r["version"]))
    return rows


def filter_excluded_locations(
    rows: list[dict[str, str]], policy: LicensePolicy
) -> tuple[list[dict[str, str]], dict[str, int]]:
    """Drop rows whose ``location`` is under an excluded top-level directory.

    Returns ``(kept_rows, excluded_counts)`` where ``excluded_counts`` is
    keyed by the matching ``excluded_locations`` entry so callers can report
    how many rows were filtered per excluded directory.
    """
    if not policy.excluded_locations:
        return rows, {}
    kept: list[dict[str, str]] = []
    counts: dict[str, int] = {excl: 0 for excl in policy.excluded_locations}
    for row in rows:
        location = row.get("location", "")
        excluded_under = next(
            (excl for excl in policy.excluded_locations if location == excl or location.startswith(excl + "/")),
            None,
        )
        if excluded_under is None:
            kept.append(row)
        else:
            counts[excluded_under] += 1
    return kept, counts


def annotate_with_policy(rows: list[dict[str, str]], policy: LicensePolicy) -> list[dict[str, str]]:
    """Add ``license_normalized``, ``classification`` and ``osrb_ticket`` to each row."""
    annotated: list[dict[str, str]] = []
    for row in rows:
        normalized = normalize_license(row.get("license", ""))
        classification, osrb_ticket = policy.classify(row["name"], row["version"], normalized)
        annotated.append(
            {
                "name": row["name"],
                "version": row["version"],
                "license": row.get("license", "Unknown"),
                "license_normalized": normalized,
                "location": row.get("location", ""),
                "classification": classification,
                "osrb_ticket": osrb_ticket,
            }
        )
    return annotated


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    # lineterminator="\n" overrides csv's default \r\n so the file matches the
    # repo's LF-only convention and doesn't show as "modified" on every regen.
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def read_csv(path: Path) -> list[dict[str, str]]:
    """Read a baseline / snapshot CSV. Returns [] if the file is missing or empty.

    Tolerates extra columns and missing optional columns (license_normalized,
    classification, osrb_ticket) by filling defaults so older baselines still
    load cleanly across schema additions.
    """
    if not path.exists() or path.stat().st_size == 0:
        return []
    rows: list[dict[str, str]] = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(
                {
                    "name": row.get("name", ""),
                    "version": row.get("version", ""),
                    "license": row.get("license", ""),
                    "license_normalized": row.get("license_normalized", ""),
                    "location": row.get("location", ""),
                    "classification": row.get("classification", ""),
                    "osrb_ticket": row.get("osrb_ticket", ""),
                }
            )
    return rows


# ---------------------------------------------------------------------------
# Diff + regression detection
# ---------------------------------------------------------------------------


def diff_snapshots(
    baseline: list[dict[str, str]],
    current: list[dict[str, str]],
    policy: LicensePolicy,
) -> dict:
    """Compute added / removed / version-changed / regression sets.

    Keying is on ``(name, version)`` because the baseline can legitimately
    contain the same package at multiple versions (e.g. aioboto3 14.x and
    15.x co-exist when different extensions pin different versions). Keying
    by name alone would silently drop all but one row per name and
    potentially miss a restricted-license regression.

    "version_changed" is now a derived view computed AFTER the raw
    add/remove set difference: a name that has at least one row in both the
    added and removed sets is flagged as a version bump, and those rows are
    moved out of ``added`` / ``removed`` into ``version_changed`` for human
    readability. The restricted-license check is applied uniformly to both
    ``added`` and ``version_changed`` rows.
    """
    bl_keys: dict[tuple[str, str], dict[str, str]] = {(r["name"], r["version"]): r for r in baseline}
    cur_keys: dict[tuple[str, str], dict[str, str]] = {(r["name"], r["version"]): r for r in current}

    added_keys = sorted(cur_keys.keys() - bl_keys.keys())
    removed_keys = sorted(bl_keys.keys() - cur_keys.keys())

    # Group raw add/remove by package name to detect version-bump pairs.
    added_by_name: dict[str, list[dict[str, str]]] = {}
    for k in added_keys:
        added_by_name.setdefault(k[0], []).append(cur_keys[k])
    removed_by_name: dict[str, list[dict[str, str]]] = {}
    for k in removed_keys:
        removed_by_name.setdefault(k[0], []).append(bl_keys[k])
    bumped_names = added_by_name.keys() & removed_by_name.keys()

    added: list[dict[str, str]] = []
    # version_changed rows carry an extra "previous_versions" key (list[str]).
    version_changed: list[dict[str, str | list[str]]] = []
    for name, rows in added_by_name.items():
        if name in bumped_names:
            previous_versions = sorted({r["version"] for r in removed_by_name[name]})
            for r in rows:
                version_changed.append({**r, "previous_versions": previous_versions})
        else:
            added.extend(rows)

    removed: list[dict[str, str]] = []
    for name, rows in removed_by_name.items():
        if name not in bumped_names:
            removed.extend(rows)

    regressions: list[dict[str, str]] = []
    for row in added:
        _maybe_record_regression(row, policy, regressions, change_kind="added")
    for row in version_changed:
        _maybe_record_regression(row, policy, regressions, change_kind="version_changed")

    summary = {
        "total_baseline": len(baseline),
        "total_current": len(current),
        "added": len(added),
        "removed": len(removed),
        "version_changed": len(version_changed),
        "regressions": len(regressions),
    }

    return {
        "summary": summary,
        "added": added,
        "removed": removed,
        "version_changed": version_changed,
        "regressions": regressions,
        "policy": {
            "path": str(policy.path),
            "unknown_policy": policy.unknown_policy,
            "allowed_count": len(policy.allowed),
            "restricted_count": len(policy.restricted),
            "exception_count": len(policy.exceptions),
        },
    }


def _maybe_record_regression(
    row: dict[str, str],
    policy: LicensePolicy,
    regressions: list[dict[str, str]],
    change_kind: str,
) -> None:
    classification = row.get("classification", CLASSIFICATION_UNKNOWN)
    reason: str | None = None
    if classification == CLASSIFICATION_RESTRICTED:
        reason = REGRESSION_RESTRICTED
    elif classification == CLASSIFICATION_UNKNOWN and policy.unknown_policy == "fail":
        reason = REGRESSION_UNKNOWN
    if reason is None:
        return
    regressions.append(
        {
            "name": row["name"],
            "version": row["version"],
            "license": row.get("license", ""),
            "license_normalized": row.get("license_normalized", ""),
            "location": row.get("location", ""),  # surfaced in the failure log
            "classification": classification,
            "change_kind": change_kind,
            "reason": reason,
        }
    )


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------


def print_diff_summary(diff: dict, policy: LicensePolicy) -> None:
    summary = diff["summary"]
    print("=" * 80)
    print("OSS BASELINE DIFF")
    print("=" * 80)
    print(f"Baseline packages: {summary['total_baseline']}")
    print(f"Current packages:  {summary['total_current']}")
    print(f"Added:             {summary['added']}")
    print(f"Removed:           {summary['removed']}")
    print(f"Version changed:   {summary['version_changed']}")
    print(f"Regressions:       {summary['regressions']}")
    print(f"unknown_policy:    {policy.unknown_policy}")
    print("-" * 80)

    if diff["added"]:
        print("ADDED:")
        for row in diff["added"]:
            print(
                f"  + {row['name']}=={row['version']}  "
                f"[{row.get('license_normalized', '?')} / {row.get('classification', '?')}]"
            )
    if diff["version_changed"]:
        print("VERSION CHANGED:")
        for row in diff["version_changed"]:
            previous = ",".join(row.get("previous_versions") or []) or "?"
            print(
                f"  ~ {row['name']}: {previous} -> {row['version']}  "
                f"[{row.get('license_normalized', '?')} / {row.get('classification', '?')}]"
            )
    if diff["removed"]:
        print("REMOVED:")
        for row in diff["removed"]:
            print(f"  - {row['name']}=={row['version']}")

    if diff["regressions"]:
        print("-" * 80)
        print("REGRESSIONS (this run will FAIL):")
        for row in diff["regressions"]:
            location = row.get("location") or "(unknown location)"
            print(f"  ! {row['name']}=={row['version']}")
            print(f"      location: {location}")
            print(f"      license:  {row['license_normalized']}  ({row['reason']})")
        # relative_to() raises ValueError when the policy isn't under REPO_ROOT
        # (e.g. ad-hoc `--policy /tmp/foo.toml`); fall back to the absolute path.
        try:
            display_policy_path = policy.path.relative_to(REPO_ROOT)
        except ValueError:
            display_policy_path = policy.path
        print(
            "\nResolve by either: (1) removing the dependency from the location "
            "above, (2) replacing it with an allowed-licensed equivalent, or "
            "(3) filing an OSRB nvbug (clone "
            "https://nvbugspro.nvidia.com/bug/2885977) and adding an "
            f"[[exceptions]] entry to {display_policy_path} with the new ticket URL."
        )
    print("=" * 80)


# ---------------------------------------------------------------------------
# Mode implementations
# ---------------------------------------------------------------------------


def _print_exclusion_summary(excluded_counts: dict[str, int]) -> None:
    if not excluded_counts:
        return
    total = sum(excluded_counts.values())
    if total == 0:
        return
    print(f"Excluded {total} packages owned by other teams (per excluded_locations):")
    for excl in sorted(excluded_counts):
        n = excluded_counts[excl]
        if n:
            print(f"  - {excl}/: {n} packages dropped")


def run_generate(
    release_dir: Path,
    baseline_path: Path,
    policy_path: Path,
    update_baseline: bool,
    output_dir: Path,
) -> int:
    policy = LicensePolicy.load(policy_path)
    print(f"Scanning {release_dir} for Python packages...")
    rows = collect_packages(release_dir)
    rows, excluded_counts = filter_excluded_locations(rows, policy)
    _print_exclusion_summary(excluded_counts)
    annotated = annotate_with_policy(rows, policy)

    snapshot_path = output_dir / CURRENT_SNAPSHOT_FILENAME
    write_csv(snapshot_path, annotated)
    print(f"Wrote current snapshot ({len(annotated)} packages) to {snapshot_path}")

    if update_baseline:
        write_csv(baseline_path, annotated)
        print(f"Updated committed baseline at {baseline_path}")

    classification_counts: dict[str, int] = {}
    for row in annotated:
        classification_counts[row["classification"]] = classification_counts.get(row["classification"], 0) + 1
    print("Classification breakdown:")
    for label in (
        CLASSIFICATION_ALLOWED,
        CLASSIFICATION_EXCEPTION,
        CLASSIFICATION_UNKNOWN,
        CLASSIFICATION_RESTRICTED,
    ):
        print(f"  {label}: {classification_counts.get(label, 0)}")
    return 0


def run_check(
    release_dir: Path,
    baseline_path: Path,
    policy_path: Path,
    output_dir: Path,
    snapshot_path: Path | None = None,
) -> int:
    policy = LicensePolicy.load(policy_path)
    if snapshot_path is not None:
        # Fast path: a pre-computed snapshot is provided (e.g. emitted by an
        # upstream job, or saved from a previous local run). Diff directly
        # against the committed baseline -- skips the release-tree scan.
        print(f"Loading pre-computed snapshot from {snapshot_path}...")
        if not snapshot_path.exists():
            raise FileNotFoundError(f"Snapshot CSV not found: {snapshot_path}")
        current_annotated = read_csv(snapshot_path)
        if not current_annotated:
            raise ValueError(f"Snapshot CSV is empty or has no data rows: {snapshot_path}")
        # Re-apply exclusions + re-classify against the current policy in case
        # license_policy.toml changed since the snapshot was generated.
        # (Re-uses the snapshot's stored license_normalized rather than
        # re-running normalize_license -- fine for single-job CI.)
        current_annotated, excluded_counts = filter_excluded_locations(current_annotated, policy)
        _print_exclusion_summary(excluded_counts)
        reclassified: list[dict[str, str]] = []
        for row in current_annotated:
            classification, osrb_ticket = policy.classify(row["name"], row["version"], row["license_normalized"])
            reclassified.append({**row, "classification": classification, "osrb_ticket": osrb_ticket})
        current_annotated = reclassified
        print(f"Loaded {len(current_annotated)} packages from snapshot")
    else:
        print(f"Scanning {release_dir} for Python packages...")
        current_rows = collect_packages(release_dir)
        current_rows, excluded_counts = filter_excluded_locations(current_rows, policy)
        _print_exclusion_summary(excluded_counts)
        current_annotated = annotate_with_policy(current_rows, policy)

    out_snapshot = output_dir / CURRENT_SNAPSHOT_FILENAME
    write_csv(out_snapshot, current_annotated)
    print(f"Wrote current snapshot ({len(current_annotated)} packages) to {out_snapshot}")

    baseline_rows = read_csv(baseline_path)
    if not baseline_rows:
        print(
            f"WARNING: baseline at {baseline_path} is empty or missing; treating every "
            "current package as 'added' for this run. Regenerate with "
            "`repo generate_oss_baseline --update-baseline` to bootstrap.",
            file=sys.stderr,
        )

    diff = diff_snapshots(baseline_rows, current_annotated, policy)
    diff_path = output_dir / DIFF_REPORT_FILENAME
    diff_path.parent.mkdir(parents=True, exist_ok=True)
    with open(diff_path, "w", encoding="utf-8") as f:
        json.dump(diff, f, indent=2, sort_keys=True)
    print(f"Wrote diff report to {diff_path}")

    print_diff_summary(diff, policy)

    if diff["regressions"]:
        return 1
    return 0


# ---------------------------------------------------------------------------
# CLI / repo-tool entry points
# ---------------------------------------------------------------------------


def _add_common_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--release-dir",
        default=DEFAULT_RELEASE_DIR,
        help=f"Path to the built release directory to scan (default: {DEFAULT_RELEASE_DIR}).",
    )
    parser.add_argument(
        "--baseline",
        default=str(DEFAULT_BASELINE),
        help=f"Path to the committed baseline CSV (default: {DEFAULT_BASELINE.relative_to(REPO_ROOT)}).",
    )
    parser.add_argument(
        "--policy",
        default=str(DEFAULT_POLICY),
        help=f"Path to the license policy TOML (default: {DEFAULT_POLICY.relative_to(REPO_ROOT)}).",
    )
    parser.add_argument(
        "--output-dir",
        default=str(DEFAULT_OUTPUT_DIR),
        help=(
            "Directory to write oss_baseline_current.csv and oss_baseline_diff.json "
            "(default: repo root, matching where CI artifacts are collected)."
        ),
    )


def _add_check_only_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--snapshot",
        default=None,
        help=(
            "Path to a pre-computed snapshot CSV (oss_baseline_current.csv) to diff "
            "against the committed baseline. When set, --release-dir is ignored. "
            "Used by the CI gate so the lightweight check job does not need to ship "
            "the multi-GB loose release tree -- the upstream build job emits the "
            "snapshot directly."
        ),
    )


def _resolve_paths(
    options: argparse.Namespace,
) -> tuple[Path, Path, Path, Path, Path | None]:
    release_dir = Path(options.release_dir)
    if not release_dir.is_absolute():
        release_dir = (REPO_ROOT / release_dir).resolve()
    baseline = Path(options.baseline)
    if not baseline.is_absolute():
        baseline = (REPO_ROOT / baseline).resolve()
    policy = Path(options.policy)
    if not policy.is_absolute():
        policy = (REPO_ROOT / policy).resolve()
    output_dir = Path(options.output_dir)
    if not output_dir.is_absolute():
        output_dir = (REPO_ROOT / output_dir).resolve()
    snapshot: Path | None = None
    snapshot_arg = getattr(options, "snapshot", None)
    if snapshot_arg:
        snapshot = Path(snapshot_arg)
        if not snapshot.is_absolute():
            snapshot = (REPO_ROOT / snapshot).resolve()
    return release_dir, baseline, policy, output_dir, snapshot


def setup_repo_tool_generate(parser: argparse.ArgumentParser, config: dict) -> Callable:
    """Entry point for ``repo generate_oss_baseline``."""
    parser.description = "Scan the built release tree and write the OSS baseline CSV."
    _add_common_args(parser)
    parser.add_argument(
        "--update-baseline",
        action="store_true",
        help="Overwrite the committed baseline.csv in addition to the current snapshot.",
    )

    def run_repo_tool(options: argparse.Namespace, config: dict) -> None:
        release_dir, baseline, policy, output_dir, _ = _resolve_paths(options)
        rc = run_generate(
            release_dir=release_dir,
            baseline_path=baseline,
            policy_path=policy,
            update_baseline=options.update_baseline,
            output_dir=output_dir,
        )
        if rc != 0:
            sys.exit(rc)

    return run_repo_tool


def setup_repo_tool_check(parser: argparse.ArgumentParser, config: dict) -> Callable:
    """Entry point for ``repo check_oss_baseline`` (used by the MR pipeline gate)."""
    parser.description = (
        "Diff the current OSS snapshot against the committed baseline and fail if a "
        "new package with a restricted license is added without an OSRB exception."
    )
    _add_common_args(parser)
    _add_check_only_args(parser)

    def run_repo_tool(options: argparse.Namespace, config: dict) -> None:
        release_dir, baseline, policy, output_dir, snapshot = _resolve_paths(options)
        rc = run_check(
            release_dir=release_dir,
            baseline_path=baseline,
            policy_path=policy,
            output_dir=output_dir,
            snapshot_path=snapshot,
        )
        if rc != 0:
            sys.exit(rc)

    return run_repo_tool


def _build_standalone_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate or check the Isaac Sim third-party OSS baseline (Python deps).",
    )
    sub = parser.add_subparsers(dest="mode", required=True)
    p_gen = sub.add_parser("generate", help="Write current snapshot (and optionally update baseline.csv).")
    _add_common_args(p_gen)
    p_gen.add_argument("--update-baseline", action="store_true")
    p_chk = sub.add_parser("check", help="Diff against baseline.csv; fail on restricted-license regression.")
    _add_common_args(p_chk)
    _add_check_only_args(p_chk)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_standalone_parser()
    options = parser.parse_args(argv)
    release_dir, baseline, policy, output_dir, snapshot = _resolve_paths(options)
    if options.mode == "generate":
        return run_generate(
            release_dir=release_dir,
            baseline_path=baseline,
            policy_path=policy,
            update_baseline=options.update_baseline,
            output_dir=output_dir,
        )
    return run_check(
        release_dir=release_dir,
        baseline_path=baseline,
        policy_path=policy,
        output_dir=output_dir,
        snapshot_path=snapshot,
    )


if __name__ == "__main__":
    sys.exit(main())
