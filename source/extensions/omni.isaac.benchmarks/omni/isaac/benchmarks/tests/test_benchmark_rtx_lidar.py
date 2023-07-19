# Copyright (c) 2023, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

import omni.kit.test
from omni.isaac.core.utils.render_product import create_hydra_texture
from omni.syntheticdata import sensors
from pxr import Gf

from ..utils.base_isaac_benchmark import BaseIsaacBenchmark

TEST_NUM_APP_UPDATES = 60 * 10


class TestBenchmarkRtxLidar(BaseIsaacBenchmark):
    async def setUp(self):
        await super().setUp()
        pass

    async def tearDown(self):
        await super().tearDown()
        pass

    # ----------------------------------------------------------------------
    async def benchmark_rtx_lidar(self, n_sensor):
        self.test_run.test_name = f"rtx_lidar_{n_sensor}"
        self.set_phase("loading")
        self.start_runtime()
        scene_path = "/Isaac/Environments/Simple_Warehouse/full_warehouse.usd"
        await self.fully_load_stage(self.assets_root_path + scene_path)
        timeline = omni.timeline.get_timeline_interface()
        hydra_textures = []
        for i in range(n_sensor):
            lidar_path = "/World/RtxLidar_" + str(i)
            sensor_translation = Gf.Vec3f([-8, 13 + i * 2.0, 2.0])  # these positions are used for full_warehouse.usd

            _, sensor = omni.kit.commands.execute(
                "IsaacSensorCreateRtxLidar",
                path=lidar_path,
                parent=None,
                config="Example_Rotary",
                translation=sensor_translation,
                orientation=Gf.Quatd(0.5, 0.5, -0.5, -0.5),  # Gf.Quatd is w,i,j,k
            )

            texture, render_product_path = create_hydra_texture([1, 1], sensor.GetPath().pathString)
            hydra_textures.append(texture)
            # Create the post process graph that publishes the render var
            sensors.get_synthetic_data().activate_node_template(
                "Test" + "IsaacPrintRTXLidarInfo", 0, [render_product_path]
            )

            await omni.kit.app.get_app().next_update_async()

        self.stop_runtime()
        await self.store_measurements()

        self.set_phase("benchmark")
        timeline.play()
        self.start_collecting_frametime()

        for _ in range(1 if self.test_mode else TEST_NUM_APP_UPDATES):
            await omni.kit.app.get_app().next_update_async()

        self.stop_collecting_frametime()
        await self.store_measurements()

        timeline.stop()
        hydra_textures = None

    async def test_benchmark_1_rtx_lidar(self):
        await self.benchmark_rtx_lidar(1)

    async def test_benchmark_2_rtx_lidar(self):
        await self.benchmark_rtx_lidar(2)

    async def test_benchmark_4_rtx_lidar(self):
        await self.benchmark_rtx_lidar(4)

    async def test_benchmark_8_rtx_lidar(self):
        await self.benchmark_rtx_lidar(8)
