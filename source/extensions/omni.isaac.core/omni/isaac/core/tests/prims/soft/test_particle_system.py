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
from omni.isaac.core.utils.prims import define_prim
import omni.kit.test
from omni.isaac.core import World

# Import extension python module we are testing with absolute import path, as if we are external user (other extension)
from pxr import Gf, Usd, UsdGeom
from omni.isaac.core.prims import ParticleSystem
from omni.isaac.core.utils.stage import create_new_stage_async, update_stage_async
from omni.isaac.core.tests.test_semantics import TestProperties

# Having a test class dervived from omni.kit.test.AsyncTestCase declared on the root of module will make it auto-discoverable by omni.kit.test
class TestParticleSystem(omni.kit.test.AsyncTestCase, TestProperties):
    async def setUp(self):
        World.clear_instance()
        await create_new_stage_async()
        self.my_world = World(backend="torch", device="cuda")
        await self.my_world.initialize_simulation_context_async()
        self._test_cfg = dict()
        pass

    async def tearDown(self):
        World.clear_instance()
        await update_stage_async()
        pass

    async def test_particle_system(self):
        await update_stage_async()
        self.stage = omni.usd.get_context().get_stage()
        radius = 0.5 * (0.6 / 5.0)
        restOffset = radius
        contactOffset = restOffset * 1.5
        self.particle_system = ParticleSystem(
            prim_path="/particleSystem",
            simulation_owner=self.my_world.get_physics_context().prim_path,
            rest_offset=restOffset,
            contact_offset=contactOffset,
            solid_rest_offset=restOffset,
            fluid_rest_offset=restOffset,
            particle_contact_offset=contactOffset,
        )
        await update_stage_async()
        await self.scalar_prop_test(self.particle_system.get_rest_offset, self.particle_system.set_rest_offset)
        await self.scalar_prop_test(
            self.particle_system.get_solid_rest_offset, self.particle_system.set_solid_rest_offset
        )
        await self.scalar_prop_test(
            self.particle_system.get_fluid_rest_offset, self.particle_system.set_fluid_rest_offset
        )
        await self.scalar_prop_test(self.particle_system.get_contact_offset, self.particle_system.set_contact_offset)
        await self.scalar_prop_test(
            self.particle_system.get_particle_contact_offset, self.particle_system.set_particle_contact_offset
        )
        await self.scalar_prop_test(
            self.particle_system.get_max_depenetration_velocity, self.particle_system.set_max_depenetration_velocity
        )
        await self.scalar_prop_test(self.particle_system.get_max_velocity, self.particle_system.set_max_velocity)

        # bool properties
        await self.bool_prop_test(self.particle_system.get_enable_ccd, self.particle_system.set_enable_ccd)
        await self.bool_prop_test(
            self.particle_system.get_global_self_collision_enabled,
            self.particle_system.set_global_self_collision_enabled,
        )
        await self.bool_prop_test(
            self.particle_system.get_particle_system_enabled, self.particle_system.set_particle_system_enabled
        )

        # int properties
        await self.bool_prop_test(self.particle_system.get_max_neighborhood, self.particle_system.set_max_neighborhood)

        # vector properties
        await self.vector_prop_test(self.particle_system.get_wind, self.particle_system.set_wind)

        self.my_world.stop()
        self.my_world.clear_instance()
