# Copyright (c) 2018-2023, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

import carb
import carb.tokens
import numpy as np
import omni.kit.commands

# NOTE:
#   omni.kit.test - std python's unittest module with additional wrapping to add suport for async/await tests
#   For most things refer to unittest docs: https://docs.python.org/3/library/unittest.html
import omni.kit.test
import omni.kit.ui_test as ui_test
import omni.ui as ui
from omni.isaac.core.utils.nucleus import get_assets_root_path
from omni.isaac.core.utils.prims import get_prim_path
from omni.isaac.core.utils.stage import clear_stage, create_new_stage, traverse_stage
from omni.kit.mainwindow import get_main_window
from omni.kit.ui_test.menu import *
from omni.kit.ui_test.query import *
from pxr import UsdPhysics


# Having a test class dervived from omni.kit.test.AsyncTestCase declared on the root of module will make it auto-discoverable by omni.kit.test
class TestMenuAssets(omni.kit.test.AsyncTestCase):
    # Before running each test
    async def setUp(self):
        self._timeline = omni.timeline.get_timeline_interface()

        self._assets_root_path = get_assets_root_path()
        if self._assets_root_path is None:
            carb.log_error("Could not find Isaac Sim assets folder")
            return

        result = create_new_stage()
        # Make sure the stage loaded
        self.assertTrue(result)
        await omni.kit.app.get_app().next_update_async()

        # list all the Isaac Sim's Robot assets' menu path
        window = get_main_window()
        self.menu_dict = await get_context_menu(window._ui_main_window.main_menu_bar, get_all=False)

        pass

    # After running each test
    async def tearDown(self):
        # self.my_world.stop()
        # self.my_world.clear_instance()
        await omni.kit.app.get_app().next_update_async()
        # In some cases the test will end before the asset is loaded, in this case wait for assets to load
        while omni.usd.get_context().get_stage_loading_status()[2] > 0:
            await omni.kit.app.get_app().next_update_async()
        pass

    # Actual test, notice it is "async" function, so "await" can be used if needed
    async def test_loading_robots(self):

        self.robot_menu_dict = self.menu_dict["Create"]["Isaac"]["Robots"]
        self.ee_menu_dict = self.menu_dict["Create"]["Isaac"]["End Effectors"]

        ## check everything under "Robot"

        robot_root_path = "Create/Isaac/Robots"
        ee_root_path = "Create/Isaac/End Effectors"

        def get_menu_path(d, path, result, root_path):

            for key, value in d.items():
                if key != "_":
                    new_path = path + "/" + str(key)
                if isinstance(value, dict):
                    get_menu_path(value, new_path, result, root_path)
                elif isinstance(value, str):
                    result.append(root_path + path + "/" + str(value))
                elif isinstance(value, list):
                    for robot in value:
                        result.append(root_path + path + "/" + str(robot))
            return result

        empty_list = []
        empty_path = ""
        robot_menu_list = get_menu_path(self.robot_menu_dict, empty_path, empty_list, robot_root_path)
        empty_list = []
        empty_path = ""
        ee_menu_list = get_menu_path(self.ee_menu_dict, empty_path, empty_list, ee_root_path)

        test_list = robot_menu_list + ee_menu_list

        # surface gripper is just a graph, and jetracer has no articulation root
        skip_list = ["Create/Isaac/End Effectors/Surface Gripper", "Create/Isaac/Robots/NVIDIA/Jetracer"]

        failed_robots = []
        for test_path in test_list:
            print(test_path)
            if test_path in skip_list:
                print("skipping ", test_path)
                continue

            # for each item on the robot's asset path, load it and check if successful by checking if there is an articulation on stage
            clear_stage()
            await omni.kit.app.get_app().next_update_async()
            await omni.kit.app.get_app().next_update_async()
            has_robot = False
            await menu_click(test_path, human_delay_speed=10)
            for i in range(20):
                await omni.kit.app.get_app().next_update_async()

            # # waiting for stage to load
            while omni.usd.get_context().get_stage_loading_status()[2] > 0:
                await omni.kit.app.get_app().next_update_async()

            # # once stage loading finishes, check if there's an articulation root on stage
            for prim in traverse_stage():
                if prim.HasAPI(UsdPhysics.ArticulationRootAPI):
                    has_robot = True
                    prim_path = get_prim_path(prim)
                    print(f"articulation root found at {prim_path}")
                    break
            if not has_robot:
                print(f"failed to find articulation at {test_path}")
                failed_robots.append(test_path)

        print(failed_robots)

        # if failed_robot array has 0 entries, then test passed
        self.assertEqual(len(failed_robots), 0)

    async def test_apriltag_menu(self):
        apriltag_root_path = "Create/Isaac/April Tag"

        def get_menu_path(d, path, result, root_path):

            for key, value in d.items():
                if key != "_":
                    new_path = path + "/" + str(key)
                if isinstance(value, dict):
                    get_menu_path(value, new_path, result, root_path)
                elif isinstance(value, str):
                    result.append(root_path + path + "/" + str(value))
                elif isinstance(value, list):
                    for robot in value:
                        result.append(root_path + path + "/" + str(robot))
            return result

        empty_list = []
        empty_path = ""
        apriltag_menu_list = get_menu_path(
            self.menu_dict["Create"]["Isaac"]["April Tag"], empty_path, empty_list, apriltag_root_path
        )

        # for each item on the robot's asset path, load it and check if successful by checking if there is an articulation on stage
        clear_stage()
        await omni.kit.app.get_app().next_update_async()
        await omni.kit.app.get_app().next_update_async()
        has_robot = False
        await menu_click(apriltag_menu_list[0], human_delay_speed=10)
        await omni.kit.app.get_app().next_update_async()

        omni.kit.commands.execute("CreateMeshPrimWithDefaultXform", prim_type="Cube", above_ground=True)

        await omni.kit.app.get_app().next_update_async()
        omni.kit.commands.execute(
            "BindMaterial", material_path="/Looks/AprilTag", prim_path=["/Cube"], strength=["weakerThanDescendants"]
        )

        await omni.kit.app.get_app().next_update_async()

    async def test_loading_environment(self):

        self.robot_menu_dict = self.menu_dict["Create"]["Isaac"]["Environments"]
        ## check everything under "Robot"

        environment_root_path = "Create/Isaac/Environments"

        def get_menu_path(d, path, result, root_path):

            for key, value in d.items():
                if key != "_":
                    new_path = path + "/" + str(key)
                if isinstance(value, dict):
                    get_menu_path(value, new_path, result, root_path)
                elif isinstance(value, str):
                    result.append(root_path + path + "/" + str(value))
                elif isinstance(value, list):
                    for environment in value:
                        result.append(root_path + path + "/" + str(environment))
            return result

        empty_list = []
        skip_list = []
        failed_environments = []

        empty_path = ""
        robot_menu_list = get_menu_path(self.robot_menu_dict, empty_path, empty_list, environment_root_path)

        test_list = robot_menu_list

        print(test_list)

        for test_path in test_list:
            print(test_path)
            if test_path in skip_list:
                print("skipping ", test_path)
                continue

            clear_stage()
            await omni.kit.app.get_app().next_update_async()
            await omni.kit.app.get_app().next_update_async()
            has_robot = False
            await menu_click(test_path, human_delay_speed=10)
            for i in range(20):
                await omni.kit.app.get_app().next_update_async()

            # # waiting for stage to load
            while omni.usd.get_context().get_stage_loading_status()[2] > 0:
                await omni.kit.app.get_app().next_update_async()

            # count the numver of prims in the stage
            num_prims = 0
            for prim in traverse_stage():
                num_prims += 1

            if num_prims == 0:
                print(f"failed to find any prims at {test_path}")
                failed_environments.append(test_path)

        print(failed_environments)

        # if failed_environments array has 0 entries, then test passed
        self.assertEqual(len(failed_environments), 0)

    async def test_loading_sensors(self):
        self.robot_menu_dict = self.menu_dict["Create"]["Isaac"]["Sensors"]
        ## check everything under "Sensors"

        sensor_root_path = "Create/Isaac/Sensors"

        def get_menu_path(d, path, result, root_path):

            for key, value in d.items():
                if key != "_":
                    new_path = path + "/" + str(key)
                if isinstance(value, dict):
                    get_menu_path(value, new_path, result, root_path)
                elif isinstance(value, str):
                    result.append(root_path + path + "/" + str(value))
                elif isinstance(value, list):
                    for sensor in value:
                        result.append(root_path + path + "/" + str(sensor))
            return result

        empty_list = []
        skip_list = []
        failed_sensors = []

        empty_path = ""
        robot_menu_list = get_menu_path(self.robot_menu_dict, empty_path, empty_list, sensor_root_path)

        test_list = robot_menu_list

        print(test_list)

        for test_path in test_list:
            print(test_path)
            if test_path in skip_list:
                print("skipping ", test_path)
                continue

            clear_stage()
            await omni.kit.app.get_app().next_update_async()
            await omni.kit.app.get_app().next_update_async()
            has_robot = False
            await menu_click(test_path, human_delay_speed=10)
            for i in range(20):
                await omni.kit.app.get_app().next_update_async()

            # # waiting for stage to load
            while omni.usd.get_context().get_stage_loading_status()[2] > 0:
                await omni.kit.app.get_app().next_update_async()

            num_prims = 0
            # count the number of prims on the stage, shoudl be greater than 1
            for prim in traverse_stage():
                num_prims += 1

            if num_prims == 0:
                print(f"failed to find any prims at {test_path}")
                failed_sensors.append(test_path)

        print(failed_sensors)

        # if failed_sensors array has 0 entries, then test passed
        self.assertEqual(len(failed_sensors), 0)
