# SPDX-FileCopyrightText: Copyright (c) 2025-2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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

import os
import sys
from typing import Dict

import carb
from pxr import Gf

try:
    import pysurvive
    from pysurvive.pysurvive_generated import survive_simple_close

    PYSURVIVE_AVAILABLE = True
    carb.log_info("pysurvive imported successfully")
except ImportError as e:
    carb.log_error(f"pysurvive not available")
    PYSURVIVE_AVAILABLE = False


class IsaacSimViveTracker:
    def __init__(self):
        """Initialize the Vive tracker interface and state.

        Creates a `pysurvive.SimpleContext` when `pysurvive` is available.
        When initialization succeeds, `is_connected` is set to True. Device
        poses are collected in `device_data` keyed by device identifiers.
        """
        self.device_data = {}
        self.is_connected = False

        if PYSURVIVE_AVAILABLE:
            try:
                self._ctx = pysurvive.SimpleContext([sys.argv[0]])
                if self._ctx is None:
                    raise RuntimeError("Failed to initialize Survive context.")
                self.is_connected = True
                carb.log_info("Vive tracker initialized with pysurvive")
            except Exception as e:
                carb.log_warn(f"Failed to initialize Vive tracker: {e}")
        else:
            self._ctx = None

    def update(self):
        """Poll the Vive tracking system and update device poses.

        Reads updated poses from the `pysurvive` context, converts them to Isaac
        Sim conventions, and stores them in `device_data`.

        Coordinate system:
        - Converted from Vive left handed to Isaac right handed.
        """
        if not PYSURVIVE_AVAILABLE:
            raise RuntimeError("pysurvive not available")
        if not self.is_connected:
            return

        try:
            max_iterations = 10  # Prevent infinite loops
            iteration = 0
            while iteration < max_iterations:
                updated = self._ctx.NextUpdated()
                if not updated:
                    break
                iteration += 1

                pose_obj, _ = updated.Pose()
                pos = pose_obj.Pos  # (x, y, z)
                ori = pose_obj.Rot  # (w, x, y, z)
                device_id = updated.Name().decode("utf-8")

                # Convert from left handed to right handed coordinate system
                self.device_data[device_id] = {
                    "position": [
                        float(pos[0]),
                        float(-pos[2]),
                        float(pos[1]),
                    ],
                    "orientation": [float(ori[0]), float(ori[1]), float(-ori[3]), float(ori[2])],
                }

        except Exception as e:
            carb.log_error(f"Failed to update Vive tracker data: {e}")

    def get_data(self) -> Dict:
        """Return the latest Vive tracker device data.

        Returns a mapping from device identifiers to dicts with:
        - `position`: `[x, y, z]` in meters
        - `orientation`: quaternion `[w, x, y, z]`
        """
        return self.device_data

    def cleanup(self):
        """Release Vive tracker resources and disconnect.

        Closes the underlying `pysurvive` context when present and sets
        `is_connected` to False.
        """
        try:
            if PYSURVIVE_AVAILABLE and hasattr(self, "_ctx") and self._ctx is not None:
                carb.log_info("Cleaning up Vive tracker context")
                survive_simple_close(self._ctx.ptr)
            self.is_connected = False
        except Exception as e:
            carb.log_error(f"Error during Vive tracker cleanup: {e}")
