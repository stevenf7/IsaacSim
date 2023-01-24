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
from .common import PyaliceApp, ConstantDiffBaseControl, BodyMonitor, get_selected_path, create_application
from omni.isaac.core.utils.physics import simulate_async
import omni.graph.core as og
from omni.isaac.core_nodes.scripts.utils import set_target_prims


# Having a test class dervived from omni.kit.test.AsyncTestCase declared on the root of module will make it auto-discoverable by omni.kit.test
class TestREBPyaliceDiffbase(omni.kit.test.AsyncTestCase):
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

        self._pyalice_app = PyaliceApp()
        pass

    # After running each test
    async def tearDown(self):
        self.assertTrue(omni.kit.commands.execute("RobotEngineBridgeDestroyApplication")[1])
        self._pyalice_app = None
        while omni.usd.get_context().get_stage_loading_status()[2] > 0:
            print("tearDown, assets still loading, waiting to finish...")
            await asyncio.sleep(1.0)
        # await omni.usd.get_context().new_stage_async()
        gc.collect()
        pass

    async def add_carter(self, path):
        from pxr import Gf, PhysicsSchemaTools

        assets_root_path = get_assets_root_path()
        if assets_root_path is None:
            carb.log_error("Could not find Isaac Sim assets folder")
            return
        stage = omni.usd.get_context().get_stage()
        prim = stage.DefinePrim(path, "Xform")
        prim.GetReferences().AddReference(assets_root_path + "/Isaac/Robots/Carter/carter_v1.usd")
        await omni.kit.app.get_app().next_update_async()
        PhysicsSchemaTools.addGroundPlane(stage, "/World/groundPlane", "Z", 1500, Gf.Vec3f(0, 0, -0.25), Gf.Vec3f(0.5))
        await omni.kit.app.get_app().next_update_async()
        return prim

    async def create_differential_base(self, graph_path, left_wheel, right_wheel, wheel_base=0.5, wheel_radius=0.24):
        try:
            keys = og.Controller.Keys
            (graph, nodes, _, _) = og.Controller.edit(
                {"graph_path": graph_path, "evaluator_name": "execution"},
                {
                    keys.CREATE_NODES: [
                        ("OnPlaybackTick", "omni.graph.action.OnPlaybackTick"),
                        ("ReadSimTime", "omni.isaac.core_nodes.IsaacReadSimulationTime"),
                        ("computeOdom", "omni.isaac.core_nodes.IsaacComputeOdometry"),
                        ("publishOdom", "omni.isaac.robot_engine_bridge.REBPublishDifferentialState"),
                        ("subscribeTwist", "omni.isaac.robot_engine_bridge.REBSubscribeDifferentialCommand"),
                        ("diffController", "omni.isaac.wheeled_robots.DifferentialController"),
                        ("artController", "omni.isaac.core_nodes.IsaacArticulationController"),
                    ],
                    keys.CONNECT: [
                        ("OnPlaybackTick.outputs:tick", "computeOdom.inputs:execIn"),
                        ("OnPlaybackTick.outputs:tick", "publishOdom.inputs:execIn"),
                        ("ReadSimTime.outputs:simulationTime", "publishOdom.inputs:timeStamp"),
                        ("computeOdom.outputs:angularVelocity", "publishOdom.inputs:angularVelocity"),
                        ("computeOdom.outputs:linearVelocity", "publishOdom.inputs:linearVelocity"),
                        ("OnPlaybackTick.outputs:tick", "subscribeTwist.inputs:execIn"),
                        ("OnPlaybackTick.outputs:tick", "artController.inputs:execIn"),
                        ("subscribeTwist.outputs:execOut", "diffController.inputs:execIn"),
                        ("subscribeTwist.outputs:linearVelocity", "diffController.inputs:linearVelocity"),
                        ("subscribeTwist.outputs:angularVelocity", "diffController.inputs:angularVelocity"),
                        ("diffController.outputs:effortCommand", "artController.inputs:effortCommand"),
                        ("diffController.outputs:positionCommand", "artController.inputs:positionCommand"),
                        ("diffController.outputs:velocityCommand", "artController.inputs:velocityCommand"),
                    ],
                    og.Controller.Keys.SET_VALUES: [
                        ("diffController.inputs:wheelRadius", wheel_radius),
                        ("diffController.inputs:wheelDistance", wheel_base),
                        ("artController.inputs:jointNames", [left_wheel, right_wheel]),
                        ("artController.inputs:usePath", False),
                    ],
                },
            )
        except Exception as e:
            print(e)

        set_target_prims(
            primPath=graph_path + "/computeOdom", inputName="inputs:chassisPrim", targetPrimPaths=["/carter"]
        )

        set_target_prims(
            primPath=graph_path + "/artController", inputName="inputs:targetPrim", targetPrimPaths=["/carter"]
        )

        pass

    async def test_diffbase_og_carter(self):
        carter_path = "/carter"
        carter = await self.add_carter(carter_path)
        await self.create_differential_base("/ActionGraph", "left_wheel", "right_wheel")
        self._timeline.play()
        # settle the robot
        await simulate_async(1)
        art = self._dc.get_articulation(carter_path)
        self.assertNotEqual(art, _dynamic_control.INVALID_HANDLE)

        self._pyalice_app.app.load(
            filename=self._reb_extension_path + "/data/config/navsim_tcp.subgraph.json", prefix="simulation"
        )
        sim_in = self._pyalice_app.app.nodes["simulation.interface"]["input"]
        sim_out = self._pyalice_app.app.nodes["simulation.interface"]["output"]

        control = self._pyalice_app.app.add("controller").add(ConstantDiffBaseControl, name="ConstantDiffBaseControl")
        # Convert the velocity to cm/s
        control.config.linear = 0.5
        control.config.rotation = 0.0
        self._pyalice_app.app.connect(control, "cmd", sim_in, "base_command")
        monitor = self._pyalice_app.app.add("monitor").add(BodyMonitor, name="BodyMonitor")
        monitor.config.linear_target = control.config.linear
        monitor.config.angular_target = control.config.rotation
        monitor.config.check = False
        self._pyalice_app.app.connect(sim_out, "bodies", monitor, "bodies")
        self._pyalice_app.app.connect(sim_out, "base_state", monitor, "state")
        self._pyalice_app.start()
        # Run test for 2 seconds, check the linear velocity
        await simulate_async(1)

        root_body_ptr = self._dc.get_articulation_root_body(art)
        lin_vel = self._dc.get_rigid_body_linear_velocity(root_body_ptr)
        self.assertAlmostEqual(control.config.linear, np.linalg.norm([lin_vel.x, lin_vel.y, lin_vel.z]), delta=0.2)
        self.assertEqual(monitor.config.check, True)

        control.config.linear = 0.0
        await simulate_async(2)

        lin_vel = self._dc.get_rigid_body_linear_velocity(root_body_ptr)
        self.assertAlmostEqual(control.config.linear, np.linalg.norm([lin_vel.x, lin_vel.y, lin_vel.z]), delta=0.2)

        control.config.rotation = 1.0
        monitor.config.linear_target = control.config.linear
        monitor.config.angular_target = control.config.rotation
        monitor.config.check = False
        await simulate_async(4)
        ang_vel = self._dc.get_rigid_body_angular_velocity(root_body_ptr)
        self.assertAlmostEqual(control.config.rotation, ang_vel[2], delta=0.2)
        self.assertEqual(monitor.config.check, True)

        self._timeline.stop()
        self._pyalice_app.stop()

        pass

    # Test diffbase component that was loaded from usd
    async def test_diffbase_carter(self):
        (result, error) = await open_stage_async(
            self._assets_root_path + "/Isaac/Samples/Isaac_SDK/Robots/Carter_REB.usd"
        )
        # Make sure the stage loaded
        self.assertTrue(result)

        self._timeline.play()
        # settle the robot
        await simulate_async(1)
        art = self._dc.get_articulation("/Carter")
        self.assertNotEqual(art, _dynamic_control.INVALID_HANDLE)

        self._pyalice_app.app.load(
            filename=self._reb_extension_path + "/data/config/navsim_tcp.subgraph.json", prefix="simulation"
        )
        sim_in = self._pyalice_app.app.nodes["simulation.interface"]["input"]
        sim_out = self._pyalice_app.app.nodes["simulation.interface"]["output"]

        control = self._pyalice_app.app.add("controller").add(ConstantDiffBaseControl, name="ConstantDiffBaseControl")
        # Convert the velocity to cm/s
        control.config.linear = 0.5
        control.config.rotation = 0.0
        self._pyalice_app.app.connect(control, "cmd", sim_in, "base_command")
        monitor = self._pyalice_app.app.add("monitor").add(BodyMonitor, name="BodyMonitor")
        monitor.config.linear_target = control.config.linear
        monitor.config.angular_target = control.config.rotation
        monitor.config.check = False
        self._pyalice_app.app.connect(sim_out, "bodies", monitor, "bodies")
        self._pyalice_app.app.connect(sim_out, "base_state", monitor, "state")
        self._pyalice_app.start()
        # Run test for 2 seconds, check the linear velocity
        await simulate_async(2)

        root_body_ptr = self._dc.get_articulation_root_body(art)
        lin_vel = self._dc.get_rigid_body_linear_velocity(root_body_ptr)
        self.assertAlmostEqual(
            control.config.linear, np.linalg.norm([lin_vel.x, lin_vel.y, lin_vel.z]) / 100.0, delta=0.2
        )
        self.assertEqual(monitor.config.check, True)

        control.config.linear = 0.0
        await simulate_async(2)

        lin_vel = self._dc.get_rigid_body_linear_velocity(root_body_ptr)
        self.assertAlmostEqual(
            control.config.linear, np.linalg.norm([lin_vel.x, lin_vel.y, lin_vel.z]) / 100.0, delta=0.2
        )

        control.config.rotation = 1.0
        monitor.config.linear_target = control.config.linear
        monitor.config.angular_target = control.config.rotation
        monitor.config.check = False
        await simulate_async(4)
        ang_vel = self._dc.get_rigid_body_angular_velocity(root_body_ptr)
        self.assertAlmostEqual(control.config.rotation, ang_vel[2], delta=0.2)
        self.assertEqual(monitor.config.check, True)
        # print(lin_vel, ang_vel)
        self._timeline.stop()
        self._pyalice_app.stop()
        pass

    # Creating a REB diffbase component from scratch
    async def test_diffbase_str(self):
        (result, error) = await open_stage_async(
            self._assets_root_path + "/Isaac/Robots/Transporter/transporter_sensors.usd"
        )

        # Make sure the stage loaded
        self.assertTrue(result)
        result, prim = omni.kit.commands.execute(
            "RobotEngineBridgeCreateDifferentialBase",
            path="/REB_DifferentialBase",
            parent=get_selected_path(),
            input_component="input",
            input_channel="base_command",
            output_component="output",
            output_channel="base_state",
            chassis_prim_rel=["/Transporter"],
            left_wheel_joint_name="left_wheel_joint",
            right_wheel_joint_name="right_wheel_joint",
            robot_front=(1, 0, 0),
            wheel_radius=0.08,
            wheel_base=0.28963,
            max_speed=(2.0, 4.0),
            time_without_command=0.2,
            acceleration_smoothing=1.0,
        )

        self._timeline.play()
        await omni.kit.app.get_app().next_update_async()
        art = self._dc.get_articulation("/Transporter")
        self.assertNotEqual(art, _dynamic_control.INVALID_HANDLE)
        root_body_ptr = self._dc.get_articulation_root_body(art)

        self._pyalice_app.app.load(
            filename=self._reb_extension_path + "/data/config/navsim_tcp.subgraph.json", prefix="simulation"
        )
        sim_in = self._pyalice_app.app.nodes["simulation.interface"]["input"]

        control = self._pyalice_app.app.add("controller").add(ConstantDiffBaseControl, name="ConstantDiffBaseControl")
        # Convert the velocity to cm/s
        control.config.linear = 0.5
        control.config.rotation = 0.0
        self._pyalice_app.app.connect(control, "cmd", sim_in, "base_command")
        self._pyalice_app.start()
        # Run test for a while
        await simulate_async(3)
        # check that we reached the target velocity
        lin_vel = self._dc.get_rigid_body_linear_velocity(root_body_ptr)
        self.assertAlmostEqual(
            control.config.linear, np.linalg.norm([lin_vel.x, lin_vel.y, lin_vel.z]) / 100.0, delta=0.2
        )
        # stop robot
        control.config.linear = 0.0
        await simulate_async(1)
        # check that we reached the target velocity
        lin_vel = self._dc.get_rigid_body_linear_velocity(root_body_ptr)
        self.assertAlmostEqual(
            control.config.linear, np.linalg.norm([lin_vel.x, lin_vel.y, lin_vel.z]) / 100.0, delta=0.2
        )
        # rotate in place
        control.config.rotation = 1.0
        await simulate_async(4)
        # check that we reached the target velocity
        ang_vel = self._dc.get_rigid_body_angular_velocity(root_body_ptr)
        self.assertAlmostEqual(control.config.rotation, ang_vel[2], delta=0.2)
        self._timeline.stop()
        self._pyalice_app.stop()

        pass
