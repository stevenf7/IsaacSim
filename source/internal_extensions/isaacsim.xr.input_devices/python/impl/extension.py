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

"""Extension lifecycle for `isaacsim.xr.input_devices`.

This extension creates a singleton `ManusViveIntegration` instance on startup,
registers available devices (hand-tracker via C API plugin and Vive trackers
via pysurvive), and tears down resources on shutdown.

Use `Extension.get_instance()` to retrieve the active extension instance and
its `manus_vive_integration` during runtime. Prefer using
`get_manus_vive_integration()` from `manus_vive_integration.py` in client code.
"""

import carb
import omni.ext

from .manus_vive_integration import ManusViveIntegration


class Extension(omni.ext.IExt):
    """Extension lifecycle management."""

    _instance = None

    def on_startup(self, ext_id: str) -> None:
        """Create the integration and register devices when the extension loads.

        Args:
            ext_id: The unique identifier of the extension being started.
        """
        carb.log_info("IsaacSim XR Input Devices extension startup")
        Extension._instance = self
        self.manus_vive_integration = ManusViveIntegration()
        self._register_devices()

    def on_shutdown(self):
        """Cleanup device resources when the extension unloads."""
        carb.log_info("IsaacSim XR Input Devices extension shutdown")
        if hasattr(self, "manus_vive_integration"):
            self.manus_vive_integration.cleanup()
        Extension._instance = None

    def _register_devices(self):
        """Register the hand-tracker plugin and Vive tracking devices."""
        self.manus_vive_integration.register_devices()

    @classmethod
    def get_instance(cls):
        """Return the active extension instance or `None` if not started.

        Returns:
            The active extension instance, or None if not started.
        """
        return cls._instance
