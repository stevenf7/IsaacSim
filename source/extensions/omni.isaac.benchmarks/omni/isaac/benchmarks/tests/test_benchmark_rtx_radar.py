# Copyright (c) 2023, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

import omni.kit.test
import omni.replicator.core as rep
from omni.isaac.core.utils.prims import delete_prim
from omni.isaac.core.utils.render_product import create_hydra_texture
from pxr import Gf

from ..utils.base_isaac_benchmark import BaseIsaacBenchmark

# TODOMTC - Radar appears to not allow allow multiple, but the transoform for each one is the same.
#           and the results only appear to last for the first few frames.
TEST_NUM_APP_UPDATES = 60 * 10


class TestBenchmarkRtxRadar(BaseIsaacBenchmark):
    async def setUp(self):
        await super().setUp()
        pass

    async def tearDown(self):
        await super().tearDown()
        pass

    # ----------------------------------------------------------------------
    async def benchmark_rtx_radar(self, n_sensor):
        self.test_run.test_name = f"rtx_radar_{n_sensor}"
        self.set_phase("loading")
        self.start_runtime()
        scene_path = "/Isaac/Environments/Simple_Warehouse/full_warehouse.usd"
        await self.fully_load_stage(self.assets_root_path + scene_path)
        timeline = omni.timeline.get_timeline_interface()
        hydra_textures = []
        writers = []
        sensors = []
        for i in range(n_sensor):
            radar_path = "/World/RtxRadar_" + str(i)
            sensor_translation = Gf.Vec3f(
                [-0.937, -2.0 + i * 2.0, 0.8940]
            )  # these positions are used for full_warehouse.usd

            _, sensor = omni.kit.commands.execute(
                "IsaacSensorCreateRtxRadar",
                path=radar_path,
                parent=None,
                config="Example",
                translation=sensor_translation,
                orientation=Gf.Quatd(0.6283473, 0.6283473, -0.3243142, -0.3243142),  # Gf.Quatd is w,i,j,k
            )
            sensors.append(sensor)
            texture, render_product_path = create_hydra_texture([1, 1], sensor.GetPath().pathString)
            hydra_textures.append(texture)
            # Create the post process graph that publishes the render var
            writer = rep.writers.get("Writer" + "IsaacPrintRTXRadarInfo")
            writer.initialize(testMode=True)
            writer.attach([render_product_path])
            writers.append(writer)

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
        for writer in writers:
            writer.detach()
        await omni.kit.app.get_app().next_update_async()

        for sensor in sensors:
            delete_prim(sensor.GetPath())
        await omni.kit.app.get_app().next_update_async()

        for texture in hydra_textures:
            texture = None
        await omni.kit.app.get_app().next_update_async()

    async def test_benchmark_1_rtx_radar(self):
        await self.benchmark_rtx_radar(1)

    async def test_benchmark_2_rtx_radar(self):
        await self.benchmark_rtx_radar(2)

    async def test_benchmark_4_rtx_radar(self):
        await self.benchmark_rtx_radar(4)

    async def test_benchmark_8_rtx_radar(self):
        await self.benchmark_rtx_radar(8)
