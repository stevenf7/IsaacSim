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

"""Provides access to the Extension class for transformer rules functionality."""

import os as _os

from .extension import Extension, register_all_rules  # noqa: F401

_EXTENSION_ROOT = _os.path.normpath(_os.path.join(_os.path.dirname(__file__), "..", "..", "..", ".."))

DEFAULT_PROFILE_PATH = _os.path.join(_EXTENSION_ROOT, "data", "isaacsim_structure.json")
"""Absolute path to the default Isaac Sim asset-structure profile shipped with this extension."""

__all__ = ["DEFAULT_PROFILE_PATH", "register_all_rules"]
