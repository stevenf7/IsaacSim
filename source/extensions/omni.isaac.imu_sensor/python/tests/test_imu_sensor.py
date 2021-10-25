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
import math
import omni.kit.test

import omni.kit.commands
import carb.tokens
import os
import asyncio
import numpy as np
from pxr import Gf, Usd, UsdGeom, UsdShade, UsdLux, UsdPhysics, PhysxSchema

# Import extension python module we are testing with absolute import path, as if we are external user (other extension)
from omni.isaac.imu_sensor import _imu_sensor

# Having a test class dervived from omni.kit.test.AsyncTestCase declared on the root of module will make it auto-discoverable by omni.kit.test
class TestIMUSensor(omni.kit.test.AsyncTestCaseFailOnLogError):
    # Before running each test
    async def setUp(self):

        # This needs to be set so that kit updates match physics updates
        self._physics_rate = 60
        self._sensor_rate = 500
        carb.settings.get_settings().set_bool("/app/runLoops/main/rateLimitEnabled", True)
        carb.settings.get_settings().set_int("/app/runLoops/main/rateLimitFrequency", int(self._physics_rate))
        carb.settings.get_settings().set_int("/persistent/simulation/minFrameRate", int(self._physics_rate))

        self._is = _imu_sensor.acquire_imu_sensor_interface()

        ext_manager = omni.kit.app.get_app().get_extension_manager()
        ext_id = ext_manager.get_enabled_extension_id("omni.isaac.imu_sensor")
        self._extension_path = ext_manager.get_extension_path(ext_id)

        self.leg_paths = ["/Ant/Arm_{:02d}/Lower_Arm".format(i + 1) for i in range(4)]
        self.sensor_ofsets = [carb.Float3(0, 0, 0), carb.Float3(0, 0, 0), carb.Float3(0, 0, 0), carb.Float3(0, 0, 0)]

        self.shoulder_joints = ["/Ant/Arm_{:02d}/Upper_Arm/shoulder_joint".format(i + 1) for i in range(4)]

        self.lower_joints = ["{}/lower_arm_joint".format(i) for i in self.leg_paths]
        self._sensor_handles = [0 for i in range(4)]

        await omni.usd.get_context().open_stage_async(self._extension_path + "/data/ant.usd")
        self._stage = omni.usd.get_context().get_stage()
        self._timeline = omni.timeline.get_timeline_interface()
        await omni.kit.app.get_app().next_update_async()
        await omni.kit.app.get_app().next_update_async()
        pass

    # After running each test
    async def tearDown(self):
        await omni.kit.app.get_app().next_update_async()
        self._timeline.stop()
        while omni.usd.get_context().get_stage_loading_status()[2] > 0:
            print("tearDown, assets still loading, waiting to finish...")
            await asyncio.sleep(1.0)
        await omni.kit.app.get_app().next_update_async()
        pass

    async def test_add_sensors(self):

        # Add IMU Sensor
        props = _imu_sensor.SensorProperties()
        props.position = carb.Float3(0, 0, 0)
        props.orientation = carb.Float4(0, 0, 0, 1)
        props.sensorPeriod = 1 / self._sensor_rate  # 2ms

        for i in range(4):
            props.position = self.sensor_ofsets[i]
            self._sensor_handles[i] = self._is.add_sensor_on_body(self.leg_paths[i], props)
            self.assertNotEqual(self._sensor_handles[i], _imu_sensor.INVALID_HANDLE)
        pass

    async def test_remove_sensor(self):
        await self.test_add_sensors()
        self.assertTrue(self._is.remove_sensor(self._sensor_handles[0]))
        pass

    async def test_get_num_sensors_on_body(self):
        await self.test_add_sensors()
        n_sensors = self._is.get_num_sensors_on_body(self.leg_paths[0])
        self.assertEqual(n_sensors, 1)
        pass

    async def test_get_sensors_on_body(self):
        await self.test_add_sensors()
        sensors = self._is.get_sensors_on_body(self.leg_paths[0])
        self.assertEqual(len(sensors), 1)
        self.assertEqual(sensors[0], self._sensor_handles[0])
        pass

    # notice the ways of reading data for get_sensor_readings
    # and get_sensor_sim_reading are very different
    async def test_get_sensor_readings(self):
        await self.test_add_sensors()
        self._timeline.play()
        for i in range(120):
            await omni.kit.app.get_app().next_update_async()
            sensor_reading = self._is.get_sensor_readings(self._sensor_handles[0])
            # this should be
            num_readings = self._sensor_rate / self._physics_rate
            # print(len(sensor_reading))
            self.assertIn(len(sensor_reading), [math.floor(num_readings), math.ceil(num_readings)])
            # the last is the newest
            sensor_reading = sensor_reading[-1]
            # print(sensor_reading["lin_acc_x"], "\t", sensor_reading["ang_vel_x"])
            self.assertIsNotNone(sensor_reading["lin_acc_x"])
            self.assertIsNotNone(sensor_reading["ang_vel_x"])
        pass

    async def test_get_sensor_sim_reading(self):
        await self.test_add_sensors()
        self._timeline.play()
        for i in range(20):
            await omni.kit.app.get_app().next_update_async()
            sensor_reading = self._is.get_sensor_sim_reading(self._sensor_handles[0])
            # print(sensor_reading.lin_acc_x, "\t", sensor_reading.ang_vel_x)
            self.assertIsNotNone(sensor_reading.lin_acc_x)
            self.assertIsNotNone(sensor_reading.ang_vel_x)
        pass

    pass
