# NOTE:
#   omni.kit.test - std python's unittest module with additional wrapping to add suport for async/await tests
#   For most things refer to unittest docs: https://docs.python.org/3/library/unittest.html
import omni.kit.test

import omni.kit.usd
import carb.tokens
import os
import asyncio
import numpy as np
import gc

# Import extension python module we are testing with absolute import path, as if we are external user (other extension)
import omni.isaac.RobotEngineBridgeSchema as REBSchema
from omni.isaac.robot_engine_bridge import _robot_engine_bridge
from omni.isaac.dynamic_control import _dynamic_control

from omni.isaac.utils.scripts.test_utils import load_test_file
from omni.isaac.utils.scripts.nucleus_utils import find_nucleus_server
from .common import PyaliceApp, setup_base_prim
from omni.isaac.pyalice import Codelet
from omni.isaac.pyalice import Composite

# Having a test class dervived from omni.kit.test.AsyncTestCase declared on the root of module will make it auto-discoverable by omni.kit.test
class TestREBPyalice(omni.kit.test.AsyncTestCase):
    # Before running each test
    async def setUp(self):
        await omni.usd.get_context().new_stage_async()
        self._timeline = omni.timeline.get_timeline_interface()
        self._usd_context = omni.usd.get_context()
        self._dc = _dynamic_control.acquire_dynamic_control_interface()
        self._re_bridge = _robot_engine_bridge.acquire_robot_engine_bridge_interface()

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

        self.create_application()
        pass

    # After running each test
    async def tearDown(self):
        self._re_bridge.destroy_application()
        gc.collect()
        pass

    async def simulate(self, seconds, art=None, steps_per_sec=60):
        for frame in range(steps_per_sec * seconds):
            if art is not None:
                self._dc.wake_up_articulation(art)
            await omni.kit.app.get_app().next_update_async()

    def create_application(self):
        json_path = self._reb_extension_path + "/resources/isaac_engine/json/isaacsim.app.json"

        print("create application with: ", self._reb_extension_path, json_path)
        self._re_bridge.create_application(self._reb_extension_path, json_path, [], [])

    async def test_pyalice_init(self):
        self._timeline.play()

        test_app = PyaliceApp()
        test_app.app.load_module("sight")

        test_app.start()

        await asyncio.sleep(2)
        self._timeline.stop()

        test_app.stop()
        pass

    async def test_diffbase_carter(self):
        (result, error) = await load_test_file(self._nucleus_path + "/Robots/Carter/carter_sphere_wheels_lidar.usd")
        # (result, error) = await load_test_file(
        #    self._dc_extension_path + "/data/usd/robots/carter/carter.usd"
        # )
        # Make sure the stage loaded
        self.assertTrue(result)
        stage = self._usd_context.get_stage()
        path = omni.kit.utils.get_stage_next_free_path(stage, "/REB_DifferentialBase", True)
        prim = REBSchema.RobotEngineDifferentialBase.Define(stage, path)
        setup_base_prim(prim)

        prim.CreateInputComponentAttr("input")
        prim.CreateInputChannelAttr("base_command")

        prim.CreateOutputComponentAttr("output")
        prim.CreateOutputChannelAttr("base_state")

        prim.CreateChassisPrimRel().SetTargets(["/carter"])
        prim.CreateLeftWheelJointNameAttr("left_wheel")
        prim.CreateRightWheelJointNameAttr("right_wheel")

        prim.CreateRobotFrontAttr((1, 0, 0))
        prim.CreateMaxSpeedAttr((2.0, 4.0))
        prim.CreateMaxTimeWithoutCommandAttr(0.2)
        prim.CreateAccelerationSmoothingAttr(1.0)
        prim.CreateWheelRadiusAttr(0.24)
        prim.CreateWheelBaseAttr(0.26613607)

        self._timeline.play()
        ELEMENT_TYPE_F64 = 3
        await omni.kit.app.get_app().next_update_async()
        art = self._dc.get_articulation("/carter")
        self.assertNotEqual(art, _dynamic_control.INVALID_HANDLE)
        root_body_ptr = self._dc.get_articulation_root_body(art)

        class ConstantDiffBaseControl(Codelet):
            """
            Publish constant speed command
            """

            def start(self):
                self.tx = self.isaac_proto_tx("StateProto", "cmd")
                self.tick_periodically(0.05)

            def tick(self):
                tx_message = self.tx.init()
                pack = tx_message.proto.pack
                pack.elementType = ELEMENT_TYPE_F64
                sizes = pack.init("sizes", 3)
                sizes[0] = 1
                sizes[1] = 1
                sizes[2] = 2
                pack.scanlineStride = 0
                pack.dataBufferIndex = 0
                tx_message.buffers = [np.array([self.config.linear, self.config.rotation])]
                self.tx.publish()

        test_app = PyaliceApp()
        test_app.app.load(
            filename=self._reb_extension_path + "/data/config/navsim_tcp.subgraph.json", prefix="simulation"
        )
        sim_in = test_app.app.nodes["simulation.interface"]["input"]

        control = test_app.app.add("controller").add(ConstantDiffBaseControl, name="ConstantDiffBaseControl")
        # Convert the velocity to cm/s
        control.config.linear = 0.5
        control.config.rotation = 0.0
        test_app.app.connect(control, "cmd", sim_in, "base_command")
        test_app.start()
        # Run test for 2 seconds, check the linear velocity
        await self.simulate(2)

        lin_vel = self._dc.get_rigid_body_linear_velocity(root_body_ptr)
        self.assertAlmostEqual(
            control.config.linear, np.linalg.norm([lin_vel.x, lin_vel.y, lin_vel.z]) / 100.0, delta=0.2
        )

        control.config.linear = 0.0
        await self.simulate(2)

        lin_vel = self._dc.get_rigid_body_linear_velocity(root_body_ptr)
        self.assertAlmostEqual(
            control.config.linear, np.linalg.norm([lin_vel.x, lin_vel.y, lin_vel.z]) / 100.0, delta=0.2
        )

        control.config.rotation = 1.0
        await self.simulate(4)
        ang_vel = self._dc.get_rigid_body_angular_velocity(root_body_ptr)
        self.assertAlmostEqual(control.config.rotation, ang_vel[2], delta=0.2)
        print(lin_vel, ang_vel)
        self._timeline.stop()
        test_app.stop()
        test_app = None
        self._re_bridge.destroy_application()
        pass

    async def test_diffbase_str(self):
        (result, error) = await load_test_file(self._nucleus_path + "/Robots/STR/STR_V4_Physics_Caster_Sensors.usda")

        # (result, error) = await load_test_file(self._dc_extension_path + "/data/usd/robots/str/str_physics.usd")
        # Make sure the stage loaded
        self.assertTrue(result)
        stage = self._usd_context.get_stage()
        path = omni.kit.utils.get_stage_next_free_path(stage, "/REB_DifferentialBase", True)
        prim = REBSchema.RobotEngineDifferentialBase.Define(stage, path)
        setup_base_prim(prim)

        prim.CreateInputComponentAttr("input")
        prim.CreateInputChannelAttr("base_command")

        prim.CreateOutputComponentAttr("output")
        prim.CreateOutputChannelAttr("base_state")

        prim.CreateChassisPrimRel().SetTargets(["/STR_V4"])
        prim.CreateLeftWheelJointNameAttr("left_wheel_joint")
        prim.CreateRightWheelJointNameAttr("right_wheel_joint")
        prim.CreateRobotFrontAttr((1, 0, 0))
        prim.CreateMaxSpeedAttr((2.0, 4.0))
        prim.CreateMaxTimeWithoutCommandAttr(0.2)
        prim.CreateAccelerationSmoothingAttr(1.0)
        prim.CreateWheelRadiusAttr(0.08)
        prim.CreateWheelBaseAttr(0.28963)
        self._timeline.play()
        ELEMENT_TYPE_F64 = 3
        await omni.kit.app.get_app().next_update_async()
        art = self._dc.get_articulation("/STR_V4")
        self.assertNotEqual(art, _dynamic_control.INVALID_HANDLE)
        root_body_ptr = self._dc.get_articulation_root_body(art)

        class ConstantDiffBaseControl(Codelet):
            """
            Publish constant speed command
            """

            def start(self):
                self.tx = self.isaac_proto_tx("StateProto", "cmd")
                self.tick_periodically(0.05)

            def tick(self):
                tx_message = self.tx.init()
                pack = tx_message.proto.pack
                pack.elementType = ELEMENT_TYPE_F64
                sizes = pack.init("sizes", 3)
                sizes[0] = 1
                sizes[1] = 1
                sizes[2] = 2
                pack.scanlineStride = 0
                pack.dataBufferIndex = 0
                tx_message.buffers = [np.array([self.config.linear, self.config.rotation])]
                self.tx.publish()

        test_app = PyaliceApp()
        test_app.app.load(
            filename=self._reb_extension_path + "/data/config/navsim_tcp.subgraph.json", prefix="simulation"
        )
        sim_in = test_app.app.nodes["simulation.interface"]["input"]

        control = test_app.app.add("controller").add(ConstantDiffBaseControl, name="ConstantDiffBaseControl")
        # Convert the velocity to cm/s
        control.config.linear = 0.5
        control.config.rotation = 0.0
        test_app.app.connect(control, "cmd", sim_in, "base_command")
        test_app.start()
        # Run test for a while
        await self.simulate(3)

        lin_vel = self._dc.get_rigid_body_linear_velocity(root_body_ptr)
        self.assertAlmostEqual(
            control.config.linear, np.linalg.norm([lin_vel.x, lin_vel.y, lin_vel.z]) / 100.0, delta=0.2
        )

        control.config.linear = 0.0
        await self.simulate(1)
        print(lin_vel)
        control.config.rotation = 1.0
        await self.simulate(4)
        ang_vel = self._dc.get_rigid_body_angular_velocity(root_body_ptr)
        print(ang_vel)
        self.assertAlmostEqual(control.config.rotation, ang_vel[2], delta=0.2)
        self._timeline.stop()
        test_app.stop()
        test_app = None

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
        await self.simulate(1)
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
        await self.simulate(4)

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
        await self.simulate(1)
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
        await self.simulate(5)

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
        await self.simulate(1)

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
