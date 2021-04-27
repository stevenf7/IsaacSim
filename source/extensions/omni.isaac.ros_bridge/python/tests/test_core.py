# NOTE:
#   omni.kit.test - std python's unittest module with additional wrapping to add suport for async/await tests
#   For most things refer to unittest docs: https://docs.python.org/3/library/unittest.html
import omni.kit.test
import omni.kit.usd
import gc
import asyncio

# Import extension python module we are testing with absolute import path, as if we are external user (other extension)
import omni.kit.commands
from omni.isaac.ros_ui.scripts.roscore import Roscore
from .common import wait_for_rosmaster
import rospy
import carb

# Having a test class dervived from omni.kit.test.AsyncTestCase declared on the root of module will make it auto-discoverable by omni.kit.test
class TestRosBridge(omni.kit.test.AsyncTestCase):
    # Before running each test
    async def setUp(self):
        # await omni.usd.get_context().new_stage_async()
        self._timeline = omni.timeline.get_timeline_interface()
        self._stage = omni.usd.get_context().get_stage()
        ext_manager = omni.kit.app.get_app().get_extension_manager()
        ext_id = ext_manager.get_enabled_extension_id("omni.isaac.ros_bridge")
        self._ros_extension_path = ext_manager.get_extension_path(ext_id)
        kit_folder = carb.tokens.get_tokens_interface().resolve("${kit}")
        self._roscore = Roscore()
        self._roscore.startup(kit_folder + "/python/bin", self._ros_extension_path + "/noetic", "_CATKIN_SETUP_DIR")
        await wait_for_rosmaster()
        # You must disable signals so that the init node call does not take over the ctrl-c callback for kit
        pass

    # After running each test
    async def tearDown(self):
        self._stage = None
        self._timeline = None
        self._roscore.shutdown()
        self._roscore = None

        # await omni.usd.get_context().new_stage_async()
        gc.collect()
        pass

    async def test_core(self):
        self._timeline.play()
        await asyncio.sleep(1.0)
        self._timeline.stop()
        pass
