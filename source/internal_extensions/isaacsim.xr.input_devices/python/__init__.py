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

from .impl.extension import Extension

# Re-export hand tracker plugin bindings if available
try:
    from .bindings._isaac_xr_input_devices import (
        ISAACSIM_HAND_COUNT,
        ISAACSIM_HAND_JOINT_COUNT,
        handtracker_get_data,
        handtracker_initialize,
        handtracker_load,
        handtracker_shutdown,
        handtracker_unload,
    )
except Exception:
    # Keep module importable even if bindings are missing
    pass

__all__ = [
    "Extension",
    "handtracker_load",
    "handtracker_unload",
    "handtracker_initialize",
    "handtracker_get_data",
    "handtracker_shutdown",
    "ISAACSIM_HAND_JOINT_COUNT",
    "ISAACSIM_HAND_COUNT",
]
