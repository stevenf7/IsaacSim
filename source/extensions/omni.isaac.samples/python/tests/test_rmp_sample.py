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
from omni.isaac.samples.scripts.rmp_sample.sample import RMPSample
from .common import simulate
from pxr import Gf

import omni.physx as _physx


class TestRMPSample(omni.kit.test.AsyncTestCaseFailOnLogError):

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
        self._sample.follow_target()
        self._sample.has_arrived()
        self._sample.gripper_state()
        self._sample.add_obstacle()
        self._sample.toggle_obstacle()
        self._sample.toggle_gripper()
        self._sample.get_states()
        self._sample.reset()
        pass

    # enable following target, check that we reached it
    async def test_follow(self):
        self._sample.create_robot()
        await omni.kit.app.get_app().next_update_async()
        self._timeline.play()
        await simulate(1)
        self._sample.follow_target()
        await simulate(0.1)
        self.assertEqual(self._sample.has_arrived(), False)  # not enough time passed for it to reach target
        await simulate(2)
        self.assertEqual(self._sample.has_arrived(), True)
        self._timeline.stop()
        await omni.kit.app.get_app().next_update_async()
        pass

    # enable following target, check that we reached it
    async def test_gripper(self):
        self._sample.create_robot()
        await omni.kit.app.get_app().next_update_async()
        self._timeline.play()
        await simulate(1)
        left, right = self._sample.gripper_state()
        self.assertAlmostEqual(left, 0.0, delta=0.1)
        self.assertAlmostEqual(right, 0.0, delta=0.1)
        self._sample.toggle_gripper()
        await simulate(2)
        left, right = self._sample.gripper_state()
        self.assertAlmostEqual(left, 4.0, delta=0.1)
        self.assertAlmostEqual(right, 4.0, delta=0.1)
        self._sample.toggle_gripper()
        await simulate(2)
        left, right = self._sample.gripper_state()
        self.assertAlmostEqual(left, 0.0, delta=0.1)
        self.assertAlmostEqual(right, 0.0, delta=0.1)
        self._timeline.stop()
        await omni.kit.app.get_app().next_update_async()
        pass

    async def test_obstacle(self):
        self._sample.create_robot()
        await omni.kit.app.get_app().next_update_async()
        self._timeline.play()
        self._sample.follow_target()
        await simulate(1)
        self._sample.add_obstacle()
        # move target to location just above cube, we should not be able to reach
        self._sample.move_target(Gf.Vec3d(30.0, -20.0, 12))
        await simulate(3)
        self.assertEqual(self._sample.has_arrived(), False)
        # toggle, we should be able to reach
        self._sample.toggle_obstacle()
        await simulate(3)
        self.assertEqual(self._sample.has_arrived(), True)
        # toggle, we should not be able to reach
        self._sample.toggle_obstacle()
        await simulate(3)
        self.assertEqual(self._sample.has_arrived(), False)
        # toggle, we should be able to reach
        self._sample.toggle_obstacle()
        await simulate(3)
        self.assertEqual(self._sample.has_arrived(), True)
        # move target to above clear spot, we should be able to reach
        self._sample.move_target(Gf.Vec3d(30.0, 30.0, 20))
        await simulate(4)
        self.assertEqual(self._sample.has_arrived(), True)
        # move target to inside ground, we should not reach
        self._sample.move_target(Gf.Vec3d(30.0, 30.0, 0))
        await simulate(4)
        self.assertEqual(self._sample.has_arrived(), False)
        self._timeline.stop()
        await omni.kit.app.get_app().next_update_async()

    async def test_data_collection(self):
        self._sample.create_robot()
        await omni.kit.app.get_app().next_update_async()
        self._timeline.play()
        self._sample.follow_target()
        await simulate(4)
        self._sample.reset_action_state_dict()
        print("Collect data")
        self._sample.collect_action_state()
        state_action_dict = self._sample.get_action_state_dict()

        import numpy as np

        print("Checking collected data")
        np.testing.assert_almost_equal(
            state_action_dict["joint command"][0],
            np.array([-0.00882683, -0.78860676, 0.00875621, -2.84749961, 0.00704176, 2.05903769, 0.77942944, 0.0, 0.0]),
            decimal=3,
        )
        np.testing.assert_almost_equal(
            state_action_dict["joint state"][0],
            np.array([-8.8267e-03, -7.8861e-01, 8.75626e-03, -2.8475, 7.04182e-03, 2.0590, 7.7940e-01, 0.0, 0.0]),
            decimal=3,
        )
        self._timeline.stop()
        await omni.kit.app.get_app().next_update_async()

    # Run all functions with simulation enabled
    async def test_simulation(self):
        self._sample.create_robot()
        await omni.kit.app.get_app().next_update_async()
        self._timeline.play()
        await simulate(1)
        self._sample.follow_target()
        await simulate(1)
        self._sample.add_obstacle()
        await simulate(1)
        self._sample.toggle_obstacle()
        await simulate(1)
        self._sample.toggle_gripper()
        await simulate(1)
        self._sample.get_states()
        self._sample.gripper_state()
        self._sample.has_arrived()
        await simulate(1)
        self._sample.reset()
        await simulate(1)
        self._sample.stop_tasks()
        await simulate(1)
        self._timeline.stop()
        await omni.kit.app.get_app().next_update_async()
        pass
