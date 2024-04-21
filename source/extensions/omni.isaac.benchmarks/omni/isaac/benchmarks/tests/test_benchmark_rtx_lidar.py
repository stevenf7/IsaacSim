# Copyright (c) 2023-2024, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

import omni.kit.test
import omni.replicator.core as rep
from omni.isaac.benchmark.services.base_isaac_benchmark_async import BaseIsaacBenchmarkAsync
from omni.isaac.core.utils.prims import delete_prim
from pxr import Gf

TEST_NUM_APP_UPDATES = 60 * 10


class TestBenchmarkRtxLidar(BaseIsaacBenchmarkAsync):
    async def setUp(self):
        await super().setUp()
        pass

    async def tearDown(self):
        await super().tearDown()
        pass

    # ----------------------------------------------------------------------
    async def benchmark_rtx_lidar(self, n_sensor):
        self.benchmark_name = f"rtx_lidar_{n_sensor}"
        self.set_phase("loading")
        scene_path = "/Isaac/Environments/Simple_Warehouse/full_warehouse.usd"
        await self.fully_load_stage(self.assets_root_path + scene_path)
        timeline = omni.timeline.get_timeline_interface()
        hydra_textures = []
        writers = []
        sensors = []
        for i in range(n_sensor):
            lidar_type = "Rotary"
            if i % 2:
                lidar_type = "Solid_State"
            lidar_path = "/World/Rtx" + lidar_type + "Lidar_" + str(i)
            sensor_translation = Gf.Vec3f([-8, 13 + i * 2.0, 2.0])  # these positions are used for full_warehouse.usd
            # make sure to test rotary and solid state together.
            lidar_config = "Example_" + lidar_type

            _, sensor = omni.kit.commands.execute(
                "IsaacSensorCreateRtxLidar",
                path=lidar_path,
                parent=None,
                config=lidar_config,
                translation=sensor_translation,
                orientation=Gf.Quatd(1.0, 0.0, 0.0, 0.0),  # Gf.Quatd is w,i,j,k
            )
            sensors.append(sensor)
            hydra_texture = rep.create.render_product(sensor.GetPath(), [1, 1], name="Isaac")
            hydra_textures.append(hydra_texture)
            # Create the post process graph that publishes the render var
            writer = rep.writers.get("Writer" + "IsaacPrintRTXLidarInfo")
            writer.initialize(testMode=True)
            writer.attach([hydra_texture])
            writers.append(writer)

            await omni.kit.app.get_app().next_update_async()

        await self.store_measurements()

        self.set_phase("benchmark")
        timeline.play()

        for _ in range(1 if self.test_mode else TEST_NUM_APP_UPDATES):
            await omni.kit.app.get_app().next_update_async()

        await self.store_measurements()

        timeline.stop()

        for writer in writers:
            writer.detach()
        await omni.kit.app.get_app().next_update_async()

        for sensor in sensors:
            delete_prim(sensor.GetPath())
        await omni.kit.app.get_app().next_update_async()

        for texture in hydra_textures:
            texture.destroy()
            texture = None
        hydra_textures.clear()
        await omni.kit.app.get_app().next_update_async()

    async def test_benchmark_1_rtx_lidar(self):
        await self.benchmark_rtx_lidar(1)

    async def test_benchmark_2_rtx_lidar(self):
        await self.benchmark_rtx_lidar(2)

    async def test_benchmark_4_rtx_lidar(self):
        await self.benchmark_rtx_lidar(4)

    async def test_benchmark_8_rtx_lidar(self):
        await self.benchmark_rtx_lidar(8)
