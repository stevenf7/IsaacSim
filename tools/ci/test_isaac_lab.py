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
import sys
import xml.etree.ElementTree as ET

import omni.repo.ci
from omni.repo.man import find_and_extract_package


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
    git_clone_command = ["git", "clone", isaac_lab_repo, "_isaaclab"]
    omni.repo.ci.launch(git_clone_command)

    os.chdir("_isaaclab")

    isaac_lab_branch = os.getenv("ISAAC_LAB_BRANCH", "develop")
    git_checkout_command = ["git", "checkout", isaac_lab_branch]
    omni.repo.ci.launch(git_checkout_command)

    os.chdir("..")

    folder, _ = find_and_extract_package("_build/packages/isaac-sim-standalone*.7z")

    link_cmd = ["ln", "-s", f"../{folder}", "_isaaclab/_isaac_sim"]
    omni.repo.ci.launch(link_cmd)

    os.chdir("_isaaclab")

    os.environ["TERM"] = "linux"
    os.environ["PIP_EXTRA_INDEX_URL"] = "https://pypi.nvidia.com"

    setup_command = ["./isaaclab.sh", "-i"]
    omni.repo.ci.launch(setup_command)

    os.makedirs("tests", exist_ok=True)

    test_command = ["./isaaclab.sh", "-p", "-m", "pytest", "tools", "-v",
                    "--junit-xml=tests/full_report.xml"]

    if os.getenv("RUN_NIGHTLY_TESTS", "") != "true":
        test_command += ["-m", "isaacsim_ci"]

    test_exit_code = 0
    try:
        omni.repo.ci.launch(test_command)
    except SystemExit as e:
        test_exit_code = e.code if isinstance(e.code, int) else 1

    # pytest may crash (INTERNALERROR) before writing the combined report, e.g.
    # when a timeout test case contains null bytes that lxml rejects as non-XML.
    # Fall back to combining the individual per-test XMLs that were written first.
    if not os.path.exists("tests/full_report.xml"):
        _combine_junit_xmls("tests", "tests/full_report.xml")

    sys.exit(test_exit_code)
