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
class TestCarterv2(omni.kit.test.AsyncTestCaseFailOnLogError):
    # Before running each test
    async def setUp(self):
        self._timeline = omni.timeline.get_timeline_interface()

        ext_manager = omni.kit.app.get_app().get_extension_manager()
        ext_id = ext_manager.get_enabled_extension_id("omni.isaac.dynamic_control")
        self._dc_extension_path = ext_manager.get_extension_path(ext_id)
        self.dc = _dynamic_control.acquire_dynamic_control_interface()

        result, self._nucleus_server = find_nucleus_server()
        if result is False:
            carb.log_error("Could not find nucleus server with /Isaac folder")
            return

        pass

    # After running each test
    async def tearDown(self):
        await omni.kit.app.get_app().next_update_async()
        # In some cases the test will end before the asset is loaded, in this case wait for assets to load
        while omni.usd.get_context().get_stage_loading_status()[2] > 0:
            await omni.kit.app.get_app().next_update_async()

        pass

    async def simulate(self, seconds, art=None, steps_per_sec=60):
        for frame in range(steps_per_sec * seconds):
            if art is not None:
                self.dc.wake_up_articulation(art)
            await omni.kit.app.get_app().next_update_async()

    # Actual test, notice it is "async" function, so "await" can be used if needed
    async def test_carterv2(self):

        self.usd_path = self._nucleus_server + "/Isaac/Robots/Carter/carter_v2.usd"
        (result, error) = await load_test_file(self.usd_path)
        # Make sure the stage loaded
        self.assertTrue(result)

        # Start Simulation and wait
        self._timeline.play()
        await omni.kit.app.get_app().next_update_async()

        # get the dofbot
        self.ar = self.dc.get_articulation("/carter_v2")
        self.chassis = self.dc.get_articulation_root_body(self.ar)
        self.starting_pos = np.array(self.dc.get_rigid_body_pose(self.chassis).p)

        self.wheel_left = self.dc.find_articulation_dof(self.ar, "joint_wheel_left")
        self.wheel_right = self.dc.find_articulation_dof(self.ar, "joint_wheel_right")

        # move the jetbot
        self.dc.set_dof_velocity_target(self.wheel_left, 1)
        self.dc.set_dof_velocity_target(self.wheel_right, 1)

        await self.simulate(1, self.ar)

        self.current_pos = np.array(self.dc.get_rigid_body_pose(self.chassis).p)

        delta = np.linalg.norm(self.current_pos - self.starting_pos)
        print("Diff is ", delta)
        self.assertTrue(delta > 2)

        pass
