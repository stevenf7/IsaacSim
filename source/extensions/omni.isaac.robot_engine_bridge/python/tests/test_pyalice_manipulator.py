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
import carb.tokens
import numpy as np
import gc
import asyncio

# Import extension python module we are testing with absolute import path, as if we are external user (other extension)
from omni.isaac.dynamic_control import _dynamic_control

from omni.isaac.core.utils.stage import open_stage_async
from omni.isaac.core.utils.nucleus import get_assets_root_path
from omni.isaac.pyalice import Composite
from .common import PyaliceApp, create_application
from omni.isaac.core.utils.physics import simulate_async

# Having a test class dervived from omni.kit.test.AsyncTestCase declared on the root of module will make it auto-discoverable by omni.kit.test
class TestREBPyaliceManipulator(omni.kit.test.AsyncTestCase):
    # Before running each test
    async def setUp(self):
        await omni.usd.get_context().new_stage_async()
        self._timeline = omni.timeline.get_timeline_interface()
        self._usd_context = omni.usd.get_context()
        self._dc = _dynamic_control.acquire_dynamic_control_interface()

        ext_manager = omni.kit.app.get_app().get_extension_manager()
        ext_id = ext_manager.get_enabled_extension_id("omni.isaac.robot_engine_bridge")
        self._reb_extension_path = ext_manager.get_extension_path(ext_id)

        self._asset_path = self._reb_extension_path

        self._assets_root_path = get_assets_root_path()
        if self._assets_root_path is None:
            carb.log_error("Could not find Isaac Sim assets folder")
            return

        self.assertTrue(create_application()[1])

        self._physics_rate = 60
        carb.settings.get_settings().set_bool("/app/runLoops/main/rateLimitEnabled", True)
        carb.settings.get_settings().set_int("/app/runLoops/main/rateLimitFrequency", int(self._physics_rate))
        carb.settings.get_settings().set_int("/persistent/simulation/minFrameRate", int(self._physics_rate))

        await omni.kit.app.get_app().next_update_async()

        pass

    # After running each test
    async def tearDown(self):
        self.assertTrue(omni.kit.commands.execute("RobotEngineBridgeDestroyApplication")[1])
        while omni.usd.get_context().get_stage_loading_status()[2] > 0:
            print("tearDown, assets still loading, waiting to finish...")
            await asyncio.sleep(1.0)
        gc.collect()
        pass

    def create_joint_command_message(self, joints, values):
        quantities = [[x, "position", 1] for x in joints]
        values = np.array(values, dtype=np.dtype("float64"))
        return quantities, Composite.create_composite_message(quantities, values)

    async def test_ur10_basic(self):
        (result, error) = await open_stage_async(
            self._assets_root_path + "/Isaac/Samples/Isaac_SDK/Scenario/ur10_basic.usd"
        )
        self.assertTrue(result)
        self._timeline.play()
        await omni.kit.app.get_app().next_update_async()

        test_app = PyaliceApp()
        test_app.app.load(
            filename=self._reb_extension_path + "/data/config/navsim_tcp.subgraph.json", prefix="simulation"
        )
        sim_in = test_app.app.nodes["simulation.interface"]["input"]
        sim_out = test_app.app.nodes["simulation.interface"]["output"]

        test_app.start()
        # Run test so tcp is connected
        await simulate_async(1)
        # Send commands
        joints = [
            "shoulder_pan_joint",
            "shoulder_lift_joint",
            "elbow_joint",
            "wrist_1_joint",
            "wrist_2_joint",
            "wrist_3_joint",
        ]
        quantities = [[x, "position", 1] for x in joints]
        values = np.array([-1.57, -2.2, 1.9, -1.383, -1.57, 0.796], dtype=np.dtype("float64"))
        cmd_msg = Composite.create_composite_message(quantities, values)
        test_app.app.publish("simulation.interface", "input", "joint_position", cmd_msg)
        # Run test for a while for the arm to move
        await simulate_async(4)

        state_msg = test_app.app.receive("simulation.interface", "output", "joint_state")
        self.assertIsNotNone(state_msg)
        states = Composite.parse_composite_message(state_msg, quantities)
        self.assertIsNotNone(states)
        delta = np.abs(states - values)
        self.assertLessEqual(np.max(delta), 0.01)

        self._timeline.stop()
        test_app.stop()
        test_app = None

        pass

    async def test_franka_basic(self):
        (result, error) = await open_stage_async(
            self._assets_root_path + "/Isaac/Samples/Isaac_SDK/Scenario/franka_basic.usd"
        )
        self.assertTrue(result)
        self._timeline.play()
        await omni.kit.app.get_app().next_update_async()

        test_app = PyaliceApp()
        test_app.app.load(
            filename=self._reb_extension_path + "/data/config/navsim_tcp.subgraph.json", prefix="simulation"
        )
        sim_in = test_app.app.nodes["simulation.interface"]["input"]
        sim_out = test_app.app.nodes["simulation.interface"]["output"]

        test_app.start()
        # Run test so tcp is connected
        await simulate_async(1)
        # Send commands to move arm and open gripper
        joints = [
            "panda_joint1",
            "panda_joint2",
            "panda_joint3",
            "panda_joint4",
            "panda_joint5",
            "panda_joint6",
            "panda_joint7",
        ]
        quantities = [[x, "position", 1] for x in joints]
        values = np.array([-0.64, -0.35, 0.58, -2.3, 0.21, 2.0, 0.61], dtype=np.dtype("float64"))
        cmd_msg = Composite.create_composite_message(quantities, values)
        test_app.app.publish("simulation.interface", "input", "joint_position", cmd_msg)

        open_gripper = Composite.create_composite_message(
            [["gripper", "none", 1]], np.array([0.0], dtype=np.dtype("float64"))
        )
        test_app.app.publish("simulation.interface", "input", "io_command", open_gripper)

        # Run test for a while for the arm to move
        await simulate_async(3)

        # validate joint angles
        state_msg = test_app.app.receive("simulation.interface", "output", "joint_state")
        self.assertIsNotNone(state_msg)
        states = Composite.parse_composite_message(state_msg, quantities)
        self.assertIsNotNone(states)
        delta = np.abs(states - values)
        self.assertTrue(np.max(delta) < 0.03)
        # validate gripper is open
        gripper_msg = test_app.app.receive("simulation.interface", "output", "io_state")
        self.assertIsNotNone(gripper_msg)
        buffer = gripper_msg.tensor
        self.assertIsNotNone(buffer)
        self.assertTrue(buffer[0] == 0.0)

        # Send command to close gripper
        close_gripper = Composite.create_composite_message(
            [["gripper", "none", 1]], np.array([1.0], dtype=np.dtype("float64"))
        )
        test_app.app.publish("simulation.interface", "input", "io_command", close_gripper)
        await simulate_async(1)

        # validate gripper is closed
        gripper_msg = test_app.app.receive("simulation.interface", "output", "io_state")
        self.assertIsNotNone(gripper_msg)
        buffer = gripper_msg.tensor
        self.assertIsNotNone(buffer)
        self.assertTrue(buffer[0] == 1.0)

        self._timeline.stop()
        test_app.stop()
        test_app = None

        pass

    async def test_revolute(self):
        (result, error) = await open_stage_async(
            self._assets_root_path + "/Isaac/Samples/Isaac_SDK/Robots/Simple_Articulation_REB.usd"
        )
        self.assertTrue(result)
        self._timeline.play()
        await omni.kit.app.get_app().next_update_async()

        test_app = PyaliceApp()
        test_app.app.load(
            filename=self._reb_extension_path + "/data/config/navsim_tcp.subgraph.json", prefix="simulation"
        )
        sim_in = test_app.app.nodes["simulation.interface"]["input"]
        sim_out = test_app.app.nodes["simulation.interface"]["output"]

        test_app.start()
        # Run test so tcp is connected
        await simulate_async(1)

        async def check_joint(joints, values, actual_value, time=1.0):

            # Send commands to move arm and test joint limits
            quantities, cmd_msg = self.create_joint_command_message(joints, values)
            test_app.app.publish("simulation.interface", "input", "joint_position", cmd_msg)

            # Run test for a while for the arm to move
            await simulate_async(time)

            # validate joint angles
            state_msg = test_app.app.receive("simulation.interface", "output", "joint_state")
            self.assertIsNotNone(state_msg)
            states = Composite.parse_composite_message(state_msg, quantities)
            self.assertIsNotNone(states)
            delta = np.abs(states - actual_value)
            self.assertTrue(np.max(delta) < 0.03)

        await check_joint(["RevoluteJoint"], [0], [0])
        await check_joint(["RevoluteJoint"], [6], [6])
        await check_joint(["RevoluteJoint"], [7], [6.25])
        self._timeline.stop()
        test_app.stop()
        test_app = None
        pass

    async def test_prismatic(self):
        (result, error) = await open_stage_async(
            self._assets_root_path + "/Isaac/Samples/Isaac_SDK/Robots/Simple_Articulation_REB.usd"
        )
        self.assertTrue(result)

        self._timeline.play()
        await omni.kit.app.get_app().next_update_async()

        test_app = PyaliceApp()
        test_app.app.load(
            filename=self._reb_extension_path + "/data/config/navsim_tcp.subgraph.json", prefix="simulation"
        )
        sim_in = test_app.app.nodes["simulation.interface"]["input"]
        sim_out = test_app.app.nodes["simulation.interface"]["output"]

        test_app.start()
        # Run test so tcp is connected
        await simulate_async(1)

        async def check_joint(joints, values, actual_value, time=1.0):

            # Send commands to move arm and test joint limits
            quantities, cmd_msg = self.create_joint_command_message(joints, values)
            test_app.app.publish("simulation.interface", "input", "joint_position", cmd_msg)

            # Run test for a while for the arm to move
            await simulate_async(time)

            # validate joint angles
            state_msg = test_app.app.receive("simulation.interface", "output", "joint_state")
            self.assertIsNotNone(state_msg)
            states = Composite.parse_composite_message(state_msg, quantities)
            self.assertIsNotNone(states)
            delta = np.abs(states - actual_value)
            self.assertTrue(np.max(delta) < 0.03)

        await check_joint(["PrismaticJoint"], [0], [0])
        await check_joint(["PrismaticJoint"], [-100], [-1])
        await check_joint(["PrismaticJoint"], [100], [100])
        self._timeline.stop()
        test_app.stop()
        test_app = None
        pass
