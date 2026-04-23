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

"""Tests for the RaycastSensor wrapper, RaycastSensorBackend lifecycle, and error paths."""

from __future__ import annotations

import numpy as np
import omni.kit.test
import omni.timeline
import omni.usd
from isaacsim.core.simulation_manager import SimulationManager
from isaacsim.sensors.experimental.physics import RaycastSensor, RaycastSensorBackend
from pxr import Gf, Sdf, UsdGeom, UsdPhysics

from .common import step_simulation


async def _create_basic_scene():
    """Create a minimal scene with physics and collision geometry."""
    stage = omni.usd.get_context().get_stage()
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
    UsdGeom.SetStageMetersPerUnit(stage, 1.0)
    UsdPhysics.Scene.Define(stage, Sdf.Path("/World/PhysicsScene"))

    ground = UsdGeom.Cube.Define(stage, "/World/Ground")
    ground.GetSizeAttr().Set(1.0)
    ground.AddTranslateOp().Set(Gf.Vec3d(0, 0, -0.5))
    ground.AddScaleOp().Set(Gf.Vec3f(50, 50, 1))
    UsdPhysics.CollisionAPI.Apply(ground.GetPrim())

    wall = UsdGeom.Cube.Define(stage, "/World/Wall")
    wall.GetSizeAttr().Set(1.0)
    wall.AddTranslateOp().Set(Gf.Vec3d(5, 0, 1.5))
    wall.AddScaleOp().Set(Gf.Vec3f(0.2, 8, 3))
    UsdPhysics.CollisionAPI.Apply(wall.GetPrim())

    UsdGeom.Xform.Define(stage, "/World/Sensors")
    await omni.kit.app.get_app().next_update_async()
    return stage


class TestRaycastSensorWrapper(omni.kit.test.AsyncTestCase):
    """Test the RaycastSensor high-level wrapper."""

    async def setUp(self):
        self._timeline = omni.timeline.get_timeline_interface()
        await omni.usd.get_context().new_stage_async()
        await omni.kit.app.get_app().next_update_async()

    async def tearDown(self):
        if self._timeline.is_playing():
            self._timeline.stop()
        SimulationManager.invalidate_physics()
        await omni.kit.app.get_app().next_update_async()

    async def test_wrapper_creates_new_sensor(self):
        """RaycastSensor creates a new prim when the path does not exist."""
        await _create_basic_scene()

        RaycastSensor(
            "/World/Sensors/TestSensor",
            ray_origins=[[0.0, 0.0, 0.0]],
            ray_directions=[[1.0, 0.0, 0.0]],
            min_range=0.5,
            max_range=50.0,
            output_frame="WORLD",
        )

        stage = omni.usd.get_context().get_stage()
        prim = stage.GetPrimAtPath("/World/Sensors/TestSensor")
        self.assertTrue(prim.IsValid(), "RaycastSensor should create a prim")
        self.assertEqual(prim.GetTypeName(), "IsaacRaycastSensor")
        self.assertEqual(prim.GetAttribute("numRays").Get(), 1)
        self.assertAlmostEqual(prim.GetAttribute("minRange").Get(), 0.5, places=5)
        self.assertAlmostEqual(prim.GetAttribute("maxRange").Get(), 50.0, places=5)

    async def test_wrapper_wraps_existing_sensor(self):
        """RaycastSensor wraps an existing prim and applies overrides."""
        await _create_basic_scene()

        sensor = RaycastSensor.create(
            "/World/Sensors/ExistingSensor",
            min_range=0.4,
            max_range=100.0,
            ray_origins=[[0.0, 0.0, 0.0]],
            ray_directions=[[1.0, 0.0, 0.0]],
        )
        self.assertIsNotNone(sensor)
        await omni.kit.app.get_app().next_update_async()

        RaycastSensor(
            "/World/Sensors/ExistingSensor",
            min_range=1.0,
            max_range=25.0,
            output_frame="WORLD",
        )

        stage = omni.usd.get_context().get_stage()
        prim = stage.GetPrimAtPath("/World/Sensors/ExistingSensor")
        self.assertAlmostEqual(prim.GetAttribute("minRange").Get(), 1.0, places=5)
        self.assertAlmostEqual(prim.GetAttribute("maxRange").Get(), 25.0, places=5)
        self.assertEqual(prim.GetAttribute("outputFrameOfReference").Get(), "WORLD")

    async def test_wrapper_get_current_frame(self):
        """get_current_frame returns dict with expected keys and valid data after simulation."""
        await _create_basic_scene()

        sensor = RaycastSensor(
            "/World/Sensors/FrameSensor",
            ray_origins=[[0.0, 0.0, 0.0]],
            ray_directions=[[1.0, 0.0, 0.0]],
            min_range=0.1,
            max_range=100.0,
            output_frame="WORLD",
            translation=np.array([0.0, 0.0, 1.5]),
        )

        self._timeline.play()
        await step_simulation(0.3)

        frame = sensor.get_current_frame()
        for key in ["depths", "hit_positions", "hit_normals", "hit_prim_paths", "time", "physics_step"]:
            self.assertIn(key, frame, f"Frame missing key '{key}'")

        self.assertIsInstance(frame["physics_step"], int)
        self.assertGreater(len(frame["depths"]), 0, "Should have depth data")

    async def test_wrapper_get_sensor_reading(self):
        """get_sensor_reading returns a C++ reading struct."""
        await _create_basic_scene()

        sensor = RaycastSensor(
            "/World/Sensors/ReadingSensor",
            ray_origins=[[0.0, 0.0, 0.0]],
            ray_directions=[[1.0, 0.0, 0.0]],
            min_range=0.1,
            max_range=100.0,
            output_frame="WORLD",
            translation=np.array([0.0, 0.0, 1.5]),
        )

        self._timeline.play()
        await step_simulation(0.3)

        reading = sensor.get_sensor_reading()
        self.assertTrue(reading.is_valid, "Reading should be valid after simulation")
        self.assertEqual(reading.ray_count, 1)

    async def test_wrapper_invalid_frame_before_play(self):
        """get_current_frame returns empty arrays before simulation starts."""
        await _create_basic_scene()

        sensor = RaycastSensor(
            "/World/Sensors/NoPlaySensor",
            ray_origins=[[0.0, 0.0, 0.0]],
            ray_directions=[[1.0, 0.0, 0.0]],
        )

        frame = sensor.get_current_frame()
        self.assertEqual(len(frame["depths"]), 0)
        self.assertEqual(frame["hit_positions"].shape, (0, 3))

    async def test_wrapper_position_and_translation_conflict(self):
        """Specifying both position and translation raises ValueError."""
        await _create_basic_scene()

        with self.assertRaises(ValueError):
            RaycastSensor(
                "/World/Sensors/ConflictSensor",
                ray_origins=[[0.0, 0.0, 0.0]],
                ray_directions=[[1.0, 0.0, 0.0]],
                position=np.array([1.0, 0.0, 0.0]),
                translation=np.array([1.0, 0.0, 0.0]),
            )

    async def test_wrapper_mismatched_origins_directions_raises(self):
        """Mismatched ray_origins and ray_directions lengths raises ValueError."""
        await _create_basic_scene()

        with self.assertRaises(ValueError):
            RaycastSensor(
                "/World/Sensors/MismatchSensor",
                ray_origins=[[0.0, 0.0, 0.0], [1.0, 0.0, 0.0]],
                ray_directions=[[1.0, 0.0, 0.0]],
            )


class TestRaycastSensorBackendLifecycle(omni.kit.test.AsyncTestCase):
    """Test RaycastSensorBackend lifecycle: remove, reset, timeline stop."""

    async def setUp(self):
        self._timeline = omni.timeline.get_timeline_interface()
        await omni.usd.get_context().new_stage_async()
        await omni.kit.app.get_app().next_update_async()

    async def tearDown(self):
        if self._timeline.is_playing():
            self._timeline.stop()
        SimulationManager.invalidate_physics()
        await omni.kit.app.get_app().next_update_async()

    async def test_remove_sensor(self):
        """removeSensor stops future readings from being valid."""
        await _create_basic_scene()

        sensor_path = "/World/Sensors/RemoveSensor"
        sensor = RaycastSensor.create(
            "/World/Sensors/RemoveSensor",
            min_range=0.1,
            max_range=100.0,
            ray_origins=[[0.0, 0.0, 0.0]],
            ray_directions=[[1.0, 0.0, 0.0]],
            output_frame="WORLD",
            translation=Gf.Vec3d(0, 0, 1.5),
        )
        self.assertIsNotNone(sensor)
        await omni.kit.app.get_app().next_update_async()

        backend = RaycastSensorBackend(sensor_path)

        self._timeline.play()
        await step_simulation(0.3)

        reading = backend.get_sensor_reading()
        self.assertTrue(reading.is_valid, "Should have valid reading before remove")

        from isaacsim.sensors.experimental.physics.impl.extension import get_raycast_sensor_interface

        iface = get_raycast_sensor_interface()
        self.assertIsNotNone(iface)
        iface.remove_sensor(sensor_path)

        reading_after = iface.get_sensor_reading(sensor_path)
        self.assertFalse(reading_after.is_valid, "Reading should be invalid after remove")

    async def test_backend_reset(self):
        """Backend reset() removes sensor and clears state."""
        await _create_basic_scene()

        sensor_path = "/World/Sensors/ResetSensor"
        sensor = RaycastSensor.create(
            "/World/Sensors/ResetSensor",
            min_range=0.1,
            max_range=100.0,
            ray_origins=[[0.0, 0.0, 0.0]],
            ray_directions=[[1.0, 0.0, 0.0]],
            output_frame="WORLD",
            translation=Gf.Vec3d(0, 0, 1.5),
        )
        self.assertIsNotNone(sensor)
        await omni.kit.app.get_app().next_update_async()

        backend = RaycastSensorBackend(sensor_path)

        self._timeline.play()
        await step_simulation(0.3)

        reading = backend.get_sensor_reading()
        self.assertTrue(reading.is_valid)

        backend.reset()
        self.assertFalse(backend._sensor_created, "reset() should clear _sensor_created")

    async def test_backend_on_timeline_stop(self):
        """on_timeline_stop clears interface and sensor state."""
        await _create_basic_scene()

        sensor_path = "/World/Sensors/TimelineStopSensor"
        sensor = RaycastSensor.create(
            "/World/Sensors/TimelineStopSensor",
            min_range=0.1,
            max_range=100.0,
            ray_origins=[[0.0, 0.0, 0.0]],
            ray_directions=[[1.0, 0.0, 0.0]],
            output_frame="WORLD",
            translation=Gf.Vec3d(0, 0, 1.5),
        )
        self.assertIsNotNone(sensor)
        await omni.kit.app.get_app().next_update_async()

        backend = RaycastSensorBackend(sensor_path)

        self._timeline.play()
        await step_simulation(0.3)

        reading = backend.get_sensor_reading()
        self.assertTrue(reading.is_valid)

        backend.on_timeline_stop()
        self.assertFalse(backend._sensor_created)
        self.assertIsNone(backend._iface)

    async def test_create_sensor_invalid_prim(self):
        """createSensor with a non-existent prim returns false."""
        await _create_basic_scene()

        self._timeline.play()
        await step_simulation(0.1)

        from isaacsim.sensors.experimental.physics.impl.extension import get_raycast_sensor_interface

        iface = get_raycast_sensor_interface()
        if iface is None:
            self.skipTest("IRaycastSensor interface not available")

        result = iface.create_sensor("/World/NonExistent/FakeSensor")
        self.assertFalse(result, "createSensor should return false for non-existent prim")

    async def test_get_reading_nonexistent_sensor(self):
        """getSensorReading for a non-existent sensor returns invalid reading."""
        await _create_basic_scene()

        self._timeline.play()
        await step_simulation(0.1)

        from isaacsim.sensors.experimental.physics.impl.extension import get_raycast_sensor_interface

        iface = get_raycast_sensor_interface()
        if iface is None:
            self.skipTest("IRaycastSensor interface not available")

        reading = iface.get_sensor_reading("/World/NonExistent/FakeSensor")
        self.assertFalse(reading.is_valid, "Reading should be invalid for non-existent sensor")

    async def test_mismatched_origins_vs_numrays_disables_sensor(self):
        """Sensor with rayOrigins length != numRays produces invalid readings."""
        stage = omni.usd.get_context().get_stage()
        UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
        UsdGeom.SetStageMetersPerUnit(stage, 1.0)
        UsdPhysics.Scene.Define(stage, Sdf.Path("/World/PhysicsScene"))
        UsdGeom.Xform.Define(stage, "/World/Sensors")

        from pxr import Vt

        prim = stage.DefinePrim("/World/Sensors/BadSensor", "IsaacRaycastSensor")
        prim.CreateAttribute("numRays", Sdf.ValueTypeNames.UInt).Set(2)
        prim.CreateAttribute("rayOrigins", Sdf.ValueTypeNames.Float3Array).Set(Vt.Vec3fArray([(0, 0, 0)]))
        prim.CreateAttribute("rayDirections", Sdf.ValueTypeNames.Float3Array).Set(Vt.Vec3fArray([(1, 0, 0)]))
        await omni.kit.app.get_app().next_update_async()

        backend = RaycastSensorBackend("/World/Sensors/BadSensor")

        self._timeline.play()
        await step_simulation(0.3)

        reading = backend.get_sensor_reading()
        self.assertFalse(reading.is_valid, "rayOrigins length != numRays should produce invalid reading")

    async def test_numrays_zero_disables_sensor(self):
        """Sensor with numRays=0 produces invalid readings."""
        stage = omni.usd.get_context().get_stage()
        UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
        UsdGeom.SetStageMetersPerUnit(stage, 1.0)
        UsdPhysics.Scene.Define(stage, Sdf.Path("/World/PhysicsScene"))
        UsdGeom.Xform.Define(stage, "/World/Sensors")

        prim = stage.DefinePrim("/World/Sensors/ZeroRaysSensor", "IsaacRaycastSensor")
        prim.CreateAttribute("numRays", Sdf.ValueTypeNames.UInt).Set(0)
        await omni.kit.app.get_app().next_update_async()

        backend = RaycastSensorBackend("/World/Sensors/ZeroRaysSensor")

        self._timeline.play()
        await step_simulation(0.3)

        reading = backend.get_sensor_reading()
        self.assertFalse(reading.is_valid, "numRays=0 should produce invalid reading")

    async def test_mismatched_time_offsets_disables_sensor(self):
        """Sensor with rayTimeOffsets length != numRays produces invalid readings."""
        stage = omni.usd.get_context().get_stage()
        UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
        UsdGeom.SetStageMetersPerUnit(stage, 1.0)
        UsdPhysics.Scene.Define(stage, Sdf.Path("/World/PhysicsScene"))
        UsdGeom.Xform.Define(stage, "/World/Sensors")

        from pxr import Vt

        prim = stage.DefinePrim("/World/Sensors/BadOffsetsSensor", "IsaacRaycastSensor")
        prim.CreateAttribute("numRays", Sdf.ValueTypeNames.UInt).Set(2)
        prim.CreateAttribute("rayOrigins", Sdf.ValueTypeNames.Float3Array).Set(Vt.Vec3fArray([(0, 0, 0), (1, 0, 0)]))
        prim.CreateAttribute("rayDirections", Sdf.ValueTypeNames.Float3Array).Set(Vt.Vec3fArray([(1, 0, 0), (0, 1, 0)]))
        prim.CreateAttribute("rayTimeOffsets", Sdf.ValueTypeNames.FloatArray).Set(Vt.FloatArray([0.0]))
        await omni.kit.app.get_app().next_update_async()

        backend = RaycastSensorBackend("/World/Sensors/BadOffsetsSensor")

        self._timeline.play()
        await step_simulation(0.3)

        reading = backend.get_sensor_reading()
        self.assertFalse(reading.is_valid, "rayTimeOffsets length != numRays should produce invalid reading")
