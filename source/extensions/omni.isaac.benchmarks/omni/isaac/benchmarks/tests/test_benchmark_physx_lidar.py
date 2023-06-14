# Copyright (c) 2018-2023, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#


import omni.kit.test
from omni.isaac.core.utils.rotations import euler_angles_to_quat
from omni.isaac.core.utils.viewports import destroy_all_viewports
from pxr import Gf

from ..utils.base_isaac_benchmark import BaseIsaacBenchmark
from ..utils.helper import add_physx_lidar

TEST_NUM_APP_UPDATES = 60 * 10


class TestBenchmarkLidar(BaseIsaacBenchmark):
    async def setUp(self):
        await super().setUp()
        pass

    async def tearDown(self):
        await super().tearDown()
        pass

    # ----------------------------------------------------------------------
    async def benchmark_physx_lidar(self, n_sensor):
        self.test_run.test_name = f"{n_sensor}_physx_lidars"
        self.set_phase("loading")
        self.start_collecting_frametime()
        scene_path = "/Isaac/Environments/Simple_Warehouse/full_warehouse.usd"
        await self.fully_load_stage(self.assets_root_path + scene_path)
        stage = omni.usd.get_context().get_stage()

        timeline = omni.timeline.get_timeline_interface()
        timeline.play()

        await omni.kit.app.get_app().next_update_async()

        timeline = omni.timeline.get_timeline_interface()
        timeline.play()
        for i in range(n_sensor):

            # add a sensor on stage
            sensor_path = "/World/Lidar_" + str(i)
            sensor_translation = Gf.Vec3f([-8, 13, 2.0])  # these positions are used for full_warehouse.usd
            q = euler_angles_to_quat([90, 0, 90 + i * 360 / n_sensor], degrees=True)
            sensor_orientation = Gf.Quatf(q[0], q[1], q[2], q[3])
            add_physx_lidar(prim_path=sensor_path, translation=sensor_translation, orientation=sensor_orientation)

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

    async def test_benchmark_1_physx_lidar(self):
        await self.benchmark_physx_lidar(1)

    async def test_benchmark_5_physx_lidar(self):
        await self.benchmark_physx_lidar(5)

    async def test_benchmark_10_physx_lidar(self):
        await self.benchmark_physx_lidar(10)

    async def test_benchmark_50_physx_lidar(self):
        await self.benchmark_physx_lidar(50)
