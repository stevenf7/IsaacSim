# NOTE:
#   omni.kit.test - std python's unittest module with additional wrapping to add suport for async/await tests
#   For most things refer to unittest docs: https://docs.python.org/3/library/unittest.html
import omni.kit.test

import omni.kit.usd
import gc

# Import extension python module we are testing with absolute import path, as if we are external user (other extension)
from .common import create_application, simulate
from omni.isaac.robot_engine_bridge import _robot_engine_bridge


# Having a test class dervived from omni.kit.test.AsyncTestCase declared on the root of module will make it auto-discoverable by omni.kit.test
class TestREBCore(omni.kit.test.AsyncTestCase):
    # Before running each test
    async def setUp(self):
        await omni.usd.get_context().new_stage_async()
        self._timeline = omni.timeline.get_timeline_interface()
        self._usd_context = omni.usd.get_context()
        self._stage = self._usd_context.get_stage()
        pass

    # After running each test
    async def tearDown(self):
        await omni.kit.app.get_app().next_update_async()
        gc.collect()
        pass

    # Create and destroy the app
    async def test_spawn_app(self):
        # Base create destroy test
        self.assertTrue(create_application()[1])
        self.assertTrue(omni.kit.commands.execute("RobotEngineBridgeDestroyApplication")[1])
        # destroy should not fail even if called multiple times
        self.assertFalse(omni.kit.commands.execute("RobotEngineBridgeDestroyApplication")[1])

    async def test_spawn_twice(self):
        # should only create app successfully once and destroy once
        self.assertTrue(create_application()[1])
        self.assertFalse(create_application()[1])
        self.assertTrue(omni.kit.commands.execute("RobotEngineBridgeDestroyApplication")[1])
        self.assertFalse(omni.kit.commands.execute("RobotEngineBridgeDestroyApplication")[1])

    async def test_destroy_app(self):
        # try to destroy app that was never created, should always return false
        self.assertFalse(omni.kit.commands.execute("RobotEngineBridgeDestroyApplication")[1])
        self.assertFalse(omni.kit.commands.execute("RobotEngineBridgeDestroyApplication")[1])

    async def test_spawn_app_fail(self):
        # Try to create app with non existent json
        self.assertFalse(create_application("does_not_exist.json")[1])
        self.assertFalse(omni.kit.commands.execute("RobotEngineBridgeDestroyApplication")[1])
        # appwas already destroyed, should return false
        self.assertFalse(omni.kit.commands.execute("RobotEngineBridgeDestroyApplication")[1])

    async def test_spawn_app_active(self):
        # Create after play
        self._timeline.play()
        self.assertTrue(create_application()[1])
        await simulate(1.0)
        self._timeline.stop()
        self.assertTrue(omni.kit.commands.execute("RobotEngineBridgeDestroyApplication")[1])

        # Create before play
        self.assertTrue(create_application()[1])
        self._timeline.play()
        await simulate(1.0)
        self.assertTrue(omni.kit.commands.execute("RobotEngineBridgeDestroyApplication")[1])
        self._timeline.stop()

    async def test_execute_command(self):

        cubePrim = self._stage.GetPrimAtPath("/cube")
        self.assertFalse(cubePrim)
        self._re_bridge = _robot_engine_bridge.acquire_robot_engine_bridge_interface()
        imports = "import omni.kit.commands\n"
        command = "omni.kit.commands.execute('CreatePrimCommand', prim_path='/cube', prim_type='Cube')"
        self._re_bridge.execute_command(imports + command)
        await omni.kit.app.get_app().next_update_async()

        cubePrim = self._stage.GetPrimAtPath("/cube")

        self.assertTrue(cubePrim)
