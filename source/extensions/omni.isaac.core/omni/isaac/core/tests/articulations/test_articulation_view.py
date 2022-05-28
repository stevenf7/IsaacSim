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
    async def setUp(self):
        await create_new_stage_async()
        self._my_world = World(stage_units_in_meters=1.0, backend="torch")
        await self._my_world.initialize_simulation_context_async()
        await omni.kit.app.get_app().next_update_async()
        self._my_world.scene.add_default_ground_plane()
        assets_root_path = get_assets_root_path()
        asset_path = assets_root_path + "/Isaac/Robots/Franka/franka_alt_fingers.usd"
        add_reference_to_stage(usd_path=asset_path, prim_path="/World/Franka_1")
        add_reference_to_stage(usd_path=asset_path, prim_path="/World/Franka_2")
        self._frankas_view = ArticulationView(prim_paths_expr="/World/Franka_[1-2]", name="frankas_view")
        self._my_world.scene.add(self._frankas_view)
        await self._my_world.reset_async()
        pass

    async def tearDown(self):
        self._my_world.clear_instance()

    async def test_world_poses(self):
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
        self._frankas_view.switch_control_mode(mode="velocity")
        kps, kds = self._frankas_view.get_gains()
        self.assertTrue(not np.any(kps.numpy()))
        self.assertTrue(np.any(kds.numpy()))

    async def test_max_effort(self):
        gt_efforts = torch.tensor(
            [
                [100.0, 100.0, 100.0, 100.0, 100.0, 100.0, 100.0, 100.0, 500.0],
                [100.0, 100.0, 100.0, 100.0, 100.0, 100.0, 100.0, 100.0, 400.0],
            ]
        )
        self._frankas_view.set_max_efforts(gt_efforts)
        new_efforts = self._frankas_view.get_max_efforts()
        self.assertTrue(np.isclose(gt_efforts.numpy(), new_efforts.numpy()).all())

    async def test_physics_callback(self):
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
        new_translations = torch.tensor([[0, 1.0, 0], [0, 2.0, 0]])
        self._frankas_view.set_local_poses(translations=new_translations)
        return

    async def test_physics_properties(self):
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
