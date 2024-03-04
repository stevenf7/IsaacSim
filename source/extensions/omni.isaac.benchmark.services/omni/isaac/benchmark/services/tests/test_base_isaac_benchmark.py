# Copyright (c) 2024, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
from omni.isaac.benchmark.services.base_isaac_benchmark_async import BaseIsaacBenchmarkAsync


class TestBaseIsaacBenchmarkAsync(BaseIsaacBenchmarkAsync):
    async def setUp(self):
        await super().setUp()
        pass

    async def tearDown(self):
        await super().tearDown()
        pass

    async def test_base_isaac_benchmark(self):

        self.set_phase("loading")
        await self.store_measurements()
