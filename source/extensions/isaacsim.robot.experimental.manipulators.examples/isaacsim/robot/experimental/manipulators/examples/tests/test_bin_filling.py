# SPDX-FileCopyrightText: Copyright (c) 2018-2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import annotations

import isaacsim.core.experimental.utils.app as app_utils
import omni.kit.test
from isaacsim.robot.experimental.manipulators.examples.interactive.bin_filling import BinFilling


class TestBinFillingExampleExtension(omni.kit.test.AsyncTestCase):
    """Test suite for the bin filling interactive example."""

    async def setUp(self):
        """Set up test environment before each test."""
        self._sample = BinFilling()
        await self._sample.load_world_async()
        await app_utils.update_app_async()

    async def tearDown(self):
        """Clean up after each test."""
        if app_utils.is_playing():
            app_utils.stop()
        await self._sample.clear_async()
        await app_utils.update_app_async()
        self._sample = None

    async def test_bin_filling_task(self):
        """Test bin filling simulation runs and robot operates correctly."""
        await self._sample.reset_async()
        await app_utils.update_app_async()

        self.assertIsNotNone(self._sample._robot)
        self.assertIsNotNone(self._sample._bin_prim)

        await self._sample.on_fill_bin_event_async()
        await app_utils.update_app_async()

        for i in range(1500):
            await app_utils.update_app_async()

            if self._sample._event == 3:
                break

        self.assertGreaterEqual(self._sample._event, 1)

    async def test_reset(self):
        """Test reset functionality during bin filling."""
        await self._sample.reset_async()
        await app_utils.update_app_async()

        await self._sample.on_fill_bin_event_async()
        await app_utils.update_app_async()

        await app_utils.update_app_async(steps=500)

        await self._sample.reset_async()
        await app_utils.update_app_async()

        self.assertEqual(self._sample._event, 0)

        await self._sample.on_fill_bin_event_async()
        await app_utils.update_app_async()

        await app_utils.update_app_async(steps=500)
