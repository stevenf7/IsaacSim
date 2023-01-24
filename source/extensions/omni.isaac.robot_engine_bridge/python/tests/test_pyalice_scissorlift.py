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
class TestREBPyaliceScissorLift(omni.kit.test.AsyncTestCase):
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

    async def test_scissorlift(self):
        (result, error) = await open_stage_async(
            self._assets_root_path + "/Isaac/Samples/Isaac_SDK/Robots/Transporter_REB.usd"
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
        test_app.app.load_module("message_generators")
        self.generator = test_app.app.add("commander").add(
            test_app.app.registry.isaac.message_generators.DifferentialBaseControlGenerator
        )
        test_app.app.connect(
            self.generator, "command", test_app.app.nodes["simulation.interface"]["input"], "lift_command"
        )
        self.generator.config.tick_period = "100Hz"
        self.generator.config.angular_speed = 0.0
        self.generator.config.linear_speed = 0.0

        test_app.start()
        # Run test so tcp is connected
        await simulate_async(1)
        lift_msg = test_app.app.receive("simulation.interface", "output", "lift_state")
        self.assertIsNotNone(lift_msg)
        self.assertEqual(lift_msg.tensor[0], -1)
        self.assertEqual(lift_msg.tensor[1], 0)

        self.generator.config.linear_speed = 1.0
        await simulate_async(3)
        lift_msg = test_app.app.receive("simulation.interface", "output", "lift_state")
        self.assertIsNotNone(lift_msg)
        self.assertEqual(lift_msg.tensor[0], 1)
        self.assertAlmostEqual(lift_msg.tensor[1], 4.0, delta=0.1)
        # check that the lift is at the correct height
        art = self._dc.get_articulation("/Transporter")
        self.assertNotEqual(art, _dynamic_control.INVALID_HANDLE)
        dof_ptr = self._dc.find_articulation_dof(art, "lift_joint")
        dof_pos = self._dc.get_dof_position(dof_ptr)
        self.assertAlmostEqual(dof_pos, 4.0, delta=0.1)

        self._timeline.stop()
        test_app.stop()
        test_app = None
        pass
