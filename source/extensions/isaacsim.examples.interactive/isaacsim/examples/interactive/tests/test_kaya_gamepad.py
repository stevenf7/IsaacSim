# SPDX-FileCopyrightText: Copyright (c) 2018-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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

import asyncio

import carb
import omni.kit

# NOTE:
#   omni.kit.test - std python's unittest module with additional wrapping to add suport for async/await tests
#   For most things refer to unittest docs: https://docs.python.org/3/library/unittest.html
import omni.kit.test
from isaacsim.core.api.world.world import World
from isaacsim.core.prims import RigidPrim
from isaacsim.core.utils.stage import create_new_stage_async, is_stage_loading, update_stage_async

# Import extension python module we are testing with absolute import path, as if we are external user (other extension)
from isaacsim.examples.interactive.kaya_gamepad import KayaGamepad


class TestKayaGamepadSample(omni.kit.test.AsyncTestCase):

    # Before running each test
    async def setUp(self):
        await create_new_stage_async()
        self._provider = carb.input.acquire_input_provider()
        self._gamepad = self._provider.create_gamepad("test", "0")
        await update_stage_async()
        self._sample = KayaGamepad()
        World.clear_instance()
        self._sample.set_world_settings(physics_dt=1.0 / 60, stage_units_in_meters=1.0)
        await self._sample.load_world_async()
        return

    # After running each test
    async def tearDown(self):
        # In some cases the test will end before the asset is loaded, in this case wait for assets to load
        while is_stage_loading():
            print("tearDown, assets still loading, waiting to finish...")
            await asyncio.sleep(1.0)
        await omni.kit.app.get_app().next_update_async()
        self._sample._world_cleanup()
        self._sample = None
        await update_stage_async()
        self._provider.destroy_gamepad(self._gamepad)
        await update_stage_async()
        World.clear_instance()
        pass

    # Run all functions with simulation enabled
    async def test_simulation(self):
        await update_stage_async()
        while is_stage_loading():
            await update_stage_async()

        # Access the kaya robot prim directly by path
        kaya_prim = RigidPrim("/kaya/base_link")

        # Connect the gamepad so OmniGraph nodes can detect it
        self._provider.set_gamepad_connected(self._gamepad, True)
        await update_stage_async()

        # Check initial position
        self.assertLess(kaya_prim.get_world_poses()[0][0][0], 0.1)

        # Start the simulation - Action Graphs only execute when timeline is playing
        world = self._sample.get_world()
        await world.play_async()
        await update_stage_async()

        # Send gamepad input to move the robot forward
        for i in range(100):
            self._provider.buffer_gamepad_event(self._gamepad, carb.input.GamepadInput.LEFT_STICK_UP, 1.0)
            await update_stage_async()

        # Stop simulation and disconnect gamepad
        await world.pause_async()
        self._provider.set_gamepad_connected(self._gamepad, False)
        await update_stage_async()
        # Verify robot moved forward (positive X direction)
        self.assertGreater(kaya_prim.get_world_poses()[0][0][0], 0.9)
        pass
