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

from omni.isaac.core.utils.nucleus import get_assets_root_path
from omni.isaac.pyalice import Composite
from omni.isaac.core.utils.physics import simulate_async
from .common import PyaliceApp, create_application, create_physics_scene, add_cube

from pxr import Gf, UsdPhysics, PhysxSchema, PhysicsSchemaTools

# Having a test class dervived from omni.kit.test.AsyncTestCase declared on the root of module will make it auto-discoverable by omni.kit.test
class TestREBPyaliceContact(omni.kit.test.AsyncTestCase):
    # Before running each test
    async def setUp(self):
        await omni.usd.get_context().new_stage_async()
        self._timeline = omni.timeline.get_timeline_interface()
        self._usd_context = omni.usd.get_context()
        self._dc = _dynamic_control.acquire_dynamic_control_interface()
        self._stage = self._usd_context.get_stage()

        create_physics_scene(self._stage)

        ext_manager = omni.kit.app.get_app().get_extension_manager()
        ext_id = ext_manager.get_enabled_extension_id("omni.isaac.robot_engine_bridge")
        self._reb_extension_path = ext_manager.get_extension_path(ext_id)

        self._asset_path = self._reb_extension_path

        self._assets_root_path = get_assets_root_path()
        if self._assets_root_path is None:
            carb.log_error("Could not find Isaac Sim assets folder")
            return

        self.assertTrue(create_application()[1])

        # self._physics_rate = 60
        # carb.settings.get_settings().set_bool("/app/runLoops/main/rateLimitEnabled", True)
        # carb.settings.get_settings().set_int("/app/runLoops/main/rateLimitFrequency", int(self._physics_rate))
        # carb.settings.get_settings().set_int("/persistent/simulation/minFrameRate", int(self._physics_rate))

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

    async def test_contact_sensor(self):
        PhysicsSchemaTools.addGroundPlane(
            self._stage, "/World/groundPlane", "Z", 1500, Gf.Vec3f(0, 0, 0), Gf.Vec3f(0.5)
        )
        await omni.kit.app.get_app().next_update_async()
        cube_prim = add_cube(self._stage, "/cube", 100, (0, 0, 200), physics=True)
        await omni.kit.app.get_app().next_update_async()
        result, prim = omni.kit.commands.execute(
            "RobotEngineBridgeCreateContactMonitor",
            path="/REB_ContactMonitor",
            parent=None,
            output_component="output",
            output_channel="collision",
            target_prim_rel=[cube_prim.GetPrimPath()],
            ignored_prims_rel=None,
            force_threshold=0,
        )
        # because the contact report api schema is added after start, we need to reload physics to have this work.
        self._timeline.play()
        await omni.kit.app.get_app().next_update_async()
        self._timeline.stop()
        await omni.kit.app.get_app().next_update_async()
        self._timeline.play()
        await omni.kit.app.get_app().next_update_async()

        test_app = PyaliceApp()
        test_app.app.load(
            filename=self._reb_extension_path + "/data/config/navsim_tcp.subgraph.json", prefix="simulation"
        )
        # sim_in = test_app.app.nodes["simulation.interface"]["input"]
        # sim_out = test_app.app.nodes["simulation.interface"]["output"]

        test_app.start()
        # Run test so tcp is connected
        await simulate_async(3)
        collision_msg = test_app.app.receive("simulation.interface", "output", "collision")
        self.assertIsNotNone(collision_msg)
        self.assertEqual(collision_msg.proto.thisName, "/cube")

        self._timeline.stop()
        test_app.stop()
        test_app = None

        pass
