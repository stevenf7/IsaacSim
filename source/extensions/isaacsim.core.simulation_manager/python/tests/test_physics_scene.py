# SPDX-FileCopyrightText: Copyright (c) 2024-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import dataclasses

import isaacsim.core.experimental.utils.stage as stage_utils
import omni.kit.test
from isaacsim.core.simulation_manager import PhysicsScene, PhysxGpuCfg, PhysxScene


class TestPhysxScene(omni.kit.test.AsyncTestCase):
    async def setUp(self):
        """Method called to prepare the test fixture"""
        super().setUp()
        # ---------------
        await stage_utils.create_new_stage_async()
        # ---------------

    async def tearDown(self):
        """Method called immediately after the test method has been called"""
        # ------------------
        # Do custom tearDown
        # ------------------
        super().tearDown()

    # --------------------------------------------------------------------
    async def test_physx_scene_constructor(self):
        # no PhysicsScene in stage (create new)
        self.assertListEqual(PhysicsScene.get_physics_scene_paths(), [])
        path = "/physicsScene_0"
        physx_scene = PhysxScene(path)
        self.assertEqual(physx_scene.path, path)
        self.assertEqual(physx_scene.prim.GetPath().pathString, path)
        self.assertEqual(physx_scene.physics_scene.GetPrim().GetPath().pathString, path)
        # PhysicsScene already in stage (wrap existing)
        path = "/physicsScene_1"
        prim = stage_utils.define_prim(path, type_name="PhysicsScene")
        self.assertListEqual(PhysicsScene.get_physics_scene_paths(), ["/physicsScene_0", path])
        physx_scene = PhysxScene(prim)
        self.assertEqual(physx_scene.path, path)
        self.assertEqual(physx_scene.prim.GetPath().pathString, path)
        self.assertEqual(physx_scene.physics_scene.GetPrim().GetPath().pathString, path)
        # wrap non-PhysicsScene prim
        stage_utils.define_prim("/cube", type_name="Cube")
        with self.assertRaises(ValueError):
            PhysxScene("/cube")

    async def test_get_physics_scene_paths(self):
        stages = [None, stage_utils.get_current_stage()]
        # no PhysicsScene in stage
        for stage in stages:
            paths = PhysicsScene.get_physics_scene_paths(stage)
            self.assertListEqual(paths, [])
        # one PhysicsScene in stage
        stage_utils.define_prim("/World/physicsScene", type_name="PhysicsScene")
        for stage in stages:
            paths = PhysicsScene.get_physics_scene_paths(stage)
            self.assertListEqual(paths, ["/World/physicsScene"])
        # several PhysicsScene(s)
        for i in range(5):
            stage_utils.define_prim(f"/World/physicsScene_{i}", type_name="PhysicsScene")
        for stage in stages:
            paths = PhysicsScene.get_physics_scene_paths(stage)
            self.assertListEqual(paths, ["/World/physicsScene"] + [f"/World/physicsScene_{i}" for i in range(5)])

    async def test_steps_per_second_and_dt(self):
        physx_scene = PhysxScene("/World/physicsScene")
        self.assertEqual(physx_scene.get_steps_per_second(), 60)
        self.assertAlmostEqual(physx_scene.get_dt(), 1.0 / 60.0)
        # steps per second
        for steps_per_second in [120, 30]:
            physx_scene.set_steps_per_second(steps_per_second)
            self.assertEqual(physx_scene.get_steps_per_second(), steps_per_second)
            self.assertAlmostEqual(physx_scene.get_dt(), 1.0 / steps_per_second)
        # dt
        for dt in [0.01, 0.005]:
            physx_scene.set_dt(dt)
            self.assertEqual(physx_scene.get_steps_per_second(), int(1.0 / dt))
            self.assertAlmostEqual(physx_scene.get_dt(), dt)
        # special case: zero
        physx_scene.set_steps_per_second(0)
        self.assertEqual(physx_scene.get_steps_per_second(), 0)
        self.assertEqual(physx_scene.get_dt(), 0.0)
        physx_scene.set_dt(0.0)
        self.assertEqual(physx_scene.get_steps_per_second(), 0)
        self.assertEqual(physx_scene.get_dt(), 0.0)
        # exceptions
        self.assertRaises(ValueError, physx_scene.set_steps_per_second, -1)
        self.assertRaises(ValueError, physx_scene.set_dt, -1.0)
        self.assertRaises(ValueError, physx_scene.set_dt, 1.1)

    async def test_solver_type(self):
        physx_scene = PhysxScene("/World/physicsScene")
        self.assertEqual(physx_scene.get_solver_type(), "TGS")
        for solver_type in ["TGS", "PGS"]:
            physx_scene.set_solver_type(solver_type)
            self.assertEqual(physx_scene.get_solver_type(), solver_type)

    async def test_enabled_gpu_dynamics(self):
        physx_scene = PhysxScene("/World/physicsScene")
        self.assertTrue(physx_scene.get_enabled_gpu_dynamics())
        for enabled in [False, True]:
            physx_scene.set_enabled_gpu_dynamics(enabled)
            self.assertEqual(physx_scene.get_enabled_gpu_dynamics(), enabled)

    async def test_enabled_ccd(self):
        physx_scene = PhysxScene("/World/physicsScene")
        self.assertFalse(physx_scene.get_enabled_ccd())
        for enabled in [True, False]:
            physx_scene.set_enabled_ccd(enabled)
            self.assertEqual(physx_scene.get_enabled_ccd(), enabled)

    async def test_broadphase_type(self):
        physx_scene = PhysxScene("/World/physicsScene")
        self.assertEqual(physx_scene.get_broadphase_type(), "GPU")
        for broadphase_type in ["MBP", "GPU", "SAP"]:
            physx_scene.set_broadphase_type(broadphase_type)
            self.assertEqual(physx_scene.get_broadphase_type(), broadphase_type)

    async def test_enabled_stabilization(self):
        physx_scene = PhysxScene("/World/physicsScene")
        self.assertFalse(physx_scene.get_enabled_stabilization())
        for enabled in [True, False]:
            physx_scene.set_enabled_stabilization(enabled)
            self.assertEqual(physx_scene.get_enabled_stabilization(), enabled)

    async def test_gpu_configuration(self):
        physx_scene = PhysxScene("/World/physicsScene")
        config = [
            ("gpu_collision_stack_size", 67108864),
            ("gpu_found_lost_aggregate_pairs_capacity", 1024),
            ("gpu_found_lost_pairs_capacity", 262144),
            ("gpu_heap_capacity", 67108864),
            ("gpu_max_deformable_surface_contacts", 1048576),
            ("gpu_max_num_partitions", 8),
            ("gpu_max_particle_contacts", 1048576),
            ("gpu_max_rigid_contact_count", 524288),
            ("gpu_max_rigid_patch_count", 81920),
            ("gpu_max_soft_body_contacts", 1048576),
            ("gpu_temp_buffer_capacity", 16777216),
            ("gpu_total_aggregate_pairs_capacity", 1024),
        ]
        # check for configuration fields
        self.assertListEqual(
            sorted(dataclasses.asdict(PhysxGpuCfg()).keys()),
            sorted([name for name, _ in config]),
        )
        # check for configuration values
        for i, (name, value) in enumerate(config):
            self.assertEqual(
                dataclasses.asdict(physx_scene.get_gpu_configuration())[name],
                value,
                msg=f"Invalid '{name}' default value",
            )
            physx_scene.set_gpu_configuration({name: i})
            self.assertEqual(
                dataclasses.asdict(physx_scene.get_gpu_configuration())[name],
                i,
                msg=f"Invalid '{name}' expected value",
            )
