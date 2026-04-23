# SPDX-FileCopyrightText: Copyright (c) 2025-2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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

"""Test physics raycast sensor functionality."""

from __future__ import annotations

import omni.kit.test
import omni.timeline
import omni.usd
from isaacsim.core.experimental.objects import Cube
from isaacsim.core.experimental.prims import GeomPrim, RigidPrim
from isaacsim.core.simulation_manager import SimulationManager
from isaacsim.sensors.experimental.physics import RaycastSensor, RaycastSensorBackend
from pxr import Gf, Sdf, UsdGeom, UsdPhysics

from .common import step_simulation


class TestRaycastSensor(omni.kit.test.AsyncTestCase):
    """Test physics raycast sensor on dynamic rigid bodies."""

    async def setUp(self):
        """Set up test fixtures."""
        self._timeline = omni.timeline.get_timeline_interface()
        await omni.usd.get_context().new_stage_async()
        await omni.kit.app.get_app().next_update_async()

    async def tearDown(self):
        """Tear down test fixtures."""
        if self._timeline.is_playing():
            self._timeline.stop()
        SimulationManager.invalidate_physics()
        await omni.kit.app.get_app().next_update_async()

    async def test_sensor_follows_falling_rigid_body(self):
        """Verify beam origins track a rigid body falling under gravity."""
        stage = omni.usd.get_context().get_stage()
        UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
        UsdGeom.SetStageMetersPerUnit(stage, 1.0)
        UsdPhysics.Scene.Define(stage, Sdf.Path("/World/PhysicsScene"))

        ground = UsdGeom.Cube.Define(stage, "/World/Ground")
        ground.GetSizeAttr().Set(1.0)
        ground.AddTranslateOp().Set(Gf.Vec3d(0, 0, -0.5))
        ground.AddScaleOp().Set(Gf.Vec3f(50, 50, 1))
        UsdPhysics.CollisionAPI.Apply(ground.GetPrim())

        cube_path = "/World/FallingCube"
        start_z = 5.0
        Cube(cube_path, sizes=1.0, positions=[0.0, 0.0, start_z])
        GeomPrim(cube_path, apply_collision_apis=True)
        RigidPrim(cube_path, masses=[1.0])
        await omni.kit.app.get_app().next_update_async()

        sensor_path = "/World/FallingCube/Physics_Raycast_Sensor"
        sensor = RaycastSensor.create(
            cube_path + "/Physics_Raycast_Sensor",
            min_range=0.1,
            max_range=20.0,
            ray_origins=[[0.0, 0.0, 0.0]],
            ray_directions=[[0.0, 0.0, -1.0]],
            output_frame="WORLD",
        )
        self.assertIsNotNone(sensor, "Failed to create physics raycast sensor")
        await omni.kit.app.get_app().next_update_async()

        backend = RaycastSensorBackend(sensor_path)

        self._timeline.play()
        await step_simulation(0.1)

        origin_z_samples = []
        for _ in range(30):
            await omni.kit.app.get_app().next_update_async()
            reading = backend.get_sensor_reading()
            if reading.is_valid and reading.ray_count > 0:
                oz = reading.ray_origins_world[0][2]
                origin_z_samples.append(oz)

        self.assertGreaterEqual(len(origin_z_samples), 2, "Not enough valid readings collected")

        self.assertGreater(
            origin_z_samples[0],
            origin_z_samples[-1],
            "Beam origin Z should decrease as the rigid body falls",
        )

        self.assertLess(
            origin_z_samples[-1],
            start_z,
            "Beam origin should have moved below the starting height",
        )

    async def test_beam_endpoints_hit_ground(self):
        """Verify beam end points reach the ground when a sensor falls toward it."""
        stage = omni.usd.get_context().get_stage()
        UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
        UsdGeom.SetStageMetersPerUnit(stage, 1.0)
        UsdPhysics.Scene.Define(stage, Sdf.Path("/World/PhysicsScene"))

        ground = UsdGeom.Cube.Define(stage, "/World/Ground")
        ground.GetSizeAttr().Set(1.0)
        ground.AddTranslateOp().Set(Gf.Vec3d(0, 0, -0.5))
        ground.AddScaleOp().Set(Gf.Vec3f(50, 50, 1))
        UsdPhysics.CollisionAPI.Apply(ground.GetPrim())

        cube_path = "/World/FallingCube"
        Cube(cube_path, sizes=1.0, positions=[0.0, 0.0, 3.0])
        GeomPrim(cube_path, apply_collision_apis=True)
        RigidPrim(cube_path, masses=[1.0])
        await omni.kit.app.get_app().next_update_async()

        sensor_path = cube_path + "/Physics_Raycast_Sensor"
        sensor = RaycastSensor.create(
            cube_path + "/Physics_Raycast_Sensor",
            min_range=0.6,
            max_range=20.0,
            ray_origins=[[0.0, 0.0, 0.0]],
            ray_directions=[[0.0, 0.0, -1.0]],
            output_frame="WORLD",
        )
        self.assertIsNotNone(sensor)
        await omni.kit.app.get_app().next_update_async()

        backend = RaycastSensorBackend(sensor_path)

        self._timeline.play()
        # Cube rests on ground at z=0.5 (half-size). Sensor at cube center → z=0.5.
        # Let the cube fall and settle on the ground.
        await step_simulation(2.0)

        reading = backend.get_sensor_reading()
        self.assertTrue(reading.is_valid, "Sensor reading should be valid")
        self.assertEqual(reading.ray_count, 1)

        depth = reading.depths[0]
        self.assertLess(depth, 20.0, "Ray should hit the ground (depth < max_range)")

        end_z = reading.ray_end_points_world[0][2]
        self.assertAlmostEqual(end_z, 0.0, delta=0.15, msg="Beam end point Z should be near ground level")

    async def test_sensor_direction_follows_rotated_body(self):
        """Verify ray directions rotate with the parent rigid body."""
        stage = omni.usd.get_context().get_stage()
        UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
        UsdGeom.SetStageMetersPerUnit(stage, 1.0)
        UsdPhysics.Scene.Define(stage, Sdf.Path("/World/PhysicsScene"))

        wall = UsdGeom.Cube.Define(stage, "/World/Wall")
        wall.GetSizeAttr().Set(1.0)
        wall.AddTranslateOp().Set(Gf.Vec3d(5, 0, 2))
        wall.AddScaleOp().Set(Gf.Vec3f(0.2, 10, 10))
        UsdPhysics.CollisionAPI.Apply(wall.GetPrim())

        import math

        xform = UsdGeom.Xform.Define(stage, "/World/SensorMount")
        xform.AddTranslateOp().Set(Gf.Vec3d(0, 0, 2))
        orient_op = xform.AddOrientOp(precision=UsdGeom.XformOp.PrecisionFloat)
        orient_op.Set(Gf.Quatf(1, 0, 0, 0))
        UsdPhysics.RigidBodyAPI.Apply(xform.GetPrim())

        xform.GetPrim().CreateAttribute("physics:kinematicEnabled", Sdf.ValueTypeNames.Bool).Set(True)

        sensor_path = "/World/SensorMount/Physics_Raycast_Sensor"
        sensor = RaycastSensor.create(
            "/World/SensorMount/Physics_Raycast_Sensor",
            min_range=0.1,
            max_range=20.0,
            ray_origins=[[0.0, 0.0, 0.0]],
            ray_directions=[[1.0, 0.0, 0.0]],
            output_frame="WORLD",
        )
        self.assertIsNotNone(sensor)
        await omni.kit.app.get_app().next_update_async()

        backend = RaycastSensorBackend(sensor_path)

        self._timeline.play()
        await step_simulation(0.3)

        reading_fwd = backend.get_sensor_reading()
        self.assertTrue(reading_fwd.is_valid)
        depth_fwd = reading_fwd.depths[0]
        self.assertLess(depth_fwd, 20.0, "Forward ray should hit the wall")

        self._timeline.stop()
        await omni.kit.app.get_app().next_update_async()

        yaw_90 = Gf.Quatf(math.cos(math.pi / 4), 0, 0, math.sin(math.pi / 4))
        orient_op.Set(yaw_90)
        await omni.kit.app.get_app().next_update_async()

        self._timeline.play()
        await step_simulation(0.3)

        reading_rot = backend.get_sensor_reading()
        self.assertTrue(reading_rot.is_valid)
        depth_rot = reading_rot.depths[0]
        self.assertAlmostEqual(
            depth_rot, 20.0, delta=0.5, msg="After 90-degree yaw, ray should miss the wall (pointing along Y)"
        )
