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

# Import extension python module we are testing with absolute import path, as if we are external user (other extension)
from omni.isaac.gamepad import _gamepad
import carb

# Having a test class dervived from omni.kit.test.AsyncTestCase declared on the root of module will make it auto-discoverable by omni.kit.test
class TestGamepad(omni.kit.test.AsyncTestCaseFailOnLogError):
    # Before running each test
    async def setUp(self):
        self._gamepad = _gamepad.acquire_gamepad_interface()
        await omni.kit.app.get_app().next_update_async()
        pass

    # After running each test
    async def tearDown(self):
        await omni.kit.app.get_app().next_update_async()
        pass

    def event_callback(self, axis, signal):
        self.latest_axis = axis
        self.latest_signal = signal

    # Basic unit test to make sure callback works
    async def test_gamepad(self):
        await omni.kit.app.get_app().next_update_async()

        m = _gamepad.acquire_gamepad_interface()
        provider = carb.input.acquire_input_provider()
        gamepad = provider.create_gamepad("test", "0")
        provider.set_gamepad_connected(gamepad, True)

        m.bind_gamepad(self.event_callback)
        await omni.kit.app.get_app().next_update_async()
        # check that we have a value
        provider.buffer_gamepad_event(gamepad, carb.input.GamepadInput.LEFT_STICK_UP, 1.0)
        await omni.kit.app.get_app().next_update_async()
        self.assertEqual(self.latest_signal, 1.0)
        # check that value changed
        provider.buffer_gamepad_event(gamepad, carb.input.GamepadInput.RIGHT_STICK_RIGHT, -1.0)
        await omni.kit.app.get_app().next_update_async()
        self.assertEqual(self.latest_signal, -1.0)
        m.unbind_gamepad()
        provider.destroy_gamepad(gamepad)
        await omni.kit.app.get_app().next_update_async()

        pass
