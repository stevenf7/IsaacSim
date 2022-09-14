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

import gxf
import gxf.std.vault
import gxf.accessor
import gxf.core

from omni.isaac.dynamic_control import _dynamic_control

from omni.isaac.core.utils.stage import open_stage_async
from omni.isaac.core.utils.nucleus import get_assets_root_path
from omni.isaac.core.utils.physics import simulate_async
import omni.kit.usd
import carb
import gc

# Having a test class dervived from omni.kit.test.AsyncTestCase declared on the root of module will make it auto-discoverable by omni.kit.test
class TestGXFVehicle(omni.kit.test.AsyncTestCase):
    # Before running each test
    async def setUp(self):
        await omni.usd.get_context().new_stage_async()
        self._timeline = omni.timeline.get_timeline_interface()
        self._usd_context = omni.usd.get_context()
        self._stage = self._usd_context.get_stage()
        self._dc = _dynamic_control.acquire_dynamic_control_interface()
        ext_manager = omni.kit.app.get_app().get_extension_manager()
        ext_id = ext_manager.get_enabled_extension_id("omni.isaac.gxf_bridge")
        self._reb_extension_path = ext_manager.get_extension_path(ext_id)

        self._assets_root_path = get_assets_root_path()
        if self._assets_root_path is None:
            carb.log_error("Could not find Isaac Sim assets folder")
            return

        self._physics_rate = 60
        carb.settings.get_settings().set_bool("/app/runLoops/main/rateLimitEnabled", True)
        carb.settings.get_settings().set_int("/app/runLoops/main/rateLimitFrequency", int(self._physics_rate))
        carb.settings.get_settings().set_int("/persistent/simulation/minFrameRate", int(self._physics_rate))

        await omni.kit.app.get_app().next_update_async()
        pass

    # After running each test
    async def tearDown(self):
        await omni.kit.app.get_app().next_update_async()
        gc.collect()
        pass

    # Create and destroy the app
    async def test_drive_forward(self):
        result, status = omni.kit.commands.execute(
            "RobotEngineBridgeGxfCreateApplication",
            base_path=self._reb_extension_path + "/lib",
            manifest_file="manifest.yaml",
            graph_files=[
                f"{self._reb_extension_path}/data/test/vehicle_control_forward.yaml",
                self._reb_extension_path + "/data/config/isaac_sim_allocator.yaml",
            ],
        )

        (result, error) = await open_stage_async(
            self._assets_root_path + "/Isaac/Samples/Isaac_SDK/Robots/Basic_Vehicle_M_REB.usd"
        )
        # Make sure the stage loaded
        self.assertTrue(result)
        self._timeline.play()
        await omni.kit.app.get_app().next_update_async()
        handle = self._dc.get_rigid_body("/World/basic_vehicle_m/WizardVehicle1/Vehicle")

        pos = self._dc.get_rigid_body_pose(handle).p
        vel = self._dc.get_rigid_body_linear_velocity(handle)
        self.assertAlmostEqual(pos.x, 0.0, delta=0.1)
        self.assertAlmostEqual(vel.x, 0.0, delta=0.1)
        await simulate_async(10)
        pos = self._dc.get_rigid_body_pose(handle).p
        vel = self._dc.get_rigid_body_linear_velocity(handle)
        self.assertGreater(pos.x, 4.0)
        self.assertAlmostEqual(vel.x, 1.0, delta=0.1)
        self._timeline.stop()
        result, status = omni.kit.commands.execute("RobotEngineBridgeGxfDestroyApplication")
