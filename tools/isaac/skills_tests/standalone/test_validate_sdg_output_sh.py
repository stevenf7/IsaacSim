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

"""Standalone tier: data-collection-sim/validate_sdg_output.sh (pure bash, runs headless)."""

from __future__ import annotations

import subprocess

import pytest
from _util import skill_path

pytestmark = pytest.mark.standalone

VALIDATE = skill_path("data-collection-sim", "scripts", "validate_sdg_output.sh")


def _run(*args, timeout=30):
    return subprocess.run(["bash", VALIDATE, *args], capture_output=True, text=True, timeout=timeout)


def _make_output(tmp_path, n_png=1, n_json=1, png_size=2048):
    d = tmp_path / "out"
    d.mkdir()
    for i in range(n_png):
        (d / f"rgb_{i:04d}.png").write_bytes(b"\x89PNG" + b"\0" * png_size)
    for i in range(n_json):
        (d / f"ann_{i:04d}.json").write_text("{}")
    return d


def test_missing_directory_fails(tmp_path):
    r = _run(str(tmp_path / "does_not_exist"))
    assert r.returncode == 1
    assert "does not exist" in r.stdout


def test_counts_and_passes(tmp_path):
    d = _make_output(tmp_path, n_png=3, n_json=3)
    r = _run(str(d))
    assert r.returncode == 0, r.stdout
    assert "RGB images: 3" in r.stdout
    assert "Annotation files: 3" in r.stdout
    assert "PASSED" in r.stdout


def test_expected_frames_shortfall_fails(tmp_path):
    d = _make_output(tmp_path, n_png=1, n_json=1)
    r = _run(str(d), "5")
    assert r.returncode == 1
    assert "Expected 5" in r.stdout


def test_empty_image_warning(tmp_path):
    # NOTE: the script uses `find -size -1k`, which rounds file size up to the next
    # 1K block, so in practice only 0-byte files trip the warning.
    d = tmp_path / "out"
    d.mkdir()
    (d / "rgb_0000.png").write_bytes(b"")  # 0 bytes
    r = _run(str(d))
    assert "potentially empty" in r.stdout
