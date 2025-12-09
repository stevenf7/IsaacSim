# Check Extension Support Levels
#
# This script validates that Isaac Sim extensions follow proper support level dependency rules.
# It extracts the isaac-sim-standalone package, runs Kit with the dump script to collect
# extension support level data, and reports any conflicts or errors.
#
# Support Level Rules Validated:
# 1. No extension should have "Internal" support level (legacy)
# 2. No extension should depend on another extension with "Internal" support level
# 3. Core support level extensions cannot depend on Sample support level extensions
#    (unless the dependency is marked as optional)
# 4. Extensions with "Enterprise" support level should be updated to "Core" (legacy)
#
# How to run:
#   ./repo.sh ci check_extension_support_levels
#
# This command is configured in repo_internal.toml:
#   [repo_ci.jobs.check_extension_support_levels]
#   script = "${root}/tools/ci/check_extension_support_levels/check_extension_support_levels.py"
#
# Prerequisites:
#   - _build/packages/isaac-sim-standalone*.7z must be present (built package)
#
# The script performs these steps:
# 1. Extracts the isaac-sim-standalone package to get Kit executable and extensions
# 2. Launches Kit with dump_extension_support_level_conflicts.py to collect data
# 3. Parses the resulting JSON to identify and report conflicts
# 4. Prints detailed information about violations
#
# Outputs:
#   - ext_conflicts.json: JSON file with extension support level conflicts
#   - Console output: Formatted report of conflicts and errors
#
# Exit codes:
#   0: No support level conflicts or errors found
#   1: Support level conflicts or errors detected
#

import json
import sys
from pathlib import Path

import omni.repo.ci
import omni.repo.man
from omni.repo.man import resolve_tokens

_ROOT = Path(resolve_tokens("${root}"))
_ALL_TEMPLATE_FILE_NAME = "isaacsim.exp.extscache"
_KIT_FILE_PATH = str(_ROOT / "source" / "apps" / f"{_ALL_TEMPLATE_FILE_NAME}.kit")


def _generate_dependencies(kit_root: Path) -> dict:
    """Generate extension dependency data by running Kit with the dump script.
    
    Args:
        kit_root: Path to the extracted Kit package root directory.
        
    Returns:
        Dictionary containing extension support level conflict data.
    """
    ext_conflicts_filepath = str(_ROOT / "ext_conflicts.json")
    print("Collecting support level conflicts... This may take some time.")

    platform = "windows" if sys.platform == "win32" else "linux"
    executable_extension = ".exe" if sys.platform == "win32" else ""

    # Use the Kit executable from the extracted package
    kit_shell_path = str(kit_root / "kit" / f"kit{executable_extension}")

    # Point directly to the extracted package directories instead of copying
    omni.repo.ci.launch(
        [
            kit_shell_path,
            _KIT_FILE_PATH,
            "--enable",
            "omni.kit.loop",
            "--no-window",
            "--ext-folder",
            str(kit_root / "exts"),
            "--ext-folder",
            str(kit_root / "extscache"),
            "--ext-folder",
            str(kit_root / "apps"),
            "--exec",
            f"tools/ci/check_extension_support_levels/dump_extension_support_level_conflicts.py {ext_conflicts_filepath} {_ALL_TEMPLATE_FILE_NAME}",
        ]
    )

    return json.loads(open(ext_conflicts_filepath, "r").read())


def _validate_extension_support_levels(extension_data: dict) -> bool:
    """Validate extension support levels and report conflicts and errors.

    Analyzes the extension data to identify and report support level conflicts and
    errors. Prints detailed information about Enterprise extensions that need updating,
    extensions with dependency conflicts, and extensions with validation errors.

    Args:
        extension_data: Dictionary containing extension support level conflict and error data.

    Returns:
        True if conflicts or errors were found, False otherwise.
    """
    # Direct Conflicts
    conflict_exts = [ext for ext in extension_data["data"] if ext["conflicts"]["count"] > 0]
    conflict_count = sum([ext["conflicts"]["count"] for ext in extension_data["data"]])

    print(" ")  # Empty Character for generating new line in CI/CD
    print("#" * 50)
    print(f"# {conflict_count} Extension Support Level Conflicts Found!")
    print("#" * 50)
    print(" ")  # Empty Character for generating new line in CI/CD

    if has_conflicts := conflict_count > 0:
        # Collect all extensions that have been marked "Enterprise" support level and list them accordingly
        enterprise_exts = [
            conflict_exts.pop(conflict_exts.index(e))
            for e in conflict_exts[:]
            if e["support_level"].lower() == "enterprise"
        ]
        if len(enterprise_exts) > 0:
            print("The following extensions are labeled as 'Enterprise' and need to be updated to 'Core':")
            for e in enterprise_exts:
                print(f" -- {e['id']}")
            print(" ")  # Empty Character for generating new line in CI/CD

        if len(conflict_exts) > 0:
            print("The following extensions have dependencies that fail one of the following Support Level rulesets:")
            print(" > Dependency Support Level is Internal.")
            print(" > Extension is Core Support Level and dependency Support Level is Sample and not optional.")
            print(" ")  # Empty Character for generating new line in CI/CD
            for e in conflict_exts:
                ext_id = e["id"]
                support_level = e["support_level"].title()
                conflicts = e["conflicts"]["internal"] + e["conflicts"]["core"]

                print(f"{ext_id} | {support_level}")
                for c in conflicts:
                    print(f" -- {c['id']} | Optional: {c['optional']} | Fail Type: {c['support_level'].title()} ")
                print(" ")  # Empty Character for generating new line in CI/CD

    # Extensions with Errors
    error_exts = [ext for ext in extension_data["data"] if len(ext["errors"]) > 0]
    # Collect all errors and prune duplicates
    errors = set({(err["id"], err["error"]) for ext in error_exts for err in ext["errors"]})
    error_count = len(errors)

    print(" ")  # Empty Character for generating new line in CI/CD
    print("#" * 50)
    print(f"# {error_count} Extension Support Level Errors Found!")
    print("#" * 50)
    print(" ")  # Empty Character for generating new line in CI/CD

    if has_errors := error_count > 0:

        print("The following extensions had an issure or error retrieving data from the Extension Manager:")
        for e in sorted(errors):
            print(f" -- {e[0]} | {e[1]}")
        print(" ")  # Empty Character for generating new line in CI/CD

    return has_conflicts or has_errors


def _extract_package() -> Path:
    """Extract the isaac-sim-standalone package.
    
    Returns:
        Path to the extracted package root directory containing the Kit executable.
    """
    archive_patterns = [
        str(Path("_build") / "packages/isaac-sim-standalone*.7z"),
    ]
    kit_root = None
    for pattern in archive_patterns:
        print(f"> Extracting {pattern}")
        root, _ = omni.repo.man.find_and_extract_package(pattern)
        kit_root = Path(root)
        print(f"> Extracted to {kit_root}")
    
    if kit_root is None:
        raise RuntimeError("Failed to extract isaac-sim-standalone package")
    
    return kit_root


def main(args):
    """Main function to check extension support levels.
    
    Extracts prebuilt packages, runs Kit to collect extension support level data,
    and validates that extensions follow support level rules.
    
    Args:
        args: Command line arguments (unused).
    """
    # Extract prebuilt package
    kit_root = _extract_package()

    # Generate The extension dependency JSON
    extension_dependencies: dict = _generate_dependencies(kit_root)

    # Parse the JSON to validate support level
    has_conflicts: bool = _validate_extension_support_levels(extension_dependencies)

    sys.exit(1 if has_conflicts else 0)
