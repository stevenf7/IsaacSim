# SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: LicenseRef-NvidiaProprietary
#
# NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
# property and proprietary rights in and to this material, related
# documentation and any modifications thereto. Any use, reproduction,
# disclosure or distribution of this material and related documentation
# without an express license agreement from NVIDIA CORPORATION or
# its affiliates is strictly prohibited.

"""
omni.kit.test-based tests for Manus+Vive integration that exercises the hand tracker.

plugin through the integration layer. The test forces the use of the test
hand-tracker shared library by setting ISAACSIM_HANDTRACKER_LIB.
"""

import os
import sys

import omni.kit.app
import omni.kit.test


def _discover_test_handtracker_library(module_dir: str):
    """Return the absolute path to the test hand-tracker library if found.

    This mirrors the discovery strategy used in the handtracker plugin tests.
    """
    ext_roots = []
    try:
        ext_mgr = omni.kit.app.get_app().get_extension_manager()
        ext_roots.append(ext_mgr.get_extension_path("isaacsim.xr.input_devices"))
    except Exception:
        pass

    # In built layout: .../exts/isaacsim.xr.input_devices/isaacsim/xr/input_devices
    # In source layout, tests may still resolve similarly after staging.
    ext_roots.append(os.path.abspath(os.path.join(module_dir, "..", "..", "..")))

    if sys.platform.startswith("linux"):
        cand_names = ["libIsaacSimHandTracker_test.so"]
    elif sys.platform == "win32":
        cand_names = ["IsaacSimHandTracker_test.dll"]
    elif sys.platform == "darwin":
        cand_names = ["libIsaacSimHandTracker_test.dylib"]
    else:
        cand_names = ["libIsaacSimHandTracker_test.so"]

    for root in ext_roots:
        if not root:
            continue
        for name in cand_names:
            lib_path = os.path.join(root, "bin", name)
            if os.path.exists(lib_path):
                return lib_path
    return None


class TestManusViveIntegration(omni.kit.test.AsyncTestCase):
    """Test manus vive integration."""

    async def setUp(self):
        """Set up test fixtures."""
        pass

    async def tearDown(self):
        """Tear down test fixtures."""
        try:
            import isaacsim.xr.input_devices as xr

            xr.handtracker_shutdown()
            xr.handtracker_unload()
        except Exception:
            pass
        await omni.kit.app.get_app().next_update_async()

    async def test_integration_uses_test_handtracker_plugin(self):
        """Test integration uses test handtracker plugin."""
        # Import module to locate its directory and for constants
        import isaacsim.xr.input_devices as xr

        # Discover the test hand-tracker library shipped with this extension
        module_dir = os.path.dirname(xr.__file__)
        test_lib = _discover_test_handtracker_library(module_dir)
        if test_lib is None:
            self.skipTest("Test hand-tracker library not found in extension bin/")
        print(f"[manus_vive_integration:test] Using test hand-tracker lib: {test_lib}")

        # Also set env var as a fallback for any indirect native discovery
        os.environ["ISAACSIM_HANDTRACKER_LIB"] = test_lib

        # Get integration passing the override so register happens with the test library
        from isaacsim.xr.input_devices.impl.manus_vive_integration import get_manus_vive_integration

        integration = get_manus_vive_integration(handtracker_lib_override=test_lib)

        # Ensure hand tracker was initialized and marked connected
        print(
            f"[manus_vive_integration:test] Handtracker loaded={integration._handtracker_loaded}, "
            f"initialized={integration._handtracker_initialized}"
        )
        print(f"[manus_vive_integration:test] Device status: {integration.device_status}")
        self.assertTrue(integration._handtracker_loaded, "Hand tracker library did not load")
        self.assertTrue(integration._handtracker_initialized, "Hand tracker did not initialize")
        self.assertTrue(
            integration.device_status["manus_gloves"]["connected"],
            "Manus gloves not reported connected",
        )

        # Validate data fetch through the integration's Manus tracker facade
        data = integration.manus_tracker.get_data()
        print(f"[manus_vive_integration:test] get_data entries={len(data) if data else 'n/a'}")
        self.assertIsInstance(data, dict)

        # Expect left then right keys, each with ISAACSIM_HAND_JOINT_COUNT entries
        expected_per_hand = xr.ISAACSIM_HAND_JOINT_COUNT
        left_keys = [f"left_{i}" for i in range(expected_per_hand)]
        right_keys = [f"right_{i}" for i in range(expected_per_hand)]
        for k in left_keys + right_keys:
            self.assertIn(k, data)
            v = data[k]
            self.assertIsInstance(v, dict)
            self.assertIn("position", v)
            self.assertIn("orientation", v)
            self.assertTrue(isinstance(v["position"], list) and len(v["position"]) == 3)
            self.assertTrue(isinstance(v["orientation"], list) and len(v["orientation"]) == 4)

        # Cleanup integration resources explicitly
        integration.cleanup()
