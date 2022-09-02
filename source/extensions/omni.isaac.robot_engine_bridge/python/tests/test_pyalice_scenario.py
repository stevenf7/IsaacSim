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
import gc
import asyncio

# Import extension python module we are testing with absolute import path, as if we are external user (other extension)
from omni.isaac.dynamic_control import _dynamic_control

from omni.isaac.core.utils.nucleus import get_assets_root_path
from omni.isaac.pyalice import Message
from omni.kit.viewport.utility import get_active_viewport
from .common import PyaliceApp, create_application, add_cube, create_physics_scene
from omni.isaac.core.utils.physics import simulate_async

# Having a test class dervived from omni.kit.test.AsyncTestCase declared on the root of module will make it auto-discoverable by omni.kit.test
class TestREBPyaliceScenario(omni.kit.test.AsyncTestCase):
    # Before running each test
    async def setUp(self):
        await omni.usd.get_context().new_stage_async()
        context = omni.usd.get_context()
        self._stage = context.get_stage()
        self._timeline = omni.timeline.get_timeline_interface()
        self._usd_context = omni.usd.get_context()
        self._dc = _dynamic_control.acquire_dynamic_control_interface()
        create_physics_scene(self._stage)
        ext_manager = omni.kit.app.get_app().get_extension_manager()
        ext_id = ext_manager.get_enabled_extension_id("omni.isaac.robot_engine_bridge")
        self._reb_extension_path = ext_manager.get_extension_path(ext_id)
        ext_id = ext_manager.get_enabled_extension_id("omni.isaac.dynamic_control")
        self._dc_extension_path = ext_manager.get_extension_path(ext_id)

        self._asset_path = self._reb_extension_path

        self._assets_root_path = get_assets_root_path()
        if self._assets_root_path is None:
            carb.log_error("Could not find Isaac Sim assets folder")
            return

        self.assertTrue(create_application()[1])
        pass

    # After running each test
    async def tearDown(self):
        self.assertTrue(omni.kit.commands.execute("RobotEngineBridgeDestroyApplication")[1])
        # In some cases the test will end before the asset is loaded, in this case wait for assets to load
        while omni.usd.get_context().get_stage_loading_status()[2] > 0:
            print("tearDown, assets still loading, waiting to finish...")
            await asyncio.sleep(1.0)
        gc.collect()
        pass

    async def test_actor_spawner(self):

        result, prim = omni.kit.commands.execute(
            "RobotEngineBridgeCreateScenarioFromMessage",
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

        self._timeline.play()
        await omni.kit.app.get_app().next_update_async()

        test_app = PyaliceApp()
        test_app.app.load(
            filename=self._reb_extension_path + "/data/config/navsim_tcp.subgraph.json", prefix="simulation"
        )

        test_app.start()
        # Run test so tcp is connected
        await simulate_async(1)

        # Spawn actors
        msg = Message.create_message_builder("ActorGroupProto")
        proto = msg.proto
        request = proto.init("spawnRequests", 2)
        actor = request[0]
        actor.name = "World/cracker_box"
        actor.prefab = self._assets_root_path + "/Isaac/Props/YCB/Axis_Aligned/003_cracker_box.usd"
        actor.pose.translation.x = 0.5
        actor = request[1]
        actor.name = "World/power_drill"
        actor.prefab = self._assets_root_path + "/Isaac/Props/YCB/Axis_Aligned/035_power_drill.usd"
        actor.pose.translation.z = 0.5
        actor.pose.rotation.q.w = 0.707
        actor.pose.rotation.q.x = 0.707
        test_app.app.publish("simulation.interface", "input", "scenario_actors", msg)

        # Verify actors are created
        await simulate_async(1.0)
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

        await simulate_async(0.2)
        # check that the prim moved as a result of teleport
        self.assertTrue(cracker_box.GetAttribute("xformOp:translate").Get() == (-100, 0, 0))

        # Rigidbody Sink
        msg = test_app.app.receive("simulation.interface", "output", "bodies")
        self.assertTrue(msg)
        self.assertAlmostEqual(msg.proto.bodies[0].refTBody.translation.x, -1.0, delta=0.001)

        # Wait for prims to completeley load before deleting
        while omni.usd.get_context().get_stage_loading_status()[2] > 0:
            await omni.kit.app.get_app().next_update_async()
        await omni.kit.app.get_app().next_update_async()
        # Destroy
        msg = Message.create_message_builder("ActorGroupProto")
        proto = msg.proto
        request = proto.init("destroyRequests", 2)
        request[0] = "/World/cracker_box"
        request[1] = "World/power_drill"  # Paths are converted to absolute, so both / and no / should work
        test_app.app.publish("simulation.interface", "input", "scenario_actors", msg)
        await simulate_async(0.2)
        # cracker_box should return a null prim
        cracker_box = self._stage.GetPrimAtPath("/World/cracker_box")
        self.assertFalse(cracker_box)
        power_drill = self._stage.GetPrimAtPath("/World/power_drill")
        self.assertFalse(power_drill)

        self._timeline.stop()
        test_app.stop()
        test_app = None

        pass

    async def test_sink_manual(self):
        cube_prim = add_cube(self._stage, "/cube", 100, (0, 0, 10))
        result, prim = omni.kit.commands.execute(
            "RobotEngineBridgeCreateRigidBodySink",
            path="/REB_RigidBodySink",
            parent=None,
            enabled=False,
            output_component="output",
            output_channel="bodies",
            rigid_body_prims_rel=["/cube"],
        )

        self.assertTrue(result)

        self._timeline.play()
        await omni.kit.app.get_app().next_update_async()

        test_app = PyaliceApp()
        test_app.app.load(
            filename=self._reb_extension_path + "/data/config/navsim_tcp.subgraph.json", prefix="simulation"
        )

        test_app.start()
        # Run test so tcp is connected
        await simulate_async(1)

        # Rigidbody Sink is disabled to start
        msg = test_app.app.receive("simulation.interface", "output", "bodies")
        self.assertFalse(msg)
        # Publish data manually
        self.assertTrue(omni.kit.commands.execute("RobotEngineBridgeTickComponent", path="/REB_RigidBodySink")[1])
        # move cube and simulate time so that message is received
        # This also makes sure that the component isn't publishing the pose while simulating
        cube_prim.GetAttribute("xformOp:translate").Set((100, 100, 100))
        await simulate_async(0.5)
        # Check that we got a message
        msg = test_app.app.receive("simulation.interface", "output", "bodies")
        self.assertTrue(msg)
        self.assertAlmostEqual(msg.proto.bodies[0].refTBody.translation.z, 0.1, delta=0.001)
        # publish again, now we will get latest pose
        self.assertTrue(omni.kit.commands.execute("RobotEngineBridgeTickComponent", path="/REB_RigidBodySink")[1])

        await simulate_async(0.5)
        msg = test_app.app.receive("simulation.interface", "output", "bodies")
        self.assertTrue(msg)
        self.assertAlmostEqual(msg.proto.bodies[0].refTBody.translation.z, 1.0, delta=0.001)

        self._timeline.stop()
        test_app.stop()
        test_app = None

        pass

    async def test_sink_batch(self):
        rel_list = []
        num_cubes = 100
        for p in range(num_cubes):
            cube_prim = add_cube(self._stage, f"/cube_{p}", 100, (0, 0, 10))
            rel_list.append(cube_prim.GetPath())

        result, prim = omni.kit.commands.execute(
            "RobotEngineBridgeCreateRigidBodySink",
            path="/REB_RigidBodySink",
            parent=None,
            enabled=True,
            output_component="output",
            output_channel="bodies",
            rigid_body_prims_rel=rel_list,
        )

        self.assertTrue(result)

        self._timeline.play()
        await omni.kit.app.get_app().next_update_async()

        test_app = PyaliceApp()
        test_app.app.load(
            filename=self._reb_extension_path + "/data/config/navsim_tcp.subgraph.json", prefix="simulation"
        )

        test_app.start()
        # Run test so tcp is connected
        await simulate_async(1)
        # Check that we got a message
        msg = test_app.app.receive("simulation.interface", "output", "bodies")

        self.assertTrue(msg)
        # Check that the number of bodies in the message matches what we expect
        self.assertEqual(len(msg.proto.bodies), num_cubes)

        self._timeline.stop()
        test_app.stop()
        test_app = None

        pass

    # This test is failing currently, need to investigate and file a bug
    # async def test_actor_spawner_dynamic(self):
    #     result, prim = omni.kit.commands.execute(
    #         "RobotEngineBridgeCreateScenarioFromMessage",
    #         path="/REB_ScenarioFromMessage",
    #         parent=None,
    #         input_component="input",
    #         input_channel="scenario_actors",
    #         teleport_input_component="input",
    #         teleport_input_channel="teleport",
    #         rigid_body_sink_output_component="output",
    #         rigid_body_sink_output_channel="bodies",
    #     )
    #     self.assertTrue(result)
    #     self._timeline.play()
    #     await omni.kit.app.get_app().next_update_async()

    #     test_app = PyaliceApp()
    #     test_app.app.load(
    #         filename=self._reb_extension_path + "/data/config/navsim_tcp.subgraph.json", prefix="simulation"
    #     )

    #     test_app.start()
    #     # Run test so tcp is connected
    #     await simulate_async(1)

    #     # Spawn actors
    #     msg = Message.create_message_builder("ActorGroupProto")
    #     proto = msg.proto
    #     request = proto.init("spawnRequests", 3)
    #     actor = request[0]
    #     actor.name = "/World/bin_1"
    #     actor.prefab = self._assets_root_path + "/Isaac/Props/KLT_Bin/small_KLT.usd"
    #     actor.pose.translation.x = 0.6
    #     actor.pose.translation.y = -0.5
    #     actor.pose.translation.z = 0.2
    #     actor = request[1]
    #     actor.name = "/World/bin_2"
    #     actor.prefab = self._assets_root_path + "/Isaac/Props/KLT_Bin/small_KLT.usd"
    #     actor.pose.translation.x = 0.6
    #     actor.pose.translation.y = 0.5
    #     actor.pose.translation.z = 0.2
    #     # actor.pose.rotation.q.w = 0.707
    #     # actor.pose.rotation.q.x = 0.707
    #     actor = request[2]
    #     actor.name = "/World/bin_3"
    #     actor.prefab = self._assets_root_path + "/Isaac/Props/KLT_Bin/small_KLT.usd"
    #     actor.pose.translation.x = 1.0
    #     actor.pose.translation.y = -0.5
    #     actor.pose.translation.z = 0.2
    #     # actor.pose.rotation.q.w = 0.707
    #     # actor.pose.rotation.q.x = 0.707
    #     test_app.app.publish("simulation.interface", "input", "scenario_actors", msg)

    #     # Verify actors are created
    #     await simulate_async(1.0)
    #     # cracker_box = self._stage.GetPrimAtPath("/World/cracker_box")
    #     # self.assertIsNotNone(cracker_box)
    #     # self.assertTrue(cracker_box.GetAttribute("xformOp:translate").Get() == (50, 0, 0))
    #     # self.assertTrue(cracker_box.GetAttribute("xformOp:rotateXYZ").Get() == (0, 0, 0))

    #     # power_drill = self._stage.GetPrimAtPath("/World/power_drill")
    #     # self.assertIsNotNone(power_drill)
    #     # self.assertTrue(power_drill.GetAttribute("xformOp:translate").Get() == (0, 0, 50))
    #     # self.assertAlmostEqual(power_drill.GetAttribute("xformOp:rotateXYZ").Get()[0], 90, delta=0.02)

    #     # # Teleport
    #     # msg = Message.create_message_builder("RigidBody3GroupProto")
    #     # proto = msg.proto
    #     # bodies = proto.init("bodies", 1)
    #     # bodies[0].refTBody.translation.x = -1.0
    #     # bodies[0].scales.x = 1.0
    #     # bodies[0].scales.y = 1.0
    #     # bodies[0].scales.z = 1.0
    #     # names = proto.init("names", 1)
    #     # names[0] = "World/cracker_box"
    #     # test_app.app.publish("simulation.interface", "input", "teleport", msg)

    #     # await simulate_async(0.2)
    #     # # check that the prim moved as a result of teleport
    #     # self.assertTrue(cracker_box.GetAttribute("xformOp:translate").Get() == (-100, 0, 0))

    #     # # Rigidbody Sink
    #     # msg = test_app.app.receive("simulation.interface", "output", "bodies")
    #     # self.assertTrue(msg)
    #     # self.assertAlmostEqual(msg.proto.bodies[0].refTBody.translation.x, -1.0, delta=0.001)

    #     # # Destroy
    #     # msg = Message.create_message_builder("ActorGroupProto")
    #     # proto = msg.proto
    #     # request = proto.init("destroyRequests", 1)
    #     # request[0] = "World/cracker_box"
    #     # test_app.app.publish("simulation.interface", "input", "scenario_actors", msg)
    #     # await simulate_async(0.2)
    #     # # cracker_box should return a null prim
    #     # cracker_box = self._stage.GetPrimAtPath("/World/cracker_box")
    #     # self.assertFalse(cracker_box)
    #     # power_drill = self._stage.GetPrimAtPath("/World/power_drill")
    #     # self.assertTrue(power_drill)

    #     self._timeline.stop()
    #     test_app.stop()
    #     test_app = None

    async def test_camera_switcher(self):

        self._stage.DefinePrim("/World/Camera_1", "Camera")
        self._stage.DefinePrim("/World/Camera_2", "Camera")

        viewport_api = get_active_viewport()
        viewport_api.set_active_camera("/World/Camera_1")
        await omni.kit.app.get_app().next_update_async()
        self.assertEqual(viewport_api.get_active_camera(), "/World/Camera_1")

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
        await simulate_async(1.0)
        self.assertEqual(vpi.get_viewport_window().get_active_camera(), "/World/Camera_2")
        self._timeline.stop()
