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

"""Shared helpers for the skills test-suite (path resolution + dynamic import)."""

from __future__ import annotations

import importlib.util
import os
import sys
import types

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))


def _find_skills_dir(start: str) -> str:
    """Locate the repo's skills/ directory by walking up from start.

    The test-suite lives outside skills/ (under tools/isaac/skills_tests), so the
    skills root is resolved via the SKILLS.md marker rather than a fixed relative
    depth.
    """
    path = start
    while True:
        candidate = os.path.join(path, "skills")
        if os.path.isfile(os.path.join(candidate, "SKILLS.md")):
            return candidate
        parent = os.path.dirname(path)
        if parent == path:
            raise RuntimeError(f"could not locate the skills/ directory above {start}")
        path = parent


SKILLS_DIR = _find_skills_dir(TESTS_DIR)
REPO_ROOT = os.path.dirname(SKILLS_DIR)


def skill_path(*parts: str) -> str:
    """Absolute path to a file under skills/ (use leading '..' to reach the repo root)."""
    return os.path.join(SKILLS_DIR, *parts)


def load_module_from_path(path: str, name: str | None = None, fake_modules: dict | None = None):
    """Import a standalone .py file as a module object.

    fake_modules: optional {dotted_name: module} stubs temporarily installed in
    sys.modules so scripts that import unavailable packages (e.g. omni) can be
    exercised in isolation. Restored afterwards.
    """
    name = name or ("sut_" + os.path.splitext(os.path.basename(path))[0])
    saved: dict[str, types.ModuleType | None] = {}
    if fake_modules:
        for key, value in fake_modules.items():
            saved[key] = sys.modules.get(key)
            sys.modules[key] = value
    try:
        spec = importlib.util.spec_from_file_location(name, path)
        if spec is None or spec.loader is None:
            raise ImportError(f"cannot load module from {path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    finally:
        if fake_modules:
            for key, old in saved.items():
                if old is None:
                    sys.modules.pop(key, None)
                else:
                    sys.modules[key] = old
