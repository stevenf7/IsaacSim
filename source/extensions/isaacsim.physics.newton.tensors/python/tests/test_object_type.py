# SPDX-FileCopyrightText: Copyright (c) 2024-2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""Tests for SimulationView.get_object_type with the Newton backend."""

from __future__ import annotations

import omni.physics.tensors as tensors

from .test_helpers import NewtonTensorTestBase, run_on_device_configs


@run_on_device_configs()
class TestObjectTypeRigidBody(NewtonTensorTestBase):
    """Standalone rigid bodies should be classified as RigidBody."""

    async def test_rigid_body(self):
        self.setup_ball_grid(num_envs=2)
        sim = await self.create_sim()

        otype = sim.get_object_type("/envs/env0/ball")
        self.assertEqual(otype, tensors.ObjectType.RigidBody, "Standalone rigid body should return RigidBody")

    async def test_invalid_path(self):
        self.setup_ball_grid(num_envs=2)
        sim = await self.create_sim()

        otype = sim.get_object_type("/nonexistent/path")
        self.assertEqual(otype, tensors.ObjectType.Invalid, "Unknown path should return Invalid")


@run_on_device_configs()
class TestObjectTypeArticulation(NewtonTensorTestBase):
    """Articulation links and joints should be classified correctly."""

    async def test_articulation_root_link(self):
        self.setup_ant_grid(num_envs=2)
        sim = await self.create_sim()

        otype = sim.get_object_type("/envs/env0/ant/torso")
        self.assertEqual(
            otype, tensors.ObjectType.ArticulationRootLink, "Articulation root body should return ArticulationRootLink"
        )

    async def test_articulation_link(self):
        self.setup_ant_grid(num_envs=2)
        sim = await self.create_sim()

        otype = sim.get_object_type("/envs/env0/ant/front_left_leg")
        self.assertEqual(
            otype, tensors.ObjectType.ArticulationLink, "Non-root articulation body should return ArticulationLink"
        )

    async def test_articulation_joint(self):
        self.setup_ant_grid(num_envs=2)
        sim = await self.create_sim()

        otype = sim.get_object_type("/envs/env0/ant/joints/front_left_leg")
        self.assertEqual(
            otype, tensors.ObjectType.ArticulationJoint, "Articulation joint should return ArticulationJoint"
        )

    async def test_nonphysics_xform(self):
        self.setup_ant_grid(num_envs=2)
        sim = await self.create_sim()

        otype = sim.get_object_type("/envs/env0/ant")
        self.assertEqual(otype, tensors.ObjectType.Invalid, "Non-physics xform should return Invalid")
