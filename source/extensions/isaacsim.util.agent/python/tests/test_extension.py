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

"""Unit tests for repo-root discovery in the extension entry point."""

import os
import tempfile

import omni.kit.test
from isaacsim.util.agent.impl.extension import _find_repo_root


class TestFindRepoRoot(omni.kit.test.AsyncTestCase):
    """Marker preference and fallbacks for _find_repo_root."""

    async def test_prefers_skills_marker(self) -> None:
        """The nearest ancestor containing skills/isaac-sim-remote wins."""
        with tempfile.TemporaryDirectory() as root:
            os.makedirs(os.path.join(root, "skills", "isaac-sim-remote"))
            start = os.path.join(root, "a", "b")
            os.makedirs(start)
            self.assertEqual(_find_repo_root(start), os.path.abspath(root))

    async def test_skills_marker_beats_a_closer_git_ancestor(self) -> None:
        """A closer .git ancestor does not override the primary skills marker."""
        with tempfile.TemporaryDirectory() as root:
            os.makedirs(os.path.join(root, "skills", "isaac-sim-remote"))
            nested = os.path.join(root, "a")
            os.makedirs(os.path.join(nested, ".git"))
            start = os.path.join(nested, "b")
            os.makedirs(start)
            self.assertEqual(_find_repo_root(start), os.path.abspath(root))

    async def test_falls_back_to_git_or_build_marker(self) -> None:
        """Without the primary marker, the nearest .git/build.sh ancestor is used."""
        with tempfile.TemporaryDirectory() as root:
            os.makedirs(os.path.join(root, ".git"))
            start = os.path.join(root, "a", "b")
            os.makedirs(start)
            self.assertEqual(_find_repo_root(start), os.path.abspath(root))
