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

import omni.kit.app
import omni.usd
from isaacsim.core.utils.stage import traverse_stage
from isaacsim.test.utils import MenuUITestCase, get_all_menu_paths
from omni.kit.mainwindow import get_main_window
from omni.kit.ui_test import get_context_menu

# Menu dict is populated lazily in test setUp to avoid hanging during test discovery.
# At module load time, we use empty dict so dynamic test generation creates a placeholder test.
_menu_dict = {}


class TestPhysxMenuAssets(MenuUITestCase):
    """Test class for verifying PhysX sensor menu functionality."""

    _menu_loaded = False

    async def setUp(self):
        """Set up test environment and populate menu dict if needed."""
        await super().setUp()
        # Populate menu dict on first test run (not at module load time)
        if not TestPhysxMenuAssets._menu_loaded:
            global _menu_dict
            window = get_main_window()
            _menu_dict = await get_context_menu(window._ui_main_window.main_menu_bar, get_all=False)
            TestPhysxMenuAssets._menu_loaded = True


def _create_test_for_physx_lidar_option(test_path):
    """Create a test function for a PhysX Lidar menu option."""

    async def test_function(self):
        await self.click_menu_with_retry(test_path)
        await self.run_timeline_frames(5)

        num_prims = 0
        sensor_passed = False

        for prim in traverse_stage():
            num_prims += 1
            prim_type = prim.GetTypeName()
            if prim_type in ("Lidar", "Generic"):
                sensor_passed = True
                break

        self.assertGreater(num_prims, 0, "No prims added to stage.")
        self.assertTrue(sensor_passed, f"{test_path} did not pass, missing prim or wrong prim type")

    test_name = test_path.replace("/", "_").replace(" ", "_")
    test_function.__name__ = f"test_reference_{test_name}"
    test_function.__doc__ = f"Test adding {test_path} as a reference"

    return test_function


def _create_test_for_lightbeam_option(test_path):
    """Create a test function for a LightBeam Sensor menu option."""

    async def test_function(self):
        await self.click_menu_with_retry(test_path)
        await self.run_timeline_frames(5)

        num_prims = 0
        sensor_passed = False

        for prim in traverse_stage():
            num_prims += 1
            prim_type = prim.GetTypeName()
            if prim_type == "IsaacLightBeamSensor":
                sensor_passed = True
                break
            if prim_type == "Xform" and "TS" in prim.GetPath().pathString:
                sensor_passed = True
                break

        self.assertGreater(num_prims, 0, "No prims added to stage.")
        self.assertTrue(sensor_passed, f"{test_path} did not pass, missing prim or wrong prim type")

    test_name = test_path.replace("/", "_").replace(" ", "_")
    test_function.__name__ = f"test_reference_{test_name}"
    test_function.__doc__ = f"Test adding {test_path} as a reference"

    return test_function


# Find all PhysX Lidar and LightBeam sensor creation menu items and dynamically add test methods
physx_lidar_root_path = "Create/Sensors/PhysX Lidar"
lightbeam_root_path = "Create/Sensors/LightBeam Sensor"

physx_lidar_menu_dict = _menu_dict.get("Create", {}).get("Sensors", {}).get("PhysX Lidar", {})
lightbeam_menu_dict = _menu_dict.get("Create", {}).get("Sensors", {}).get("LightBeam Sensor", {})

# Collect PhysX Lidar menu items
physx_lidar_menu_list = get_all_menu_paths(physx_lidar_menu_dict, root_path=physx_lidar_root_path)
# Collect LightBeam Sensor menu items
lightbeam_menu_list = get_all_menu_paths(lightbeam_menu_dict, root_path=lightbeam_root_path)
# Combine both sensor lists
sensor_menu_list = physx_lidar_menu_list + lightbeam_menu_list

if len(sensor_menu_list) == 0:

    async def test_no_menu_items_found(self):
        self.fail("No menu items found in PhysX Lidar or LightBeam Sensor menus")

    setattr(TestPhysxMenuAssets, "test_no_menu_items_found", test_no_menu_items_found)
else:
    for test_path in sensor_menu_list:
        if test_path.startswith(physx_lidar_root_path):
            test_func = _create_test_for_physx_lidar_option(test_path)
        else:
            test_func = _create_test_for_lightbeam_option(test_path)
        setattr(TestPhysxMenuAssets, test_func.__name__, test_func)
