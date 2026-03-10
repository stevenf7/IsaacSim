#!/usr/bin/env python3
# Copyright (c) 2026, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

"""
Scan Isaac Sim release packages for internal URLs that should not be shipped.

Downloads packages from packman (cloudfront), unpacks them, searches for
internal URL patterns, and produces a CSV report.

Usage:
    # List matching packages without downloading
    python scan_packages.py --version 6.0.0-rc.19 --list-only

    # Full run: download, unzip, scan, report
    python scan_packages.py --version 6.0.0-rc.19

    # Skip download (reuse previously downloaded packages)
    python scan_packages.py --version 6.0.0-rc.19 --skip-download

    # Skip download and unzip (reuse already-unpacked directories)
    python scan_packages.py --version 6.0.0-rc.19 --skip-download --skip-unzip

    # Scan only linux release packages
    python scan_packages.py --version 6.0.0-rc.19 --filter linux --filter release

    # Use custom banned words file
    python scan_packages.py --version 6.0.0-rc.19 --banned-words my_banned_words.json

    # Skip scanning certain subdirectories
    python scan_packages.py --version 6.0.0-rc.19 --exclude-dir kit --exclude-dir extscache

Zip files are downloaded to --packages-dir/ (default: _build/packages/).
In CI, zips are already present as artifact dependencies so --skip-download can be used.
Unpacked directories go to --packages-dir/<version>/<short_name>/.
Report is written to --packages-dir/internal_url_report.csv.
"""

import argparse
import csv
import json
import os
import subprocess
import sys
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[2]

PACKMAN_LIST_API = "http://omnipackages.nvidia.com/api/v1/list/cloudfront/isaac-sim-standalone"
CLOUDFRONT_BASE = "https://d4i3qtqj3r0z5.cloudfront.net"
PACKAGE_NAME = "isaac-sim-standalone"
DEFAULT_BANNED_WORDS_FILE = SCRIPT_DIR / "banned_words.json"
DEFAULT_PACKAGES_DIR = REPO_ROOT / "_build" / "packages"


def load_banned_words(banned_words_file: Path) -> tuple[list[str], list[str]]:
    """Load banned words and allowed patterns from a JSON file."""
    with open(banned_words_file, "r") as f:
        data = json.load(f)
    banned = data.get("banned_words", [])
    allowed = data.get("allowed_patterns", [])
    if not banned:
        print(f"ERROR: No banned_words found in {banned_words_file}", file=sys.stderr)
        sys.exit(1)
    return banned, allowed


def list_packages(version_prefix: str) -> dict:
    """Query the packman cloudfront API and return packages matching version_prefix."""
    print(f"Querying packman API for '{PACKAGE_NAME}' packages matching '{version_prefix}'...")
    try:
        req = urllib.request.Request(PACKMAN_LIST_API, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode())
    except Exception as e:
        print(f"ERROR: Failed to query packman API: {e}", file=sys.stderr)
        sys.exit(1)

    matches = {}
    for filename, info in data.items():
        if "kit-tot" in filename:
            continue
        name_at_version = filename.removesuffix(".zip")
        _, _, version_part = name_at_version.partition("@")
        if version_part.startswith(version_prefix):
            matches[filename] = info

    return matches


def short_name(filename: str) -> str:
    """Extract short platform.config name from a full packman filename.

    e.g. 'isaac-sim-standalone@6.0.0-rc.19+...gl.manylinux_2_35_x86_64.release.zip'
      -> 'manylinux_2_35_x86_64.release.zip'
    """
    parts = filename.split(".gl.")
    if len(parts) == 2:
        return parts[1]
    return filename


def download_package(filename: str, output_dir: Path) -> Path:
    """Download a single package zip from cloudfront."""
    name_version = filename.removesuffix(".zip")
    name, _, version = name_version.partition("@")
    encoded = urllib.parse.quote(f"{name}@{version}", safe="") + ".zip"
    url = f"{CLOUDFRONT_BASE}/{encoded}"

    dest = output_dir / filename
    if dest.exists():
        print(f"  Already exists: {dest.name}")
        return dest

    print(f"  Downloading: {filename}")
    print(f"    URL: {url}")
    try:
        urllib.request.urlretrieve(url, str(dest))
    except Exception as e:
        print(f"  ERROR downloading {filename}: {e}", file=sys.stderr)
        if dest.exists():
            dest.unlink()
        raise
    size_gb = dest.stat().st_size / (1024**3)
    print(f"    Done ({size_gb:.2f} GB)")
    return dest


def unzip_package(zip_path: Path, output_dir: Path, dir_name: str = None) -> Path:
    """Unzip a package to a named directory under output_dir."""
    extract_dir = output_dir / (dir_name or zip_path.stem)
    if extract_dir.exists() and any(extract_dir.iterdir()):
        print(f"  Already unpacked: {extract_dir.name}")
        return extract_dir

    print(f"  Unpacking: {zip_path.name}")
    extract_dir.mkdir(parents=True, exist_ok=True)
    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(extract_dir)
    except zipfile.BadZipFile:
        print(f"  ERROR: {zip_path.name} is not a valid zip file", file=sys.stderr)
        raise
    print(f"    Unpacked to {extract_dir.name}")
    return extract_dir


def scan_directory(scan_dir: Path, patterns: list[str], allowed: list[str],
                   exclude_dirs: list[str] = None) -> list[dict]:
    """Search for internal URL patterns using grep. Returns list of findings."""
    findings = []
    grep_pattern = "|".join(patterns)

    grep_cmd = ["grep", "-rn", "--binary-files=text", "-E", grep_pattern]
    for ed in (exclude_dirs or []):
        grep_cmd.extend(["--exclude-dir", ed])
    grep_cmd.extend(["--exclude-dir", "PACKAGE-LICENSES"])
    grep_cmd.append(".")

    try:
        result = subprocess.run(
            grep_cmd,
            cwd=scan_dir,
            capture_output=True,
            timeout=600,
        )
    except subprocess.TimeoutExpired:
        print(f"  WARNING: grep timed out scanning {scan_dir.name}", file=sys.stderr)
        return findings
    except FileNotFoundError:
        print("ERROR: 'grep' not found. Install grep and try again.", file=sys.stderr)
        sys.exit(1)

    stdout = result.stdout.decode("utf-8", errors="replace")
    for line in stdout.splitlines():
        parts = line.split(":", 2)
        if len(parts) < 3:
            continue
        filepath = parts[0].lstrip("./")
        line_num = parts[1]
        matched_line = parts[2].strip()

        if not line_num.isdigit() or "\x00" in filepath or "\ufffd" in filepath:
            continue

        if any(ap in matched_line for ap in allowed):
            continue

        for pattern in patterns:
            if pattern in matched_line:
                findings.append({
                    "package": scan_dir.name,
                    "file": filepath,
                    "line": line_num,
                    "pattern": pattern,
                    "context": matched_line[:300],
                })
    return findings


def scan_nested_archives(scan_dir: Path, patterns: list[str]) -> list[dict]:
    """Search inside nested .zip and .gz files for internal URL patterns."""
    findings = []
    grep_pattern = "|".join(patterns)

    # .zip files
    try:
        result = subprocess.run(
            ["find", ".", "-name", "*.zip", "-print0"],
            cwd=scan_dir, capture_output=True, text=True, timeout=60,
        )
        zip_files = [f for f in result.stdout.split("\0") if f.strip()]
    except Exception:
        zip_files = []

    for zf in zip_files:
        try:
            result = subprocess.run(
                ["zipgrep", "-l", grep_pattern, zf],
                cwd=scan_dir, capture_output=True, text=True, timeout=60,
            )
            if result.returncode == 0 and result.stdout.strip():
                for inner_file in result.stdout.strip().splitlines():
                    for pattern in patterns:
                        findings.append({
                            "package": scan_dir.name,
                            "file": f"{zf.lstrip('./')}!{inner_file}",
                            "line": "?",
                            "pattern": pattern,
                            "context": f"(inside nested zip: {zf})",
                        })
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

    # .gz files
    try:
        result = subprocess.run(
            ["find", ".", "-name", "*.gz", "-print0"],
            cwd=scan_dir, capture_output=True, text=True, timeout=60,
        )
        gz_files = [f for f in result.stdout.split("\0") if f.strip()]
    except Exception:
        gz_files = []

    for gf in gz_files:
        try:
            result = subprocess.run(
                ["zgrep", "-l", grep_pattern, gf],
                cwd=scan_dir, capture_output=True, text=True, timeout=60,
            )
            if result.returncode == 0 and result.stdout.strip():
                for pattern in patterns:
                    findings.append({
                        "package": scan_dir.name,
                        "file": gf.lstrip("./"),
                        "line": "?",
                        "pattern": pattern,
                        "context": f"(inside gzip: {gf})",
                    })
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

    return findings


def write_report(findings: list[dict], report_path: Path):
    """Write findings to a CSV report."""
    fieldnames = ["package", "file", "line", "pattern", "context"]
    with open(report_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(findings)
    print(f"\nReport written to: {report_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Scan Isaac Sim release packages for internal URLs.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--version", required=True,
        help="Version prefix to match, e.g. '6.0.0-rc.19'",
    )
    parser.add_argument(
        "--list-only", action="store_true",
        help="Only list matching packages, don't download or scan.",
    )
    parser.add_argument(
        "--skip-download", action="store_true",
        help="Skip download step; use already-downloaded packages.",
    )
    parser.add_argument(
        "--skip-unzip", action="store_true",
        help="Skip unzip step; use already-unpacked directories.",
    )
    parser.add_argument(
        "--filter", action="append", default=[],
        help="Only process packages whose filename contains this substring. "
             "Can be specified multiple times (all must match).",
    )
    parser.add_argument(
        "--banned-words", type=Path, default=DEFAULT_BANNED_WORDS_FILE,
        dest="banned_words_file",
        help=f"JSON file with banned_words and allowed_patterns (default: {DEFAULT_BANNED_WORDS_FILE.name})",
    )
    parser.add_argument(
        "--packages-dir", type=Path, default=DEFAULT_PACKAGES_DIR,
        help=f"Directory containing (or to download) zip packages (default: {DEFAULT_PACKAGES_DIR})",
    )
    parser.add_argument(
        "--exclude-dir", action="append", default=[], dest="exclude_dirs",
        help="Subdirectory name to skip during scanning (e.g. kit, extscache). "
             "Can be specified multiple times.",
    )
    parser.add_argument(
        "--scan-nested", action="store_true",
        help="Also scan inside nested .zip and .gz files (slower).",
    )
    args = parser.parse_args()

    # --- List packages ---
    packages = list_packages(args.version)
    if not packages:
        print(f"No packages found matching version '{args.version}'.")
        sys.exit(1)

    if args.filter:
        packages = {
            k: v for k, v in packages.items()
            if all(f in k for f in args.filter)
        }
        if not packages:
            print(f"No packages left after applying filters: {args.filter}")
            sys.exit(1)

    print(f"\nFound {len(packages)} package(s):")
    for filename, info in sorted(packages.items()):
        size_gb = info["size"] / (1024**3)
        print(f"  {filename}  ({size_gb:.2f} GB)")

    if args.list_only:
        return

    # --- Load patterns ---
    patterns, allowed = load_banned_words(args.banned_words_file)
    print(f"\nBanned patterns ({len(patterns)}):")
    for p in patterns:
        print(f"  - {p}")
    if allowed:
        print(f"\nAllowed exceptions ({len(allowed)}):")
        for a in allowed:
            print(f"  + {a}")
    if args.exclude_dirs:
        print(f"\nExcluded directories: {', '.join(args.exclude_dirs)}")

    # --- Download ---
    pkg_dir = args.packages_dir
    pkg_dir.mkdir(parents=True, exist_ok=True)
    unpack_dir_root = pkg_dir / args.version
    unpack_dir_root.mkdir(parents=True, exist_ok=True)

    if not args.skip_download:
        print(f"\nDownloading to: {pkg_dir}")
        for filename in sorted(packages):
            download_package(filename, pkg_dir)
    else:
        print("\nSkipping download (--skip-download).")

    # --- Unzip ---
    unpack_dirs = []
    if not args.skip_unzip:
        print(f"\nUnpacking archives to: {unpack_dir_root}")
        for filename in sorted(packages):
            zip_path = pkg_dir / filename
            if not zip_path.exists():
                print(f"  WARNING: {filename} not found, skipping.", file=sys.stderr)
                continue
            sname = short_name(filename).removesuffix(".zip")
            udir = unzip_package(zip_path, unpack_dir_root, dir_name=sname)
            unpack_dirs.append(udir)
    else:
        print("\nSkipping unzip (--skip-unzip).")
        for filename in sorted(packages):
            sname = short_name(filename).removesuffix(".zip")
            d = unpack_dir_root / sname
            if d.is_dir():
                unpack_dirs.append(d)

    if not unpack_dirs:
        print("No unpacked directories to scan.")
        sys.exit(1)

    # --- Scan ---
    print(f"\nScanning {len(unpack_dirs)} package(s) for internal URLs...")
    all_findings = []
    for scan_dir in unpack_dirs:
        print(f"\n  Scanning: {scan_dir.name}")
        findings = scan_directory(scan_dir, patterns, allowed, args.exclude_dirs)
        print(f"    Found {len(findings)} match(es) in flat files")
        all_findings.extend(findings)

        if args.scan_nested:
            nested = scan_nested_archives(scan_dir, patterns)
            print(f"    Found {len(nested)} match(es) in nested archives")
            all_findings.extend(nested)

    # --- Report ---
    report_path = pkg_dir / "internal_url_report.csv"
    write_report(all_findings, report_path)

    # Summary
    unique_files = len({(f["package"], f["file"]) for f in all_findings})
    unique_patterns = len({f["pattern"] for f in all_findings})
    print(f"\nSummary:")
    print(f"  Total matches:    {len(all_findings)}")
    print(f"  Unique files:     {unique_files}")
    print(f"  Patterns matched: {unique_patterns} of {len(patterns)}")

    if all_findings:
        print(f"\n  Breakdown by pattern:")
        for pattern in patterns:
            count = sum(1 for f in all_findings if f["pattern"] == pattern)
            files = len({(f["package"], f["file"]) for f in all_findings if f["pattern"] == pattern})
            print(f"    {pattern}: {count} matches in {files} files")

        print(f"\n  Breakdown by package:")
        for d in unpack_dirs:
            count = sum(1 for f in all_findings if f["package"] == d.name)
            if count:
                print(f"    {d.name}: {count} matches")

    if all_findings:
        sys.exit(2)
    else:
        print("\n  No internal URLs found. All clean!")
        sys.exit(0)


if __name__ == "__main__":
    main()
