# SPDX-FileCopyrightText: Copyright (c) 2018-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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
from pathlib import Path

import omni.kit.app
import omni.kit.commands
import omni.kit.test
import omni.usd
from isaacsim.core.experimental.utils import prim as prim_utils
from isaacsim.core.utils.viewports import set_camera_view
from isaacsim.test.utils import (
    MenuUITestCase,
    capture_viewport_annotator_data_async,
    compare_arrays_within_tolerances,
    get_all_menu_paths,
    read_image_as_array,
)
from omni.kit.mainwindow import get_main_window
from omni.kit.ui_test import get_context_menu, menu_click
from omni.kit.viewport.utility import get_active_viewport
from pxr import UsdPhysics

EXTENSION_FOLDER_PATH = Path(omni.kit.app.get_app().get_extension_manager().get_extension_path_by_module(__name__))
TEST_DATA_PATH = EXTENSION_FOLDER_PATH.joinpath("data/tests")

# Get menu structure at module load time
_window = get_main_window()
_menu_dict = asyncio.run(get_context_menu(_window._ui_main_window.main_menu_bar, get_all=False))

# =============================================================================
# Robot Menu Tests
# =============================================================================

ROBOT_SKIP_LIST = ["Create/Robots/Asset Browser"]


class TestRobotMenuAssets(MenuUITestCase):
    """Test class for verifying robot menu asset loading functionality."""

    pass


def _create_robot_test(test_path: str):
    """Create a test function for a specific robot menu option."""

    async def test_function(self):
        await menu_click(test_path, human_delay_speed=50)
        await self.wait_n_frames(20)
        await self.wait_for_stage_loading()

        has_robot = False
        for prim in self._stage.Traverse():
            if prim.HasAPI(UsdPhysics.ArticulationRootAPI):
                has_robot = True
                prim_path = prim_utils.get_prim_path(prim)
                print(f"articulation root found at {prim_path}")
                break

        self.assertTrue(has_robot, f"Failed to find articulation root for {test_path}")

    test_name = test_path.replace("/", "_").replace(" ", "_")
    test_function.__name__ = f"test_robot_{test_name}"
    test_function.__doc__ = f"Test loading robot from menu: {test_path}"

    return test_function


# Dynamically add robot test methods
_robot_menu_dict = _menu_dict.get("Create", {}).get("Robots", {})
_robot_menu_list = get_all_menu_paths(_robot_menu_dict, root_path="Create/Robots")

if len(_robot_menu_list) == 0:

    async def test_no_robot_menu_items_found(self):
        self.fail("No menu items found in Create/Robots")

    setattr(TestRobotMenuAssets, "test_no_robot_menu_items_found", test_no_robot_menu_items_found)
else:
    for _test_path in _robot_menu_list:
        if _test_path not in ROBOT_SKIP_LIST:
            _test_func = _create_robot_test(_test_path)
            setattr(TestRobotMenuAssets, _test_func.__name__, _test_func)


# =============================================================================
# Environment Menu Tests
# =============================================================================

ENVIRONMENT_SKIP_LIST = ["Create/Environments/Asset Browser"]


class TestEnvironmentMenuAssets(MenuUITestCase):
    """Test class for verifying environment menu asset loading functionality."""

    async def setUp(self):
        """Set up test environment before each test method."""
        await super().setUp()
        self._golden_img_dir = TEST_DATA_PATH.absolute().joinpath("golden_img").absolute()
        self._usd_selection = omni.usd.get_context().get_selection()


def _create_environment_test(test_path: str):
    """Create a test function for a specific environment menu option."""

    async def test_function(self):
        await self.click_menu_with_retry(test_path, delays=[100, 150, 200])
        await self.wait_n_frames(10)
        await self.wait_for_stage_loading()
        await self.wait_n_frames(1)

        golden_img_name = test_path.split("/")[-1] + ".png"
        viewport_api = get_active_viewport()
        viewport_api.resolution = (1280, 720)
        self._usd_selection.clear_selected_prim_paths()
        await self.wait_n_frames(1)

        if "Office" in test_path or "Hospital" in test_path or "Warehouse" in test_path:
            set_camera_view(eye=[-4, 4, 2], target=[0, 0, 1])
        else:
            set_camera_view(eye=[3, -3, 3], target=[0, 0, 0])

        await self.wait_n_frames(10)

        rgb_data = await capture_viewport_annotator_data_async(viewport_api)
        golden_img_data = read_image_as_array(self._golden_img_dir / golden_img_name)
        results = compare_arrays_within_tolerances(
            golden_img_data,
            rgb_data,
            allclose_rtol=None,
            allclose_atol=None,
            mean_tolerance=10,
            print_all_stats=True,
        )
        self.assertTrue(results["passed"], f"Results: {test_path} - {results}")

        num_prims = sum(1 for _ in self._stage.Traverse())
        self.assertGreaterEqual(num_prims, 9, f"Failed to find sufficient prims for {test_path}")

    test_name = test_path.replace("/", "_").replace(" ", "_")
    test_function.__name__ = f"test_environment_{test_name}"
    test_function.__doc__ = f"Test loading environment from menu: {test_path}"

    return test_function


# Dynamically add environment test methods
_environment_menu_dict = _menu_dict.get("Create", {}).get("Environments", {})
_environment_menu_list = get_all_menu_paths(_environment_menu_dict, root_path="Create/Environments")

if len(_environment_menu_list) == 0:

    async def test_no_environment_menu_items_found(self):
        self.fail("No menu items found in Create/Environments")

    setattr(TestEnvironmentMenuAssets, "test_no_environment_menu_items_found", test_no_environment_menu_items_found)
else:
    for _test_path in _environment_menu_list:
        if _test_path not in ENVIRONMENT_SKIP_LIST:
            _test_func = _create_environment_test(_test_path)
            setattr(TestEnvironmentMenuAssets, _test_func.__name__, _test_func)


# =============================================================================
# April Tag Menu Test
# =============================================================================


class TestAprilTagMenu(MenuUITestCase):
    """Test class for verifying April Tag menu functionality."""

    async def test_apriltag_menu(self):
        """Test that April Tags menu creates material that can be bound to a mesh."""
        apriltag_path = "Create/April Tags"

        await self.wait_n_frames(1)
        await self.click_menu_with_retry(apriltag_path)
        await self.wait_n_frames(1)

        omni.kit.commands.execute("CreateMeshPrimWithDefaultXform", prim_type="Cube", above_ground=True)
        await self.wait_n_frames(1)

        omni.kit.commands.execute(
            "BindMaterial", material_path="/Looks/AprilTag", prim_path=["/Cube"], strength=["weakerThanDescendants"]
        )
        await self.wait_n_frames(1)
