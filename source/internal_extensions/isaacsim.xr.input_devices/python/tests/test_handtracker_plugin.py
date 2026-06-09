# SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: LicenseRef-NvidiaProprietary
#
# NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
# property and proprietary rights in and to this material, related
# documentation and any modifications thereto. Any use, reproduction,
# disclosure or distribution of this material and related documentation
# without an express license agreement from NVIDIA CORPORATION or
# its affiliates is strictly prohibited.

"""Validate the XR input-device hand-tracker C API bindings with the test plugin."""

import os
import sys

import omni.kit.test


class TestHandTrackerPlugin(omni.kit.test.AsyncTestCase):
    """Exercise test-plugin loading, initialization, joint data reads, and unload."""

    async def setUp(self) -> None:
        """Use per-test plugin discovery instead of shared fixture setup."""

    async def tearDown(self) -> None:
        """Best-effort shutdown/unload of hand-tracker state and drain one Kit frame."""
        try:
            import isaacsim.xr.input_devices as xr

            xr.handtracker_shutdown()
            xr.handtracker_unload()
        except Exception:
            pass
        # Allow one frame for any async teardown on the app side
        await omni.kit.app.get_app().next_update_async()

    async def test_handtracker_plugin_bindings(self) -> None:
        """Load the test hand-tracker library and verify returned hand joint records."""
        import isaacsim.xr.input_devices as xr

        # Explicitly load the test hand-tracker shared library from this extension's bin folder.
        # Derive extension root robustly: prefer Extension Manager, then fall back to module path ascension.
        ext_roots = []
        try:
            ext_mgr = omni.kit.app.get_app().get_extension_manager()
            ext_roots.append(ext_mgr.get_extension_path("isaacsim.xr.input_devices"))
        except Exception:
            pass

        mod_dir = os.path.dirname(xr.__file__)
        # In built layout: .../exts/isaacsim.xr.input_devices/isaacsim/xr/input_devices
        # In source layout, tests may still resolve similarly after staging.
        ext_roots.append(os.path.abspath(os.path.join(mod_dir, "..", "..", "..")))

        if sys.platform.startswith("linux"):
            cand_names = ["libIsaacSimHandTracker_test.so"]
        elif sys.platform == "win32":
            cand_names = ["IsaacSimHandTracker_test.dll"]
        elif sys.platform == "darwin":
            cand_names = ["libIsaacSimHandTracker_test.dylib"]
        else:
            cand_names = ["libIsaacSimHandTracker_test.so"]

        tried_paths = []
        loaded = False
        for root in ext_roots:
            if not root:
                continue
            for name in cand_names:
                lib_path = os.path.join(root, "bin", name)
                tried_paths.append(lib_path)
                if os.path.exists(lib_path):
                    loaded = xr.handtracker_load(lib_path)
                    if loaded:
                        break
            if loaded:
                break
        if not loaded:
            self.skipTest(f"Test hand-tracker library not found. Tried: {tried_paths}")

        # Initialize the device via the C API
        self.assertTrue(xr.handtracker_initialize(), "handtracker_initialize failed")

        # Retrieve joint data
        ok, hands = xr.handtracker_get_data()
        self.assertTrue(ok, "handtracker_get_data reported failure")

        # Validate structure and expected counts
        self.assertIsInstance(hands, list, "hands should be a list")
        self.assertEqual(len(hands), xr.ISAACSIM_HAND_COUNT)
        for hand_list in hands:
            self.assertIsInstance(hand_list, list)
            self.assertEqual(len(hand_list), xr.ISAACSIM_HAND_JOINT_COUNT)

        # Validate a few entries have required keys and shapes
        sample = hands[0][0]
        self.assertTrue(
            {"hand", "joint", "position", "orientation", "radius", "location_flags"}.issubset(sample.keys())
        )
        pos = sample["position"]
        ori = sample["orientation"]
        self.assertTrue(isinstance(pos, tuple) and len(pos) == 3)
        self.assertTrue(isinstance(ori, tuple) and len(ori) == 4)
        # Print the first 3 joint data entries for inspection (left hand)
        print("Sample joint data (left hand, first 3 joints):")
        for i, joint in enumerate(hands[0][:3]):
            print(f"Hand 0, Joint {i}: {joint}")

        # Shutdown and unload
        xr.handtracker_shutdown()
        xr.handtracker_unload()
