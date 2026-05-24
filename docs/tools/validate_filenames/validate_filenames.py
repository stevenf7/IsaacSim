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

"""Validate Isaac Sim documentation image and video filenames.

New documentation media assets should follow:

    isim_<VERSION_NUM>_<APP_TYPE>_<DOC_TYPE>_<APP_VIEW>_<YOUR_FILE_NAME>.<ext>

Examples:
    isim_6.0_full_tut_gui_robot_import.png
    isim_6.0_ros_ext-isaacsim.ros2.bridge-3.0.0_viewport_camera.gif
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

VALID_EXTENSIONS = {
    ".avi",
    ".bmp",
    ".flv",
    ".gif",
    ".jpeg",
    ".jpg",
    ".mkv",
    ".mov",
    ".mp4",
    ".png",
    ".svg",
    ".tiff",
    ".webm",
    ".webp",
}
VALID_APP_TYPES = {"base", "full", "isaaclab", "replicator", "ros"}
VALID_APP_VIEWS = {"external", "gui", "viewport"}
VALID_DOC_TYPES = {"ref", "tut"}

FILENAME_RE = re.compile(
    r"^isim_"
    r"(?P<version>\d+\.\d+(?:\.\d+)?)_"
    r"(?P<app_type>base|full|isaaclab|replicator|ros)_"
    r"(?P<doc_type>.+?)_"
    r"(?P<app_view>external|gui|viewport)_"
    r"(?P<name>.+)"
    r"(?P<extension>\.[A-Za-z0-9]+)$"
)
EXTENSION_DOC_TYPE_RE = re.compile(r"^ext-(?P<name>[A-Za-z0-9._]+)-(?P<version>\d+\.\d+\.\d+)$")

NAMING_CONVENTION = """isim_<VERSION_NUM>_<APP_TYPE>_<DOC_TYPE>_<APP_VIEW>_<YOUR_FILE_NAME>.<ext>

  VERSION_NUM: x.y or x.y.z, for example 6.0 or 6.0.0
  APP_TYPE: base, full, isaaclab, replicator, or ros
  DOC_TYPE: tut, ref, or ext-<extension_name>-<version>, for example ext-isaacsim.ros2.bridge-3.0.0
  APP_VIEW: external, gui, or viewport
  YOUR_FILE_NAME: non-empty descriptive text
  ext: image or video extension such as png, jpg, gif, webp, mp4, or svg
"""


@dataclass(frozen=True)
class ValidationResult:
    path: Path
    valid: bool
    reason: str = ""


def is_media_file(path: Path) -> bool:
    return path.suffix.lower() in VALID_EXTENSIONS


def validate_doc_type(doc_type: str) -> str | None:
    if doc_type in VALID_DOC_TYPES:
        return None

    if doc_type.startswith("ext-"):
        if EXTENSION_DOC_TYPE_RE.match(doc_type):
            return None
        return "DOC_TYPE extensions must use ext-<extension_name>-<x.y.z>"

    return "DOC_TYPE must be tut, ref, or ext-<extension_name>-<x.y.z>"


def validate_filename(path: Path) -> ValidationResult:
    filename = path.name
    match = FILENAME_RE.match(filename)
    if not match:
        return ValidationResult(path, False, "filename does not match the required isim_* pattern")

    fields = match.groupdict()
    extension = fields["extension"].lower()
    if extension not in VALID_EXTENSIONS:
        return ValidationResult(path, False, f"unsupported media extension: {fields['extension']}")

    doc_type_error = validate_doc_type(fields["doc_type"])
    if doc_type_error:
        return ValidationResult(path, False, doc_type_error)

    return ValidationResult(path, True)


def collect_directory_files(directory: Path) -> list[Path]:
    if not directory.is_dir():
        raise FileNotFoundError(f'Directory "{directory}" does not exist.')

    return [path for path in directory.rglob("*") if path.is_file()]


def read_file_list(path: Path) -> list[Path]:
    if not path.is_file():
        raise FileNotFoundError(f'File list "{path}" does not exist.')

    return [Path(line.strip()) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def run_git(args: list[str], cwd: Path | None = None) -> list[str]:
    output = subprocess.check_output(["git", *args], cwd=cwd, text=True)
    return [line.strip() for line in output.splitlines() if line.strip()]


def git_root() -> Path:
    return Path(run_git(["rev-parse", "--show-toplevel"])[0])


def git_ref_exists(ref: str, cwd: Path) -> bool:
    try:
        subprocess.check_call(
            ["git", "rev-parse", "--verify", "--quiet", ref],
            cwd=cwd,
            stderr=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
        )
    except subprocess.CalledProcessError:
        return False
    return True


def collect_git_changed_files(base_ref: str) -> list[Path]:
    root = git_root()
    if not git_ref_exists(base_ref, root):
        print(f'WARNING: base ref "{base_ref}" was not found; no git diff files collected.', file=sys.stderr)
        return []

    merge_base = run_git(["merge-base", base_ref, "HEAD"], cwd=root)[0]
    paths: list[str] = []
    paths.extend(run_git(["diff", "--name-only", "--diff-filter=ACMR", merge_base, "HEAD"], cwd=root))
    paths.extend(run_git(["diff", "--name-only", "--diff-filter=ACMR"], cwd=root))
    paths.extend(run_git(["diff", "--cached", "--name-only", "--diff-filter=ACMR"], cwd=root))
    paths.extend(run_git(["ls-files", "--others", "--exclude-standard"], cwd=root))
    return [Path(path) for path in dict.fromkeys(paths)]


def expand_file_args(file_args: list[str]) -> list[Path]:
    paths: list[Path] = []
    for file_arg in file_args:
        paths.extend(Path(path) for path in file_arg.split() if path)
    return paths


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate Isaac Sim documentation image/video filenames.",
        epilog=NAMING_CONVENTION,
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument("--files", nargs="*", default=[], help="Specific files to validate.")
    parser.add_argument("--files-from", type=Path, help="Newline-delimited file containing files to validate.")
    parser.add_argument("--file-directory", type=Path, help="Directory to recursively scan for media files.")
    parser.add_argument(
        "--base-ref",
        default="upstream/develop",
        help="Base ref for no-argument git diff mode. Defaults to upstream/develop.",
    )
    parser.add_argument("--print-valid", action="store_true", help="Print valid media filenames too.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    try:
        paths: list[Path] = []
        if args.files_from:
            paths.extend(read_file_list(args.files_from))
        if args.files:
            paths.extend(expand_file_args(args.files))
        if args.file_directory:
            paths.extend(collect_directory_files(args.file_directory))
        if not paths:
            paths.extend(collect_git_changed_files(args.base_ref))
    except (FileNotFoundError, subprocess.CalledProcessError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    # Keep order deterministic while preserving the first instance of each path.
    unique_paths = list(dict.fromkeys(paths))
    media_paths = [path for path in unique_paths if is_media_file(path)]

    if not media_paths:
        print("No image or video files to validate.")
        return 0

    results = [validate_filename(path) for path in media_paths]
    failures = [result for result in results if not result.valid]

    for result in results:
        if result.valid and args.print_valid:
            print(f"VALID: {result.path}")

    if failures:
        print("Invalid image/video filenames:")
        for failure in failures:
            print(f"  {failure.path}: {failure.reason}")
        print("\nAll documentation media assets should follow:")
        print(NAMING_CONVENTION)
        return 1

    print(f"Validated {len(media_paths)} image/video filename(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
