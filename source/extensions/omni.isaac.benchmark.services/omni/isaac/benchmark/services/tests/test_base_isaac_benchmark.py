# Copyright (c) 2024, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
import omni
from omni.isaac.benchmark.services import BaseIsaacBenchmarkAsync
from omni.isaac.core import SimulationContext


class TestBaseIsaacBenchmarkAsync(BaseIsaacBenchmarkAsync):
    async def setUp(self):
        await super().setUp(backend_type="LocalLogMetrics")
        pass

    async def tearDown(self):
        await super().tearDown()
        pass

    async def test_base_isaac_benchmark(self):
        self.benchmark_name = "test_base_isaac_benchmark"
        self.set_phase("loading", False, True)
        await omni.kit.app.get_app().next_update_async()
        await omni.kit.app.get_app().next_update_async()
        simulation_context = SimulationContext()
        await simulation_context.initialize_simulation_context_async()
        await self.store_measurements()
        simulation_context.play()

        self.set_phase("benchmark")
        for frame in range(10):
            await omni.kit.app.get_app().next_update_async()
        await self.store_measurements()
