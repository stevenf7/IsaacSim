# Copyright (c) 2018-2023, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

import numpy as np
import omni.kit.test
from omni.isaac.core import PhysicsContext
from omni.isaac.core.utils.types import ArticulationAction
from omni.isaac.core.utils.viewports import set_camera_view
from omni.isaac.sensor import Camera
from omni.isaac.wheeled_robots.robots import WheeledRobot
from omni.kit.viewport.utility import get_active_viewport

from ..utils.base_isaac_benchmark import BaseIsaacBenchmark

# from parameterized import parameterized


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
        sensor_name = ""
        if enable_lidar:
            sensor_name += "_lidar"
        if enable_camera:
            sensor_name += "_camera"
        if len(sensor_name) == 0:
            sensor_name = "_no_sensor"

        self.test_run.test_name = f"{n_robot}_robots{sensor_name}"
        self.set_phase("loading")
        self.start_runtime()

        robot_path = "/Isaac/Robots/Carter/carter_v2.usd"
        scene_path = "/Isaac/Environments/Simple_Warehouse/full_warehouse.usd"
        await self.fully_load_stage(self.assets_root_path + scene_path)
        stage = omni.usd.get_context().get_stage()
        PhysicsContext(physics_dt=1.0 / 60.0)
        set_camera_view(eye=[-6, -15.5, 6.5], target=[-6, 10.5, -1], camera_prim_path="/OmniverseKit_Persp")
        robots = []
        cameras = []
        for i in range(n_robot):
            robot_prim_path = "/Robots/Robot_" + str(i)
            robot_camera_prim_path = (
                robot_prim_path + "/chassis_link/stereo_cam_right/stereo_cam_right_sensor_frame/camera_sensor_right"
            )
            robot_usd_path = self.assets_root_path + robot_path
            # position the robot robot
            MAX_IN_LINE = 10
            robot_position = np.array([-2 * (i % MAX_IN_LINE), -2 * np.floor(i / MAX_IN_LINE), 0])
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
                render_product_path = None
                if i == 0:
                    viewport_api = get_active_viewport()
                    render_product_path = viewport_api.get_render_product_path()
                cameras.append(
                    Camera(
                        prim_path=robot_camera_prim_path,
                        resolution=[1280, 720],
                        render_product_path=render_product_path,
                    )
                )
                await omni.kit.app.get_app().next_update_async()
                cameras[i].initialize()
            else:
                viewport_api = get_active_viewport()
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

        self.stop_runtime()
        await self.store_measurements()

        # perform benchmark
        self.set_phase("benchmark")
        self.start_collecting_frametime()

        for _ in range(1 if self.test_mode else TEST_NUM_APP_UPDATES):
            await omni.kit.app.get_app().next_update_async()

        self.stop_collecting_frametime()
        await self.store_measurements()

        timeline.stop()

    # ROBOT_NO_SENSOR_TESTS = range(1, 51)
    # ROBOT_NO_SENSOR_TESTS = [1, 5, 10, 25, 50]
    # using parameterized.expand requires parameterized version 0.9.0 or higher, current version in kit is 0.8.1 (_build/linux-x86_64/release/extscache/omni.kit.testing.services-1.6.28/pip_prebundle/parameterized/__init__.py)
    # @parameterized.expand([("with " + str(x) + " robots", x) for x in ROBOT_NO_SENSOR_TESTS])
    # @parameterized.expand([("with " + str(x) + " robots", x) for x in ROBOT_NO_SENSOR_TESTS])
    # async def test_benchmark(self, name, n):
    #     await self.benchmark_robots(n)

    # ROBOT_LIDAR_TESTS = [1, 5, 10]
    # @parameterized.expand([("with " + str(x) + " robots", x) for x in ROBOT_LIDAR_TESTS])
    # async def test_benchmark_lidar(self, name, n):
    #     await self.benchmark_robots(n, True)

    # ROBOT_CAMERA_TESTS = [1, 5, 10]
    # @parameterized.expand([("with " + str(x) + " robots", x) for x in ROBOT_CAMERA_TESTS])
    # async def test_benchmark_camera(self, name, n):
    #     await self.benchmark_robots(n, False, True)

    # ROBOT_LIDAR_CAMERA_TESTS = [1, 5, 10]
    # @parameterized.expand([("with " + str(x) + " robots", x) for x in ROBOT_LIDAR_CAMERA_TESTS])
    # async def test_benchmark_lidar_camera(self, name, n):
    #     await self.benchmark_robots(n, True, True)

    async def test_benchmark_1_robot(self):
        await self.benchmark_robots(1)

    async def test_benchmark_5_robot(self):
        await self.benchmark_robots(5)

    async def test_benchmark_10_robot(self):
        await self.benchmark_robots(10)

    async def test_benchmark_25_robot(self):
        await self.benchmark_robots(25)

    async def test_benchmark_50_robot(self):
        await self.benchmark_robots(50)

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

    async def test_benchmark_10_robot_camera(self):
        await self.benchmark_robots(10, False, True)

    async def test_benchmark_1_robot_lidar_camera(self):
        await self.benchmark_robots(1, True, True)

    async def test_benchmark_5_robot_lidar_camera(self):
        await self.benchmark_robots(5, True, True)

    async def test_benchmark_10_robot_lidar_camera(self):
        await self.benchmark_robots(10, True, True)
