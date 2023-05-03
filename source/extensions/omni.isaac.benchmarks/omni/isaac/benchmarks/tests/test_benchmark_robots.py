# Copyright (c) 2018-2022, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#


import asyncio

import carb
import numpy as np
import omni.kit.test
import yaml
from omni.isaac.core.utils.nucleus import get_assets_root_path
from omni.isaac.core.utils.stage import open_stage_async
from omni.isaac.core.utils.types import ArticulationAction
from omni.isaac.core.utils.viewports import destroy_all_viewports, get_viewport_names, set_camera_view
from omni.isaac.core.utils.render_product import create_hydra_texture, set_camera_prim_path, set_resolution
from omni.isaac.wheeled_robots.robots import WheeledRobot
from omni.kit.viewport.utility import (
    create_viewport_window,
    get_active_viewport,
    get_active_viewport_and_window,
    get_num_viewports,
    get_viewport_from_window_name,
)
from omni.kit.widget.viewport.capture import FileCapture

from ..utils.base_isaac_benchmark import BaseIsaacBenchmark
from ..utils.helper import delete_prim_and_children
from ..utils.logger import get_memory_stats, log_header

TEST_NUM_APP_UPDATES = 60 * 10


class TestBenchmarkRobots(BaseIsaacBenchmark):
    async def setUp(self):
        await super().setUp()
        pass

    async def tearDown(self):
        await super().tearDown()
        pass

    # ----------------------------------------------------------------------
    async def benchmark_robots(
        self, n_robot, enable_lidar: bool = False, enable_camera: bool = False, camera_resolution=[1280, 720]
    ):
        self.test_run.test_name = f"{n_robot}_robots_no_sensor"
        self.set_phase("loading")
        self.start_collecting_frametime()
        robot_path = "/Isaac/Robots/Carter/carter_v2.usd"
        scene_path = "/Isaac/Environments/Simple_Warehouse/full_warehouse.usd"
        await self.fully_load_stage(self.assets_root_path + scene_path)
        stage = omni.usd.get_context().get_stage()

        set_camera_view(eye=[-6, -15.5, 6.5], target=[-6, 10.5, -1], camera_prim_path="/OmniverseKit_Persp")
        robots = []
        for i in range(n_robot):
            robot_prim_path = "/Robots/Robot_" + str(i)
            robot_camera_prim_path = (
                robot_prim_path + "/chassis_link/stereo_cam_right/stereo_cam_right_sensor_frame/camera_sensor_right"
            )
            robot_usd_path = self.assets_root_path + robot_path
            # position the robot robot
            robot_position = np.array([-2 * i, 0, 0])
            current_robot = WheeledRobot(
                prim_path=robot_prim_path,
                wheel_dof_names=["joint_wheel_left", "joint_wheel_right"],
                create_robot=True,
                usd_path=robot_usd_path,
                position=robot_position,
            )
            # disable lidar sensors
            lidar_prim_path = robot_prim_path + "/chassis_link/carter_lidar"
            lidar_prim = stage.GetPrimAtPath(lidar_prim_path)
            if enable_lidar:
                lidar_prim.GetAttribute("enabled").Set(True)
            else:
                lidar_prim.GetAttribute("enabled").Set(False)

            if enable_camera:
                texture, texture_path = create_hydra_texture(camera_resolution, robot_camera_prim_path)
            else:
                viewport_api, active_window = get_active_viewport_and_window()
                viewport_api.set_texture_resolution([1280, 720])
            await omni.kit.app.get_app().next_update_async()
            await omni.kit.app.get_app().next_update_async()

            robots.append(current_robot)

        timeline = omni.timeline.get_timeline_interface()
        timeline.play()
        await omni.kit.app.get_app().next_update_async()

        for robot in robots:
            robot.initialize()
            # start the robot rotating in place so not to run into each
            robot.apply_wheel_actions(
                ArticulationAction(joint_positions=None, joint_efforts=None, joint_velocities=5 * np.array([0, 1]))
            )

        await omni.kit.app.get_app().next_update_async()
        await omni.kit.app.get_app().next_update_async()

        self.stop_collecting_frametime()
        await self.store_measurements()

        # perform benchmark
        self.set_phase("benchmark")
        self.start_collecting_frametime()

        while self.get_num_frames() < TEST_NUM_APP_UPDATES:
            await omni.kit.app.get_app().next_update_async()

        self.stop_collecting_frametime()
        await self.store_measurements()

        timeline.stop()

    async def test_benchmark_1_robot(self):
        await self.benchmark_robots(1)

    async def test_benchmark_5_robot(self):
        await self.benchmark_robots(5)

    # async def test_benchmark_10_robot(self):
    #     await self.benchmark_robots(10)

    # async def test_benchmark_50_robot(self):
    #     await self.benchmark_robots(50)

    async def test_benchmark_1_robot_lidar(self):
        await self.benchmark_robots(1, True)

    async def test_benchmark_5_robot_lidar(self):
        await self.benchmark_robots(5, True)

    async def test_benchmark_10_robot_lidar(self):
        await self.benchmark_robots(10, True)

    async def test_benchmark_1_robot_camera(self):
        await self.benchmark_robots(1, False, True)

    async def test_benchmark_5_robot_camera(self):
        await self.benchmark_robots(5, False, True)

    # async def test_benchmark_10_robot_camera(self):
    #     await self.benchmark_robots(10, False, True)

    async def test_benchmark_1_robot_lidar_camera(self):
        await self.benchmark_robots(1, True, True)

    async def test_benchmark_5_robot_lidar_camera(self):
        await self.benchmark_robots(5, True, True)

    # async def test_benchmark_10_robot_lidar_camera(self):
    #     await self.benchmark_robots(10, True, True)
