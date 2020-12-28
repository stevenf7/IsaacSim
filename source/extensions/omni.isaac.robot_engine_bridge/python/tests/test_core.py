# NOTE:
#   omni.kit.test - std python's unittest module with additional wrapping to add suport for async/await tests
#   For most things refer to unittest docs: https://docs.python.org/3/library/unittest.html
import omni.kit.test

import omni.kit.usd
import gc

# Import extension python module we are testing with absolute import path, as if we are external user (other extension)
from omni.isaac.robot_engine_bridge import _robot_engine_bridge
from .common import create_application, simulate


# Having a test class dervived from omni.kit.test.AsyncTestCase declared on the root of module will make it auto-discoverable by omni.kit.test
class TestREBCore(omni.kit.test.AsyncTestCase):
    # Before running each test
    async def setUp(self):
        await omni.usd.get_context().new_stage_async()
        self._timeline = omni.timeline.get_timeline_interface()
        self._usd_context = omni.usd.get_context()
        self._stage = self._usd_context.get_stage()
        self._re_bridge = _robot_engine_bridge.acquire_robot_engine_bridge_interface()
        pass

    # After running each test
    async def tearDown(self):
        gc.collect()
        pass

    # Create and destroy the app
    async def test_spawn_reb_init(self):
        # Base create destroy test
        create_application(self._re_bridge)
        self._re_bridge.destroy_application()

        # Create after play
        self._timeline.play()
        create_application(self._re_bridge)
        await simulate(1.0)
        self._timeline.stop()
        self._re_bridge.destroy_application()

        # Create before play
        create_application(self._re_bridge)
        self._timeline.play()
        await simulate(1.0)
        self._re_bridge.destroy_application()
        self._timeline.stop()
