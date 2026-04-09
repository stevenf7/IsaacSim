# SPDX-FileCopyrightText: Copyright (c) 2021-2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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

from __future__ import annotations

import asyncio
import time

import omni.kit.commands
import omni.kit.test
from pxr import Gf, PhysxSchema, UsdGeom, UsdPhysics
from usdrt import Sdf, Usd


# Having a test class dervived from omni.kit.test.AsyncTestCase declared on the root of module will make it auto-discoverable by omni.kit.test
async def simulate_async(seconds: float, steps_per_sec: int = 60) -> None:
    """Helper function to simulate async for seconds * steps_per_sec frames.

    Args:
        seconds: Time in seconds to simulate for.
        steps_per_sec: Steps per second.
    """
    for frame in range(int(steps_per_sec * seconds)):
        await omni.kit.app.get_app().next_update_async()


def add_cube(
    stage: Usd.Stage, path: str, size: float, offset: tuple[float, float, float], physics: bool = False
) -> Usd.Prim:
    """Creates a cube geometry primitive in the USD stage.

    Args:
        stage: The USD stage to create the cube in.
        path: Path where the cube primitive will be created.
        size: Size of the cube.
        offset: Translation offset as (x, y, z) coordinates.
        physics: Whether to apply rigid body physics to the cube.

    Returns:
        The created cube primitive.
    """
    cubeGeom = UsdGeom.Cube.Define(stage, path)
    cubePrim = stage.GetPrimAtPath(path)

    cubeGeom.CreateSizeAttr(size)
    cubeGeom.AddTranslateOp().Set(offset)
    if physics:
        rigid_api = UsdPhysics.RigidBodyAPI.Apply(cubePrim)
        rigid_api.CreateRigidBodyEnabledAttr(True)

    UsdPhysics.CollisionAPI.Apply(cubePrim)
    return cubePrim


def create_physics_scene(stage: Usd.Stage, gravity: float = 9.81) -> None:
    """Creates a physics scene with gravity and PhysX settings.

    Args:
        stage: The USD stage to create the physics scene in.
        gravity: Gravity magnitude value.
    """
    scene = UsdPhysics.Scene.Define(stage, "/physics")
    scene.CreateGravityDirectionAttr().Set(Gf.Vec3f(0.0, 0.0, -1.0))
    scene.CreateGravityMagnitudeAttr().Set(gravity)

    PhysxSchema.PhysxSceneAPI.Apply(stage.GetPrimAtPath("/physics"))
    physxSceneAPI = PhysxSchema.PhysxSceneAPI.Get(stage, "/physics")
    physxSceneAPI.CreateEnableCCDAttr(True)
    physxSceneAPI.CreateEnableStabilizationAttr(True)
    physxSceneAPI.CreateEnableGPUDynamicsAttr(False)
    physxSceneAPI.CreateBroadphaseTypeAttr("MBP")
    physxSceneAPI.CreateSolverTypeAttr("TGS")


class TestConveyor(omni.kit.test.AsyncTestCase):
    """Test suite for conveyor belt functionality in Isaac Sim.

    This class provides comprehensive testing for the conveyor belt system, including creation,
    velocity control, physics interactions, and performance validation. It tests both linear
    and angular conveyor belt movements, physics-enabled and physics-disabled scenarios,
    and validates that objects placed on conveyor belts move correctly according to the
    conveyor's velocity and direction settings.

    The tests cover:
    - Creating conveyor belts from cube primitives
    - Setting linear and angular velocities
    - Validating physics interactions with objects on the conveyor
    - Testing conveyor belts in different directions
    - Performance testing with multiple conveyor belts
    - Proper cleanup and teardown procedures
    """

    # Before running each test
    async def setUp(self) -> None:
        """Set up the test environment before each test.

        Initializes the conveyor node, creates a new USD stage, sets up the timeline,
        and creates a physics scene for the test.
        """
        self.conveyor_node = None
        await omni.usd.get_context().new_stage_async()
        self._stage = omni.usd.get_context().get_stage()
        self._timeline = omni.timeline.get_timeline_interface()
        create_physics_scene(self._stage)
        await omni.kit.app.get_app().next_update_async()
        pass

    # After running each test
    async def tearDown(self) -> None:
        """Clean up the test environment after each test.

        Stops the timeline, clears the conveyor node, and waits for any loading assets
        to finish before proceeding.
        """
        await omni.kit.app.get_app().next_update_async()
        self._timeline.stop()
        self.conveyor_node = None
        while omni.usd.get_context().get_stage_loading_status()[2] > 0:
            print("tearDown, assets still loading, waiting to finish...")
            await asyncio.sleep(1.0)
        await omni.kit.app.get_app().next_update_async()
        pass

    async def test_add_conveyor(self, physics: bool = True) -> None:
        """Test creating a conveyor belt with a cube primitive.

        Creates a cube primitive, applies rigid body properties if physics is enabled,
        and creates a conveyor belt using the CreateConveyorBelt command.

        Args:
            physics: Whether to enable physics on the cube.
        """
        stage = omni.usd.get_context().get_stage()
        cube_prim = add_cube(self._stage, "/cube", 1.00, (0, 0, 0), physics=physics)
        rigid_prim = UsdPhysics.RigidBodyAPI(cube_prim)
        if rigid_prim:
            rigid_prim.GetKinematicEnabledAttr().Set(True)
        _, og_prim = omni.kit.commands.execute("CreateConveyorBelt", conveyor_prim=cube_prim)
        self.assertIsNotNone(og_prim)
        self.conveyor_node = og_prim
        self.velocity_attr = stage.GetPrimAtPath("/ConveyorBeltGraph").GetAttribute("graph:variable:Velocity")
        self.assertTrue(self.conveyor_node.IsValid())
        pass

    async def test_add_conveyor_without_physics(self) -> None:
        """Test creating a conveyor belt without physics enabled on the cube."""
        await self.test_add_conveyor(physics=False)

    async def test_set_velocity(self, direction: list[float] | None = None) -> None:
        """Test setting the velocity of a conveyor belt.

        Creates a conveyor belt, sets its direction and velocity, plays the timeline,
        and verifies that the surface velocity matches the expected value.

        Args:
            direction: Direction vector for the conveyor belt movement.
        """
        if direction is None:
            direction = [1.0, 0.0, 0.0]
        await self.test_add_conveyor()
        dir_attr = self.conveyor_node.GetAttribute("inputs:direction")
        dir_attr.Set(Gf.Vec3f(*direction))
        attr = self.conveyor_node.GetAttribute("inputs:velocity")
        self.velocity_attr.Set(0.10)
        self.assertAlmostEqual(self.velocity_attr.Get(), 0.10, delta=1e-4)
        self._timeline.play()
        await simulate_async(0.4)
        rigid_prim = UsdPhysics.RigidBodyAPI(self._stage.GetPrimAtPath("/cube"))
        surface_velocity = PhysxSchema.PhysxSurfaceVelocityAPI(rigid_prim)
        usd_velocity = surface_velocity.GetSurfaceVelocityAttr().Get()
        self.assertAlmostEqual(usd_velocity.GetLength(), 0.10, delta=1e-4)
        self._timeline.stop()
        pass

    async def test_set_angular_velocity(self, direction: list[float] | None = None) -> None:
        """Test setting the angular velocity of a curved conveyor belt.

        Creates a conveyor belt, enables curved mode, sets its direction and velocity,
        plays the timeline, and verifies that the surface angular velocity matches
        the expected value.

        Args:
            direction: Direction vector for the conveyor belt angular movement.
        """
        if direction is None:
            direction = [0.0, 0.0, 1.0]
        await self.test_add_conveyor()
        dir_attr = self.conveyor_node.GetAttribute("inputs:curved")
        dir_attr.Set(True)
        dir_attr = self.conveyor_node.GetAttribute("inputs:direction")
        dir_attr.Set(Gf.Vec3f(*direction))
        self.velocity_attr.Set(0.10)
        self.assertAlmostEqual(self.velocity_attr.Get(), 0.10, delta=1e-4)
        self._timeline.play()
        await simulate_async(0.4)
        rigid_prim = UsdPhysics.RigidBodyAPI(self._stage.GetPrimAtPath("/cube"))
        rigid_prim.GetKinematicEnabledAttr().Set(True)
        surface_velocity = PhysxSchema.PhysxSurfaceVelocityAPI(rigid_prim)
        usd_velocity = surface_velocity.GetSurfaceAngularVelocityAttr().Get()
        self.assertAlmostEqual(usd_velocity.GetLength(), 0.10, delta=1e-4)
        self._timeline.stop()
        pass

    async def test_conveyor(self, d: list[float] | None = None) -> None:
        """Test conveyor belt functionality with a moving object.

        Creates a conveyor belt with specified direction, places a small cube on top,
        runs the simulation, and verifies that the cube moves in the expected direction
        with the correct velocity.

        Args:
            d: Direction vector for the conveyor belt movement.
        """
        if d is None:
            d = [1.0, 0.0, 0.0]
        await self.test_set_velocity(d)

        cube_prim = add_cube(self._stage, "/cube2", 0.1, (0, 0, 0.55), physics=True)
        self._timeline.play()
        await simulate_async(1)
        rigid_prim = UsdPhysics.RigidBodyAPI(cube_prim)
        rt_stage = Usd.Stage.Attach(omni.usd.get_context().get_stage_id())
        rt_prim = rt_stage.GetPrimAtPath(Sdf.Path(str(cube_prim.GetPath())))
        # usd_velocity = rigid_prim.GetVelocityAttr().Get()
        usd_velocity = rt_prim.GetAttribute(rigid_prim.GetVelocityAttr().GetName()).Get()
        self.assertAlmostEqual(d[0] * 0.1, usd_velocity[0], delta=1e-2)
        self.assertAlmostEqual(d[1] * 0.1, usd_velocity[1], delta=1e-2)
        self.assertAlmostEqual(d[2] * 0.1, usd_velocity[2], delta=1e-2)
        pass

    async def test_conveyor_y(self) -> None:
        """Test conveyor belt functionality with movement in the Y direction."""
        await self.test_conveyor(d=[0.0, 1.0, 0.0])

    async def test_100_conveyors(self) -> None:
        """Test performance with 100 conveyor belts.

        Creates a 10x10 grid of conveyor belts, each with different directional
        properties based on their position, runs the simulation, and measures
        performance over 100 frames.
        """
        conveyor_nodes = []
        for i in range(10):
            for j in range(10):
                cube_prim = add_cube(self._stage, f"/cube_{i}_{j}", 1.00, (i, j, 0), physics=True)
                _, og_prim = omni.kit.commands.execute("CreateConveyorBelt", conveyor_prim=cube_prim)
                self.assertIsNotNone(og_prim)
                conveyor_nodes.append(og_prim)
                self.assertTrue(conveyor_nodes[-1].IsValid())
                dir_attr = conveyor_nodes[-1].GetAttribute("inputs:direction")
                dir_attr.Set(Gf.Vec3f(*[float(i <= j), float(i > j), 0.0]))
                attr = conveyor_nodes[-1].GetAttribute("inputs:velocity")
                attr.Set(1)
        self._timeline.play()
        await simulate_async(1.0)
        t = time.time()
        # SImulate exacly 100 frames
        for i in range(100):
            await omni.kit.app.get_app().next_update_async()
