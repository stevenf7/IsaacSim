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
"""Menu-driven asset creation tests for Isaac Sim."""

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
from omni.kit.ui_test import get_context_menu
from omni.kit.viewport.utility import get_active_viewport
from pxr import UsdPhysics

EXTENSION_FOLDER_PATH = Path(omni.kit.app.get_app().get_extension_manager().get_extension_path_by_module(__name__))
TEST_DATA_PATH = EXTENSION_FOLDER_PATH.joinpath("data/tests")

# =============================================================================
# Robot Menu Tests
# =============================================================================

ROBOT_ROOT_PATH = "Create/Robots"
ROBOT_SKIP_LIST = ["Create/Robots/Asset Browser"]


class TestRobotMenuAssets(MenuUITestCase):
    """Test class for verifying robot menu asset loading functionality."""

    async def _test_robot_menu_option(self, test_path: str) -> None:
        """Test a specific robot menu option.

        Args:
            test_path: Menu path to trigger.
        """
        await self.menu_click_with_retry(test_path)
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

    async def test_robot_menu_items(self):
        """Test all robot menu items."""
        # Get menu dict at runtime instead of module load time
        window = get_main_window()
        menu_dict = await get_context_menu(window._ui_main_window.main_menu_bar, get_all=False)

        robot_menu_dict = menu_dict.get("Create", {}).get("Robots", {})
        robot_menu_list = get_all_menu_paths(robot_menu_dict, root_path=ROBOT_ROOT_PATH)

        self.assertGreater(len(robot_menu_list), 0, f"No menu items found in {ROBOT_ROOT_PATH}")

        for test_path in robot_menu_list:
            if test_path not in ROBOT_SKIP_LIST:
                with self.subTest(menu_path=test_path):
                    await self._test_robot_menu_option(test_path)
                    # Reset stage for next iteration
                    await self.new_stage()


# =============================================================================
# Environment Menu Tests
# =============================================================================

ENVIRONMENT_ROOT_PATH = "Create/Environments"
ENVIRONMENT_SKIP_LIST = ["Create/Environments/Asset Browser"]


class TestEnvironmentMenuAssets(MenuUITestCase):
    """Test class for verifying environment menu asset loading functionality."""

    async def setUp(self):
        """Set up test environment before each test method."""
        await super().setUp()
        self._golden_img_dir = TEST_DATA_PATH.absolute().joinpath("golden_img").absolute()
        self._usd_selection = omni.usd.get_context().get_selection()

    async def _test_environment_menu_option(self, test_path: str) -> None:
        """Test a specific environment menu option.

        Args:
            test_path: Menu path to trigger.
        """
        await self.menu_click_with_retry(test_path, delays=[100, 150, 200])
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

        retries = 3
        while retries > 0:
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
            if results["passed"]:
                break
            retries -= 1
            await self.wait_n_frames(10)

        self.assertTrue(results["passed"], f"Results: {test_path} - {results}")

        num_prims = sum(1 for _ in self._stage.Traverse())
        self.assertGreaterEqual(num_prims, 9, f"Failed to find sufficient prims for {test_path}")

    async def test_environment_menu_items(self):
        """Test all environment menu items."""
        # Get menu dict at runtime instead of module load time
        window = get_main_window()
        menu_dict = await get_context_menu(window._ui_main_window.main_menu_bar, get_all=False)

        environment_menu_dict = menu_dict.get("Create", {}).get("Environments", {})
        environment_menu_list = get_all_menu_paths(environment_menu_dict, root_path=ENVIRONMENT_ROOT_PATH)

        self.assertGreater(len(environment_menu_list), 0, f"No menu items found in {ENVIRONMENT_ROOT_PATH}")

        for test_path in environment_menu_list:
            if test_path not in ENVIRONMENT_SKIP_LIST:
                with self.subTest(menu_path=test_path):
                    await self._test_environment_menu_option(test_path)
                    # Reset stage for next iteration
                    await self.new_stage()


# =============================================================================
# April Tag Menu Test
# =============================================================================


class TestAprilTagMenu(MenuUITestCase):
    """Test class for verifying April Tag menu functionality."""

    async def test_apriltag_menu(self):
        """Test that April Tags menu creates material that can be bound to a mesh."""
        apriltag_path = "Create/April Tags"

        await self.wait_n_frames(1)
        await self.menu_click_with_retry(apriltag_path)
        await self.wait_n_frames(1)

        omni.kit.commands.execute("CreateMeshPrimWithDefaultXform", prim_type="Cube", above_ground=True)
        await self.wait_n_frames(1)

        omni.kit.commands.execute(
            "BindMaterial", material_path="/Looks/AprilTag", prim_path=["/Cube"], strength=["weakerThanDescendants"]
        )
        await self.wait_n_frames(1)
