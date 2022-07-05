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
from omni.isaac.core.utils.types import DynamicsViewState

import omni.kit.test

# Import extension python module we are testing with absolute import path, as if we are external user (other extension)
from omni.isaac.core.prims import RigidPrimView

from omni.isaac.core.utils.numpy.rotations import euler_angles_to_quats as euler_angles_to_quats_numpy
from omni.isaac.core.utils.torch.rotations import euler_angles_to_quats as euler_angles_to_quats_torch

import numpy as np
import torch
import asyncio

from omni.isaac.core.utils.stage import create_new_stage_async, update_stage_async
from omni.isaac.core import World
from omni.isaac.core.objects import DynamicCuboid


default_physics_material = {"static_friction": 1.0, "dynamic_friction": 1.0, "restitution": 0.0}

default_sim_params = {
    ### Per-scene settings
    "use_gpu": False,
    "worker_thread_count": 4,
    "solver_type": 1,  # 0: PGS, 1:TGS
    "bounce_threshold_velocity": 0.2,
    "friction_offset_threshold": 0.04,  # A threshold of contact separation distance used to decide if a contact
    # point will experience friction forces.
    "friction_correlation_distance": 0.025,  # Contact points can be merged into a single friction anchor if the
    # distance between the contacts is smaller than correlation distance.
    # disabling these can be useful for debugging
    "enable_sleeping": True,
    "enable_stabilization": True,
    # GPU buffers
    "gpu_max_rigid_contact_count": 512 * 1024,
    "gpu_max_rigid_patch_count": 80 * 1024,
    "gpu_found_lost_pairs_capacity": 1024,
    "gpu_found_lost_aggregate_pairs_capacity": 1024,
    "gpu_total_aggregate_pairs_capacity": 1024,
    "gpu_max_soft_body_contacts": 1024 * 1024,
    "gpu_max_particle_contacts": 1024 * 1024,
    "gpu_heap_capacity": 64 * 1024 * 1024,
    "gpu_temp_buffer_capacity": 16 * 1024 * 1024,
    "gpu_max_num_partitions": 8,
    ### Per-actor settings ( can override in actor_options )
    "solver_position_iteration_count": 4,
    "solver_velocity_iteration_count": 1,
    "sleep_threshold": 0.0,  # Mass-normalized kinetic energy threshold below which an actor may go to sleep.
    # Allowed range [0, max_float).
    "stabilization_threshold": 0.0,  # Mass-normalized kinetic energy threshold below which an actor may
    # participate in stabilization. Allowed range [0, max_float).
    ### Per-body settings ( can override in actor_options )
    "enable_gyroscopic_forces": False,
    "density": 1000.0,  # density to be used for bodies that do not specify mass or density
    "max_depenetration_velocity": 100.0,
    ### Per-shape settings ( can override in actor_options )
    "contact_offset": 0.02,
    "rest_offset": 0.001,
    "gravity": [0.0, 0.0, 0.0],
    "dt": 1.0 / 60.0,
    "substeps": 1,
    "use_gpu_pipeline": False,
    "add_ground_plane": False,
    "default_physics_material": default_physics_material,
}


# Having a test class dervived from omni.kit.test.AsyncTestCase declared on the root of module will make it auto-discoverable by omni.kit.test
class TestRigidPrimView(omni.kit.test.AsyncTestCase):
    async def setUp(self):
        self._sim_params = default_sim_params
        self._test_cfg = dict()

    async def tearDown(self):
        pass
        self._my_world.clear_instance()

    async def test_rigid_prim_view_gpu_pipeline(self):
        test_configs = {"use_gpu": True, "use_gpu_pipeline": True, "backend": "torch", "device": "gpu"}

        self._sim_params["use_gpu"] = test_configs["use_gpu"]
        self._sim_params["use_gpu_pipeline"] = test_configs["use_gpu_pipeline"]
        self._test_cfg["use_gpu"] = test_configs["use_gpu"]
        self._test_cfg["use_gpu_pipeline"] = test_configs["use_gpu_pipeline"]
        self._test_cfg["backend"] = test_configs["backend"]
        self._test_cfg["device"] = test_configs["device"]

        self.euler_angles_to_quats = euler_angles_to_quats_torch
        self.isclose = torch.isclose
        if self._test_cfg["device"] == "gpu":
            self._array_container = torch.cuda.FloatTensor
            self._device = "cuda:0"

        await self._runner()

    async def test_rigid_prim_view_cpu_pipeline(self):
        test_configs = {
            "use_gpu": [False, False, True, True],
            "use_gpu_pipeline": [False, False, False, False],
            "backend": ["numpy", "torch", "numpy", "torch"],
            "device": ["cpu", "cpu", "cpu", "cpu"],
        }

        for i in range(0, 4):
            self._sim_params["use_gpu"] = test_configs["use_gpu"][i]
            self._sim_params["use_gpu_pipeline"] = test_configs["use_gpu_pipeline"][i]
            self._test_cfg["use_gpu"] = test_configs["use_gpu"][i]
            self._test_cfg["use_gpu_pipeline"] = test_configs["use_gpu_pipeline"][i]
            self._test_cfg["backend"] = test_configs["backend"][i]
            self._test_cfg["device"] = test_configs["device"][i]

            if self._test_cfg["backend"] == "numpy":
                self._array_container = np.array
                self.euler_angles_to_quats = euler_angles_to_quats_numpy
                self.isclose = np.isclose
                self._device = "cpu"
            elif self._test_cfg["backend"] == "torch":
                self.euler_angles_to_quats = euler_angles_to_quats_torch
                self.isclose = torch.isclose
                if self._test_cfg["device"] == "gpu":
                    self._array_container = torch.cuda.FloatTensor
                    self._device = "cuda"
                else:
                    self._array_container = torch.Tensor
                    self._device = "cpu"

            await self._runner()

    async def _runner(self):
        self._timeline = omni.timeline.get_timeline_interface()
        await create_new_stage_async()
        self._my_world = World(sim_params=self._sim_params, backend=self._test_cfg["backend"], device=self._device)
        await self._my_world.initialize_simulation_context_async()
        await update_stage_async()
        await omni.kit.app.get_app().next_update_async()
        self._my_world._physics_context.set_gravity(0)
        await omni.kit.app.get_app().next_update_async()

        num_cubes = 3
        for i in range(num_cubes):
            DynamicCuboid(
                prim_path=f"/World/Cube_{i+1}", name=f"cube_{i}", size=1.0, color=np.array([0.5, 0, 0]), mass=0.0
            )
        await update_stage_async()
        self._cubes_view = RigidPrimView(
            prim_paths_expr="/World/Cube_[1-3]",
            name="cubes_view",
            positions=self._array_container([[0.0, 0.0, 0.0], [0.0, 10.0, 0.0], [0.0, -10.0, 0.0]]),
        )
        self._my_world.scene.add(self._cubes_view)

        for indexed in [False, True]:
            self._test_cfg["indexed"] = indexed
            print(i, self._test_cfg)
            await self.world_poses_test()
            await self.linear_velocities_test()
            await self.angular_velocities_test()
            await self.transforms_test()
            await self.velocities_test()
            await self.apply_forces_test()

        # masses_test() is done seperately from the rest to ensure apply_forces_test() runs properly
        for indexed in [False, True]:
            self._test_cfg["indexed"] = indexed
            await self.masses_test()

        await self.default_state_post_reset_test()

        self._my_world.stop()
        self._my_world.clear_instance()

    async def world_poses_test(self):
        print("world poses test")
        await self._my_world.reset_async()
        await omni.kit.app.get_app().next_update_async()
        indices = [1, 2] if self._test_cfg["indexed"] else None

        new_positions = self._array_container([[25.0, -20.0, 10.0], [15.0, 10.0, 0.0], [-40.0, -40.0, 0.0]])
        new_orientations = self.euler_angles_to_quats(
            euler_angles=self._array_container([[0, np.pi / 4.0, 0], [0, 0, np.pi / 4.0], [0, 0, -np.pi / 8.0]]),
            device=self._device,
        )
        self._cubes_view.set_world_poses(
            positions=new_positions[indices].squeeze(),
            orientations=new_orientations[indices].squeeze(),
            indices=indices,
        )
        self._my_world.step_async(0)
        self._my_world._physics_sim_view.flush()
        await omni.kit.app.get_app().next_update_async()
        # await asyncio.sleep(5.0)
        current_positions, current_orientations = self._cubes_view.get_world_poses(indices=indices)
        print(current_positions)
        print(new_positions)
        self.assertTrue(self.isclose(current_positions, new_positions[indices].squeeze()).all())
        self.assertTrue(self.isclose(current_orientations, new_orientations[indices].squeeze(), atol=1e-4).all())

        return

    async def linear_velocities_test(self):
        print("linear velocities test")
        if self._device == "cpu":
            await self._my_world.reset_async()
            await omni.kit.app.get_app().next_update_async()
            indices = [1, 2] if self._test_cfg["indexed"] else None

            linear_velocities = self._array_container([[10.0, 0.0, 0.0], [20.0, 0.0, 0.0], [-10, 0, 0]])[
                indices
            ].squeeze()
            self._cubes_view.set_linear_velocities(linear_velocities, indices)
            self._my_world.step_async()
            self._my_world._physics_sim_view.flush()
            await omni.kit.app.get_app().next_update_async()
            await asyncio.sleep(0.1)

            current_linear_velocities = self._cubes_view.get_linear_velocities(indices)
            print(current_linear_velocities)
            print(linear_velocities)
            self.assertTrue(self.isclose(current_linear_velocities, linear_velocities).all())

        return

    async def angular_velocities_test(self):
        print("angular velocities test")
        if self._device == "cpu":
            await self._my_world.reset_async()
            await omni.kit.app.get_app().next_update_async()
            indices = [1, 2] if self._test_cfg["indexed"] else None

            angular_velocities = self._array_container([[20.0, 0, 0], [0, -20, 0], [0, 0, 20]])[indices].squeeze()
            self._cubes_view.set_angular_velocities(angular_velocities, indices)
            self._my_world.step_async()
            self._my_world._physics_sim_view.flush()
            await omni.kit.app.get_app().next_update_async()
            current_angular_velocities = self._cubes_view.get_angular_velocities(indices)
            print(current_angular_velocities)
            print(angular_velocities)
            self.assertTrue(self.isclose(current_angular_velocities, angular_velocities, atol=1e-1).all())
        return

    async def masses_test(self):
        print("masses test")
        await self._my_world.reset_async()
        await omni.kit.app.get_app().next_update_async()
        indices = [1, 2] if self._test_cfg["indexed"] else None

        masses = self._array_container([10, 20, 30])[indices].squeeze()
        self._cubes_view.set_masses(masses, indices)
        current_masses = self._cubes_view.get_masses(indices)
        self.assertTrue(self.isclose(masses, current_masses).all())
        return

    async def default_state_post_reset_test(self):
        print("default state post test")
        await self._my_world.reset_async()
        await omni.kit.app.get_app().next_update_async()
        indices = [1, 2] if self._test_cfg["indexed"] else None

        desired_default_state = DynamicsViewState(
            positions=self._array_container([[10.0, 10.0, 0.0], [0.0, 10.0, 0.0], [0.0, -10.0, 0.0]])[
                indices
            ].squeeze(),
            orientations=self.euler_angles_to_quats(
                self._array_container([[0.0, np.pi / 4.0, 0], [0, 0, np.pi / 4.0], [0, 0, -np.pi / 8.0]]),
                device=self._device,
            )[indices].squeeze(),
            linear_velocities=self._array_container([[0.0, 10, 0], [10, 0, 0], [-10, 0, 0]])[indices].squeeze(),
            angular_velocities=self._array_container([[0.0, 360, 0], [360, 0, 0], [-360, 0, 0]])[indices].squeeze(),
        )
        self._cubes_view.set_default_state(
            positions=desired_default_state.positions,
            orientations=desired_default_state.orientations,
            linear_velocities=desired_default_state.linear_velocities,
            angular_velocities=desired_default_state.angular_velocities,
            indices=indices,
        )
        default_state = self._cubes_view.get_default_state()
        self.assertTrue(self.isclose(desired_default_state.positions, default_state.positions[indices].squeeze()).all())
        self.assertTrue(
            self.isclose(desired_default_state.orientations, default_state.orientations[indices].squeeze()).all()
        )
        self.assertTrue(
            self.isclose(
                desired_default_state.linear_velocities, default_state.linear_velocities[indices].squeeze()
            ).all()
        )
        self.assertTrue(
            self.isclose(
                desired_default_state.angular_velocities, default_state.angular_velocities[indices].squeeze()
            ).all()
        )

        if not self._test_cfg["indexed"]:
            # resets to default state
            self._cubes_view.post_reset()
            current_state = self._cubes_view.get_current_dynamic_state()
            self.assertTrue(self.isclose(desired_default_state.positions, current_state.positions).all())
            self.assertTrue(self.isclose(desired_default_state.orientations, current_state.orientations).all())
            self.assertTrue(
                self.isclose(desired_default_state.linear_velocities, current_state.linear_velocities).all()
            )
            self.assertTrue(
                self.isclose(desired_default_state.angular_velocities, current_state.angular_velocities).all()
            )

    async def transforms_test(self):
        print("transforms test")
        await self._my_world.reset_async()
        await omni.kit.app.get_app().next_update_async()
        indices = [1, 2] if self._test_cfg["indexed"] else None

        new_transforms = self._array_container(
            [
                [25.0, -20.0, 10.0, 0.0, 0.0, 1.0, 0.0],
                [15.0, 10.0, 0.0, 0.0, 0.0, 1.0, 0.0],
                [-45.0, -40.0, 0.0, 0.0, 0.0, 1.0, 0.0],
            ]
        )[indices].squeeze()
        self._cubes_view.set_world_poses(
            positions=new_transforms[:, 0:3], orientations=new_transforms[:, 3:], indices=indices
        )
        self._my_world.step_async()
        self._my_world._physics_sim_view.flush()
        await omni.kit.app.get_app().next_update_async()
        current_positions, current_orientations = self._cubes_view.get_world_poses(indices=indices)
        self.assertTrue(self.isclose(current_positions, new_transforms[:, 0:3]).all())
        self.assertTrue(self.isclose(current_orientations, new_transforms[:, 3:]).all())
        return

    async def velocities_test(self):
        print("velocities test")
        await self._my_world.reset_async()
        await omni.kit.app.get_app().next_update_async()
        indices = [1, 2] if self._test_cfg["indexed"] else None

        velocities = self._array_container(
            [[10.0, 0.0, 0.0, 20.0, 0.0, 0.0], [20.0, 0.0, 0.0, 0.0, -20.0, 0.0], [-10.0, 0.0, 0.0, 0.0, 0.0, 20.0]]
        )[indices].squeeze()
        self._cubes_view.set_velocities(velocities, indices)
        self._my_world.step_async()
        self._my_world._physics_sim_view.flush()
        await omni.kit.app.get_app().next_update_async()
        current_velocities = self._cubes_view.get_velocities(indices)
        self.assertTrue(self.isclose(current_velocities, velocities, atol=1e-1).all())
        return

    async def apply_forces_test(self):
        print("apply forces test")
        await self._my_world.reset_async()
        await omni.kit.app.get_app().next_update_async()
        indices = [1, 2] if self._test_cfg["indexed"] else None

        new_positions = self._array_container([[20.0, -20.0, 10.0], [30.0, 30.0, 0], [-40, -40, 0]])
        new_orientations = self.euler_angles_to_quats(
            euler_angles=self._array_container([[0.0, 0, 0], [0, 0, 0], [0, 0, 0]]), device=self._device
        )
        self._cubes_view.set_world_poses(
            positions=new_positions[indices].squeeze(),
            orientations=new_orientations[indices].squeeze(),
            indices=indices,
        )

        forces = self._array_container([[3000, 0, 0], [-3000, 0, 0], [3000, 0, 0]])[indices].squeeze()
        self._cubes_view.apply_forces(forces, indices)
        self._my_world.step_async()
        self._my_world._physics_sim_view.flush()
        await omni.kit.app.get_app().next_update_async()

        current_linear_velocities = self._cubes_view.get_linear_velocities(indices)

        self.assertTrue(
            self.isclose(
                current_linear_velocities[:, 1:], self._array_container([[0, 0], [0, 0], [0, 0]])[indices].squeeze()
            ).all()
        )

        if self._test_cfg["backend"] == "numpy":
            self.assertTrue(
                np.logical_not(
                    self.isclose(current_linear_velocities[:, 0], self._array_container([0, 0, 0])[indices].squeeze())
                ).all()
            )
        elif self._test_cfg["backend"] == "torch":
            self.assertTrue(
                torch.logical_not(
                    self.isclose(current_linear_velocities[:, 0], self._array_container([0, 0, 0])[indices].squeeze())
                ).all()
            )
