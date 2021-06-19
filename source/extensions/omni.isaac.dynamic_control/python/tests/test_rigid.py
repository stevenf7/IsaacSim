# Copyright (c) 2018-2021, NVIDIA CORPORATION.  All rights reserved.
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

import carb.tokens

# carb data types are used as return values, need this
import carb
import asyncio
from pxr import Gf, PhysxSchema, UsdPhysics, Sdf, UsdGeom

# Import extension python module we are testing with absolute import path, as if we are external user (other extension)
from omni.isaac.dynamic_control import _dynamic_control
from .common import load_test_file, set_scene_physics_type

# Having a test class dervived from omni.kit.test.AsyncTestCase declared on the root of module will make it auto-discoverable by omni.kit.test
class TestRigidBody(omni.kit.test.AsyncTestCaseFailOnLogError):
    # Before running each test
    async def setUp(self):
        self._dc = _dynamic_control.acquire_dynamic_control_interface()
        self._timeline = omni.timeline.get_timeline_interface()

        ext_manager = omni.kit.app.get_app().get_extension_manager()
        ext_id = ext_manager.get_enabled_extension_id("omni.isaac.dynamic_control")
        self._extension_path = ext_manager.get_extension_path(ext_id)

        self._physics_rate = 60
        carb.settings.get_settings().set_bool("/app/runLoops/main/rateLimitEnabled", True)
        carb.settings.get_settings().set_int("/app/runLoops/main/rateLimitFrequency", int(self._physics_rate))
        carb.settings.get_settings().set_int("/persistent/simulation/minFrameRate", int(self._physics_rate))

        await omni.kit.app.get_app().next_update_async()
        pass

    # After running each test
    async def tearDown(self):
        await omni.kit.app.get_app().next_update_async()
        pass

    async def simulate(self, seconds, art=None, steps_per_sec=60):
        for frame in range(int(steps_per_sec * seconds)):
            if art is not None:
                self._dc.wake_up_articulation(art)
            await omni.kit.app.get_app().next_update_async()

    async def add_cube(self, path, size, offset, physics=True):

        cubeGeom = UsdGeom.Cube.Define(self._stage, path)
        cubePrim = self._stage.GetPrimAtPath(path)
        cubeGeom.CreateSizeAttr(size)
        cubeGeom.AddTranslateOp().Set(offset)
        await omni.kit.app.get_app().next_update_async()  # Need this to avoid flatcache errors
        if physics:
            rigid_api = UsdPhysics.RigidBodyAPI.Apply(cubePrim)
            rigid_api.CreateRigidBodyEnabledAttr(True)
        UsdPhysics.CollisionAPI.Apply(cubePrim)

        return cubePrim

    # Actual test, notice it is "async" function, so "await" can be used if needed
    async def test_gravity(self, gpu=False):
        await omni.usd.get_context().new_stage_async()
        self._stage = omni.usd.get_context().get_stage()

        scene = UsdPhysics.Scene.Define(self._stage, Sdf.Path("/World/physicsScene"))
        scene.CreateGravityDirectionAttr().Set(Gf.Vec3f(0.0, 0.0, -1.0))
        scene.CreateGravityMagnitudeAttr().Set(981.0)
        prim = await self.add_cube("/cube", 100, (0, 0, 100))
        await omni.kit.app.get_app().next_update_async()

        self._timeline.play()
        await omni.kit.app.get_app().next_update_async()
        handle = self._dc.get_rigid_body("/cube")

        pos = self._dc.get_rigid_body_pose(handle).p

        self._dc.set_rigid_body_disable_gravity(handle, True)
        self._dc.wake_up_rigid_body(handle)
        self._dc.set_rigid_body_linear_velocity(handle, (0, 0, 0))
        await self.simulate(1.0)
        pos = self._dc.get_rigid_body_pose(handle).p

        self.assertAlmostEqual(pos.z, 99.7, delta=0.1)

        self._dc.set_rigid_body_disable_gravity(handle, False)
        self._dc.wake_up_rigid_body(handle)
        await self.simulate(1.0)
        pos = self._dc.get_rigid_body_pose(handle).p
        self.assertLess(pos.z, 0)

        pass
