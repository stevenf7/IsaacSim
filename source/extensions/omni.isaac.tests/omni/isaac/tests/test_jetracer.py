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

import carb.tokens
import carb
import numpy as np
from pxr import Usd

from omni.isaac.core.utils.nucleus_utils import find_nucleus_server
from omni.isaac.dynamic_control import _dynamic_control


async def load_test_file(path_to_file: str):
    if not Usd.Stage.IsSupportedFile(path_to_file):
        raise ValueError("Only USD files can be loaded with this method")

    usd_context = omni.usd.get_context()
    usd_context.disable_save_to_recent_files()
    (result, error) = await omni.usd.get_context().open_stage_async(path_to_file)
    usd_context.enable_save_to_recent_files()
    return (result, error)


# Having a test class dervived from omni.kit.test.AsyncTestCase declared on the root of module will make it auto-discoverable by omni.kit.test
class TestJetRacer(omni.kit.test.AsyncTestCaseFailOnLogError):
    # Before running each test
    async def setUp(self):
        self._timeline = omni.timeline.get_timeline_interface()

        ext_manager = omni.kit.app.get_app().get_extension_manager()
        ext_id = ext_manager.get_enabled_extension_id("omni.isaac.dynamic_control")
        self._dc_extension_path = ext_manager.get_extension_path(ext_id)
        self.dc = _dynamic_control.acquire_dynamic_control_interface()

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
        result, nucleus_server = find_nucleus_server()
        if result is False:
            carb.log_error("Could not find nucleus server with /Isaac folder")
            return

        self.usd_path = nucleus_server + "/Isaac/Robots/Jetracer/jetracer.usd"
        (result, error) = await load_test_file(self.usd_path)
        # Make sure the stage loaded
        self.assertTrue(result)

        # Start Simulation and tick a few
        self._timeline.play()
        for frame in range(10):
            await omni.kit.app.get_app().next_update_async()

        # get the jetracer
        vehicle_path = "/World/Jetracer/Vehicle"
        self.chassis = self.dc.get_rigid_body(vehicle_path)
        self.starting_pos = np.array(self.dc.get_rigid_body_pose(self.chassis).p)

        # apply some accel
        stage = omni.usd.get_context().get_stage()
        self.accelerator = stage.GetPrimAtPath(vehicle_path).GetAttribute("physxVehicleController:accelerator")
        self.left_steer = stage.GetPrimAtPath(vehicle_path).GetAttribute("physxVehicleController:steerLeft")
        self.accelerator.Set(1)
        self.left_steer.Set(1)

        for frame in range(100):
            await omni.kit.app.get_app().next_update_async()

        self.current_pos = np.array(self.dc.get_rigid_body_pose(self.chassis).p)
        delta = np.linalg.norm(self.current_pos - self.starting_pos)
        print("Diff is ", delta)
        self.assertTrue(delta > 20)

        pass
