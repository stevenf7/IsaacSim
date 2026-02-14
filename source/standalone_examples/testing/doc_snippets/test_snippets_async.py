#!/usr/bin/env python3
"""Test script that loads doc snippets and checks for errors.

This script:
1. Iterates over Python files in source/standalone_examples/testing/doc_snippets/snippets
2. For files that do NOT contain SimulationApp in uncommented lines, loads SimulationApp
3. Loads each file as a module and catches/stores any exceptions
4. Prints any exceptions with the snippet file name and trace
5. Returns appropriate status code (nonzero if exceptions, zero otherwise)
"""

import argparse
import csv
import importlib.util
import os
import sys
import traceback
from collections import defaultdict
from pathlib import Path

# Note: SimulationApp is imported inside the experience loop to allow fresh imports
# after closing each SimulationApp instance.


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Test script that loads doc snippets and checks for errors.")
    parser.add_argument(
        "--filter",
        type=str,
        nargs="*",
        default=None,
        help="Filter snippets to test only those in directories matching any of the given substrings.",
    )
    parser.add_argument(
        "--experience-csv",
        type=str,
        default=None,
        help="Path to a CSV file mapping snippet files to Kit app experiences "
        "(relative to the script directory or absolute). "
        "First column is the snippet path (relative to the doc_snippets directory), "
        "second column is the experience name.",
    )
    return parser.parse_known_args()


def parse_experience_csv(csv_path, base_dir):
    """Parse the experience CSV file and return a mapping of absolute file paths to experiences.

    Args:
        csv_path: Path to the CSV file (relative to base_dir or absolute).
        base_dir: Base directory for resolving relative paths in the CSV and the CSV path itself.

    Returns:
        Dictionary mapping absolute file paths (as strings) to experience names.
    """
    experience_map = {}
    # Resolve CSV path relative to base_dir if not absolute
    csv_file = Path(csv_path)
    if not csv_file.is_absolute():
        csv_file = base_dir / csv_file
    if not csv_file.exists():
        print(f"Warning: Experience CSV file not found: {csv_file}")
        return experience_map

    with open(csv_file, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) >= 2:
                snippet_path = row[0].strip()
                experience = row[1].strip()
                # Resolve relative path to absolute
                abs_path = (base_dir / snippet_path).resolve()
                experience_map[str(abs_path)] = experience

    return experience_map


def group_files_by_experience(files, experience_map):
    """Group files by their associated experience.

    Args:
        files: List of file paths to group.
        experience_map: Dictionary mapping file paths to experiences.

    Returns:
        Dictionary mapping experience names to lists of file paths.
    """
    groups = defaultdict(list)
    for file_path in files:
        experience = experience_map.get(str(file_path.resolve()), "")
        groups[experience].append(file_path)
    return groups


def find_python_files(root_dir):
    """Find all Python files recursively in the given directory."""
    root_path = Path(root_dir)
    return list(root_path.rglob("*.py"))


def file_contains_simulation_app(file_path):
    """Check if a file contains 'SimulationApp' in uncommented lines."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                # Skip comment-only lines
                stripped = line.strip()
                if stripped.startswith("#"):
                    continue
                # Check if SimulationApp appears in the code part (before any inline comment)
                code_part = line.split("#")[0]
                if "SimulationApp" in code_part:
                    return True
        return False
    except Exception as e:
        print(f"Error reading file {file_path}: {type(e).__name__}: {e}")
        raise


def cleanup_before_new_stage(simulation_app, file_path):
    """Clean up the current stage before creating a new one."""
    import omni.timeline
    import omni.usd

    # Stop the timeline if it's playing
    timeline = omni.timeline.get_timeline_interface()
    if timeline.is_playing():
        timeline.stop()
        simulation_app.update()

    # Stop replicator if it's running
    try:
        import omni.replicator.core as rep

        if rep.orchestrator.get_status() not in [rep.orchestrator.Status.STOPPED, rep.orchestrator.Status.STOPPING]:
            rep.orchestrator.stop()
            rep.orchestrator.wait_until_complete()
        rep.orchestrator.set_capture_on_play(False)
    except Exception:
        pass

    # Run a few update frames to let everything settle
    for _ in range(5):
        simulation_app.update()

    # Close the current stage if possible
    context = omni.usd.get_context()
    if context.can_close_stage():
        context.close_stage()
        simulation_app.update()
    else:
        print(f"Error: Cannot close stage for file: {file_path}")


def load_snippet_module(file_path, snippets_root, index, simulation_app):
    """Load a snippet module and return any exception that occurred."""
    import gc

    import isaacsim.core.utils.stage as stage_utils

    unique_module_name = f"_snippet_test_{index}"
    exception = None
    module = None
    # Snapshot of modules before loading
    modules_before = set(sys.modules.keys())

    try:
        # Clean up the current stage before creating a new one
        cleanup_before_new_stage(simulation_app, file_path)

        # Open a new stage and wait for it to finish loading
        stage_utils.create_new_stage()
        simulation_app.update()
        while stage_utils.is_stage_loading():
            simulation_app.update()

        # Add the snippets root to sys.path if not already there
        snippets_root_str = str(snippets_root)
        if snippets_root_str not in sys.path:
            sys.path.insert(0, snippets_root_str)

        # Load the module with a unique name
        spec = importlib.util.spec_from_file_location(unique_module_name, file_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Could not create spec for module {unique_module_name}")

        module = importlib.util.module_from_spec(spec)
        # Execute the module
        spec.loader.exec_module(module)

    except Exception as e:
        exception = e
    finally:
        # Clear the module's namespace to release references to objects
        if module is not None:
            try:
                module.__dict__.clear()
            except Exception:
                pass

        # Unload all newly loaded modules
        modules_after = set(sys.modules.keys())
        new_modules = modules_after - modules_before
        for mod_name in new_modules:
            try:
                # Clear the module's namespace before deleting
                if mod_name in sys.modules and hasattr(sys.modules[mod_name], "__dict__"):
                    sys.modules[mod_name].__dict__.clear()
            except Exception:
                pass
            del sys.modules[mod_name]

        # Force garbage collection to clean up unreferenced objects
        gc.collect()

    return (str(file_path), exception)


# Parse command line arguments
args, _ = parse_args()

# Get the snippets directory
script_dir = Path(__file__).parent
snippets_dir = script_dir / "snippets"

if not snippets_dir.exists():
    print(f"Error: Snippets directory not found: {snippets_dir}")
    sys.exit(1)

# Find all Python files
print(f"Scanning for Python files in {snippets_dir}...")
python_files = find_python_files(snippets_dir)
print(f"Found {len(python_files)} Python files")

# Filter files that don't contain SimulationApp and exclude __init__.py files
files_to_test = []
for file_path in python_files:
    if file_path.name == "__init__.py":
        continue
    if not file_contains_simulation_app(file_path):
        files_to_test.append(file_path)

print(f"Found {len(files_to_test)} files to test")

# Apply directory filter if specified
if args.filter:
    files_to_test = [f for f in files_to_test if any(keyword in str(f) for keyword in args.filter)]
    print(f"After applying filter {args.filter}: {len(files_to_test)} files to test")

# Parse experience CSV and group files by experience
experience_map = {}
if args.experience_csv:
    experience_map = parse_experience_csv(args.experience_csv, script_dir)
    print(f"Loaded {len(experience_map)} experience mappings from CSV")

files_by_experience = group_files_by_experience(files_to_test, experience_map)
experience_names = sorted(files_by_experience.keys(), key=lambda x: (x != "", x))  # Default experience first
print(f"Files grouped into {len(experience_names)} experience group(s): {experience_names}")

# Collect all exceptions across all experience groups
all_exceptions = []
global_index = 0

# Process each experience group
for experience in experience_names:
    from isaacsim import SimulationApp

    group_files = files_by_experience[experience]
    experience_display = experience if experience else "(default)"
    print(f"\n{'=' * 80}")
    print(f"Processing experience group: {experience_display} ({len(group_files)} files)")
    print("=" * 80)

    # Load SimulationApp with the appropriate experience
    launch_config = {"headless": True}
    if experience:
        launch_config["experience"] = os.environ["EXP_PATH"] + "/" + experience

    simulation_app = SimulationApp(launch_config=launch_config)

    # Load each snippet and collect exceptions
    for file_path in group_files:
        print(f"[{global_index + 1}/{len(files_to_test)}] Testing: {file_path}")

        result_file_path, exception = load_snippet_module(file_path, snippets_dir, global_index, simulation_app)
        if exception is not None:
            all_exceptions.append((result_file_path, exception, experience_display))
        global_index += 1

    # Close SimulationApp for this experience group
    simulation_app.close()
    print(f"Closed SimulationApp for experience: {experience_display}")

# Print any exceptions
if all_exceptions:
    print("\n" + "=" * 80)
    print(f"Found {len(all_exceptions)} files with exceptions:")
    print("=" * 80)
    for file_path, exception, experience_display in all_exceptions:
        print(f"\nFile: {file_path}")
        print(f"Experience: {experience_display}")
        print(f"Exception: {type(exception).__name__}: {exception}")
        print("Traceback:")
        if hasattr(exception, "__traceback__") and exception.__traceback__:
            tb_lines = traceback.format_exception(type(exception), exception, exception.__traceback__)
            print("".join(tb_lines), end="")
        else:
            print(f"  {exception}")
        print("-" * 80)
    sys.exit(1)
else:
    print("\nAll files tested successfully!")
