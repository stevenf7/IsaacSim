# SPDX-FileCopyrightText: Copyright (c) 2018-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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

# NOTE:
#   omni.kit.test - std python's unittest module with additional wrapping to add suport for async/await tests
#   For most things refer to unittest docs: https://docs.python.org/3/library/unittest.html

import asyncio

import carb.tokens
import isaacsim.core.experimental.utils.prim as prim_utils
import isaacsim.core.experimental.utils.stage as stage_utils
import numpy as np
import omni.kit.test
import omni.timeline
from isaacsim.core.experimental.objects import Cube
from isaacsim.core.experimental.prims import GeomPrim, RigidPrim
from isaacsim.core.simulation_manager import SimulationManager
from isaacsim.sensors.experimental.physics.impl.effort_sensor import EffortSensor, EffortSensorReading
from isaacsim.storage.native import get_assets_root_path_async
from pxr import UsdPhysics


class TestEffortSensor(omni.kit.test.AsyncTestCase):
    # Before running each test
    async def setUp(self):
        self._assets_root_path = await get_assets_root_path_async()
        if self._assets_root_path is None:
            carb.log_error("Could not find Isaac Sim assets folder")
            return
        self._timeline = omni.timeline.get_timeline_interface()

    async def create_simple_articulation(
        self, physics_rate=60, include_cube=False, cube_path="/new_cube", cube_position=np.array([1, 0, 0.1])
    ):
        self.pivot_path = "/Articulation/CenterPivot"
        self.slider_path = "/Articulation/Slider"
        self.arm_path = "/Articulation/Arm"

        # load nucleus asset
        await stage_utils.open_stage_async(
            self._assets_root_path + "/Isaac/Robots/IsaacSim/SimpleArticulation/simple_articulation.usd"
        )

        await omni.kit.app.get_app().next_update_async()
        await omni.kit.app.get_app().next_update_async()
        self._stage = stage_utils.get_current_stage()
        stage_utils.set_stage_units(meters_per_unit=1.0)
        SimulationManager.setup_simulation(dt=1.0 / physics_rate)

        prim = prim_utils.get_prim_at_path("/Articulation/Arm/RevoluteJoint")
        self.assertTrue(prim.IsValid())
        joint = UsdPhysics.RevoluteJoint(prim)
        joint.CreateAxisAttr("Y")

        if include_cube:
            Cube(cube_path, sizes=0.1, positions=cube_position)
            GeomPrim(cube_path, apply_collision_apis=True)
            RigidPrim(cube_path, masses=[1.0])

        await omni.kit.app.get_app().next_update_async()
        await omni.kit.app.get_app().next_update_async()
        pass

    # After running each test
    async def tearDown(self):
        if self._timeline.is_playing():
            self._timeline.stop()
        SimulationManager.invalidate_physics()
        if self.effort_sensor is not None:
            self.effort_sensor._stage_open_callback_fn()
            self.effort_sensor = None
        await omni.kit.app.get_app().next_update_async()
        while omni.usd.get_context().get_stage_loading_status()[2] > 0:
            # print("tearDown, assets still loading, waiting to finish...")
            await asyncio.sleep(1.0)
        await omni.kit.app.get_app().next_update_async()
        pass

    async def test_sensor_reading(self):
        await self.create_simple_articulation()

        self.effort_sensor = EffortSensor("/Articulation/Arm/RevoluteJoint")
        self._timeline.play()
        # let physics warm up
        await omni.kit.app.get_app().next_update_async()
        await omni.kit.app.get_app().next_update_async()
        await omni.kit.app.get_app().next_update_async()
        await omni.kit.app.get_app().next_update_async()

        reading = self.effort_sensor.get_sensor_reading()
        self.assertTrue(reading.time != 0)

        # arm only, 2kg with C of G 1m away from the joint
        expected_effort = float(-2 * 9.81)
        self.assertAlmostEqual(reading.value, expected_effort, 1)
        await omni.kit.app.get_app().next_update_async()
        await omni.kit.app.get_app().next_update_async()

        # spawn a 1kg cube 1.5m away from the joint
        Cube("/new_cube", sizes=0.1, positions=[1.5, 0.0, 0.1])
        GeomPrim("/new_cube", apply_collision_apis=True)
        RigidPrim("/new_cube", masses=[1.0])

        await omni.kit.app.get_app().next_update_async()
        await omni.kit.app.get_app().next_update_async()

        expected_effort = float(-3.5 * 9.81)
        reading = self.effort_sensor.get_sensor_reading()
        self.assertAlmostEqual(reading.value, expected_effort, 1)

        self.effort_sensor.enabled = False

        await omni.kit.app.get_app().next_update_async()
        await omni.kit.app.get_app().next_update_async()

        reading = self.effort_sensor.get_sensor_reading()
        self.assertFalse(reading.is_valid)

    # Remove this test later
    async def test_change_to_wrong_dof_name_in_play(self):
        await self.create_simple_articulation()

        self.effort_sensor = EffortSensor("/Articulation/Arm/RevoluteJoint")
        self._timeline.play()

        # let physics warm up
        for i in range(10):
            await omni.kit.app.get_app().next_update_async()

        # sensor enabled with the correct indices, expect non zero output
        # print(f"dof index is: {self.effort_sensor.dof}")
        reading = self.effort_sensor.get_sensor_reading()
        # print(f"reading time: {reading.time}  reading value: {reading.value}")
        self.assertNotEqual(reading.time, 0)
        self.assertNotEqual(reading.value, 0)
        self.assertEqual(reading.is_valid, True)

        # set the sensor with incorrect joint
        try:
            self.effort_sensor.update_dof_name("RevoluteJoint_doesnt_exist")
        except Exception:
            print(f"can't update dof, dof index is: {self.effort_sensor.dof}")
        for i in range(10):
            await omni.kit.app.get_app().next_update_async()

        # incorrect joint, expecting zero output (and error log message)
        reading = self.effort_sensor.get_sensor_reading()
        # print(f"reading time: {reading.time}  reading value: {reading.value}")
        self.assertEqual(reading.time, 0)
        self.assertEqual(reading.value, 0)
        self.assertEqual(reading.is_valid, False)

        # update it with the correct joint again, expecting non zero output
        self.effort_sensor.update_dof_name("RevoluteJoint")
        # print(f"dof index is: {self.effort_sensor.dof}")
        for i in range(10):
            await omni.kit.app.get_app().next_update_async()
        reading = self.effort_sensor.get_sensor_reading()
        # print(f"reading time: {reading.time}  reading value: {reading.value}")
        self.assertNotEqual(reading.time, 0)
        self.assertNotEqual(reading.value, 0)
        self.assertEqual(reading.is_valid, True)

    async def test_change_buffer_size(self):
        await self.create_simple_articulation()

        self.effort_sensor = EffortSensor("/Articulation/Arm/RevoluteJoint")
        self._timeline.play()

        for i in range(10):
            await omni.kit.app.get_app().next_update_async()

        self.effort_sensor.change_buffer_size(20)

        self.assertEqual(self.effort_sensor.data_buffer_size, 20)
        self.assertEqual(len(self.effort_sensor.sensor_reading_buffer), 20)

        self.effort_sensor.change_buffer_size(5)

        self.assertEqual(self.effort_sensor.data_buffer_size, 5)
        self.assertEqual(len(self.effort_sensor.sensor_reading_buffer), 5)
