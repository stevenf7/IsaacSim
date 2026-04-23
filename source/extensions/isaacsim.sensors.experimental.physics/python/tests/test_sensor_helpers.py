# SPDX-FileCopyrightText: Copyright (c) 2018-2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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

"""Tests for sensor creation via the class-based create() API.

These tests verify that ContactSensor.create(), IMUSensor.create(), and
RaycastSensor.create() create prims at the correct paths, especially when the
stage has a default prim.

The key behavior being tested is that sensor paths should NOT be prepended with
the stage's default prim - they should be created exactly where specified.
"""

import carb
import isaacsim.core.experimental.utils.prim as prim_utils
import isaacsim.core.experimental.utils.stage as stage_utils
import omni.isaac.IsaacSensorSchema as IsaacSensorSchema
import omni.kit.test
import omni.usd
from isaacsim.core.experimental.objects import Cube
from isaacsim.sensors.experimental.physics import (
    ContactSensor,
    IMUSensor,
    RaycastSensor,
)
from isaacsim.storage.native import get_assets_root_path_async
from pxr import Gf, PhysxSchema, UsdPhysics

from .common import setup_ant_scene


class TestSensorCreate(omni.kit.test.AsyncTestCase):
    """Test sensor class create() methods for correct path handling."""

    async def setUp(self):
        self._assets_root_path = await get_assets_root_path_async()
        if self._assets_root_path is None:
            carb.log_error("Could not find Isaac Sim assets folder")
            return

    async def tearDown(self):
        stage_utils.close_stage()
        await omni.kit.app.get_app().next_update_async()

    async def _create_empty_stage_with_world(self):
        await stage_utils.create_new_stage_async()
        stage = omni.usd.get_context().get_stage()
        stage_utils.define_prim("/World", type_name="Xform")
        await omni.kit.app.get_app().next_update_async()
        return stage

    async def _create_stage_with_default_prim(self):
        await stage_utils.create_new_stage_async()
        stage = omni.usd.get_context().get_stage()
        default_prim = stage_utils.define_prim("/DefaultRoot", type_name="Xform")
        stage.SetDefaultPrim(default_prim)
        stage_utils.define_prim("/World", type_name="Xform")
        await omni.kit.app.get_app().next_update_async()
        return stage

    # ==================== IMU Sensor Tests ====================

    async def test_imu_sensor_path_no_default_prim(self):
        await self._create_empty_stage_with_world()

        cube = Cube("/World/Cube", sizes=[1.0])
        UsdPhysics.RigidBodyAPI.Apply(cube.prims[0])
        await omni.kit.app.get_app().next_update_async()

        expected_path = "/World/Cube/Imu_Sensor"
        sensor = IMUSensor.create("/World/Cube/Imu_Sensor")

        self.assertIsNotNone(sensor)
        self.assertEqual(sensor.prim_path, expected_path)
        self.assertTrue(prim_utils.get_prim_at_path(expected_path).IsValid())

    async def test_imu_sensor_path_with_default_prim(self):
        stage = await self._create_stage_with_default_prim()

        self.assertTrue(stage.HasDefaultPrim())
        self.assertEqual(stage.GetDefaultPrim().GetPath().pathString, "/DefaultRoot")

        cube = Cube("/World/Cube", sizes=[1.0])
        UsdPhysics.RigidBodyAPI.Apply(cube.prims[0])
        await omni.kit.app.get_app().next_update_async()

        expected_path = "/World/Cube/Imu_Sensor"
        sensor = IMUSensor.create("/World/Cube/Imu_Sensor")

        self.assertIsNotNone(sensor)
        created_path = sensor.prim_path

        self.assertFalse(
            created_path.startswith("/DefaultRoot/"),
            f"Sensor path should NOT start with default prim. Got: {created_path}",
        )
        self.assertEqual(created_path, expected_path)
        self.assertFalse(prim_utils.get_prim_at_path("/DefaultRoot/World/Cube/Imu_Sensor").IsValid())

    async def test_imu_sensor_with_ant_scene(self):
        await setup_ant_scene()
        stage = stage_utils.get_current_stage()

        self.assertTrue(stage.HasDefaultPrim())
        self.assertEqual(stage.GetDefaultPrim().GetPath().pathString, "/Ant")

        stage_utils.define_prim("/World", type_name="Xform")
        cube = Cube("/World/TestCube", sizes=[1.0])
        UsdPhysics.RigidBodyAPI.Apply(cube.prims[0])
        await omni.kit.app.get_app().next_update_async()

        expected_path = "/World/TestCube/Imu_Sensor"
        sensor = IMUSensor.create("/World/TestCube/Imu_Sensor")

        self.assertIsNotNone(sensor)
        created_path = sensor.prim_path
        self.assertFalse(created_path.startswith("/Ant/"))
        self.assertEqual(created_path, expected_path)

    async def test_imu_sensor_nested_hierarchy(self):
        await self._create_stage_with_default_prim()

        stage_utils.define_prim("/World/Level1", type_name="Xform")
        stage_utils.define_prim("/World/Level1/Level2", type_name="Xform")
        cube = Cube("/World/Level1/Level2/Cube", sizes=[1.0])
        UsdPhysics.RigidBodyAPI.Apply(cube.prims[0])
        await omni.kit.app.get_app().next_update_async()

        expected_path = "/World/Level1/Level2/Cube/DeepSensor"
        sensor = IMUSensor.create("/World/Level1/Level2/Cube/DeepSensor")

        self.assertIsNotNone(sensor)
        self.assertEqual(sensor.prim_path, expected_path)

    async def test_imu_sensor_attributes(self):
        await self._create_empty_stage_with_world()

        cube = Cube("/World/Cube", sizes=[1.0])
        UsdPhysics.RigidBodyAPI.Apply(cube.prims[0])
        await omni.kit.app.get_app().next_update_async()

        sensor = IMUSensor.create(
            "/World/Cube/CustomImu",
            translation=Gf.Vec3d(1.0, 2.0, 3.0),
            orientation=Gf.Quatd(0.707, 0.707, 0.0, 0.0),
            linear_acceleration_filter_size=5,
            angular_velocity_filter_size=3,
            orientation_filter_size=7,
        )

        self.assertIsNotNone(sensor)
        usd_prim = sensor.prims[0]
        schema_prim = IsaacSensorSchema.IsaacImuSensor(usd_prim)
        self.assertEqual(schema_prim.GetLinearAccelerationFilterWidthAttr().Get(), 5)
        self.assertEqual(schema_prim.GetAngularVelocityFilterWidthAttr().Get(), 3)
        self.assertEqual(schema_prim.GetOrientationFilterWidthAttr().Get(), 7)
        self.assertEqual(usd_prim.GetTypeName(), "IsaacImuSensor")

    async def test_imu_sensor_enabled_attribute(self):
        await self._create_empty_stage_with_world()

        cube = Cube("/World/Cube", sizes=[1.0])
        UsdPhysics.RigidBodyAPI.Apply(cube.prims[0])
        await omni.kit.app.get_app().next_update_async()

        sensor = IMUSensor.create("/World/Cube/Sensor")

        self.assertIsNotNone(sensor)
        base_sensor = IsaacSensorSchema.IsaacBaseSensor(sensor.prims[0])
        self.assertTrue(base_sensor.GetEnabledAttr().Get())

    async def test_imu_sensor_requires_parent(self):
        await self._create_empty_stage_with_world()

        with self.assertRaises(RuntimeError):
            IMUSensor.create("/Imu_Sensor")

    # ==================== Contact Sensor Tests ====================

    async def test_contact_sensor_path_no_default_prim(self):
        await self._create_empty_stage_with_world()

        cube = Cube("/World/Cube", sizes=[1.0])
        UsdPhysics.RigidBodyAPI.Apply(cube.prims[0])
        UsdPhysics.CollisionAPI.Apply(cube.prims[0])
        await omni.kit.app.get_app().next_update_async()

        expected_path = "/World/Cube/Contact_Sensor"
        sensor = ContactSensor.create("/World/Cube/Contact_Sensor")

        self.assertIsNotNone(sensor)
        self.assertEqual(sensor.prim_path, expected_path)

    async def test_contact_sensor_path_with_default_prim(self):
        await self._create_stage_with_default_prim()

        cube = Cube("/World/Cube", sizes=[1.0])
        UsdPhysics.RigidBodyAPI.Apply(cube.prims[0])
        UsdPhysics.CollisionAPI.Apply(cube.prims[0])
        await omni.kit.app.get_app().next_update_async()

        expected_path = "/World/Cube/Contact_Sensor"
        sensor = ContactSensor.create("/World/Cube/Contact_Sensor")

        self.assertIsNotNone(sensor)
        created_path = sensor.prim_path
        self.assertFalse(created_path.startswith("/DefaultRoot/"))
        self.assertEqual(created_path, expected_path)

    async def test_contact_sensor_attributes(self):
        stage = await self._create_empty_stage_with_world()

        cube = Cube("/World/Cube", sizes=[1.0])
        UsdPhysics.RigidBodyAPI.Apply(cube.prims[0])
        UsdPhysics.CollisionAPI.Apply(cube.prims[0])
        await omni.kit.app.get_app().next_update_async()

        sensor = ContactSensor.create(
            "/World/Cube/CustomContact",
            min_threshold=10.0,
            max_threshold=5000.0,
            color=Gf.Vec4f(1.0, 0.0, 0.0, 1.0),
            radius=0.5,
        )

        self.assertIsNotNone(sensor)
        self.assertAlmostEqual(sensor.get_min_threshold(), 10.0, places=5)
        self.assertAlmostEqual(sensor.get_max_threshold(), 5000.0, places=5)
        self.assertAlmostEqual(sensor.get_radius(), 0.5, places=5)

        parent_prim = stage.GetPrimAtPath("/World/Cube")
        self.assertTrue(parent_prim.HasAPI(PhysxSchema.PhysxContactReportAPI))

    async def test_contact_sensor_requires_parent(self):
        await self._create_empty_stage_with_world()

        with self.assertRaises(RuntimeError):
            ContactSensor.create("/Contact_Sensor")

    # ==================== Raycast Sensor Tests ====================

    async def test_raycast_sensor_requires_parent(self):
        await self._create_empty_stage_with_world()

        with self.assertRaises(RuntimeError):
            RaycastSensor.create("/Raycast_Sensor")

    async def test_raycast_sensor_path_with_default_prim(self):
        await self._create_stage_with_default_prim()

        cube = Cube("/World/Cube", sizes=[1.0])
        UsdPhysics.RigidBodyAPI.Apply(cube.prims[0])
        await omni.kit.app.get_app().next_update_async()

        expected_path = "/World/Cube/Raycast_Sensor"
        sensor = RaycastSensor.create(
            "/World/Cube/Raycast_Sensor",
            ray_origins=[[0, 0, 0]],
            ray_directions=[[1, 0, 0]],
        )

        self.assertIsNotNone(sensor)
        created_path = sensor.prim_path
        self.assertFalse(created_path.startswith("/DefaultRoot/"))
        self.assertEqual(created_path, expected_path)

    async def test_raycast_sensor_attributes(self):
        await self._create_empty_stage_with_world()

        cube = Cube("/World/Cube", sizes=[1.0])
        UsdPhysics.RigidBodyAPI.Apply(cube.prims[0])
        await omni.kit.app.get_app().next_update_async()

        origins = [[0, 0, 0], [0, 0, 0]]
        directions = [[1, 0, 0], [0, 1, 0]]

        sensor = RaycastSensor.create(
            "/World/Cube/Raycast",
            min_range=0.5,
            max_range=50.0,
            ray_origins=origins,
            ray_directions=directions,
            output_frame="WORLD",
            report_hit_prim_paths=True,
        )

        self.assertIsNotNone(sensor)
        usd_prim = sensor.prims[0]
        schema_prim = IsaacSensorSchema.IsaacRaycastSensor(usd_prim)
        self.assertAlmostEqual(schema_prim.GetMinRangeAttr().Get(), 0.5, places=5)
        self.assertAlmostEqual(schema_prim.GetMaxRangeAttr().Get(), 50.0, places=5)
        self.assertEqual(schema_prim.GetNumRaysAttr().Get(), 2)
        self.assertEqual(schema_prim.GetOutputFrameOfReferenceAttr().Get(), "WORLD")
        self.assertTrue(schema_prim.GetReportHitPrimPathsAttr().Get())

    # ==================== Path Edge Cases ====================

    async def test_path_with_trailing_slash(self):
        await self._create_empty_stage_with_world()

        cube = Cube("/World/Cube", sizes=[1.0])
        UsdPhysics.RigidBodyAPI.Apply(cube.prims[0])
        await omni.kit.app.get_app().next_update_async()

        expected_path = "/World/Cube/Sensor"
        sensor = IMUSensor.create("/World/Cube/Sensor/")

        self.assertIsNotNone(sensor)
        self.assertEqual(sensor.prim_path, expected_path)
        self.assertNotIn("//", sensor.prim_path)

    async def test_unique_path_generation(self):
        await self._create_empty_stage_with_world()

        cube = Cube("/World/Cube", sizes=[1.0])
        UsdPhysics.RigidBodyAPI.Apply(cube.prims[0])
        await omni.kit.app.get_app().next_update_async()

        sensor1 = IMUSensor.create("/World/Cube/Sensor")
        sensor2 = IMUSensor.create("/World/Cube/Sensor")

        self.assertIsNotNone(sensor1)
        self.assertIsNotNone(sensor2)

        path1 = sensor1.prim_path
        path2 = sensor2.prim_path
        self.assertNotEqual(path1, path2, "Duplicate sensors should get unique paths")
        self.assertEqual(path1, "/World/Cube/Sensor")
        self.assertTrue(path2.startswith("/World/Cube/Sensor"))
