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

"""Shared utilities for the asset transformer."""


def make_explicit_relative(rel_path: str) -> str:
    """Ensure a relative path starts with an explicit ``./`` or ``../`` prefix.

    ``os.path.relpath`` omits the ``./`` when the target is in the same
    directory or a subdirectory.  USD best practice is to always write
    explicit relative anchors so that tooling never confuses a bare
    filename with a search-path identifier.

    Args:
        rel_path: A relative path (forward or back-slash separators).

    Returns:
        The path guaranteed to start with ``./`` or ``../``.

    """
    if not rel_path:
        return rel_path
    if rel_path.startswith("./") or rel_path.startswith("../"):
        return rel_path
    if rel_path.startswith(".\\") or rel_path.startswith("..\\"):
        return rel_path
    return f"./{rel_path}"
