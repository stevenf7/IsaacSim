# Copyright (c) 2018-2024, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

import carb
import numpy as np
import omni.kit.test
from omni.isaac.benchmark.services.base_isaac_benchmark import BaseIsaacBenchmark
from omni.isaac.core import PhysicsContext
from omni.isaac.core.utils.types import ArticulationAction
from omni.isaac.core.utils.viewports import set_camera_view
from omni.isaac.wheeled_robots.robots import WheeledRobot

# from parameterized import parameterized


TEST_NUM_APP_UPDATES = 60 * 10


class TestBenchmarkRobotsNovaCarter(BaseIsaacBenchmark):
    async def setUp(self):
        await super().setUp()
        pass

    async def tearDown(self):
        await super().tearDown()
        pass

    # ----------------------------------------------------------------------

    async def benchmark_robots(self, n_robot: int = 1):
        """_summary_
        Benchmark the physics of just the nova carter robot without the rendering pipelines and omnigraph nodes
        Args:
            n_robot (_type_): _description_
        """

        self.test_run.test_name = f"robots_nova_carter_{n_robot}"
        self.set_phase("loading")
        self.start_runtime()

        robot_path = "/Isaac/Robots/Carter/nova_carter_sensors.usd"
        scene_path = "/Isaac/Environments/Simple_Warehouse/full_warehouse.usd"
        await self.fully_load_stage(self.assets_root_path + scene_path)
        stage = omni.usd.get_context().get_stage()
        PhysicsContext(physics_dt=1.0 / 60.0)
        set_camera_view(eye=[-6, -15.5, 6.5], target=[-6, 10.5, -1], camera_prim_path="/OmniverseKit_Persp")

        robots = []
        for i in range(n_robot):
            robot_prim_path = "/Robots/Robot_" + str(i)
            robot_usd_path = self.assets_root_path + robot_path
            # position the robot
            MAX_IN_LINE = 10
            robot_position = np.array([-2 * (i % MAX_IN_LINE), -2 * np.floor(i / MAX_IN_LINE), 0])
            current_robot = WheeledRobot(
                prim_path=robot_prim_path,
                wheel_dof_names=["joint_wheel_left", "joint_wheel_right"],
                create_robot=True,
                usd_path=robot_usd_path,
                position=robot_position,
            )

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

    async def test_benchmark_1_robot_nova_carter(self):
        await self.benchmark_robots(1)

    async def test_benchmark_3_robot_nova_carter(self):
        await self.benchmark_robots(3)

    async def test_benchmark_5_robot_nova_carter(self):
        await self.benchmark_robots(5)

    async def test_benchmark_10_robot_nova_carter(self):
        await self.benchmark_robots(10)
