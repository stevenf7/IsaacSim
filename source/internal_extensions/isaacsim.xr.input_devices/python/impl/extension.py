# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

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
    _instance = None

    def on_startup(self, ext_id):
        """Create the integration and register devices when the extension loads."""
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
        """Return the active extension instance or `None` if not started."""
        return cls._instance
