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

from .common import PyaliceApp, create_application
from omni.isaac.core.utils.physics import simulate_async

# Having a test class dervived from omni.kit.test.AsyncTestCase declared on the root of module will make it auto-discoverable by omni.kit.test
class TestREBPyalice(omni.kit.test.AsyncTestCaseFailOnLogError):
    # Before running each test
    async def setUp(self):
        await omni.usd.get_context().new_stage_async()
        self._timeline = omni.timeline.get_timeline_interface()
        ext_manager = omni.kit.app.get_app().get_extension_manager()
        ext_id = ext_manager.get_enabled_extension_id("omni.isaac.robot_engine_bridge")
        self._reb_extension_path = ext_manager.get_extension_path(ext_id)
        pass

    # After running each test
    async def tearDown(self):
        omni.kit.commands.execute("RobotEngineBridgeDestroyApplication")[1]
        gc.collect()
        pass

    async def test_publish_no_app(self):
        from omni.isaac.pyalice import Message

        msg = Message.create_message_builder("BooleanProto")
        msg.proto.flag = True

        # make sure it works if we publish before play
        result, state = omni.kit.commands.execute(
            "RobotEngineBridgePublishProto",
            node="interface",
            component="output",
            channel="test_channel",
            proto=msg.proto,
        )
        self._timeline.play()
        await simulate_async(1.0)
        result, state = omni.kit.commands.execute(
            "RobotEngineBridgePublishProto",
            node="interface",
            component="output",
            channel="test_channel",
            proto=msg.proto,
        )

    async def test_publish_json(self):
        from omni.isaac.pyalice import Message

        msg = Message.create_message_builder("BooleanProto")
        msg.proto.flag = True

        self.assertTrue(create_application()[1])

        test_app = PyaliceApp()

        test_app.app.load(
            filename=self._reb_extension_path + "/data/config/navsim_tcp.subgraph.json", prefix="simulation"
        )

        test_app.start()
        await simulate_async(3)

        self._timeline.play()

        result, state = omni.kit.commands.execute(
            "RobotEngineBridgePublishProto",
            node="interface",
            component="output",
            channel="test_channel",
            proto=msg.proto,
        )
        await simulate_async(1.0)

        collision_msg = test_app.app.receive("simulation.interface", "output", "test_channel")
        self.assertTrue(collision_msg.proto.flag)

        test_app.stop()
        self.assertTrue(omni.kit.commands.execute("RobotEngineBridgeDestroyApplication")[1])
