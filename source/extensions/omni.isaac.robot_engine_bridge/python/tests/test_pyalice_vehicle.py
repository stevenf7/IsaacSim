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

from omni.isaac.core.utils.stage import open_stage_async
from omni.isaac.core.utils.nucleus import get_assets_root_path
from .common import PyaliceApp, VehicleControl, create_application
from omni.isaac.core.utils.physics import simulate_async

# Having a test class dervived from omni.kit.test.AsyncTestCase declared on the root of module will make it auto-discoverable by omni.kit.test
class TestREBPyaliceVehicle(omni.kit.test.AsyncTestCase):
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
        gc.collect()
        pass

    # Test diffbase component that was loaded from usd
    async def test_basic_vehicle(self):
        (result, error) = await open_stage_async(
            self._assets_root_path + "/Isaac/Samples/Isaac_SDK/Robots/Basic_Vehicle_M_REB.usd"
        )
        # Make sure the stage loaded
        self.assertTrue(result)

        self._timeline.play()
        # settle the robot
        await simulate_async(1)

        self._pyalice_app.app.load(
            filename=self._reb_extension_path + "/data/config/navsim_tcp.subgraph.json", prefix="simulation"
        )
        sim_in = self._pyalice_app.app.nodes["simulation.interface"]["input"]
        sim_out = self._pyalice_app.app.nodes["simulation.interface"]["output"]

        control = self._pyalice_app.app.add("controller").add(VehicleControl, name="VehicleControl")
        self.assertIsNotNone(control)
        control.config.accelerator = 1.0
        control.config.steering = 0.0
        self._pyalice_app.app.connect(control, "cmd", sim_in, "vehicle_command")
        self._pyalice_app.start()
        # TODO: Check chassis linear velocity
        await simulate_async(10)
        # TODO: Compute analytical values to compare against
        control.config.accelerator = 0.0
        control.config.steering = 1.0
        await simulate_async(3)
        control.config.accelerator = 0.0
        control.config.steering = -1.0
        await simulate_async(3)

        # print(lin_vel, ang_vel)
        self._timeline.stop()
        self._pyalice_app.stop()
        pass
