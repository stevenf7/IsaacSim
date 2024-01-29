# Copyright (c) 2023-2024, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

import omni.kit.test
from omni.isaac.benchmark.services.base_isaac_benchmark_async import BaseIsaacBenchmarkAsync
from omni.isaac.core_nodes.bindings import _omni_isaac_core_nodes

TEST_NUM_APP_UPDATES = 60 * 10


class TestBenchmarkRealTimeFactor(BaseIsaacBenchmarkAsync):
    async def setUp(self):
        await super().setUp()
        self._core_nodes = _omni_isaac_core_nodes.acquire_interface()
        pass

    async def tearDown(self):
        await super().tearDown()
        pass

    # ----------------------------------------------------------------------
    async def benchmark_real_time_factor(self):
        self.test_run.test_name = "real_time_factor"
        self.set_phase("loading")
        self.start_runtime()

        scene_path = "/Isaac/Environments/Simple_Warehouse/full_warehouse.usd"
        await self.fully_load_stage(self.assets_root_path + scene_path)
        timeline = omni.timeline.get_timeline_interface()

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

    async def test_benchmark_real_time_factor(self):
        await self.benchmark_real_time_factor()
