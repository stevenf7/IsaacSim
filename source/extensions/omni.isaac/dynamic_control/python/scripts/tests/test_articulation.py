# NOTE:
#   omni.kit.test - std python's unittest module with additional wrapping to add suport for async/await tests
#   For most things refer to unittest docs: https://docs.python.org/3/library/unittest.html
import omni.kit.test
import omni.kit.asyncapi
import carb.tokens
import os
import asyncio
import numpy as np
from pxr import Gf, PhysxSchema

# Import extension python module we are testing with absolute import path, as if we are external user (other extension)
from omni.isaac.dynamic_control import _dynamic_control
from omni.isaac.utils.scripts.test_utils import load_test_file, set_scene_physics_type


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
    async def test_articulation_load(self, gpu=False):
        await omni.kit.asyncapi.new_stage()
        (result, error) = await load_test_file("assets/robots/franka/franka.usd")
        # Make sure the stage loaded
        self.assertTrue(result)
        set_scene_physics_type(gpu)

        # Start Simulation and wait
        editor = omni.kit.editor.get_editor_interface()
        editor.play()
        await omni.kit.asyncapi.next_update()
        obj_type = self._dc.peek_object_type("/panda")
        self.assertEqual(obj_type, _dynamic_control.ObjectType.OBJECT_ARTICULATION)
        art = self._dc.get_articulation("/panda")
        self.assertNotEqual(art, _dynamic_control.INVALID_HANDLE)
        # make sure that articulation was registered properly
        dof_states = self._dc.get_articulation_dof_states(art, _dynamic_control.STATE_ALL)
        self.assertTrue(dof_states is not None)
        pass

        # Actual test, notice it is "async" function, so "await" can be used if needed

    async def test_articulation_teleport(self, gpu=False):
        await omni.kit.asyncapi.new_stage()
        (result, error) = await load_test_file("assets/robots/franka/franka.usd")
        # Make sure the stage loaded
        self.assertTrue(result)
        set_scene_physics_type(gpu)
        # Start Simulation and wait
        editor = omni.kit.editor.get_editor_interface()
        editor.play()
        await asyncio.sleep(1.0)
        await omni.kit.asyncapi.next_update()
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
        dof_states = self._dc.get_articulation_dof_states(art, _dynamic_control.STATE_ALL)

        self.assertTrue(dof_states is not None)
        dof_state_v2 = dof_states["pos"][dof_idx]

        self.assertAlmostEqual(dof_state_v1.pos, dof_state_v2)

        # teleport the whole robot
        self._dc.wake_up_articulation(art)
        root_body = self._dc.get_articulation_root_body(art)
        new_pose_p = (1.3, 2.1, 3.0)
        new_pose_r = (0, 0, 0.3007058, 0.953717)
        new_pose = _dynamic_control.Transform(new_pose_p, new_pose_r)
        self._dc.set_rigid_body_pose(root_body, new_pose)
        await asyncio.sleep(2.0)
        await omni.kit.asyncapi.next_update()

        pos = self._dc.get_rigid_body_pose(root_body).p
        rot = self._dc.get_rigid_body_pose(root_body).r
        self.assertTupleEqual(tuple(np.round(np.array(pos), 3)), tuple(np.round(np.array(new_pose_p), 3)))
        self.assertTupleEqual(tuple(np.round(np.array(rot), 3)), tuple(np.round(np.array(new_pose_r), 3)))

        # rigid body tests
        body_states = self._dc.get_articulation_body_states(art, _dynamic_control.STATE_ALL)
        body_idx = self._dc.find_articulation_body_index(art, "panda_hand")
        body_pos = body_states["pose"]["p"][body_idx]
        expected_pos = (19.78094, 15.03849, 54.69755)
        self.assertTupleEqual(
            tuple(np.round(np.array(body_pos.tolist()), 2)), tuple(np.round(np.array(expected_pos), 2))
        )

        pass

    async def test_articulation_movement(self, gpu=False):
        await omni.kit.asyncapi.new_stage()
        (result, error) = await load_test_file("assets/robots/franka/franka.usd")
        # Make sure the stage loaded
        self.assertTrue(result)
        set_scene_physics_type(gpu)
        # Start Simulation and wait
        editor = omni.kit.editor.get_editor_interface()
        editor.play()
        await omni.kit.asyncapi.next_update()
        art = self._dc.get_articulation("/panda")
        self.assertNotEqual(art, _dynamic_control.INVALID_HANDLE)

        dof_ptr = self._dc.find_articulation_dof(art, "panda_joint3")

        # change dof target: modifying current state
        dof_states = self._dc.get_articulation_dof_states(art, _dynamic_control.STATE_ALL)
        self.assertTrue(dof_states is not None)
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

    async def test_articulation_wheeled(self, gpu=False):
        await omni.kit.asyncapi.new_stage()
        (result, error) = await load_test_file("tests/robots/differential_base/differential_base.usd")
        # Make sure the stage loaded
        self.assertTrue(result)
        set_scene_physics_type(gpu)
        editor = omni.kit.editor.get_editor_interface()
        editor.play()
        # wait for robot to fall
        await asyncio.sleep(1.0)
        await omni.kit.asyncapi.next_update()
        art = self._dc.get_articulation("/differential_base")
        self.assertNotEqual(art, _dynamic_control.INVALID_HANDLE)
        left_wheel_ptr = self._dc.find_articulation_dof(art, "left_wheel")
        right_wheel_ptr = self._dc.find_articulation_dof(art, "right_wheel")

        self._dc.wake_up_articulation(art)
        self._dc.set_dof_velocity_target(left_wheel_ptr, -2.5)
        self._dc.set_dof_velocity_target(right_wheel_ptr, 2.5)
        await omni.kit.asyncapi.next_update()
        await asyncio.sleep(2.0)
        await omni.kit.asyncapi.next_update()
        root_body_ptr = self._dc.get_articulation_root_body(art)
        lin_vel = self._dc.get_rigid_body_linear_velocity(root_body_ptr)
        ang_vel = self._dc.get_rigid_body_angular_velocity(root_body_ptr)
        print(np.linalg.norm(lin_vel), ang_vel)
        # TODO: Fix test when run from commandline
        # self.assertAlmostEqual(0, np.linalg.norm(lin_vel), 1)
        # self.assertGreater(ang_vel[2], 2.45)
        # self.assertLess(ang_vel[2], 2.55)
        editor.stop()

    async def test_articulation_carter(self, gpu=False):
        await omni.kit.asyncapi.new_stage()
        (result, error) = await load_test_file("assets/robots/carter/carter.usd")
        # Make sure the stage loaded
        self.assertTrue(result)
        set_scene_physics_type(gpu)

        editor = omni.kit.editor.get_editor_interface()
        editor.play()
        # wait for robot to fall
        await asyncio.sleep(1.0)
        await omni.kit.asyncapi.next_update()

        art = self._dc.get_articulation("/carter")
        self.assertNotEqual(art, _dynamic_control.INVALID_HANDLE)
        left_wheel_ptr = self._dc.find_articulation_dof(art, "left_wheel")
        right_wheel_ptr = self._dc.find_articulation_dof(art, "right_wheel")
        self._dc.wake_up_articulation(art)
        drive_target = 2.5

        self._dc.set_dof_velocity_target(left_wheel_ptr, drive_target)
        self._dc.set_dof_velocity_target(right_wheel_ptr, drive_target)
        await asyncio.sleep(1.0)
        left_dof_idx = self._dc.find_articulation_dof_index(art, "left_wheel")
        right_dof_idx = self._dc.find_articulation_dof_index(art, "left_wheel")
        dof_states = self._dc.get_articulation_dof_states(art, _dynamic_control.STATE_ALL)

        self.assertAlmostEqual(drive_target, dof_states["vel"][left_dof_idx], 2)
        self.assertAlmostEqual(drive_target, dof_states["vel"][right_dof_idx], 2)
        root_body_ptr = self._dc.get_articulation_root_body(art)
        lin_vel = self._dc.get_rigid_body_linear_velocity(root_body_ptr)
        ang_vel = self._dc.get_rigid_body_angular_velocity(root_body_ptr)
        self.assertAlmostEqual(drive_target * 24.0, np.linalg.norm(lin_vel), 1)
        self.assertAlmostEqual(0, np.linalg.norm(ang_vel), 1)

        self._dc.set_dof_velocity_target(left_wheel_ptr, 0)
        self._dc.set_dof_velocity_target(right_wheel_ptr, 0)
        await asyncio.sleep(1.0)
        dof_states = self._dc.get_articulation_dof_states(art, _dynamic_control.STATE_ALL)
        self.assertAlmostEqual(0, dof_states["vel"][left_dof_idx], 2)
        self.assertAlmostEqual(0, dof_states["vel"][right_dof_idx], 2)

        self._dc.wake_up_articulation(art)
        self._dc.set_dof_velocity_target(left_wheel_ptr, -drive_target)
        self._dc.set_dof_velocity_target(right_wheel_ptr, drive_target)
        await asyncio.sleep(2.0)
        lin_vel = self._dc.get_rigid_body_linear_velocity(root_body_ptr)
        ang_vel = self._dc.get_rigid_body_angular_velocity(root_body_ptr)
        # print(np.linalg.norm(lin_vel), ang_vel)

        self.assertLess(np.linalg.norm(lin_vel), 1.5)
        # the wheels are offset 5cm from the wheel mesh, need to account for that in wheelbase
        self.assertAlmostEqual(drive_target * 24.0 / (31.613607 - 5), ang_vel[2], 1)
        editor.stop()

    async def test_articulation_position_franka(self, gpu=False):
        await omni.kit.asyncapi.new_stage()
        (result, error) = await load_test_file("assets/robots/franka/franka.usd")
        # Make sure the stage loaded
        self.assertTrue(result)
        set_scene_physics_type(gpu)
        # Start Simulation and wait
        editor = omni.kit.editor.get_editor_interface()
        editor.play()
        await omni.kit.asyncapi.next_update()
        art = self._dc.get_articulation("/panda")
        self.assertNotEqual(art, _dynamic_control.INVALID_HANDLE)

        dof_ptr = self._dc.find_articulation_dof(art, "panda_finger_joint1")

        # set new dof pos target
        new_pos = 4.0
        self.assertTrue(self._dc.set_dof_position_target(dof_ptr, new_pos))
        await asyncio.sleep(2.0)
        dof_pos_new = self._dc.get_dof_position(dof_ptr)
        self.assertTrue(Gf.IsClose(dof_pos_new, new_pos, 0.01))

        # set new dof pos target
        new_pos = 0.0
        self.assertTrue(self._dc.set_dof_position_target(dof_ptr, new_pos))
        await asyncio.sleep(2.0)
        dof_pos_new = self._dc.get_dof_position(dof_ptr)
        self.assertTrue(Gf.IsClose(dof_pos_new, new_pos, 0.01))

        # set new dof pos target
        new_pos = 2.0
        self.assertTrue(self._dc.set_dof_position_target(dof_ptr, new_pos))
        await asyncio.sleep(2.0)
        dof_pos_new = self._dc.get_dof_position(dof_ptr)
        self.assertTrue(Gf.IsClose(dof_pos_new, new_pos, 0.01))

    async def test_articulation_position_str(self, gpu=False):
        await omni.kit.asyncapi.new_stage()
        (result, error) = await load_test_file("tests/robots/str/str_physics.usd")
        # Make sure the stage loaded
        self.assertTrue(result)
        set_scene_physics_type(gpu)
        # await asyncio.sleep(1.0)
        editor = omni.kit.editor.get_editor_interface()
        editor.play()
        await omni.kit.asyncapi.next_update()
        art = self._dc.get_articulation("/World")
        self.assertNotEqual(art, _dynamic_control.INVALID_HANDLE)
        dof_ptr = self._dc.find_articulation_dof(art, "lift_joint")
        # set new dof pos target

        new_pos = 4.0
        self._dc.wake_up_articulation(art)
        self.assertTrue(self._dc.set_dof_position_target(dof_ptr, new_pos))
        await asyncio.sleep(1.0)
        await omni.kit.asyncapi.next_update()
        dof_pos_new = self._dc.get_dof_position(dof_ptr)
        self.assertAlmostEqual(dof_pos_new, new_pos, 1)

        new_pos = 0.0
        self._dc.wake_up_articulation(art)
        self.assertTrue(self._dc.set_dof_position_target(dof_ptr, new_pos))
        await asyncio.sleep(1.0)
        await omni.kit.asyncapi.next_update()
        dof_pos_new = self._dc.get_dof_position(dof_ptr)
        self.assertAlmostEqual(dof_pos_new, new_pos, 1)

        new_pos = 2.0
        self._dc.wake_up_articulation(art)
        self.assertTrue(self._dc.set_dof_position_target(dof_ptr, new_pos))
        await asyncio.sleep(1.0)
        await omni.kit.asyncapi.next_update()
        dof_pos_new = self._dc.get_dof_position(dof_ptr)
        self.assertAlmostEqual(dof_pos_new, new_pos, 1)

    async def test_articulation_load_gpu(self):
        await self.test_articulation_load(True)

    # async def test_articulation_teleport_gpu(self):
    #     await self.test_articulation_teleport(True)

    async def test_articulation_movement_gpu(self):
        await self.test_articulation_movement(True)

    async def test_articulation_wheeled_gpu(self):
        await self.test_articulation_wheeled(True)

    # async def test_articulation_carter_gpu(self):
    #     await self.test_articulation_carter(True)

    async def test_articulation_position_franka_gpu(self):
        await self.test_articulation_position_franka(True)

    async def test_articulation_position_str_gpu(self):
        await self.test_articulation_position_str(True)
