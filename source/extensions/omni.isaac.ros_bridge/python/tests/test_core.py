# NOTE:
#   omni.kit.test - std python's unittest module with additional wrapping to add suport for async/await tests
#   For most things refer to unittest docs: https://docs.python.org/3/library/unittest.html
import omni.kit.test
import omni.kit.usd
import gc
import asyncio
from omni.isaac.ros_bridge import _ros_bridge

# Import extension python module we are testing with absolute import path, as if we are external user (other extension)
import omni.kit.commands
from .common import wait_for_rosmaster, bridge_rosmaster_connect
import carb

# Having a test class dervived from omni.kit.test.AsyncTestCase declared on the root of module will make it auto-discoverable by omni.kit.test
class TestRosBridge(omni.kit.test.AsyncTestCaseFailOnLogError):
    # Before running each test
    async def setUp(self):
        from omni.isaac.ros_bridge_ui.scripts.roscore import Roscore

        await omni.usd.get_context().new_stage_async()
        await omni.kit.app.get_app().next_update_async()
        self._timeline = omni.timeline.get_timeline_interface()
        ext_manager = omni.kit.app.get_app().get_extension_manager()
        ext_id = ext_manager.get_enabled_extension_id("omni.isaac.ros_bridge")
        self._ros_extension_path = ext_manager.get_extension_path(ext_id)
        _rosbridge = _ros_bridge.acquire_ros_bridge_interface()
        kit_folder = carb.tokens.get_tokens_interface().resolve("${kit}")
        self._roscore = Roscore()
        self._roscore.startup(kit_folder + "/python/bin", self._ros_extension_path + "/noetic", "_CATKIN_SETUP_DIR")
        await wait_for_rosmaster()
        # You must disable signals so that the init node call does not take over the ctrl-c callback for kit
        await omni.kit.app.get_app().next_update_async()
        await bridge_rosmaster_connect(_rosbridge)
        pass

    # After running each test
    async def tearDown(self):
        self._stage = None
        self._timeline = None
        self._roscore.shutdown()
        self._roscore = None
        await omni.kit.app.get_app().next_update_async()
        gc.collect()
        pass

    async def test_ros_bridge_core(self):
        self._timeline.play()
        await asyncio.sleep(1.0)
        self._timeline.stop()
        pass

    async def test_reparenting(self):
        # reparent, then play
        await omni.kit.app.get_app().next_update_async()
        result, prim1 = omni.kit.commands.execute("ROSBridgeCreatePoseTree", path="/ROS_PoseTree")
        result, prim2 = omni.kit.commands.execute("ROSBridgeCreatePoseTree", path="/ROS_PoseTree_01")
        result, prim3 = omni.kit.commands.execute("CreatePrim", prim_type="Xform")
        await omni.kit.app.get_app().next_update_async()
        omni.kit.commands.execute("MovePrim", path_from=prim1.GetPath(), path_to="/Xform/" + "ROS_PoseTree")
        self._timeline.play()
        await omni.kit.app.get_app().next_update_async()
        self._timeline.stop()
        await omni.kit.app.get_app().next_update_async()
        await omni.usd.get_context().new_stage_async()
        # play then reparent
        await omni.kit.app.get_app().next_update_async()
        self._timeline.play()
        await omni.kit.app.get_app().next_update_async()
        result, prim1 = omni.kit.commands.execute("ROSBridgeCreatePoseTree", path="/ROS_PoseTree")
        result, prim2 = omni.kit.commands.execute("ROSBridgeCreatePoseTree", path="/ROS_PoseTree_01")
        result, prim3 = omni.kit.commands.execute("CreatePrim", prim_type="Xform")
        await omni.kit.app.get_app().next_update_async()
        omni.kit.commands.execute("MovePrim", path_from=prim1.GetPath(), path_to="/Xform/" + "ROS_PoseTree")
        await omni.kit.app.get_app().next_update_async()
        pass

    async def test_deleting(self):
        # create prim, then play and then delete
        result, prim1 = omni.kit.commands.execute("ROSBridgeCreatePoseTree", path="/ROS_PoseTree")
        result, prim2 = omni.kit.commands.execute("ROSBridgeCreatePoseTree", path="/ROS_PoseTree_01")
        self._timeline.play()
        await omni.kit.app.get_app().next_update_async()
        omni.kit.commands.execute("DeletePrims", paths=[prim1.GetPath()])
        await omni.usd.get_context().new_stage_async()
        self._timeline.play()
        result, prim1 = omni.kit.commands.execute("ROSBridgeCreatePoseTree", path="/ROS_PoseTree")
        result, prim2 = omni.kit.commands.execute("ROSBridgeCreatePoseTree", path="/ROS_PoseTree_01")
        await omni.kit.app.get_app().next_update_async()
        omni.kit.commands.execute("DeletePrims", paths=[prim1.GetPath()])

    async def test_ros_sim_time_command(self):

        result = omni.kit.commands.execute("RosBridgeUseSimTime", use_sim_time=False)
        result, status = omni.kit.commands.execute("RosBridgeRosMasterCheck")
        self.assertTrue(status)

        self._timeline.play()
        await omni.kit.app.get_app().next_update_async()
        await omni.kit.app.get_app().next_update_async()
