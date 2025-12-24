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

import asyncio

from isaacsim.core.utils.stage import traverse_stage
from isaacsim.test.utils import MenuUITestCase, get_all_menu_paths
from omni.kit.mainwindow import get_main_window
from omni.kit.ui_test import get_context_menu


class TestMenuAssets(MenuUITestCase):
    pass


# Find all RTX sensor creation menu items and dynamically add test methods to the TestMenuAssets class
window = get_main_window()
menu_dict = asyncio.run(get_context_menu(window._ui_main_window.main_menu_bar, get_all=False))
sensor_menu_dict = menu_dict["Create"]["Sensors"]["RTX Lidar"]
sensor_root_path = "Create/Sensors/RTX Lidar"

sensor_menu_list = get_all_menu_paths(sensor_menu_dict, root_path=sensor_root_path)


def _create_test_for_menu_option(test_path):
    """Create a test function for a specific menu option."""

    async def test_function(self):
        await self.click_menu_with_retry(test_path)
        await self.run_timeline_frames(5)

        num_prims = 0
        sensor_passed = False

        for prim in traverse_stage():
            num_prims += 1
            if prim.IsA("OmniLidar"):
                sensor_passed = True
                break

        self.assertGreater(num_prims, 0, "No prims added to stage.")
        self.assertTrue(sensor_passed, f"{test_path} did not pass, missing prim or wrong prim type")

    test_name = test_path.replace("/", "_").replace(" ", "_")
    test_function.__name__ = f"test_reference_{test_name}"
    test_function.__doc__ = f"Test adding {test_path} as a reference"

    return test_function


if len(sensor_menu_list) == 0:

    async def test_no_menu_items_found(self):
        self.fail(f"No menu items found in {sensor_root_path}")

    setattr(TestMenuAssets, "test_no_menu_items_found", test_no_menu_items_found)
else:
    for test_path in sensor_menu_list:
        test_func = _create_test_for_menu_option(test_path)
        setattr(TestMenuAssets, test_func.__name__, test_func)
