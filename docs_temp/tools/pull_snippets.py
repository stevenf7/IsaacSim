#!/usr/bin/env python3
"""
Documentation Snippet Synchronization Tool
===========================================

This script synchronizes Python code snippets from the main Isaac Sim repository
(omni_isaac_sim) to the documentation repository (isaacsim-docs). It enables a
"Single Source of Truth" workflow where runnable, tested code lives in the main
repo and is automatically copied to the docs repo for use with Sphinx's
`literalinclude` directive.

Directory Structure
-------------------
Source (omni_isaac_sim):
    source/standalone_examples/testing/doc_snippets/snippets/
        core_api_tutorials/
            hello_world.py
            hello_robot.py
            ...
        robot_setup_tutorials/
            gripper_control.py
            ...

Destination (isaacsim-docs):
    docs/app_isaacsim/snippets/
        core_api_tutorials/
            hello_world.py
            ...
        robot_setup_tutorials/
            ...
        ros2_tutorials/
            ...

Usage
-----
Sync all snippets from remote GitLab (default):
    python3 tools/pull_snippets.py

Sync from a local source repository:
    python3 tools/pull_snippets.py --source /path/to/omni_isaac_sim

Check for divergence without modifying files:
    python3 tools/pull_snippets.py --check

Specify a different branch:
    python3 tools/pull_snippets.py --branch develop

Filter by subdirectory:
    python3 tools/pull_snippets.py --filter core_api_tutorials
    python3 tools/pull_snippets.py --filter core_api_tutorials robot_setup_tutorials

CI Integration
--------------
Use the --check flag in CI pipelines to fail the build if snippets are out of sync:
    python3 tools/pull_snippets.py --check
    # Exit code 1 if diverged, 0 if in sync

Notes
-----
- The script preserves directory structure when copying
- File metadata (timestamps) is preserved using shutil.copy2
- Missing destination directories are created automatically
- When no --source is provided, clones from GitLab using sparse checkout
"""

import argparse
import shutil
import subprocess
import tempfile
from pathlib import Path

DEFAULT_GITLAB_URL = "https://gitlab-master.nvidia.com/omniverse/isaac/omni_isaac_sim.git"
DEFAULT_BRANCH = "develop"


def clone_snippets_sparse(repo_url, branch, dest_dir):
    """
    Perform a sparse checkout of only the doc_snippets directory from the repository.

    Args:
        repo_url (str): URL of the Git repository to clone.
        branch (str): Branch name to checkout.
        dest_dir (str): Destination directory for the sparse checkout.

    Returns:
        bool: True if clone succeeded, False otherwise.
    """
    try:
        print(f"Cloning {repo_url} (branch: {branch}) with sparse checkout...")

        # Initialize empty repo
        subprocess.run(
            ["git", "init"],
            cwd=dest_dir,
            check=True,
            capture_output=True,
        )

        # Add remote
        subprocess.run(
            ["git", "remote", "add", "origin", repo_url],
            cwd=dest_dir,
            check=True,
            capture_output=True,
        )

        # Enable sparse checkout
        subprocess.run(
            ["git", "config", "core.sparseCheckout", "true"],
            cwd=dest_dir,
            check=True,
            capture_output=True,
        )

        # Set sparse checkout paths
        sparse_checkout_file = Path(dest_dir) / ".git" / "info" / "sparse-checkout"
        sparse_checkout_file.parent.mkdir(parents=True, exist_ok=True)
        sparse_checkout_file.write_text("source/standalone_examples/testing/doc_snippets/snippets/\n")

        # Fetch and checkout
        subprocess.run(
            ["git", "fetch", "--depth=1", "origin", branch],
            cwd=dest_dir,
            check=True,
            capture_output=True,
        )

        subprocess.run(
            ["git", "checkout", branch],
            cwd=dest_dir,
            check=True,
            capture_output=True,
        )

        print("Clone completed successfully.")
        return True

    except subprocess.CalledProcessError as e:
        print(f"Error during git operation: {e}")
        if e.stderr:
            print(f"stderr: {e.stderr.decode()}")
        return False


def sync_snippets(source_repo, docs_repo, check_only=False, filters=None):
    """
    Synchronize code snippets from source repository to documentation repository.

    Args:
        source_repo (str): Path to the omni_isaac_sim repository root.
        docs_repo (str): Path to the isaacsim-docs repository root.
        check_only (bool): If True, only check for differences without copying.
                          If False (default), copy files from source to destination.
        filters (list): Optional list of subdirectory names to filter by.
                       If provided, only snippets from matching subdirectories are processed.

    Returns:
        bool: True if sync succeeded (or check passed), False if errors occurred
              or files are out of sync (in check mode).
    """
    source_base = Path(source_repo) / "source/standalone_examples/testing/doc_snippets/snippets"
    dest_base = Path(docs_repo) / "docs/app_isaacsim/snippets"

    if not source_base.exists():
        print(f"Error: Source directory {source_base} does not exist.")
        return False

    print(f"Syncing snippets from {source_base} to {dest_base}...")
    if filters:
        print(f"Filtering by subdirectories: {', '.join(filters)}")

    def _collect_rel_paths(base_dir):
        """Collect filtered relative paths of .py files under base_dir."""
        rel_paths = set()
        if not base_dir.exists():
            return rel_paths
        for py_file in base_dir.rglob("*.py"):
            if not py_file.is_file() or py_file.name == "__init__.py":
                continue
            rel_path = py_file.relative_to(base_dir)
            if rel_path.parts[0] == "tests":
                continue
            if filters and rel_path.parts[0] not in filters:
                continue
            rel_paths.add(rel_path)
        return rel_paths

    source_files = _collect_rel_paths(source_base)
    dest_files = _collect_rel_paths(dest_base)

    missing = sorted(source_files - dest_files)  # in source but not docs
    extra = sorted(dest_files - source_files)  # in docs but not source
    common = sorted(source_files & dest_files)  # in both

    if check_only:
        diverged = False
        for rel_path in missing:
            print(f"MISSING: {rel_path} (exists in source but not in docs)")
            diverged = True
        for rel_path in extra:
            print(f"EXTRA: {rel_path} (exists in docs but not in source)")
            diverged = True
        for rel_path in common:
            if (source_base / rel_path).read_bytes() != (dest_base / rel_path).read_bytes():
                print(f"DIFFERENT: {rel_path}")
                diverged = True
        if diverged:
            print("FAILURE: Docs snippets are out of sync.")
            return False
        else:
            print("SUCCESS: Docs snippets are in sync.")
            return True
    else:
        # Copy new and updated files from source to docs
        for rel_path in sorted(source_files):
            dest_file = dest_base / rel_path
            dest_file.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_base / rel_path, dest_file)
        # Remove stale files from docs
        for rel_path in extra:
            print(f"REMOVING EXTRA: {rel_path} (exists in docs but not in source)")
            (dest_base / rel_path).unlink()
        print(f"Synced {len(source_files)} files, removed {len(extra)} extra files.")
        return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sync documentation snippets from source repo.")
    parser.add_argument(
        "--source",
        default=None,
        help="Path to local omni_isaac_sim repo. If not provided, clones from GitLab.",
    )
    parser.add_argument(
        "--docs",
        default=".",
        help="Path to isaacsim-docs repo (default: current dir)",
    )
    parser.add_argument(
        "--branch",
        default=DEFAULT_BRANCH,
        help=f"Branch to checkout when cloning from GitLab (default: {DEFAULT_BRANCH})",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Only check for differences, do not write",
    )
    parser.add_argument(
        "--filter",
        nargs="+",
        default=None,
        help="Only process snippets from subdirectories matching these names (e.g., core_api_tutorials)",
    )

    args = parser.parse_args()

    if args.source:
        # Use local source repository
        success = sync_snippets(args.source, args.docs, args.check, args.filter)
    else:
        # Clone from GitLab to a temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            if not clone_snippets_sparse(DEFAULT_GITLAB_URL, args.branch, temp_dir):
                print("Failed to clone repository from GitLab.")
                exit(1)
            success = sync_snippets(temp_dir, args.docs, args.check, args.filter)

    if not success:
        exit(1)
