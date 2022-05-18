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
        gc.collect()
        pass

    # Run all commands
    async def test_ros_command(self):

        result, prim = omni.kit.commands.execute("ROSBridgeCreateCamera", path="/ROS_Camera")
        result, prim = omni.kit.commands.execute("ROSBridgeCreateClock", path="/ROS_Clock")
        result, prim = omni.kit.commands.execute("ROSBridgeCreateJointState", path="/ROS_JointState")
        result, prim = omni.kit.commands.execute("ROSBridgeCreateLidar", path="/ROS_Lidar")
        result, prim = omni.kit.commands.execute("ROSBridgeCreatePoseTree", path="/ROS_PoseTree")
        result, prim = omni.kit.commands.execute("ROSBridgeCreateTeleport", path="/ROS_Teleport")
        result, prim = omni.kit.commands.execute("ROSBridgeCreateSurfaceGripper", path="/ROS_SurfaceGripper")
        result, prim = omni.kit.commands.execute("ROSBridgeCreateDifferentialBase", path="/ROS_DifferentialBase")
        self._timeline.play()
        await omni.kit.app.get_app().next_update_async()
        await omni.kit.app.get_app().next_update_async()
