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
import importlib.util
import sys
import traceback
from pathlib import Path

from isaacsim import SimulationApp


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
    return parser.parse_known_args()


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

# Load SimulationApp
simulation_app = SimulationApp(launch_config={"headless": True})

# Load each snippet and collect exceptions
exceptions = []
for index, file_path in enumerate(files_to_test):
    print(f"[{index + 1}/{len(files_to_test)}] Testing: {file_path}")

    result_file_path, exception = load_snippet_module(file_path, snippets_dir, index, simulation_app)
    if exception is not None:
        exceptions.append((result_file_path, exception))

# Print any exceptions
if exceptions:
    print("\n" + "=" * 80)
    print(f"Found {len(exceptions)} files with exceptions:")
    print("=" * 80)
    for file_path, exception in exceptions:
        print(f"\nFile: {file_path}")
        print(f"Exception: {type(exception).__name__}: {exception}")
        print("Traceback:")
        if hasattr(exception, "__traceback__") and exception.__traceback__:
            tb_lines = traceback.format_exception(type(exception), exception, exception.__traceback__)
            print("".join(tb_lines), end="")
        else:
            print(f"  {exception}")
        print("-" * 80)
else:
    print("All files testedsuccessfully!")

simulation_app.close()
