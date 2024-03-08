# Copyright (c) 2018-2023, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

import carb
import carb.tokens
import numpy as np

# NOTE:
#   omni.kit.test - std python's unittest module with additional wrapping to add suport for async/await tests
#   For most things refer to unittest docs: https://docs.python.org/3/library/unittest.html
import omni.kit.test
from omni.isaac.core.prims.rigid_prim import RigidPrim
from omni.isaac.core.utils.stage import get_current_stage, open_stage_async
from omni.isaac.nucleus import get_assets_root_path_async
from pxr import Usd


# Having a test class dervived from omni.kit.test.AsyncTestCase declared on the root of module will make it auto-discoverable by omni.kit.test
class TestJetRacer(omni.kit.test.AsyncTestCase):
    # Before running each test
    async def setUp(self):
        self._timeline = omni.timeline.get_timeline_interface()

        ext_manager = omni.kit.app.get_app().get_extension_manager()

        self._physics_rate = 60
        carb.settings.get_settings().set_bool("/app/runLoops/main/rateLimitEnabled", True)
        carb.settings.get_settings().set_int("/app/runLoops/main/rateLimitFrequency", int(self._physics_rate))
        carb.settings.get_settings().set_int("/persistent/simulation/minFrameRate", int(self._physics_rate))

        pass

    # After running each test
    async def tearDown(self):
        await omni.kit.app.get_app().next_update_async()
        # In some cases the test will end before the asset is loaded, in this case wait for assets to load
        while omni.usd.get_context().get_stage_loading_status()[2] > 0:
            await omni.kit.app.get_app().next_update_async()

        pass

    # Actual test, notice it is "async" function, so "await" can be used if needed
    async def test_jetracer_loading(self):
        assets_root_path = await get_assets_root_path_async()
        if assets_root_path is None:
            carb.log_error("Could not find Isaac Sim assets folder")
            return

        self.usd_path = assets_root_path + "/Isaac/Robots/Jetracer/jetracer.usd"
        (result, error) = await open_stage_async(self.usd_path)
        # Make sure the stage loaded
        self.assertTrue(result)

        # Start Simulation and tick a few
        self._timeline.play()
        for frame in range(10):
            await omni.kit.app.get_app().next_update_async()

        # get the jetracer
        vehicle_path = "/World/Jetracer/Vehicle"
        self.rigid_prim = RigidPrim(vehicle_path)
        self.rigid_prim._rigid_prim_view.initialize()
        self.starting_pos, _ = self.rigid_prim.get_world_pose()

        # apply some accel
        stage = get_current_stage()
        self.accelerator = stage.GetPrimAtPath(vehicle_path).GetAttribute("physxVehicleController:accelerator")
        self.left_steer = stage.GetPrimAtPath(vehicle_path).GetAttribute("physxVehicleController:steerLeft")
        self.accelerator.Set(1)
        self.left_steer.Set(1)

        for frame in range(100):
            await omni.kit.app.get_app().next_update_async()

        self.current_pos, _ = self.rigid_prim.get_world_pose()
        delta = np.linalg.norm(self.current_pos - self.starting_pos)
        print("Diff is ", delta)
        # TODO: the asset seems broken, when it is played in Isaac sim it vanishes
        # The RigidPrim constructor seems to be adding something that stabilizes it but breaks this assertion
        self.assertTrue(delta > 20)

        pass
