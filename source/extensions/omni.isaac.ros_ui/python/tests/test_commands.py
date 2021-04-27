# NOTE:
#   omni.kit.test - std python's unittest module with additional wrapping to add suport for async/await tests
#   For most things refer to unittest docs: https://docs.python.org/3/library/unittest.html
import omni.kit.test
import omni.kit.usd
import gc

# Import extension python module we are testing with absolute import path, as if we are external user (other extension)
import omni.kit.commands

# Having a test class dervived from omni.kit.test.AsyncTestCase declared on the root of module will make it auto-discoverable by omni.kit.test
class TestRosBridgeCommands(omni.kit.test.AsyncTestCase):
    # Before running each test
    async def setUp(self):
        await omni.usd.get_context().new_stage_async()
        self._timeline = omni.timeline.get_timeline_interface()
        self._stage = omni.usd.get_context().get_stage()
        pass

    # After running each test
    async def tearDown(self):
        self._stage = None
        self._timeline = None
        await omni.usd.get_context().new_stage_async()
        gc.collect()
        pass

    # Run all commands
    async def test_command(self):

        result, prim = omni.kit.commands.execute("CreateROSBridgeCameraCommand", path="/ROS_Camera")
        result, prim = omni.kit.commands.execute("CreateROSBridgeClockCommand", path="/ROS_Clock")
        result, prim = omni.kit.commands.execute("CreateROSBridgeJointStateCommand", path="/ROS_JointState")
        result, prim = omni.kit.commands.execute("CreateROSBridgeLidarCommand", path="/ROS_Lidar")
        result, prim = omni.kit.commands.execute("CreateROSBridgePoseTreeCommand", path="/ROS_PoseTree")
        result, prim = omni.kit.commands.execute("CreateROSBridgeTeleportCommand", path="/ROS_Teleport")
        self._timeline.play()
        await omni.kit.app.get_app().next_update_async()
        await omni.kit.app.get_app().next_update_async()
