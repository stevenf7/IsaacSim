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
import omni.kit
import asyncio
import carb

# Import extension python module we are testing with absolute import path, as if we are external user (other extension)
from omni.isaac.samples.scripts.dofbot_rmp_sample.sample import RMPSample
from .common import simulate
from pxr import Gf

import omni.physx as _physx
import os


class TestDofbotRMPSample(omni.kit.test.AsyncTestCaseFailOnLogError):

    # Before running each test
    async def setUp(self):
        self._sample = RMPSample()
        self._timeline = omni.timeline.get_timeline_interface()
        self._physx_subs = _physx.get_physx_interface().subscribe_physics_step_events(self._sample.step)
        self._physics_rate = 60

        carb.settings.get_settings().set_int("/app/runLoops/main/rateLimitFrequency", int(self._physics_rate))
        carb.settings.get_settings().set_bool("/app/runLoops/main/rateLimitEnabled", True)
        carb.settings.get_settings().set_int("/persistent/simulation/minFrameRate", int(self._physics_rate))
        await omni.usd.get_context().new_stage_async()
        await omni.kit.app.get_app().next_update_async()
        pass

    # After running each test
    async def tearDown(self):
        # In some cases the test will end before the asset is loaded, in this case wait for assets to load
        while omni.usd.get_context().get_stage_loading_status()[2] > 0:
            print("tearDown, assets still loading, waiting to finish...")
            await asyncio.sleep(1.0)
        await omni.kit.app.get_app().next_update_async()
        self._sample = None
        self._physx_subs = None
        await omni.kit.app.get_app().next_update_async()
        pass

    # basic test, should not crash or error if we call all functions
    async def test_no_simulation(self):
        self._sample.create_robot()
        self._sample.setup_world()
        self._sample.has_arrived()
        self._sample.get_states()
        pass

    # basic test, run functions with simulation enabled
    async def test_simulation(self):
        self._sample.create_robot()
        await omni.kit.app.get_app().next_update_async()
        self._sample.setup_world()
        await simulate(1)
        self._timeline.play()
        await simulate(1)
        self._sample.get_states()
        await simulate(1)
        self._timeline.stop()
        await omni.kit.app.get_app().next_update_async()
        pass

    # check RMP, using fixed target
    async def test_RMP(self):
        self._sample.create_robot()
        await omni.kit.app.get_app().next_update_async()
        self._sample.setup_world()
        await simulate(1)
        self._timeline.play()
        await simulate(1)
        self._sample.randomize = False

        # Put cube within reach
        self._sample.load_fixed_asset(Gf.Vec3d(20, 0.0, 3.0))
        await simulate(5)
        reached, _ = self._sample.target_reached()
        self.assertEqual(reached, True)

        # Put cube beyond reach
        self._sample.load_fixed_asset(Gf.Vec3d(20.0, 0.0, 30.0))
        await simulate(5)
        reached, _ = self._sample.target_reached()
        self.assertEqual(reached, False)

        await omni.kit.app.get_app().next_update_async()
        pass
