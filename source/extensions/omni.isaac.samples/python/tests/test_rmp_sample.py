# NOTE:
#   omni.kit.test - std python's unittest module with additional wrapping to add suport for async/await tests
#   For most things refer to unittest docs: https://docs.python.org/3/library/unittest.html
import omni.kit.test
import omni.kit

# Import extension python module we are testing with absolute import path, as if we are external user (other extension)
from omni.isaac.samples.scripts.rmp_sample.sample import RMPSample
from .common import simulate


class TestRMPSample(omni.kit.test.AsyncTestCaseFailOnLogError):

    # Before running each test
    async def setUp(self):
        self._sample = RMPSample()
        self._timeline = omni.timeline.get_timeline_interface()
        self._editor = omni.kit.editor.get_editor_interface()
        self._editor_event_subscription = self._editor.subscribe_to_update_events(self._sample.step)
        await omni.usd.get_context().new_stage_async()

        pass

    # After running each test
    async def tearDown(self):
        self._sample = None
        self._editor_event_subscription = None
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
