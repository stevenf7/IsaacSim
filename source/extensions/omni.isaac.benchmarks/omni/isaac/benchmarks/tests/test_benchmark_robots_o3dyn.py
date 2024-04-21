# Copyright (c) 2018-2024, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

import numpy as np
import omni.kit.test
from omni.isaac.benchmark.services.base_isaac_benchmark_async import BaseIsaacBenchmarkAsync
from omni.isaac.core import PhysicsContext
from omni.isaac.core.utils.types import ArticulationAction
from omni.isaac.core.utils.viewports import set_camera_view
from omni.isaac.wheeled_robots.robots import WheeledRobot
from omni.kit.viewport.utility import get_active_viewport

TEST_NUM_APP_UPDATES = 60 * 10


class TestBenchmarkRobotsO3dyn(BaseIsaacBenchmarkAsync):
    async def setUp(self):
        await super().setUp()
        pass

    async def tearDown(self):
        await super().tearDown()
        pass

    # ----------------------------------------------------------------------
    async def benchmark_robots(self, n_robot, enable_lidar: bool = False):
        sensor_name = ""
        # if enable_lidar:
        #     sensor_name += "_lidar"
        if len(sensor_name) == 0:
            sensor_name = "_no_sensor"
        self.benchmark_name = f"robots_o3dyn{sensor_name}_{n_robot}"
        self.set_phase("loading")

        robot_path = "/Isaac/Robots/O3dyn/o3dyn.usd"
        scene_path = "/Isaac/Environments/Simple_Warehouse/full_warehouse.usd"
        await self.fully_load_stage(self.assets_root_path + scene_path)
        PhysicsContext(physics_dt=1.0 / 60.0)
        set_camera_view(eye=[-6, -15.5, 6.5], target=[-6, 10.5, -1], camera_prim_path="/OmniverseKit_Persp")
        robots = []
        for i in range(n_robot):
            robot_prim_path = "/Robots/Robot_" + str(i)
            robot_usd_path = self.assets_root_path + robot_path
            # position the robot robot
            MAX_IN_LINE = 10
            robot_position = np.array([-3 * (i % MAX_IN_LINE) + 3, -3 * np.floor(i / MAX_IN_LINE), 0.1])
            current_robot = WheeledRobot(
                prim_path=robot_prim_path,
                wheel_dof_names=["wheel_fl_joint", "wheel_fr_joint", "wheel_rl_joint", "wheel_rr_joint"],
                create_robot=True,
                usd_path=robot_usd_path,
                position=robot_position,
            )

            # disable lidar sensors
            # lidar_prim_path = robot_prim_path + "/chassis_link/carter_lidar"
            # lidar_prim = stage.GetPrimAtPath(lidar_prim_path)
            # if enable_lidar:
            #     lidar_prim.GetAttribute("enabled").Set(True)
            # else:
            #     lidar_prim.GetAttribute("enabled").Set(False)

            await omni.kit.app.get_app().next_update_async()
            robots.append(current_robot)

        viewport_api = get_active_viewport()
        viewport_api.set_texture_resolution([1280, 720])

        await omni.kit.app.get_app().next_update_async()
        await omni.kit.app.get_app().next_update_async()

        timeline = omni.timeline.get_timeline_interface()
        timeline.play()
        await omni.kit.app.get_app().next_update_async()

        for robot in robots:
            robot.initialize()
            # start the robot rotating in place so not to run into each

            robot.apply_wheel_actions(
                ArticulationAction(
                    joint_positions=None, joint_efforts=None, joint_velocities=5 * np.array([1, -1, 1, -1])
                )
            )

        await omni.kit.app.get_app().next_update_async()
        await omni.kit.app.get_app().next_update_async()

        await self.store_measurements()

        # perform benchmark
        self.set_phase("benchmark")

        for _ in range(1 if self.test_mode else TEST_NUM_APP_UPDATES):
            await omni.kit.app.get_app().next_update_async()

        await self.store_measurements()

        timeline.stop()

    # ROBOT_NO_SENSOR_TESTS = range(1, 51)
    # ROBOT_NO_SENSOR_TESTS = [1, 5, 10, 25, 50]
    # using parameterized.expand requires parameterized version 0.9.0 or higher, current version in kit is 0.8.1
    # @parameterized.expand([("with " + str(x) + " robots", x) for x in ROBOT_NO_SENSOR_TESTS])
    # @parameterized.expand([("with " + str(x) + " robots", x) for x in ROBOT_NO_SENSOR_TESTS])
    # async def test_benchmark(self, name, n):
    #     await self.benchmark_robots(n)

    # ROBOT_LIDAR_TESTS = [1, 5, 10]
    # @parameterized.expand([("with " + str(x) + " robots", x) for x in ROBOT_LIDAR_TESTS])
    # async def test_benchmark_lidar(self, name, n):
    #     await self.benchmark_robots(n, True)

    async def test_benchmark_1_robot_o3dyn(self):
        await self.benchmark_robots(1)

    async def test_benchmark_5_robot_o3dyn(self):
        await self.benchmark_robots(5)

    async def test_benchmark_10_robot_o3dyn(self):
        await self.benchmark_robots(10)

    async def test_benchmark_25_robot_o3dyn(self):
        await self.benchmark_robots(25)

    async def test_benchmark_50_robot_o3dyn(self):
        await self.benchmark_robots(50)
