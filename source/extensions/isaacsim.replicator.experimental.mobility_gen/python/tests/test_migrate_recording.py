# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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

"""Unit tests for the _migrate_recording function in migrate_recordings.py.

Runs standalone — no Isaac Sim runtime required.
"""

import os
import tempfile
import unittest
from pathlib import Path

import numpy as np

# ---------------------------------------------------------------------------
# Load _migrate_recording from the standalone script via exec so we don't
# need to add it to any package path.
# ---------------------------------------------------------------------------
_SCRIPT = Path(__file__).parents[4] / "standalone_examples" / "replicator" / "mobility_gen" / "migrate_recordings.py"
_globs: dict = {}
exec(compile(_SCRIPT.read_text(), str(_SCRIPT), "exec"), _globs)
_migrate_recording = _globs["_migrate_recording"]


def _make_legacy_recording(root: str, step_data: list[dict]) -> str:
    """Write legacy .npy files (pickled dicts) under root/state/common/ and return root."""
    common_dir = os.path.join(root, "state", "common")
    os.makedirs(common_dir, exist_ok=True)
    for i, data in enumerate(step_data):
        np.save(os.path.join(common_dir, f"{i:06d}.npy"), data)
    return root


class TestMigrateRecordingNoFiles(unittest.TestCase):
    """_migrate_recording must return 0 when no .npy files are present."""

    def test_empty_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(_migrate_recording(tmp), 0)

    def test_directory_without_common_subdir(self):
        with tempfile.TemporaryDirectory() as tmp:
            os.makedirs(os.path.join(tmp, "state"))
            self.assertEqual(_migrate_recording(tmp), 0)


class TestMigrateRecordingSingleFile(unittest.TestCase):
    """_migrate_recording must convert one .npy to .npz and delete the original."""

    def test_npy_converted_to_npz(self):
        with tempfile.TemporaryDirectory() as tmp:
            data = {"pose_x": np.float32(1.0), "pose_y": np.float32(2.0)}
            _make_legacy_recording(tmp, [data])

            count = _migrate_recording(tmp)

            self.assertEqual(count, 1)
            common = os.path.join(tmp, "state", "common")
            self.assertFalse(
                os.path.exists(os.path.join(common, "000000.npy")),
                ".npy should be removed",
            )
            self.assertTrue(
                os.path.exists(os.path.join(common, "000000.npz")),
                ".npz should be created",
            )

    def test_npz_contains_correct_keys(self):
        with tempfile.TemporaryDirectory() as tmp:
            data = {"pose_x": np.float32(3.0), "joint_vel": np.array([0.1, 0.2])}
            _make_legacy_recording(tmp, [data])
            _migrate_recording(tmp)

            npz = np.load(os.path.join(tmp, "state", "common", "000000.npz"))
            self.assertIn("pose_x", npz)
            self.assertIn("joint_vel", npz)
            np.testing.assert_allclose(npz["pose_x"], np.float32(3.0))
            np.testing.assert_allclose(npz["joint_vel"], [0.1, 0.2])

    def test_none_values_excluded_from_npz(self):
        """None values in the legacy dict must be dropped (np.savez can't store None)."""
        with tempfile.TemporaryDirectory() as tmp:
            data = {"pose_x": np.float32(1.0), "optional": None}
            _make_legacy_recording(tmp, [data])
            _migrate_recording(tmp)

            npz = np.load(os.path.join(tmp, "state", "common", "000000.npz"))
            self.assertIn("pose_x", npz)
            self.assertNotIn("optional", npz)


class TestMigrateRecordingMultipleFiles(unittest.TestCase):
    """_migrate_recording must convert all .npy files in the directory."""

    def test_count_matches_file_count(self):
        with tempfile.TemporaryDirectory() as tmp:
            steps = [{"x": np.float32(i)} for i in range(5)]
            _make_legacy_recording(tmp, steps)

            count = _migrate_recording(tmp)

            self.assertEqual(count, 5)

    def test_all_npy_removed_all_npz_created(self):
        with tempfile.TemporaryDirectory() as tmp:
            steps = [{"x": np.float32(i)} for i in range(3)]
            _make_legacy_recording(tmp, steps)
            _migrate_recording(tmp)

            common = os.path.join(tmp, "state", "common")
            npy_files = list(Path(common).glob("*.npy"))
            npz_files = list(Path(common).glob("*.npz"))
            self.assertEqual(len(npy_files), 0, "All .npy files should be removed")
            self.assertEqual(len(npz_files), 3, "One .npz per original .npy")

    def test_idempotent_on_already_migrated(self):
        """A directory with no .npy files returns 0 (already migrated)."""
        with tempfile.TemporaryDirectory() as tmp:
            steps = [{"x": np.float32(i)} for i in range(2)]
            _make_legacy_recording(tmp, steps)
            _migrate_recording(tmp)
            # Run again — should find nothing to migrate
            count = _migrate_recording(tmp)
            self.assertEqual(count, 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
