# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
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

# Import extension python module we are testing with absolute import path, as if we are external user (other extension)
from omni.isaac.core.articulations import ArticulationView
from omni.isaac.core.prims import RigidPrimView
from omni.isaac.core.utils.torch.rotations import euler_angles_to_quats
import numpy as np
from omni.isaac.core.utils.stage import create_new_stage_async, add_reference_to_stage, update_stage_async
from omni.isaac.core.utils.nucleus import get_assets_root_path
from omni.isaac.core import World
import torch
import omni.physx as _physx


# Having a test class dervived from omni.kit.test.AsyncTestCase declared on the root of module will make it auto-discoverable by omni.kit.test
class TestArticulationView(omni.kit.test.AsyncTestCase):
    async def setUp(self, device="cpu"):
        await create_new_stage_async()
        self._my_world = World(stage_units_in_meters=1.0, backend="torch", device=device)
        await self._my_world.initialize_simulation_context_async()
        await omni.kit.app.get_app().next_update_async()
        self._my_world.scene.add_default_ground_plane()
        pass

    async def add_frankas(self, add_view_to_scene=True):
        assets_root_path = get_assets_root_path()
        asset_path = assets_root_path + "/Isaac/Robots/Franka/franka_alt_fingers.usd"
        add_reference_to_stage(usd_path=asset_path, prim_path="/World/Franka_1")
        add_reference_to_stage(usd_path=asset_path, prim_path="/World/Franka_2")
        self._frankas_view = ArticulationView(prim_paths_expr="/World/Franka_[1-2]", name="frankas_view")
        if add_view_to_scene:
            self._my_world.scene.add(self._frankas_view)
        await self._my_world.reset_async()
        if not add_view_to_scene:
            self._frankas_view.initialize()

    async def add_humanoids(self, add_view_to_scene=True):
        assets_root_path = get_assets_root_path()
        asset_path = assets_root_path + "/Isaac/Robots/Humanoid/humanoid.usd"
        add_reference_to_stage(usd_path=asset_path, prim_path="/World/Humanoid_1")
        add_reference_to_stage(usd_path=asset_path, prim_path="/World/Humanoid_2")
        self._humanoids_view = ArticulationView(prim_paths_expr="/World/Humanoid_[1-2]", name="humanoids_view")
        if add_view_to_scene:
            self._my_world.scene.add(self._humanoids_view)
        await self._my_world.reset_async()
        if not add_view_to_scene:
            self._humanoids_view.initialize()

    async def add_shadow_hands(self, add_view_to_scene=True):
        assets_root_path = get_assets_root_path()
        asset_path = assets_root_path + "/Isaac/Robots/ShadowHand/shadow_hand_instanceable.usd"
        add_reference_to_stage(usd_path=asset_path, prim_path="/World/ShadowHand_1")
        add_reference_to_stage(usd_path=asset_path, prim_path="/World/ShadowHand_2")
        self._hands_view = ArticulationView(
            prim_paths_expr="/World/ShadowHand_[1-2]",
            name="hands_view",
            positions=torch.tensor([[0, 0, 0.2], [0, 1, 0.2]]),
        )
        if add_view_to_scene:
            self._my_world.scene.add(self._hands_view)
        await self._my_world.reset_async()
        if not add_view_to_scene:
            self._hands_view.initialize()

    async def tearDown(self):
        self._my_world.clear_instance()

    async def test_world_poses(self):
        await self.add_frankas()
        current_positions, current_orientations = self._frankas_view.get_world_poses()
        gt_positions = torch.tensor([[10.0, 10.0, 0], [100.0, 100.0, 0]])
        gt_orientations = euler_angles_to_quats(torch.tensor([[0, 0, np.pi / 2.0], [0, 0, -np.pi / 2.0]]))
        self._frankas_view.set_world_poses(positions=gt_positions, orientations=gt_orientations)
        new_positions, new_orientations = self._frankas_view.get_world_poses()
        self.assertFalse(np.isclose(current_positions, new_positions).all())
        self.assertFalse(np.isclose(current_orientations, new_orientations).all())
        self.assertTrue(np.isclose(new_positions, gt_positions.numpy(), atol=1e-05).all())
        self.assertTrue(
            np.logical_or(
                np.isclose(new_orientations, gt_orientations.numpy(), atol=1e-05).all(axis=1),
                np.isclose(new_orientations, -gt_orientations.numpy(), atol=1e-05).all(axis=1),
            ).all()
        )
        await omni.kit.app.get_app().next_update_async()
        await self._my_world.reset_async()
        await omni.kit.app.get_app().next_update_async()
        # Tensor API path
        current_positions, current_orientations = self._frankas_view.get_world_poses()
        gt_positions = torch.tensor([[10.0, 10.0, 0], [100.0, 100.0, 0]])
        gt_orientations = euler_angles_to_quats(torch.tensor([[0, 0, np.pi / 2.0], [0, 0, -np.pi / 2.0]]))
        self._frankas_view.set_world_poses(positions=gt_positions, orientations=gt_orientations)
        new_positions, new_orientations = self._frankas_view.get_world_poses()
        self.assertFalse(np.isclose(current_positions, new_positions).all())
        self.assertFalse(np.isclose(current_orientations, new_orientations).all())

        self.assertTrue(np.isclose(new_positions, gt_positions.numpy(), atol=1e-05).all())

        self.assertTrue(
            np.logical_or(
                np.isclose(new_orientations, gt_orientations.numpy(), atol=1e-05).all(axis=1),
                np.isclose(new_orientations, -gt_orientations.numpy(), atol=1e-05).all(axis=1),
            ).all()
        )
        return

    async def test_gains(self):
        await self.add_frankas()
        new_kps = torch.tensor(
            [
                [100.0, 100.0, 100.0, 100.0, 100.0, 100.0, 100.0, 100.0, 500.0],
                [100.0, 100.0, 100.0, 100.0, 100.0, 100.0, 100.0, 100.0, 400.0],
            ]
        )
        old_kps, old_kds = self._frankas_view.get_gains()
        self._frankas_view.set_gains(kps=new_kps)
        await self._my_world.reset_async()
        kps, kds = self._frankas_view.get_gains()
        self.assertTrue(np.isclose(new_kps.numpy(), kps.numpy()).all())
        self.assertTrue(np.isclose(kds.numpy(), old_kds.numpy()).all())

    async def test_switch_control_mode(self):
        await self.add_frankas()
        self._frankas_view.switch_control_mode(mode="velocity")
        kps, kds = self._frankas_view.get_gains()
        self.assertTrue(not np.any(kps.numpy()))
        self.assertTrue(np.any(kds.numpy()))

    async def test_max_effort(self):
        await self.add_frankas()
        gt_efforts = torch.tensor(
            [
                [100.0, 100.0, 100.0, 100.0, 100.0, 100.0, 100.0, 100.0, 500.0],
                [100.0, 100.0, 100.0, 100.0, 100.0, 100.0, 100.0, 100.0, 400.0],
            ]
        )
        self._frankas_view.set_max_efforts(gt_efforts)
        new_efforts = self._frankas_view.get_max_efforts()
        self.assertTrue(np.isclose(gt_efforts.numpy(), new_efforts.numpy()).all())

    async def test_friction_coefficients(self):
        await self.add_frankas()
        cur_friction = self._frankas_view.get_friction_coefficients()
        new_friction = cur_friction + 0.5
        self._frankas_view.set_friction_coefficients(new_friction)
        friction = self._frankas_view.get_friction_coefficients()
        self.assertTrue(np.isclose(new_friction.numpy(), friction.numpy()).all())

        self._my_world.clear_instance()
        await self.setUp(device="cuda")

        await self.add_frankas()
        cur_friction = self._frankas_view.get_friction_coefficients()
        new_friction = cur_friction + 0.5
        self._frankas_view.set_friction_coefficients(new_friction)
        friction = self._frankas_view.get_friction_coefficients()
        self.assertTrue(np.isclose(new_friction.cpu().numpy(), friction.cpu().numpy()).all())

    async def test_friction_coefficients_usd(self):
        await self.add_frankas(add_view_to_scene=False)
        cur_friction = self._frankas_view.get_friction_coefficients()
        new_friction = cur_friction + 0.5
        self._frankas_view.set_friction_coefficients(new_friction)
        friction = self._frankas_view.get_friction_coefficients()
        self.assertTrue(np.isclose(new_friction.numpy(), friction.numpy()).all())

    async def test_armatures(self):
        await self.add_frankas()
        cur_armature = self._frankas_view.get_armatures()
        new_armature = cur_armature + 0.5
        self._frankas_view.set_armatures(new_armature)
        armature = self._frankas_view.get_armatures()
        self.assertTrue(np.isclose(new_armature.numpy(), armature.numpy()).all())

        self._my_world.clear_instance()
        await self.setUp(device="cuda")

        await self.add_frankas()
        cur_armature = self._frankas_view.get_armatures()
        new_armature = cur_armature + 0.5
        self._frankas_view.set_armatures(new_armature)
        armature = self._frankas_view.get_armatures()
        self.assertTrue(np.isclose(new_armature.cpu().numpy(), armature.cpu().numpy()).all())

    async def test_armatures_usd(self):
        await self.add_frankas(add_view_to_scene=False)
        cur_armature = self._frankas_view.get_armatures()
        new_armature = cur_armature + 0.5
        self._frankas_view.set_armatures(new_armature)
        armature = self._frankas_view.get_armatures()
        self.assertTrue(np.isclose(new_armature.numpy(), armature.numpy()).all())

    async def test_physics_callback(self):
        await self.add_frankas()

        def step_callback_1(step_size):
            a = self._frankas_view.get_joint_positions()

        physx_subs = _physx.get_physx_interface().subscribe_physics_step_events(step_callback_1)
        # self._my_world.add_physics_callback(callback_name="sim_step", callback_fn=step_callback_1)
        await self._my_world.reset_async()
        await update_stage_async()
        await update_stage_async()
        await self._my_world.reset_async()
        physx_subs = None

    async def test_set_local_pose(self):
        # Test constructor setting of pose
        await self.add_frankas()
        new_translations = torch.tensor([[0, 1.0, 0], [0, 2.0, 0]])
        self._frankas_view.set_local_poses(translations=new_translations)
        return

    async def test_physics_properties(self):
        await self.add_frankas()
        self._frankas_view.set_effort_modes("force")
        stiffness_tensor = torch.tensor(
            [
                [100.0, 100.0, 100.0, 100.0, 100.0, 100.0, 100.0, 100.0, 500.0],
                [100.0, 100.0, 100.0, 100.0, 100.0, 100.0, 100.0, 100.0, 400.0],
            ]
        )
        damping_tensor = torch.tensor(
            [
                [100.0, 100.0, 100.0, 100.0, 100.0, 100.0, 100.0, 100.0, 500.0],
                [100.0, 100.0, 100.0, 100.0, 100.0, 100.0, 100.0, 100.0, 400.0],
            ]
        )
        max_efforts_tensor = torch.tensor(
            [
                [100.0, 100.0, 100.0, 100.0, 100.0, 100.0, 100.0, 100.0, 500.0],
                [100.0, 100.0, 100.0, 100.0, 100.0, 100.0, 100.0, 100.0, 400.0],
            ]
        )
        self._frankas_view.set_gains(stiffness_tensor, damping_tensor)
        self._frankas_view.switch_control_mode("velocity", joint_indices=list(range(7)))
        self._frankas_view.switch_control_mode("position", joint_indices=[7, 8])
        self._frankas_view.set_max_efforts(max_efforts_tensor)

    async def test_initializing_views(self):
        await self.add_frankas()
        robots = ArticulationView(prim_paths_expr="/World/Franka_[1-2]")
        robots.initialize()
        # right-finger
        self.left_fingers = RigidPrimView(prim_paths_expr="/World/Franka_[1-2]/panda_leftfinger")
        self.left_fingers.initialize()
        # # left-finger
        self.right_fingers = RigidPrimView(prim_paths_expr="/World/Franka_[1-2]/panda_rightfinger")
        self.right_fingers.initialize()
        return

    async def test_physics_handles_none(self):
        await self.add_frankas()
        robots = ArticulationView(prim_paths_expr="/World/Franka_[1-2]")
        robots.initialize()
        # right-finger
        self.assertTrue(robots.get_joint_positions() is not None)
        await self._my_world.stop_async()
        self.assertTrue(robots.get_joint_positions() is None)
        self.assertTrue(not robots.is_physics_handle_valid())
        self.assertTrue(robots.get_world_poses() is not None)
        await self._my_world.play_async()
        self.assertTrue(not robots.is_physics_handle_valid())
        robots.initialize()
        self.assertTrue(robots.is_physics_handle_valid())
        self.assertTrue(robots.get_joint_positions() is not None)
        return

    async def test_jacobians(self):
        await self.add_frankas()
        await self._my_world.reset_async()
        jacobian_shape = self._frankas_view.get_jacobian_shape()
        jacobians = self._frankas_view.get_jacobians()
        self.assertTrue(tuple(jacobians[0].shape) == jacobian_shape)
        self.assertTrue(jacobians.shape[0] == self._frankas_view.count)
        is_nan = torch.where(torch.isnan(jacobians))
        for i in is_nan:
            self.assertTrue(len(i) == 0)

        self._my_world.clear_instance()
        await self.setUp(device="cuda")

        await self.add_frankas()
        await self._my_world.reset_async()
        jacobian_shape = self._frankas_view.get_jacobian_shape()
        jacobians = self._frankas_view.get_jacobians()
        self.assertTrue(tuple(jacobians[0].shape) == jacobian_shape)
        self.assertTrue(jacobians.shape[0] == self._frankas_view.count)
        is_nan = torch.where(torch.isnan(jacobians))
        for i in is_nan:
            self.assertTrue(len(i) == 0)

    async def test_mass_matrices(self):
        await self.add_frankas()
        await self._my_world.reset_async()
        mass_matrix_shape = self._frankas_view.get_mass_matrix_shape()
        mass_matrices = self._frankas_view.get_mass_matrices()
        self.assertTrue(tuple(mass_matrices[0].shape) == mass_matrix_shape)
        self.assertTrue(mass_matrices.shape[0] == self._frankas_view.count)
        is_nan = torch.where(torch.isnan(mass_matrices))
        for i in is_nan:
            self.assertTrue(len(i) == 0)

        self._my_world.clear_instance()
        await self.setUp(device="cuda")

        await self.add_frankas()
        await self._my_world.reset_async()
        mass_matrix_shape = self._frankas_view.get_mass_matrix_shape()
        mass_matrices = self._frankas_view.get_mass_matrices()
        self.assertTrue(tuple(mass_matrices[0].shape) == mass_matrix_shape)
        self.assertTrue(mass_matrices.shape[0] == self._frankas_view.count)
        is_nan = torch.where(torch.isnan(mass_matrices))
        for i in is_nan:
            self.assertTrue(len(i) == 0)

    async def test_coriolis_centrifugal(self):
        await self.add_frankas()
        await self._my_world.reset_async()
        forces = self._frankas_view.get_coriolis_and_centrifugal_forces()
        self.assertTrue(forces.shape == (self._frankas_view.count, self._frankas_view.num_dof))

        self._my_world.clear_instance()
        await self.setUp(device="cuda")

        await self.add_frankas()
        await self._my_world.reset_async()
        forces = self._frankas_view.get_coriolis_and_centrifugal_forces()
        self.assertTrue(forces.shape == (self._frankas_view.count, self._frankas_view.num_dof))

    async def test_generalized_gravity(self):
        self._my_world.get_physics_context().set_gravity(0.0)
        await self.add_frankas()
        await self._my_world.reset_async()
        forces = self._frankas_view.get_generalized_gravity_forces()
        self.assertTrue(forces.shape == (self._frankas_view.count, self._frankas_view.num_dof))
        self.assertTrue(torch.count_nonzero(forces) == 0)

        self._my_world.clear_instance()
        await self.setUp()

        self._my_world.get_physics_context().set_gravity(-9.81)
        await self.add_frankas()
        await self._my_world.reset_async()
        forces = self._frankas_view.get_generalized_gravity_forces()
        self.assertTrue(forces.shape == (self._frankas_view.count, self._frankas_view.num_dof))
        self.assertTrue(torch.count_nonzero(forces) == self._frankas_view.count * self._frankas_view.num_dof)

        self._my_world.clear_instance()
        await self.setUp(device="cuda")

        self._my_world.get_physics_context().set_gravity(0.0)
        await self.add_frankas()
        await self._my_world.reset_async()
        forces = self._frankas_view.get_generalized_gravity_forces()
        self.assertTrue(forces.shape == (self._frankas_view.count, self._frankas_view.num_dof))
        self.assertTrue(torch.count_nonzero(forces) == 0)

        self._my_world.clear_instance()
        await self.setUp()

        self._my_world.get_physics_context().set_gravity(-9.81)
        await self.add_frankas()
        await self._my_world.reset_async()
        forces = self._frankas_view.get_generalized_gravity_forces()
        self.assertTrue(forces.shape == (self._frankas_view.count, self._frankas_view.num_dof))
        self.assertTrue(torch.count_nonzero(forces) == self._frankas_view.count * self._frankas_view.num_dof)

    async def test_masses(self):
        await self.add_frankas()
        cur_values = self._frankas_view.get_body_masses()
        new_values = cur_values + 100.0
        self._frankas_view.set_body_masses(new_values)
        values = self._frankas_view.get_body_masses()
        self.assertTrue(np.allclose(values.numpy(), new_values.numpy()))

        inv_masses = self._frankas_view.get_body_inv_masses()
        self.assertTrue(inv_masses.shape == (self._frankas_view.count, self._frankas_view.num_bodies))

        self._my_world.clear_instance()
        await self.setUp(device="cuda")

        await self.add_frankas()
        cur_values = self._frankas_view.get_body_masses()
        new_values = cur_values + 100.0
        self._frankas_view.set_body_masses(new_values)
        values = self._frankas_view.get_body_masses()
        self.assertTrue(np.allclose(values.cpu().numpy(), new_values.cpu().numpy()))

        inv_masses = self._frankas_view.get_body_inv_masses()
        self.assertTrue(inv_masses.shape == (self._frankas_view.count, self._frankas_view.num_bodies))

    async def test_com(self):
        await self.add_frankas()
        cur_pos, cur_ori = self._frankas_view.get_body_coms()
        new_pos = cur_pos + 0.1
        self._frankas_view.set_body_coms(new_pos, cur_ori)
        pos, ori = self._frankas_view.get_body_coms()
        self.assertTrue(np.allclose(new_pos.numpy(), pos.numpy()))
        self.assertTrue(np.allclose(cur_ori.numpy(), ori.numpy()))

    async def test_inertias(self):
        await self.add_frankas()
        cur_values = self._frankas_view.get_body_inertias()
        new_values = cur_values.clone()
        new_values[:, :, [0, 4, 8]] += 0.1
        self._frankas_view.set_body_inertias(new_values)
        values = self._frankas_view.get_body_inertias()
        self.assertTrue(np.allclose(values.numpy(), new_values.numpy()))

        inv_masses = self._frankas_view.get_body_inv_inertias()
        self.assertTrue(inv_masses.shape == (self._frankas_view.count, self._frankas_view.num_bodies, 9))

        self._my_world.clear_instance()
        await self.setUp(device="cuda")

        await self.add_frankas()
        cur_values = self._frankas_view.get_body_inertias()
        new_values = cur_values.clone()
        new_values[:, :, [0, 4, 8]] += 0.1
        self._frankas_view.set_body_inertias(new_values)
        values = self._frankas_view.get_body_inertias()
        self.assertTrue(np.allclose(values.cpu().numpy(), new_values.cpu().numpy()))

        inv_masses = self._frankas_view.get_body_inv_inertias()
        self.assertTrue(inv_masses.shape == (self._frankas_view.count, self._frankas_view.num_bodies, 9))

    async def test_fixed_tendon_properties(self):
        await self.add_shadow_hands()
        stiffness = self._hands_view.get_fixed_tendon_stiffnesses()
        dampings = self._hands_view.get_fixed_tendon_dampings()
        limit_stiffness = self._hands_view.get_fixed_tendon_limit_stiffnesses()
        limits = self._hands_view.get_fixed_tendon_limits()
        rest_lengths = self._hands_view.get_fixed_tendon_rest_lengths()
        offsets = self._hands_view.get_fixed_tendon_offsets()

        new_stiffness = stiffness + 0.01
        new_dampings = dampings + 0.01
        new_limit_stiffness = limit_stiffness + 0.01
        new_limits = limits + 0.01
        new_rest_lengths = rest_lengths + 0.01
        new_offsets = offsets + 0.01

        self._hands_view.set_fixed_tendon_properties(
            stiffnesses=new_stiffness,
            dampings=new_dampings,
            limit_stiffnesses=new_limit_stiffness,
            limits=new_limits,
            rest_lengths=new_rest_lengths,
            offsets=new_offsets,
        )

        self.assertTrue(np.allclose(self._hands_view.get_fixed_tendon_stiffnesses().numpy(), new_stiffness.numpy()))
        self.assertTrue(np.allclose(self._hands_view.get_fixed_tendon_dampings().numpy(), new_dampings.numpy()))
        self.assertTrue(
            np.allclose(self._hands_view.get_fixed_tendon_limit_stiffnesses().numpy(), new_limit_stiffness.numpy())
        )
        self.assertTrue(np.allclose(self._hands_view.get_fixed_tendon_limits().numpy(), new_limits.numpy()))
        self.assertTrue(np.allclose(self._hands_view.get_fixed_tendon_rest_lengths().numpy(), new_rest_lengths.numpy()))
        self.assertTrue(np.allclose(self._hands_view.get_fixed_tendon_offsets().numpy(), new_offsets.numpy()))

        self._my_world.clear_instance()
        await self.setUp(device="cuda")

        await self.add_shadow_hands()
        stiffness = self._hands_view.get_fixed_tendon_stiffnesses()
        dampings = self._hands_view.get_fixed_tendon_dampings()
        limit_stiffness = self._hands_view.get_fixed_tendon_limit_stiffnesses()
        limits = self._hands_view.get_fixed_tendon_limits()
        rest_lengths = self._hands_view.get_fixed_tendon_rest_lengths()
        offsets = self._hands_view.get_fixed_tendon_offsets()

        new_stiffness = stiffness + 0.01
        new_dampings = dampings + 0.01
        new_limit_stiffness = limit_stiffness + 0.01
        new_limits = limits + 0.01
        new_rest_lengths = rest_lengths + 0.01
        new_offsets = offsets + 0.01

        self._hands_view.set_fixed_tendon_properties(
            stiffnesses=new_stiffness,
            dampings=new_dampings,
            limit_stiffnesses=new_limit_stiffness,
            limits=new_limits,
            rest_lengths=new_rest_lengths,
            offsets=new_offsets,
        )
