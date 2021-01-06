# NOTE:
#   omni.kit.test - std python's unittest module with additional wrapping to add suport for async/await tests
#   For most things refer to unittest docs: https://docs.python.org/3/library/unittest.html
import omni.kit.test
import omni.kit

import carb

# Import extension python module we are testing with absolute import path, as if we are external user (other extension)
from omni.isaac.samples.scripts.rmp_sample.sample import RMPSample
from .common import simulate
from pxr import Gf


class TestRMPSample(omni.kit.test.AsyncTestCaseFailOnLogError):

    # Before running each test
    async def setUp(self):
        self._sample = RMPSample()
        self._timeline = omni.timeline.get_timeline_interface()
        self._editor = omni.kit.editor.get_editor_interface()
        self._editor_event_subscription = self._editor.subscribe_to_update_events(self._sample.step)
        physics_rate = carb.settings.get_settings().get("/physics/timeStepsPerSecond")
        self.phys_num_steps = carb.settings.get_settings().get("persistent/physics/maxNumSteps")
        carb.settings.get_settings().set_int(
            "persistent/physics/maxNumSteps", int(1)
        )  # Enforce single timestep per stage update
        self.time_step = 1.0 / physics_rate
        carb.settings.get_settings().set_int("/app/runLoops/main/rateLimitFrequency", int(physics_rate))
        self._limit_fps = carb.settings.get_settings().get("/app/runLoops/main/rateLimitEnabled")
        carb.settings.get_settings().set_bool("/app/runLoops/main/rateLimitEnabled", True)
        await omni.usd.get_context().new_stage_async()

        pass

    # After running each test
    async def tearDown(self):
        self._sample = None
        self._editor_event_subscription = None
        carb.settings.get_settings().set_bool("/app/runLoops/main/rateLimitEnabled", self._limit_fps)
        carb.settings.get_settings().set_int("persistent/physics/maxNumSteps", int(self.phys_num_steps))

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
        self._timeline.play()
        await simulate(1)
        self._sample.follow_target()
        await simulate(0.1)
        self.assertEqual(self._sample.has_arrived(), False)  # not enough time passed for it to reach target
        await simulate(2)
        self.assertEqual(self._sample.has_arrived(), True)
        pass

    # enable following target, check that we reached it
    async def test_gripper(self):
        self._sample.create_robot()
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
        pass

    async def test_obstacle(self):
        self._sample.create_robot()
        self._timeline.play()
        self._sample.follow_target()
        await simulate(1)
        self._sample.add_obstacle()
        # move target to location just above cube, we should not be able to reach
        self._sample.move_target(Gf.Vec3f(30.0, -20.0, 12))
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
        self._sample.move_target(Gf.Vec3f(30.0, 30.0, 20))
        await simulate(4)
        self.assertEqual(self._sample.has_arrived(), True)
        # move target to inside ground, we should not reach
        self._sample.move_target(Gf.Vec3f(30.0, 30.0, 0))
        await simulate(4)
        self.assertEqual(self._sample.has_arrived(), False)

    # Run all functions with simulation enabled
    async def test_simulation(self):
        self._sample.create_robot()
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
        pass
