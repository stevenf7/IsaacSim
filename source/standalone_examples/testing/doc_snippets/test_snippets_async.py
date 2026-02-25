#!/usr/bin/env python3
"""Test script that loads doc snippets and checks for errors.

This script:
1. Iterates over Python files in docs/isaacsim/snippets
2. For files that do NOT contain SimulationApp in uncommented lines, loads SimulationApp
3. Loads each file as a module and catches/stores any exceptions
4. Prints any exceptions with the snippet file name and trace
5. Returns appropriate status code (nonzero if exceptions, zero otherwise)
"""

import argparse
import asyncio
import csv
import importlib.util
import os
import re
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
    parser.add_argument(
        "--expected-failures-csv",
        type=str,
        default=None,
        help="Path to a CSV file listing snippets expected to fail. "
        "First column is the snippet path (relative to the doc_snippets directory), "
        "second column is an optional exception message regex pattern.",
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


def parse_expected_failures_csv(csv_path, base_dir):
    """Parse expected failures CSV and return a list of (abs_path, compiled_pattern|None) tuples.

    Args:
        csv_path: Path to the CSV file (relative to base_dir or absolute).
        base_dir: Base directory for resolving relative paths.

    Returns:
        List of (absolute_path_str, compiled_regex_or_None) tuples.
    """
    entries = []
    csv_file = Path(csv_path)
    if not csv_file.is_absolute():
        csv_file = base_dir / csv_file
    if not csv_file.exists():
        print(f"Warning: Expected failures CSV file not found: {csv_file}")
        return entries

    with open(csv_file, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        for row in reader:
            if not row or row[0].strip().startswith("#"):
                continue
            snippet_path = row[0].strip()
            pattern_str = row[1].strip() if len(row) >= 2 and row[1].strip() else None
            abs_path = str((base_dir / snippet_path).resolve())
            compiled = re.compile(pattern_str) if pattern_str else None
            entries.append((abs_path, compiled))

    return entries


def is_expected_failure(file_path, exception, expected_failures):
    """Return True if this snippet + exception combo matches an expected-failure entry."""
    if not expected_failures:
        return False
    file_path_str = str(Path(file_path).resolve())
    exc_str = f"{type(exception).__name__}: {exception}"
    for expected_path, pattern in expected_failures:
        if file_path_str == expected_path:
            if pattern is None or pattern.search(exc_str):
                return True
    return False


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

    # Close the current stage if possible; treat inability as recoverable.
    context = omni.usd.get_context()
    if context.can_close_stage():
        context.close_stage()
        simulation_app.update()
    else:
        print(f"Warning: Cannot close stage for file: {file_path}, forcing new stage")
        for _ in range(10):
            simulation_app.update()


def _is_path_within(path, root):
    """Return True if path is inside root."""
    try:
        return Path(path).resolve().is_relative_to(Path(root).resolve())
    except Exception:
        return False


def _task_belongs_to_snippets(task, snippets_root):
    """Return True if task coroutine source file is from snippets tree."""
    try:
        coro = task.get_coro()
        code = getattr(coro, "cr_code", None) or getattr(coro, "gi_code", None)
        if code is None:
            return False
        source_file = getattr(code, "co_filename", "")
        return bool(source_file) and _is_path_within(source_file, snippets_root)
    except Exception:
        return False


def _wait_for_snippet_tasks(simulation_app, tasks, settle_frames=10):
    """Give snippet-created async tasks a chance to complete."""
    if not tasks:
        return
    for _ in range(settle_frames):
        if all(task.done() for task in tasks):
            break
        simulation_app.update()


def load_snippet_module(file_path, snippets_root, index, simulation_app):
    """Load a snippet module and return any exception that occurred."""
    import gc

    import isaacsim.core.utils.stage as stage_utils

    unique_module_name = f"_snippet_test_{index}"
    exceptions = []
    module = None
    loop = None
    baseline_tasks = set()
    captured_loop_exceptions = []
    # Snapshot of modules before loading
    modules_before = set(sys.modules.keys())

    def loop_exception_handler(loop, context):
        """Capture unhandled loop exceptions as test failures."""
        captured_loop_exceptions.append(context)

    try:
        loop = asyncio.get_event_loop()
        baseline_tasks = set(asyncio.all_tasks(loop))
        previous_exception_handler = loop.get_exception_handler()
        loop.set_exception_handler(loop_exception_handler)

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
        exceptions.append(e)
    finally:
        snippet_tasks = []
        if loop is not None:
            current_tasks = set(asyncio.all_tasks(loop))
            snippet_tasks = [
                task for task in (current_tasks - baseline_tasks) if _task_belongs_to_snippets(task, snippets_root)
            ]

            # Let snippet-created tasks finish naturally first.
            _wait_for_snippet_tasks(simulation_app, snippet_tasks, settle_frames=30)

            # Cancel still-pending snippet tasks so they do not leak across snippets.
            pending_snippet_tasks = [task for task in snippet_tasks if not task.done()]
            for task in pending_snippet_tasks:
                task.cancel()
            _wait_for_snippet_tasks(simulation_app, pending_snippet_tasks, settle_frames=5)

            # Retrieve task exceptions explicitly so they become deterministic test failures.
            for task in snippet_tasks:
                if not task.done() or task.cancelled():
                    continue
                try:
                    task_exception = task.exception()
                except asyncio.CancelledError:
                    continue
                except Exception as task_exception:
                    exceptions.append(task_exception)
                    continue
                if task_exception is not None:
                    exceptions.append(task_exception)

            # Restore the loop exception handler.
            try:
                loop.set_exception_handler(previous_exception_handler)
            except Exception:
                pass

        # Promote unhandled loop-level async exceptions to snippet failures.
        for context in captured_loop_exceptions:
            loop_exception = context.get("exception")
            if loop_exception is not None:
                exceptions.append(loop_exception)
            else:
                message = context.get("message", "Unhandled asyncio loop exception.")
                exceptions.append(RuntimeError(message))

        # Some modules monkey-patch global runtime state (e.g. asyncio loop internals).
        # Unloading them can leave patched callables referencing cleared module globals.
        module_cleanup_exclude = {"nest_asyncio"}

        # Unload only snippet-local modules. Do not wipe module dicts to avoid breaking
        # async tasks/callbacks that still reference module globals.
        modules_after = set(sys.modules.keys())
        new_modules = modules_after - modules_before
        for mod_name in new_modules:
            if mod_name in module_cleanup_exclude:
                continue
            module_obj = sys.modules.get(mod_name)
            module_file = getattr(module_obj, "__file__", None) if module_obj is not None else None
            if module_file is None or not _is_path_within(module_file, snippets_root):
                continue
            sys.modules.pop(mod_name, None)

        # Force garbage collection to clean up unreferenced objects
        gc.collect()

    if not exceptions:
        return (str(file_path), None)
    if len(exceptions) == 1:
        return (str(file_path), exceptions[0])
    return (str(file_path), ExceptionGroup(f"Multiple exceptions while testing snippet {file_path}", exceptions))


# Parse command line arguments
args, _ = parse_args()

# Get the snippets directory (canonical location: docs/isaacsim/snippets)
script_dir = Path(__file__).parent
repo_root = script_dir.parents[3]
snippets_dir = repo_root / "docs" / "isaacsim" / "snippets"

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

# Parse expected failures
expected_failures = []
if args.expected_failures_csv:
    expected_failures = parse_expected_failures_csv(args.expected_failures_csv, script_dir)
    print(f"Loaded {len(expected_failures)} expected failure rules from CSV")

# Collect all exceptions across all experience groups
all_exceptions = []
global_index = 0

# Process each experience group
for _exp_idx, experience in enumerate(experience_names):
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

    # Print the report before closing the last SimulationApp (close may exit the process).
    is_last_group = _exp_idx == len(experience_names) - 1
    if is_last_group:
        unexpected_exceptions = [
            (f, e, exp) for f, e, exp in all_exceptions if not is_expected_failure(f, e, expected_failures)
        ]
        expected_exception_items = [
            (f, e, exp) for f, e, exp in all_exceptions if is_expected_failure(f, e, expected_failures)
        ]

        if expected_exception_items:
            print(f"\n{'=' * 80}")
            print(f"Expected failures ({len(expected_exception_items)} files):")
            print("=" * 80)
            for file_path, exception, exp_disp in expected_exception_items:
                print(f"  {file_path}: {type(exception).__name__}: {exception}")

        if unexpected_exceptions:
            print(f"\n{'=' * 80}")
            print(f"UNEXPECTED failures ({len(unexpected_exceptions)} files):")
            print("=" * 80)
            for file_path, exception, exp_disp in unexpected_exceptions:
                print(f"\nFile: {file_path}")
                print(f"Experience: {exp_disp}")
                print(f"Exception: {type(exception).__name__}: {exception}")
                print("Traceback:")
                if hasattr(exception, "__traceback__") and exception.__traceback__:
                    tb_lines = traceback.format_exception(type(exception), exception, exception.__traceback__)
                    print("".join(tb_lines), end="")
                else:
                    print(f"  {exception}")
                print("-" * 80)

        if not unexpected_exceptions:
            if expected_exception_items:
                print(f"\nAll files tested successfully ({len(expected_exception_items)} expected failures)!")
            else:
                print("\nAll files tested successfully!")

        sys.stdout.flush()

    # Close SimulationApp for this experience group
    simulation_app.close()
    print(f"Closed SimulationApp for experience: {experience_display}")

# Exit with error if there are unexpected failures.
if any(not is_expected_failure(f, e, expected_failures) for f, e, _ in all_exceptions):
    sys.exit(1)
