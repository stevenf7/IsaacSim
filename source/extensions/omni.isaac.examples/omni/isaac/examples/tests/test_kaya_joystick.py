# Copyright (c) 2018-2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

# NOTE:
#   omni.kit.test - std python's unittest module with additional wrapping to add suport for async/await tests
#   For most things refer to unittest docs: https://docs.python.org/3/library/unittest.html
import omni.kit.test
import omni.kit
import asyncio
import carb
import gc

# Import extension python module we are testing with absolute import path, as if we are external user (other extension)
from omni.isaac.examples.kaya_joystick import KayaJoystick
from omni.isaac.core.utils.stage import is_stage_loading, set_stage_up_axis
from omni.isaac.core.world.world import World


class TestKayaJoystickSample(omni.kit.test.AsyncTestCaseFailOnLogError):

    # Before running each test
    async def setUp(self):
        self._physics_rate = 60
        self._provider = carb.input.acquire_input_provider()
        self._gamepad = self._provider.create_gamepad("test", "0")
        carb.settings.get_settings().set_int("/app/runLoops/main/rateLimitFrequency", int(self._physics_rate))
        carb.settings.get_settings().set_bool("/app/runLoops/main/rateLimitEnabled", True)
        carb.settings.get_settings().set_int("/persistent/simulation/minFrameRate", int(self._physics_rate))
        await omni.usd.get_context().new_stage_async()
        await omni.kit.app.get_app().next_update_async()
        self._sample = KayaJoystick()
        World.clear_instance()
        set_stage_up_axis("z")
        self._sample.set_world_settings(physics_dt=1.0 / self._physics_rate, stage_units_in_meters=0.01)
        await self._sample.load_world_async()

    # After running each test
    async def tearDown(self):
        # In some cases the test will end before the asset is loaded, in this case wait for assets to load
        while is_stage_loading():
            print("tearDown, assets still loading, waiting to finish...")
            await asyncio.sleep(1.0)
        await omni.kit.app.get_app().next_update_async()
        self._sample._world_cleanup()
        self._sample = None
        await omni.kit.app.get_app().next_update_async()
        self._provider.destroy_gamepad(self._gamepad)
        await omni.kit.app.get_app().next_update_async()
        World.clear_instance()
        pass

    # Run all functions with simulation enabled
    async def test_simulation(self):
        await omni.kit.app.get_app().next_update_async()
        while is_stage_loading():
            await omni.kit.app.get_app().next_update_async()
        self._provider.set_gamepad_connected(self._gamepad, True)
        self.assertLess(self._sample._kaya.get_world_pose()[0][1], 1)
        await omni.kit.app.get_app().next_update_async()
        await omni.kit.app.get_app().next_update_async()
        for i in range(100):
            self._provider.buffer_gamepad_event(self._gamepad, carb.input.GamepadInput.LEFT_STICK_UP, 1.0)
            await omni.kit.app.get_app().next_update_async()
        self._provider.set_gamepad_connected(self._gamepad, False)
        await omni.kit.app.get_app().next_update_async()
        self.assertGreater(self._sample._kaya.get_world_pose()[0][1], 64.0)
        pass
