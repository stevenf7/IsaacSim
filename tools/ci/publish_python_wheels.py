# Copyright (c) 2026, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
"""Publish Python wheels with per-wheel timeout and retry handling."""

from __future__ import annotations

import argparse
import logging
import os
import subprocess
import sys
import time
from collections.abc import Callable
from pathlib import Path

import omni.repo.man
from omni.repo.python_package import vendor_directory

try:
    from omni.repo.python_package.publish import _wheel_exists_on_server as _repo_wheel_exists_on_server
except ImportError as exc:
    _repo_wheel_exists_on_server = None
    _wheel_exists_import_error = exc
else:
    _wheel_exists_import_error = None

logger = logging.getLogger(os.path.basename(__file__))


def _glob_wheels(packages_wildcard_path: str) -> list[Path]:
    resolved_pattern = omni.repo.man.resolve_tokens(packages_wildcard_path)
    pattern_path = Path(resolved_pattern)

    if pattern_path.is_absolute():
        files = list(pattern_path.parent.glob(pattern_path.name))
    else:
        files = list(Path().glob(resolved_pattern))

    return sorted((path for path in files if path.is_file()), key=lambda path: path.stat().st_size, reverse=True)


def _redacted_url(repository_url: str, password: str) -> str:
    if not password:
        return repository_url
    return repository_url.replace(password, "***REDACTED***")


def _wheel_exists_on_server(wheel_path: str, repository_url: str, user: str, password: str) -> bool:
    if _repo_wheel_exists_on_server is None:
        raise omni.repo.man.exceptions.RepoToolError(
            "Unable to import omni.repo.python_package.publish._wheel_exists_on_server. "
            "Update publish_python_wheels.py if repo_python_package changes its publish API."
        ) from _wheel_exists_import_error
    return _repo_wheel_exists_on_server(wheel_path, repository_url, user, password)


def _run_twine_upload(
    wheel_path: Path,
    repository_url: str,
    user: str,
    password: str,
    timeout_seconds: int,
) -> None:
    cmd = [
        sys.executable,
        "-m",
        "twine",
        "upload",
        "--repository-url",
        repository_url,
        str(wheel_path),
    ]
    env = os.environ.copy()
    env["PYTHONPATH"] = str(vendor_directory) + os.pathsep + env.get("PYTHONPATH", "")
    env["TWINE_USERNAME"] = user
    env["TWINE_PASSWORD"] = password

    logger.info("Uploading wheel %s to %s", wheel_path.name, _redacted_url(repository_url, password))
    try:
        result = subprocess.run(cmd, env=env, timeout=timeout_seconds, check=False)
    except subprocess.TimeoutExpired as exc:
        raise omni.repo.man.exceptions.RepoToolError(
            f"Timed out after {timeout_seconds}s while uploading {wheel_path.name}"
        ) from exc

    if result.returncode != 0:
        raise omni.repo.man.exceptions.RepoToolError(f"Twine upload failed for {wheel_path.name}: {result.returncode}")


def _publish_one_wheel(
    wheel_path: Path,
    task_cfg: dict,
    timeout_seconds: int,
    retries: int,
    retry_sleep_seconds: int,
) -> None:
    pypi_config = task_cfg.get("pypi", {})
    repository_url = pypi_config.get("repository_url")
    user = pypi_config.get("user")
    password = pypi_config.get("password")

    if not repository_url:
        raise omni.repo.man.exceptions.ConfigurationError("Entry for 'pypi.repository_url' not found in tool config")
    if not user:
        raise omni.repo.man.exceptions.ConfigurationError("Entry for 'pypi.user' not found in tool config")
    if not password:
        raise omni.repo.man.exceptions.ConfigurationError("Entry for 'pypi.password' not found in tool config")

    for attempt in range(1, retries + 2):
        # Artifactory's PyPI endpoint rejects Twine's --skip-existing flag, so keep
        # the explicit pre-upload check as the compatible resume path.
        if _wheel_exists_on_server(str(wheel_path), repository_url, user, password):
            logger.warning("Package already exists on server, skipping: %s", wheel_path.name)
            return

        try:
            _run_twine_upload(wheel_path, repository_url, user, password, timeout_seconds)
            return
        except Exception:
            if attempt > retries:
                raise
            logger.exception(
                "Upload attempt %s/%s failed for %s; retrying after %ss",
                attempt,
                retries + 1,
                wheel_path.name,
                retry_sleep_seconds,
            )
            time.sleep(retry_sleep_seconds)


def _publish_task(task_cfg: dict, timeout_seconds: int, retries: int, retry_sleep_seconds: int) -> None:
    packages_wildcard_path = task_cfg.get("packages_wildcard_path")
    if not packages_wildcard_path:
        raise omni.repo.man.exceptions.ConfigurationError("Entry for 'packages_wildcard_path' not found in tool config")

    wheel_paths = _glob_wheels(packages_wildcard_path)
    if not wheel_paths:
        raise omni.repo.man.exceptions.RepoToolError(f"No whl packages found for wildcard path: {packages_wildcard_path}")

    logger.info("Publishing %d wheels, largest first", len(wheel_paths))
    for wheel_path in wheel_paths:
        _publish_one_wheel(wheel_path, task_cfg, timeout_seconds, retries, retry_sleep_seconds)


def setup_repo_tool(parser: argparse.ArgumentParser, _config: dict) -> Callable:
    parser.description = "Publish Python wheels with per-wheel timeout and retry handling."
    parser.add_argument(
        "--timeout-seconds",
        type=int,
        default=900,
        help="Maximum seconds to allow a single wheel upload to run.",
    )
    parser.add_argument(
        "--retries",
        type=int,
        default=2,
        help="Retries per wheel after the initial upload attempt fails.",
    )
    parser.add_argument(
        "--retry-sleep-seconds",
        type=int,
        default=60,
        help="Seconds to sleep between per-wheel upload retries.",
    )

    def run_repo_tool(options: dict, config: dict):
        publish_tasks = config.get("repo_python_package", {}).get("publish", {}).get("task", [])
        if not publish_tasks:
            raise omni.repo.man.exceptions.ConfigurationError("No repo_python_package.publish.task entries configured")

        for task_cfg in publish_tasks:
            _publish_task(task_cfg, options.timeout_seconds, options.retries, options.retry_sleep_seconds)

    return run_repo_tool
