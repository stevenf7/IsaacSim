# SPDX-FileCopyrightText: Copyright (c) 2024-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: LicenseRef-NvidiaProprietary
#
# NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
# property and proprietary rights in and to this material, related
# documentation and any modifications thereto. Any use, reproduction,
# disclosure or distribution of this material and related documentation
# without an express license agreement from NVIDIA CORPORATION or
# its affiliates is strictly prohibited.
from __future__ import annotations

import argparse
import glob
import os
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

import omni.repo.ci
from omni.repo.man import find_and_extract_package

# Exit codes consumed by .gitlab-ci.yml `allow_failure.exit_codes`.
# 42 lets the MR variant flag test failures as a warning while still failing
# the job hard on any infrastructure problem (66) — clone, checkout, link,
# IsaacLab installer, or pytest crashing before producing a junit report.
EXIT_TEST_FAILURE = 42
EXIT_INFRA_FAILURE = 66


def _run_step(cmd: list[str], *, step: str) -> None:
    """Run *cmd* via ``omni.repo.ci.launch`` and exit 66 on any non-zero rc.

    ``warning_only=True`` keeps ``launch`` from calling ``sys.exit`` itself so
    we can substitute the infrastructure-failure exit code instead of the
    underlying tool's rc, which keeps the GitLab `allow_failure.exit_codes`
    contract clean.
    """
    rc = omni.repo.ci.launch(cmd, warning_only=True)
    if rc != 0:
        print(
            f"[isaaclab-ci] {step} failed with exit code {rc}; "
            f"treating as infrastructure failure (exit {EXIT_INFRA_FAILURE}).",
            file=sys.stderr,
        )
        sys.exit(EXIT_INFRA_FAILURE)


def _restore_repointed_prebundle(isaac_sim_path: str) -> None:
    """Undo IsaacLab's ``_repoint_prebundle_packages()`` for the ``nvidia`` namespace.

    IsaacLab's installer may replace ``pip_prebundle/nvidia/`` (which aggregates
    CUDA libraries from 16+ pip packages) with a symlink to ``site-packages/nvidia/``
    (which may contain only a partial subset, e.g. nvidia-srl-*).  This causes
    ``libcudart.so.12`` and other CUDA shared objects to go missing at runtime.

    If a ``.bak`` backup exists we restore the original directory; otherwise we
    just remove the bad symlink so the prebundled copies remain authoritative.
    """
    ml_prebundle = Path(isaac_sim_path) / "extsDeprecated" / "omni.isaac.ml_archive" / "pip_prebundle"
    if not ml_prebundle.is_dir():
        return
    nvidia_path = ml_prebundle / "nvidia"
    nvidia_bak = ml_prebundle / "nvidia.bak"
    if nvidia_path.is_symlink():
        print(f"[isaaclab-fixup] Removing repointed symlink: {nvidia_path}")
        nvidia_path.unlink()
        if nvidia_bak.is_dir():
            print(f"[isaaclab-fixup] Restoring backup: {nvidia_bak} -> {nvidia_path}")
            nvidia_bak.rename(nvidia_path)
        else:
            print(f"[isaaclab-fixup] Warning: no .bak found at {nvidia_bak}", file=sys.stderr)


def _reconcile_exit_code(process_rc: int, junit_path: str) -> int:
    """Map pytest's process rc + junit report into one of {0, 42, 66}.

    - ``0`` — pytest exited cleanly and junit reports no failures/errors.
    - ``42`` (``EXIT_TEST_FAILURE``) — tests ran but at least one failed/errored.
      Pytest has been observed to exit 0 while still recording failures (teardown
      errors, plugin quirks); the junit report is treated as authoritative.
    - ``66`` (``EXIT_INFRA_FAILURE``) — pytest could not be trusted to have run
      the test suite, e.g. it exited non-zero before producing usable results,
      or it exited 0 but the junit report is missing/unparseable so we cannot
      verify what (if anything) ran. Caller treats this the same as a
      clone/setup failure so MR jobs still fail hard.
    """
    junit_parseable = False
    junit_has_results = False
    junit_has_failures = False
    if os.path.exists(junit_path):
        try:
            root = ET.parse(junit_path).getroot()
            junit_parseable = True
            for suite in root.iter("testsuite"):
                # Per-suite ValueError protects against a single bogus
                # attribute (e.g. tests="N/A" from a misbehaving plugin)
                # taking down the whole reconcile.
                try:
                    if int(suite.get("tests", 0)) > 0:
                        junit_has_results = True
                    if int(suite.get("failures", 0)) or int(suite.get("errors", 0)):
                        junit_has_failures = True
                except ValueError as exc:
                    print(
                        f"[isaaclab-ci] Skipping suite with non-numeric counters: {exc}",
                        file=sys.stderr,
                    )
        except ET.ParseError:
            # Matches the malformed-XML handling in _combine_junit_xmls: a
            # crashed pytest can leave behind an unparseable report.
            pass

    if process_rc == 0:
        # Clean rc means nothing if we cannot read the report — pytest may have
        # been killed before flushing the test loop, or the path may be wrong.
        # Don't paper over that with a green job.
        if not junit_parseable:
            print(
                f"[isaaclab-ci] pytest rc=0 but junit at '{junit_path}' "
                f"is missing or unparseable; treating as infrastructure failure.",
                file=sys.stderr,
            )
            return EXIT_INFRA_FAILURE
        return EXIT_TEST_FAILURE if junit_has_failures else 0
    if junit_has_results:
        return EXIT_TEST_FAILURE
    return EXIT_INFRA_FAILURE


def _combine_junit_xmls(xml_dir: str, output_path: str) -> None:
    """Combine individual JUnit XML files into a single <testsuites> report.

    Used as a fallback when pytest crashes before writing the combined report
    (e.g. due to null bytes in a timeout test case's output).  Skips any
    files that cannot be parsed as valid XML.
    """
    root = ET.Element("testsuites")
    output_abs = os.path.abspath(output_path)
    for path in sorted(glob.glob(os.path.join(xml_dir, "*.xml"))):
        if os.path.abspath(path) == output_abs:
            continue
        try:
            for element in ET.parse(path).getroot().iter("testsuite"):
                root.append(element)
        except ET.ParseError as exc:
            print(f"Warning: skipping unparseable XML {path}: {exc}", file=sys.stderr)
    ET.ElementTree(root).write(output_path, encoding="utf-8", xml_declaration=True)


def main(args: argparse.Namespace) -> None:

    isaac_lab_repo = os.getenv("ISAAC_LAB_REPO", "https://github.com/isaac-sim/IsaacLab.git")
    _run_step(["git", "clone", isaac_lab_repo, "_isaaclab"], step="git clone IsaacLab")

    os.chdir("_isaaclab")

    isaac_lab_branch = os.getenv("ISAAC_LAB_BRANCH", "develop")
    _run_step(["git", "checkout", isaac_lab_branch], step=f"git checkout {isaac_lab_branch}")

    os.chdir("..")

    folder, _ = find_and_extract_package("_build/packages/isaac-sim-standalone*.7z")

    _run_step(["ln", "-s", f"../{folder}", "_isaaclab/_isaac_sim"], step="link Isaac Sim package")

    os.chdir("_isaaclab")

    os.environ["TERM"] = "linux"
    os.environ["PIP_EXTRA_INDEX_URL"] = "https://pypi.nvidia.com"

    _run_step(["./isaaclab.sh", "-i"], step="IsaacLab installer")

    _run_step(["./isaaclab.sh", "-i", "ov[ovrtx]"], step="Install ov[ovrtx]")

    # IsaacLab's installer may replace prebundled nvidia/ directories with
    # symlinks to site-packages, losing CUDA shared objects.  Undo that.
    _restore_repointed_prebundle("_isaac_sim")

    os.makedirs("tests", exist_ok=True)

    test_command = ["./isaaclab.sh", "-p", "-m", "pytest", "tools", "-v",
                    "--junit-xml=tests/full_report.xml"]

    if os.getenv("RUN_NIGHTLY_TESTS", "") != "true":
        test_command += ["-m", "isaacsim_ci"]

    # warning_only=True makes launch() return the exit code instead of
    # calling sys.exit() on failure, so we can run cleanup before exiting.
    test_exit_code = omni.repo.ci.launch(test_command, warning_only=True)

    # pytest may crash (INTERNALERROR) before writing the combined report, e.g.
    # when a timeout test case contains null bytes that lxml rejects as non-XML.
    # Fall back to combining the individual per-test XMLs that were written first.
    if not os.path.exists("tests/full_report.xml"):
        _combine_junit_xmls("tests", "tests/full_report.xml")

    sys.exit(_reconcile_exit_code(test_exit_code, "tests/full_report.xml"))
