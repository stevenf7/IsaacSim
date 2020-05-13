# NOTE:
#   omni.kit.test - std python's unittest module with additional wrapping to add suport for async/await tests
#   For most things refer to unittest docs: https://docs.python.org/3/library/unittest.html
import omni.kit.test
import omni.kit.asyncapi
import carb.tokens
import os
import asyncio
import numpy as np

# Import extension python module we are testing with absolute import path, as if we are external user (other extension)
from omni.isaac.dynamic_control import _dynamic_control
from omni.isaac.utils.scripts.test_utils import load_test_file

# Having a test class dervived from omni.kit.test.AsyncTestCase declared on the root of module will make it auto-discoverable by omni.kit.test
class TestArticulation(omni.kit.test.AsyncTestCaseFailOnLogError):
    # Before running each test
    async def setUp(self):
        self._dc = _dynamic_control.acquire_dynamic_control_interface()

        pass

    # After running each test
    async def tearDown(self):
        pass

    # Actual test, notice it is "async" function, so "await" can be used if needed
    async def test_articulation_load(self):
        (result, error) = await load_test_file("assets/robots/franka/franka.usd")
        # Make sure the stage loaded
        self.assertTrue(result)
        # Start Simulation and wait
        editor = omni.kit.editor.get_editor_interface()
        editor.play()
        await asyncio.sleep(0.125)
        obj_type = self._dc.peek_object_type("/panda")
        self.assertEqual(obj_type, _dynamic_control.ObjectType.OBJECT_ARTICULATION)

        art = self._dc.get_articulation("/panda")
        self.assertNotEqual(art, _dynamic_control.INVALID_HANDLE)

        pass

        # Actual test, notice it is "async" function, so "await" can be used if needed

    async def test_articulation_teleport(self):
        (result, error) = await load_test_file("assets/robots/franka/franka.usd")
        # Make sure the stage loaded
        self.assertTrue(result)
        # Start Simulation and wait
        editor = omni.kit.editor.get_editor_interface()
        editor.play()
        await asyncio.sleep(0.125)
        art = self._dc.get_articulation("/panda")
        self.assertNotEqual(art, _dynamic_control.INVALID_HANDLE)

        # test basics
        num_joints = self._dc.get_articulation_joint_count(art)
        num_dofs = self._dc.get_articulation_dof_count(art)
        num_bodies = self._dc.get_articulation_body_count(art)
        self.assertEqual(num_joints, 10)
        self.assertEqual(num_dofs, 9)
        self.assertEqual(num_bodies, 11)

        # difference between joint and dof
        fixed_joint_ptr = self._dc.find_articulation_joint(art, "panda_hand_joint")
        fixed_dof_ptr = self._dc.find_articulation_dof(art, "panda_hand_joint")
        self.assertNotEqual(fixed_joint_ptr, _dynamic_control.INVALID_HANDLE)
        self.assertEqual(fixed_dof_ptr, _dynamic_control.INVALID_HANDLE)

        # get joint properties
        joint_type = self._dc.get_joint_type(fixed_joint_ptr)
        joint_dof_count = self._dc.get_joint_dof_count(fixed_joint_ptr)  # dof of the joint
        self.assertEqual(joint_type, _dynamic_control.JOINT_FIXED)
        self.assertEqual(joint_dof_count, 0)

        # get dof states
        dof_ptr = self._dc.find_articulation_dof(art, "panda_finger_joint1")
        dof_type = self._dc.get_dof_type(dof_ptr)
        self.assertEqual(dof_type, _dynamic_control.DOF_TRANSLATION)
        dof_state_v1 = self._dc.get_dof_state(dof_ptr)
        # comparing it to using .get_articulation_dof_states()
        dof_idx = self._dc.find_articulation_dof_index(art, "panda_finger_joint1")
        dof_state_v2 = self._dc.get_articulation_dof_states(art, _dynamic_control.STATE_ALL)["pos"][dof_idx]
        self.assertAlmostEqual(dof_state_v1.pos, dof_state_v2)

        # teleport the whole robot
        root_body = self._dc.get_articulation_root_body(art)
        await asyncio.sleep(1.0)
        new_pose_p = (1.3, 2.1, 3.0)
        new_pose_r = (0, 0, 0.3007058, 0.953717)
        new_pose = _dynamic_control.Transform(new_pose_p, new_pose_r)
        self._dc.set_rigid_body_pose(root_body, new_pose)
        await asyncio.sleep(0.125)
        pos = self._dc.get_rigid_body_pose(root_body).p
        rot = self._dc.get_rigid_body_pose(root_body).r
        self.assertTupleEqual(tuple(np.round(np.array(pos), 5)), tuple(np.round(np.array(new_pose_p), 5)))
        self.assertTupleEqual(tuple(np.round(np.array(rot), 5)), tuple(np.round(np.array(new_pose_r), 5)))
        await asyncio.sleep(1.0)

        # rigid body tests
        body_states = self._dc.get_articulation_body_states(art, _dynamic_control.STATE_ALL)
        body_idx = self._dc.find_articulation_body_index(art, "panda_hand")
        body_pos = body_states["pose"]["p"][body_idx]
        expected_pos = (19.815851, 15.068529, 54.849457)
        self.assertTupleEqual(
            tuple(np.round(np.array(body_pos.tolist()), 5)), tuple(np.round(np.array(expected_pos), 5))
        )

        pass

    async def test_articulation_movement(self):
        (result, error) = await load_test_file("assets/robots/franka/franka.usd")
        # Make sure the stage loaded
        self.assertTrue(result)
        # Start Simulation and wait
        editor = omni.kit.editor.get_editor_interface()
        editor.play()
        await asyncio.sleep(0.125)
        art = self._dc.get_articulation("/panda")
        self.assertNotEqual(art, _dynamic_control.INVALID_HANDLE)

        dof_ptr = self._dc.find_articulation_dof(art, "panda_joint3")

        # change dof target: modifying current state
        dof_states = self._dc.get_articulation_dof_states(art, _dynamic_control.STATE_ALL)
        dof_pos = dof_states["pos"]
        dof_old = dof_pos[3] + 0.15
        dof_pos += 0.15
        self.assertTrue(self._dc.set_articulation_dof_position_targets(art, dof_pos))
        await asyncio.sleep(1.0)
        self.assertAlmostEqual(dof_old, dof_pos[3], 4)

        # change dof velocity: set one dof at a time
        dof_pos_old = self._dc.get_dof_position(dof_ptr)
        dof_props = _dynamic_control.DofProperties()
        dof_props.drive_mode = _dynamic_control.DRIVE_VEL
        dof_props.damping = 1e7
        dof_props.stiffness = 0
        self._dc.set_dof_properties(dof_ptr, dof_props)
        self._dc.set_dof_velocity_target(dof_ptr, 0.2)
        await asyncio.sleep(3.0)

        # stop moving: setting all of the dofs at once
        num_dofs = self._dc.get_articulation_dof_count(art)
        vel_targets = np.zeros(num_dofs, dtype=np.float32)
        self._dc.set_articulation_dof_velocity_targets(art, vel_targets)

        dof_pos_new = self._dc.get_dof_position(dof_ptr)
        self.assertNotEqual(dof_pos_old, dof_pos_new)

        pass
