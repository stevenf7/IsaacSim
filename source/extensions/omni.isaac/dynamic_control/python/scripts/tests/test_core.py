# NOTE:
#   omni.kit.test - std python's unittest module with additional wrapping to add suport for async/await tests
#   For most things refer to unittest docs: https://docs.python.org/3/library/unittest.html
import omni.kit.test
import omni.kit.asyncapi
import omni.kit.usd
import carb.tokens
import os
import asyncio

# Import extension python module we are testing with absolute import path, as if we are external user (other extension)
from omni.isaac.dynamic_control import _dynamic_control
from omni.isaac.utils.scripts.test_utils import load_test_file

# Having a test class dervived from omni.kit.test.AsyncTestCase declared on the root of module will make it auto-discoverable by omni.kit.test
class TestCore(omni.kit.test.AsyncTestCaseFailOnLogError):
    # Before running each test
    async def setUp(self):
        self._dc = _dynamic_control.acquire_dynamic_control_interface()

        pass

    # After running each test
    async def tearDown(self):
        pass

    # Actual test, notice it is "async" function, so "await" can be used if needed
    async def test_is_simulating(self):
        await omni.kit.asyncapi.new_stage()

        self.assertFalse(self._dc.is_simulating())
        # Start Simulation and wait
        editor = omni.kit.editor.get_editor_interface()
        editor.play()
        await asyncio.sleep(0.125)
        self.assertTrue(self._dc.is_simulating())
        editor.stop()
        await asyncio.sleep(0.125)
        self.assertFalse(self._dc.is_simulating())
        pass
