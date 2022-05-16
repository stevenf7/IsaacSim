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
from omni.isaac.core.utils.torch.rotations import euler_angles_to_quats
import numpy as np
from omni.isaac.core.utils.stage import create_new_stage_async, add_reference_to_stage
from omni.isaac.core.utils.nucleus import get_assets_root_path
from omni.isaac.core import World
import torch


# Having a test class dervived from omni.kit.test.AsyncTestCase declared on the root of module will make it auto-discoverable by omni.kit.test
class TestArticulationView(omni.kit.test.AsyncTestCaseFailOnLogError):
    async def setUp(self):
        await create_new_stage_async()
        self._my_world = World(stage_units_in_meters=1.0, backend="torch")
        await self._my_world.initialize_simulation_context_async()
        await omni.kit.app.get_app().next_update_async()
        self._my_world.scene.add_default_ground_plane()
        assets_root_path = get_assets_root_path()
        asset_path = assets_root_path + "/Robots/Franka/franka_alt_fingers.usd"
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
