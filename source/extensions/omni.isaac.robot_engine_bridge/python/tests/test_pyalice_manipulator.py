# NOTE:
#   omni.kit.test - std python's unittest module with additional wrapping to add suport for async/await tests
#   For most things refer to unittest docs: https://docs.python.org/3/library/unittest.html
import omni.kit.test

import omni.kit.usd
import carb.tokens
import numpy as np
import gc

# Import extension python module we are testing with absolute import path, as if we are external user (other extension)
from omni.isaac.dynamic_control import _dynamic_control

from omni.isaac.utils.scripts.test_utils import load_test_file
from omni.isaac.utils.scripts.nucleus_utils import find_nucleus_server
from omni.isaac.pyalice import Composite
from .common import PyaliceApp, create_application, simulate


# Having a test class dervived from omni.kit.test.AsyncTestCase declared on the root of module will make it auto-discoverable by omni.kit.test
class TestREBPyaliceManipulator(omni.kit.test.AsyncTestCaseFailOnLogError):
    # Before running each test
    async def setUp(self):
        await omni.usd.get_context().new_stage_async()
        self._timeline = omni.timeline.get_timeline_interface()
        self._usd_context = omni.usd.get_context()
        self._dc = _dynamic_control.acquire_dynamic_control_interface()

        ext_manager = omni.kit.app.get_app().get_extension_manager()
        ext_id = ext_manager.get_enabled_extension_id("omni.isaac.robot_engine_bridge")
        self._reb_extension_path = ext_manager.get_extension_path(ext_id)
        ext_id = ext_manager.get_enabled_extension_id("omni.isaac.dynamic_control")
        self._dc_extension_path = ext_manager.get_extension_path(ext_id)

        self._asset_path = self._reb_extension_path

        result, nucleus_server = find_nucleus_server()
        if result is False:
            carb.log_error("Could not find nucleus server with /Isaac folder")
            return
        self._nucleus_path = nucleus_server + "/Isaac"

        self.assertTrue(create_application()[1])
        pass

    # After running each test
    async def tearDown(self):
        self.assertTrue(omni.kit.commands.execute("DestroyRobotEngineBridgeApplicationCommand")[1])
        gc.collect()
        pass

    async def test_ur10_basic(self):
        (result, error) = await load_test_file(self._nucleus_path + "/Samples/Isaac_SDK/Scenario/ur10_basic.usd")
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
        await simulate(1)
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
        await simulate(4)

        state_msg = test_app.app.receive("simulation.interface", "output", "joint_state")
        self.assertIsNotNone(state_msg)
        states = Composite.parse_composite_message(state_msg, quantities)
        self.assertIsNotNone(states)
        delta = np.abs(states - values)
        self.assertTrue(np.max(delta) < 0.01)

        self._timeline.stop()
        test_app.stop()
        test_app = None

        pass

    async def test_franka_basic(self):
        (result, error) = await load_test_file(self._nucleus_path + "/Samples/Isaac_SDK/Scenario/franka_basic.usd")
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
        await simulate(1)
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
        await simulate(5)

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
        await simulate(1)

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
