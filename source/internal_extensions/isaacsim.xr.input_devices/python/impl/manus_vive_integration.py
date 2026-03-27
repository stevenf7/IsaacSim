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


import carb
from isaacsim.xr.input_devices.bindings._isaac_xr_input_devices import (
    ISAACSIM_HAND_JOINT_COUNT,
    handtracker_get_data,
    handtracker_initialize,
    handtracker_load,
    handtracker_shutdown,
    handtracker_unload,
)

from .vive_tracker import IsaacSimViveTracker

_handtracker_available = True


def get_manus_vive_integration(handtracker_lib_override=None):
    """Return a shared `ManusViveIntegration` instance.

    If the extension is loaded, returns its singleton instance; otherwise creates
    a new instance. When `handtracker_lib_override` is provided, the hand-tracker
    plugin is (re)registered using that library path or name.

    Args:
        handtracker_lib_override: Optional absolute path or base name used to
            load the hand tracking library (see environment variables below).

    Environment variables:
        - `ISAACSIM_HANDTRACKER_LIB`: absolute path to the shared library
        - `ISAACSIM_HANDTRACKER_NAME`: base name to search (`lib<name>.so`, `<name>.dll`)

    Returns:
        ManusViveIntegration: integration used for device coordination.
    """
    try:

        from .extension import Extension

        ext_instance = Extension.get_instance()
        if ext_instance and hasattr(ext_instance, "manus_vive_integration"):
            integration = ext_instance.manus_vive_integration
            if handtracker_lib_override:
                # Ensure devices are registered with the override when provided
                integration.register_devices(handtracker_lib_override)
            return integration
        else:
            carb.log_warn("Extension not loaded, creating new ManusViveIntegration instance")
            integration = ManusViveIntegration()
            integration.register_devices(handtracker_lib_override)
            return integration
    except Exception as e:
        carb.log_warn(f"Failed to get extension instance: {e}, creating new ManusViveIntegration instance")
        integration = ManusViveIntegration()
        integration.register_devices(handtracker_lib_override)
        return integration


class ManusTracker:
    def __init__(self):
        """Thin wrapper around the C++ bindings for the hand-tracker plugin."""

    def update(self):
        """No-op placeholder for symmetry with Vive tracker update cadence."""
        return

    def get_data(self):
        """Return latest hand joint poses keyed by hand and joint index.

        Returns a dict mapping keys like `left_0`..`left_N` and `right_0`..`right_N`
        to pose dicts with:
        - `position`: `[x, y, z]` in meters
        - `orientation`: quaternion `[x, y, z, w]`

        Returns an empty dict when no data is available.
        """
        ok, hands = handtracker_get_data()
        if not ok or not hands:
            return {}

        output = {}
        hand_labels = ["left", "right"]
        for hand_index, joint_list in enumerate(hands):
            label = hand_labels[hand_index] if hand_index < len(hand_labels) else f"hand_{hand_index}"
            max_joint_count = min(len(joint_list), ISAACSIM_HAND_JOINT_COUNT)
            for out_index in range(max_joint_count):
                joint = joint_list[out_index]
                pos = joint.get("position", (0.0, 0.0, 0.0))
                ori = joint.get("orientation", (1.0, 0.0, 0.0, 0.0))
                output[f"{label}_{out_index}"] = {
                    "position": [pos[0], pos[1], pos[2]],
                    "orientation": [ori[3], ori[0], ori[1], ori[2]],
                }

        return output


class ManusViveIntegration:
    def __init__(self):
        """Initialize hand-tracker plugin, Vive tracker, and device status."""
        # Hand tracker plugin state
        self._handtracker_loaded = False
        self._handtracker_initialized = False

        # Vive tracker
        self.vive_tracker = IsaacSimViveTracker()

        # Manus tracker
        self.manus_tracker = ManusTracker()

        self.device_status = {
            "manus_gloves": {"connected": False, "last_data_time": 0},
            "vive_trackers": {"connected": False, "last_data_time": 0},
            "left_hand_connected": False,
            "right_hand_connected": False,
        }

    def register_devices(self, handtracker_lib_override=None):
        """Register the hand-tracker plugin and Vive trackers.

        Updates connectivity flags in `device_status` and reports status via logs.
        Honors `handtracker_lib_override` and environment variables when loading
        the hand-tracker library.
        """
        try:
            # Initialize Hand Tracker plugin (replacing Manus glove tracker)
            if _handtracker_available:
                try:
                    self._handtracker_loaded = handtracker_load(handtracker_lib_override)
                    if not self._handtracker_loaded:
                        carb.log_warn("Failed to load Hand Tracker shared library")
                    else:
                        self._handtracker_initialized = handtracker_initialize()
                        if self._handtracker_initialized:
                            carb.log_info("Hand Tracker initialized successfully")
                            self.device_status["manus_gloves"]["connected"] = True
                        else:
                            carb.log_warn("Failed to initialize Hand Tracker")
                except Exception as e:
                    carb.log_error(f"Exception during Hand Tracker initialization: {e}")
            else:
                carb.log_warn("Hand Tracker plugin bindings are unavailable")

            # Initialize Vive trackers
            if self.vive_tracker.is_connected:
                carb.log_info("Vive trackers registered successfully")
                self.device_status["vive_trackers"]["connected"] = True
            else:
                carb.log_warn("Failed to initialize Vive trackers")

        except Exception as e:
            carb.log_error(f"Failed to register Manus and Vive devices: {e}")

    def cleanup(self):
        """Clean up hand-tracker plugin and Vive tracker resources."""
        # Shutdown Hand Tracker plugin
        if _handtracker_available:
            try:
                if self._handtracker_initialized or self._handtracker_loaded:
                    handtracker_shutdown()
                    handtracker_unload()
            except Exception as e:
                carb.log_error(f"Error during Hand Tracker cleanup: {e}")

        # Shutdown Vive tracker
        if hasattr(self, "vive_tracker"):
            self.vive_tracker.cleanup()
