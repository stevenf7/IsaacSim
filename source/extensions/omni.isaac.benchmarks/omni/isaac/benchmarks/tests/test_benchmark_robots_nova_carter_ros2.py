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
import omni.graph.core as og
import omni.kit.test
from omni.isaac.benchmark.services.base_isaac_benchmark_async import BaseIsaacBenchmarkAsync
from omni.isaac.core import PhysicsContext
from omni.isaac.core.utils.types import ArticulationAction
from omni.isaac.core.utils.viewports import set_camera_view
from omni.isaac.wheeled_robots.robots import WheeledRobot

# from parameterized import parameterized


TEST_NUM_APP_UPDATES = 60 * 10


class TestBenchmarkRobotsNovaCarterROS2(BaseIsaacBenchmarkAsync):
    async def setUp(self):
        await super().setUp()
        pass

    async def tearDown(self):
        await super().tearDown()
        pass

    # ----------------------------------------------------------------------

    async def benchmark_robots(
        self, n_robot: int = 1, enable_3d_lidar: int = 0, enable_2d_lidar: int = 0, enable_hawks: int = 0
    ):
        """_summary_
        A nova carter robot can accept a maximum of 4 hawks, 2 2d lidars, and 1 3d lidar
        Args:
            n_robot (_type_): _description_
            enable_3d_lidar (int, optional): _description_. Defaults to 0.
            enable_2d_lidar (int, optional): _description_. Defaults to 0.
            enable_hawks (int, optional): _description_. Defaults to 0.
        """
        sensor_name = ""
        if enable_3d_lidar > 0:
            sensor_name += "_3dlidar"
            if enable_3d_lidar > 1:
                carb.log_warn("Warning: Nova Carter only has 1 3D lidar")
                enable_3d_lidar = 1

        if enable_2d_lidar > 0:
            sensor_name += "_2dlidar"
            if enable_2d_lidar > 2:
                carb.log_warn("Warning: Nova Carter only has 2 2D lidar")
                enable_2d_lidar = 2

        if enable_hawks > 0:
            sensor_name += "_hawk"
            if enable_hawks > 4:
                carb.log_warn("Warning: Nova Carter only has 1 3D lidar")
                enable_hawks = 4

        if len(sensor_name) == 0:
            sensor_name = "_no_sensor"

        self.test_run.test_name = f"robots_nova_carter_ros2{sensor_name}_{n_robot}"
        self.set_phase("loading")
        self.start_runtime()

        robot_path = "/Isaac/Samples/ROS2/Robots/Nova_Carter_ROS.usd"
        scene_path = "/Isaac/Environments/Simple_Warehouse/full_warehouse.usd"
        await self.fully_load_stage(self.assets_root_path + scene_path)
        stage = omni.usd.get_context().get_stage()
        PhysicsContext(physics_dt=1.0 / 60.0)
        set_camera_view(eye=[-6, -15.5, 6.5], target=[-6, 10.5, -1], camera_prim_path="/OmniverseKit_Persp")

        lidars_2d = ["/front_2d_lidar_render_product", "/back_2d_lidar_render_product"]
        hawk_actiongraphs = ["/front_hawk", "/left_hawk", "/right_hawk", "/back_hawk"]

        robots = []
        for i in range(n_robot):
            robot_prim_path = "/Robots/Robot_" + str(i)
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

            await omni.kit.app.get_app().next_update_async()
            await omni.kit.app.get_app().next_update_async()

            for i in range(len(lidars_2d)):
                if i < enable_2d_lidar:
                    og.Controller.attribute(robot_prim_path + "/ros_lidars" + lidars_2d[i] + ".inputs:enabled").set(
                        True
                    )
                else:
                    og.Controller.attribute(robot_prim_path + "/ros_lidars" + lidars_2d[i] + ".inputs:enabled").set(
                        False
                    )

            if enable_3d_lidar > 0:
                og.Controller.attribute(
                    robot_prim_path + "/ros_lidars/front_3d_lidar_render_product.inputs:enabled"
                ).set(True)
            else:
                og.Controller.attribute(
                    robot_prim_path + "/ros_lidars/front_3d_lidar_render_product.inputs:enabled"
                ).set(False)

            for i in range(len(hawk_actiongraphs)):
                if i < enable_hawks:
                    og.Controller.attribute(
                        robot_prim_path + hawk_actiongraphs[i] + "/left_camera_render_product" + ".inputs:enabled"
                    ).set(True)
                    og.Controller.attribute(
                        robot_prim_path + hawk_actiongraphs[i] + "/right_camera_render_product" + ".inputs:enabled"
                    ).set(True)
                else:
                    og.Controller.attribute(
                        robot_prim_path + hawk_actiongraphs[i] + "/left_camera_render_product" + ".inputs:enabled"
                    ).set(False)
                    og.Controller.attribute(
                        robot_prim_path + hawk_actiongraphs[i] + "/right_camera_render_product" + ".inputs:enabled"
                    ).set(False)

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

    async def test_benchmark_1_robot_nova_carter_ros2(self):
        await self.benchmark_robots(1)

    async def test_benchmark_1_robot_nova_carter_ros2_3d_lidar(self):
        await self.benchmark_robots(1, enable_3d_lidar=1)

    async def test_benchmark_1_robot_nova_carter_ros2_1_2d_lidar(self):
        await self.benchmark_robots(1, enable_2d_lidar=1)

    async def test_benchmark_1_robot_nova_carter_ros2_1_3d_lidar_2_2d_lidar(self):
        await self.benchmark_robots(1, enable_3d_lidar=1, enable_2d_lidar=2)

    async def test_benchmark_1_robot_nova_carter_ros2_1_hawk(self):
        await self.benchmark_robots(1, enable_hawks=1)

    async def test_benchmark_1_robot_nova_carter_ros2_2_hawk(self):
        await self.benchmark_robots(1, enable_hawks=2)

    async def test_benchmark_1_robot_nova_carter_ros2_4_hawk(self):
        await self.benchmark_robots(1, enable_hawks=4)

    async def test_benchmark_1_robot_nova_carter_ros2_1_hawk_1_3d_lidar(self):
        await self.benchmark_robots(1, enable_hawks=1, enable_3d_lidar=1)

    async def test_benchmark_1_robot_nova_carter_ros2_4_hawk_1_3d_lidar_2_2d_lidar(self):
        await self.benchmark_robots(1, enable_hawks=4, enable_3d_lidar=1, enable_2d_lidar=2)

    async def test_benchmark_3_robot_nova_carter_ros2(self):
        await self.benchmark_robots(3)

    async def test_benchmark_3_robot_nova_carter_ros2_1_hawk_1_3d_lidar(self):
        await self.benchmark_robots(3, enable_hawks=1, enable_3d_lidar=1)

    async def test_benchmark_3_robot_nova_carter_ros2_4_hawk_1_3d_lidar_2_2d_lidar(self):
        await self.benchmark_robots(3, enable_hawks=4, enable_3d_lidar=1, enable_2d_lidar=2)
