# NOTE:
#   omni.kit.test - std python's unittest module with additional wrapping to add suport for async/await tests
#   For most things refer to unittest docs: https://docs.python.org/3/library/unittest.html
import omni.kit.test

import omni.kit.usd
import carb.tokens
import gc

# Import extension python module we are testing with absolute import path, as if we are external user (other extension)
from omni.isaac.dynamic_control import _dynamic_control

from omni.isaac.utils.scripts.nucleus_utils import find_nucleus_server
from omni.isaac.pyalice import Message
from pxr import UsdPhysics, Sdf
from .common import PyaliceApp, create_application, simulate


# Having a test class dervived from omni.kit.test.AsyncTestCase declared on the root of module will make it auto-discoverable by omni.kit.test
class TestREBPyaliceScenario(omni.kit.test.AsyncTestCaseFailOnLogError):
    # Before running each test
    async def setUp(self):
        await omni.usd.get_context().new_stage_async()
        context = omni.usd.get_context()
        self._stage = context.get_stage()
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

    async def test_actor_spawner(self):

        result, prim = omni.kit.commands.execute(
            "CreateRobotEngineBridgeScenarioFromMessageCommand",
            path="/REB_ScenarioFromMessage",
            parent=None,
            input_component="input",
            input_channel="scenario_actors",
            teleport_input_component="input",
            teleport_input_channel="teleport",
            rigid_body_sink_output_component="output",
            rigid_body_sink_output_channel="bodies",
        )
        self.assertTrue(result)
        UsdPhysics.Scene.Define(self._stage, Sdf.Path("/World/physicsScene"))
        self._timeline.play()
        await omni.kit.app.get_app().next_update_async()

        test_app = PyaliceApp()
        test_app.app.load(
            filename=self._reb_extension_path + "/data/config/navsim_tcp.subgraph.json", prefix="simulation"
        )

        test_app.start()
        # Run test so tcp is connected
        await simulate(1)

        # Spawn actors
        msg = Message.create_message_builder("ActorGroupProto")
        proto = msg.proto
        request = proto.init("spawnRequests", 2)
        actor = request[0]
        actor.name = "World/cracker_box"
        actor.prefab = self._nucleus_path + "/Props/YCB/Axis_Aligned/003_cracker_box.usd"
        actor.pose.translation.x = 0.5
        actor = request[1]
        actor.name = "World/power_drill"
        actor.prefab = self._nucleus_path + "/Props/YCB/Axis_Aligned/035_power_drill.usd"
        actor.pose.translation.z = 0.5
        actor.pose.rotation.q.w = 0.707
        actor.pose.rotation.q.x = 0.707
        test_app.app.publish("simulation.interface", "input", "scenario_actors", msg)

        # Verify actors are created
        await simulate(1.0)
        cracker_box = self._stage.GetPrimAtPath("/World/cracker_box")
        self.assertIsNotNone(cracker_box)
        self.assertTrue(cracker_box.GetAttribute("xformOp:translate").Get() == (50, 0, 0))
        self.assertTrue(cracker_box.GetAttribute("xformOp:rotateXYZ").Get() == (0, 0, 0))

        power_drill = self._stage.GetPrimAtPath("/World/power_drill")
        self.assertIsNotNone(power_drill)
        self.assertTrue(power_drill.GetAttribute("xformOp:translate").Get() == (0, 0, 50))
        self.assertAlmostEqual(power_drill.GetAttribute("xformOp:rotateXYZ").Get()[0], 90, delta=0.02)

        # Teleport
        msg = Message.create_message_builder("RigidBody3GroupProto")
        proto = msg.proto
        bodies = proto.init("bodies", 1)
        bodies[0].refTBody.translation.x = -1.0
        bodies[0].scales.x = 1.0
        bodies[0].scales.y = 1.0
        bodies[0].scales.z = 1.0
        names = proto.init("names", 1)
        names[0] = "World/cracker_box"
        test_app.app.publish("simulation.interface", "input", "teleport", msg)

        await simulate(0.2)
        # check that the prim moved as a result of teleport
        self.assertTrue(cracker_box.GetAttribute("xformOp:translate").Get() == (-100, 0, 0))

        # Rigidbody Sink
        msg = test_app.app.receive("simulation.interface", "output", "bodies")
        self.assertTrue(msg)
        self.assertAlmostEqual(msg.proto.bodies[0].refTBody.translation.x, -1.0, delta=0.001)

        # Destroy
        msg = Message.create_message_builder("ActorGroupProto")
        proto = msg.proto
        request = proto.init("destroyRequests", 1)
        request[0] = "World/cracker_box"
        test_app.app.publish("simulation.interface", "input", "scenario_actors", msg)
        await simulate(0.2)
        # cracker_box should return a null prim
        cracker_box = self._stage.GetPrimAtPath("/World/cracker_box")
        self.assertFalse(cracker_box)
        power_drill = self._stage.GetPrimAtPath("/World/power_drill")
        self.assertTrue(power_drill)

        self._timeline.stop()
        test_app.stop()
        test_app = None

        pass

    async def test_camera_switcher(self):

        self._stage.DefinePrim("/World/Camera_1", "Camera")
        self._stage.DefinePrim("/World/Camera_2", "Camera")

        vpi = omni.kit.viewport.get_viewport_interface()
        vpi.get_viewport_window().set_active_camera("/World/Camera_1")
        await omni.kit.app.get_app().next_update_async()
        self.assertEqual(vpi.get_viewport_window().get_active_camera(), "/World/Camera_1")

        test_app = PyaliceApp()
        test_app.app.load(
            filename=self._reb_extension_path + "/data/config/navsim_tcp.subgraph.json", prefix="simulation"
        )

        sim_input = test_app.app.nodes["simulation.interface"]["input"]
        test_app.app.load_module("json")
        camera_switch = test_app.app.add("camera_switch").add(test_app.app.registry.isaac.json.JsonMockup)
        camera_switch.config.tick_period = "10Hz"
        camera_switch.config.json_mock = {"camera_name": "/World/Camera_2"}
        camera_switch.config.num_successful_publishes = 10
        camera_switch.config.report_success = True
        test_app.app.connect(camera_switch, "json", sim_input, "camera_switch")
        test_app.start()

        self._timeline.play()
        await simulate(1.0)
        self.assertEqual(vpi.get_viewport_window().get_active_camera(), "/World/Camera_2")
        self._timeline.stop()
