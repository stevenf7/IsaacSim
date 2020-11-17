# NOTE:
#   omni.kit.test - std python's unittest module with additional wrapping to add suport for async/await tests
#   For most things refer to unittest docs: https://docs.python.org/3/library/unittest.html
import omni.kit.test
import omni.kit.asyncapi
import omni.kit.usd
import carb.tokens
import os
import asyncio
import numpy as np

# Import extension python module we are testing with absolute import path, as if we are external user (other extension)
import omni.isaac.RobotEngineBridgeSchema as REBSchema
from omni.isaac.robot_engine_bridge import _robot_engine_bridge
from omni.isaac.dynamic_control import _dynamic_control

from omni.isaac.utils.scripts.test_utils import load_test_file
from .common import PyaliceApp, get_json_data_path, setup_base_prim
from omni.isaac.pyalice import Codelet

# Having a test class dervived from omni.kit.test.AsyncTestCase declared on the root of module will make it auto-discoverable by omni.kit.test
class TestREBPyalice(omni.kit.test.AsyncTestCase):
    # Before running each test
    async def setUp(self):
        await omni.kit.asyncapi.new_stage()
        self._timeline = omni.timeline.get_timeline_interface()
        self._usd_context = omni.usd.get_context()
        self._dc = _dynamic_control.acquire_dynamic_control_interface()
        self._re_bridge = _robot_engine_bridge.acquire_robot_engine_bridge_interface()

        self._asset_path = os.path.abspath(
            carb.tokens.get_tokens_interface().resolve("${app}/../exts/omni.isaac.robot_engine_bridge/")
        )

        pass

    # After running each test
    async def tearDown(self):
        pass

    def create_application(self):
        json_path = os.path.abspath(
            carb.tokens.get_tokens_interface().resolve(
                "${app}/../exts/omni.isaac.robot_engine_bridge/resources/isaac_engine/json/isaacsim.app.json"
            )
        )

        print("create application with: ", self._asset_path, json_path)
        self._re_bridge.create_application(self._asset_path, json_path, [], [])

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
        (result, error) = await load_test_file("assets/robots/carter/carter.usd")
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
        self.create_application()
        self._timeline.play()
        ELEMENT_TYPE_F64 = 3
        await omni.kit.asyncapi.next_update()
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
        test_app.app.load(filename=get_json_data_path("navsim_tcp.subgraph.json"), prefix="simulation")
        sim_in = test_app.app.nodes["simulation.interface"]["input"]

        control = test_app.app.add("controller").add(ConstantDiffBaseControl, name="ConstantDiffBaseControl")
        # Convert the velocity to cm/s
        control.config.linear = 0.5
        control.config.rotation = 0.0
        test_app.app.connect(control, "cmd", sim_in, "base_command")
        test_app.start()
        # Run test for a while
        await asyncio.sleep(1.0)

        lin_vel = self._dc.get_rigid_body_linear_velocity(root_body_ptr)
        self.assertAlmostEqual(
            control.config.linear, np.linalg.norm([lin_vel.x, lin_vel.y, lin_vel.z]) / 100.0, delta=0.01
        )

        control.config.linear = 0.0
        await asyncio.sleep(1.0)

        control.config.rotation = 4.0
        await asyncio.sleep(2.0)
        ang_vel = self._dc.get_rigid_body_angular_velocity(root_body_ptr)
        self.assertAlmostEqual(control.config.rotation, ang_vel[2], delta=0.1)
        print(lin_vel, ang_vel)
        self._timeline.stop()
        test_app.stop()
        self._re_bridge.destroy_application()
        pass

    async def test_diffbase_str(self):
        (result, error) = await load_test_file("tests/robots/str/str_physics.usd")
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

        prim.CreateChassisPrimRel().SetTargets(["/World"])
        prim.CreateLeftWheelJointNameAttr("left_wheel_joint")
        prim.CreateRightWheelJointNameAttr("right_wheel_joint")
        prim.CreateRobotFrontAttr((1, 0, 0))
        prim.CreateMaxSpeedAttr((2.0, 4.0))
        prim.CreateMaxTimeWithoutCommandAttr(0.2)
        prim.CreateAccelerationSmoothingAttr(1.0)
        prim.CreateWheelRadiusAttr(0.08)
        prim.CreateWheelBaseAttr(0.28963)
        self.create_application()
        self._timeline.play()
        ELEMENT_TYPE_F64 = 3
        await omni.kit.asyncapi.next_update()
        art = self._dc.get_articulation("/World")
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
        test_app.app.load(filename=get_json_data_path("navsim_tcp.subgraph.json"), prefix="simulation")
        sim_in = test_app.app.nodes["simulation.interface"]["input"]

        control = test_app.app.add("controller").add(ConstantDiffBaseControl, name="ConstantDiffBaseControl")
        # Convert the velocity to cm/s
        control.config.linear = 0.5
        control.config.rotation = 0.0
        test_app.app.connect(control, "cmd", sim_in, "base_command")
        test_app.start()
        # Run test for a while
        await asyncio.sleep(3.0)

        lin_vel = self._dc.get_rigid_body_linear_velocity(root_body_ptr)
        self.assertAlmostEqual(
            control.config.linear, np.linalg.norm([lin_vel.x, lin_vel.y, lin_vel.z]) / 100.0, delta=0.1
        )

        control.config.linear = 0.0
        await asyncio.sleep(1.0)
        print(lin_vel)
        control.config.rotation = 2.0
        await asyncio.sleep(2.0)
        ang_vel = self._dc.get_rigid_body_angular_velocity(root_body_ptr)
        print(ang_vel)
        self.assertAlmostEqual(control.config.rotation, ang_vel[2], delta=0.1)
        self._timeline.stop()
        test_app.stop()
        self._re_bridge.destroy_application()
        pass
