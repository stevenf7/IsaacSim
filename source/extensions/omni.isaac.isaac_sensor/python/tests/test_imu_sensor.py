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
import omni.kit.commands

import carb.tokens
import asyncio
from pxr import Gf, UsdGeom

# Import extension python module we are testing with absolute import path, as if we are external user (other extension)
from omni.isaac.isaac_sensor import _isaac_sensor

# Having a test class dervived from omni.kit.test.AsyncTestCase declared on the root of module will make it auto-discoverable by omni.kit.test
class TestIMUSensor(omni.kit.test.AsyncTestCaseFailOnLogError):
    # Before running each test
    async def setUp(self):

        # This needs to be set so that kit updates match physics updates
        self._physics_rate = 60
        self._sensor_rate = 120
        carb.settings.get_settings().set_bool("/app/runLoops/main/rateLimitEnabled", True)
        carb.settings.get_settings().set_int("/app/runLoops/main/rateLimitFrequency", int(self._physics_rate))
        carb.settings.get_settings().set_int("/persistent/simulation/minFrameRate", int(self._physics_rate))

        self._is = _isaac_sensor.acquire_imu_sensor_interface()

        ext_manager = omni.kit.app.get_app().get_extension_manager()
        ext_id = ext_manager.get_enabled_extension_id("omni.isaac.isaac_sensor")
        self._extension_path = ext_manager.get_extension_path(ext_id)

        self.leg_paths = ["/Ant/Arm_{:02d}/Lower_Arm".format(i + 1) for i in range(4)]
        self.sphere_path = "/Ant/Sphere"
        self.sensor_offsets = [
            Gf.Vec3d(0, 0, 0),
            Gf.Vec3d(0, 0, 0),
            Gf.Vec3d(0, 0, 0),
            Gf.Vec3d(0, 0, 0),
            Gf.Vec3d(0, 0, 0),
        ]

        self.sensor_quatd = [
            Gf.Quatd(1, 0, 0, 0),
            Gf.Quatd(1, 0, 0, 0),
            Gf.Quatd(1, 0, 0, 0),
            Gf.Quatd(1, 0, 0, 0),
            Gf.Quatd(1, 0, 0, 0),
        ]

        self.shoulder_joints = ["/Ant/Arm_{:02d}/Upper_Arm/shoulder_joint".format(i + 1) for i in range(4)]

        self.lower_joints = ["{}/lower_arm_joint".format(i) for i in self.leg_paths]

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

    async def test_add_sensor_prim(self):
        self.sensorGeoms = []
        for i in range(4):
            result, sensor = omni.kit.commands.execute(
                "IsaacSensorCreateImuSensor",
                path="/sensor",
                parent=self.leg_paths[i],
                sensor_period=1 / self._sensor_rate,
                offset=self.sensor_offsets[i],
                orientation=self.sensor_quatd[i],
            )
            self.sensorGeoms.append(sensor)
            self.assertTrue(result)
            # Add sensor on body sphere

            result, sensor = omni.kit.commands.execute(
                "IsaacSensorCreateImuSensor",
                path="/sensor",
                parent=self.sphere_path,
                sensor_period=self._sensor_rate,
                offset=self.sensor_offsets[4],
                orientation=self.sensor_quatd[4],
                visualize=True,
            )
            self.assertTrue(result)
            self.sensorGeoms.append(sensor)
        pass

    # notice the ways of reading data for get_sensor_readings
    # and get_sensor_sim_reading are very different
    async def test_get_sensor_readings(self):
        await self.test_add_sensor_prim()
        self._timeline.play()
        await omni.kit.app.get_app().next_update_async()

        for i in range(120):
            await omni.kit.app.get_app().next_update_async()
            sensor_reading = self._is.get_sensor_readings(self.leg_paths[0] + "/sensor")
            # this should be
            num_readings = self._sensor_rate / self._physics_rate
            # print(len(sensor_reading))
            self.assertTrue(abs(len(sensor_reading) - num_readings) <= 1)
            # the last is the newest
            sensor_reading = sensor_reading[-1]
            # print(sensor_reading["lin_acc_x"], "\t", sensor_reading["ang_vel_x"])
            self.assertIsNotNone(sensor_reading["lin_acc_x"])
            self.assertIsNotNone(sensor_reading["ang_vel_x"])
        pass

    async def test_get_sensor_sim_reading(self):
        await self.test_add_sensor_prim()
        await omni.kit.app.get_app().next_update_async()

        self._timeline.play()
        for i in range(20):
            await omni.kit.app.get_app().next_update_async()
            sensor_reading = self._is.get_sensor_sim_reading(self.leg_paths[0] + "/sensor")
            # print(sensor_reading.lin_acc_x, "\t", sensor_reading.ang_vel_x)
            self.assertIsNotNone(sensor_reading.lin_acc_x)
            self.assertIsNotNone(sensor_reading.ang_vel_x)
        pass

    async def test_gravity_m(self):
        UsdGeom.SetStageMetersPerUnit(self._stage, 1.0)

        await self.test_add_sensor_prim()
        await omni.kit.app.get_app().next_update_async()

        self._timeline.play()
        for i in range(200):
            await omni.kit.app.get_app().next_update_async()
            sensor_reading = self._is.get_sensor_sim_reading(self.sphere_path + "/sensor")
            # print(sensor_reading.lin_acc_x, "\t", sensor_reading.lin_acc_y, "\t", sensor_reading.lin_acc_z)
        self.assertAlmostEqual(sensor_reading.lin_acc_z, -9.80665, delta=0.1)
        pass

    async def test_gravity_cm(self):
        UsdGeom.SetStageMetersPerUnit(self._stage, 0.01)
        await self.test_add_sensor_prim()
        await omni.kit.app.get_app().next_update_async()

        await omni.kit.app.get_app().next_update_async()
        self._timeline.play()
        for i in range(200):
            await omni.kit.app.get_app().next_update_async()
            sensor_reading = self._is.get_sensor_sim_reading(self.sphere_path + "/sensor")
            # print(sensor_reading.lin_acc_x, "\t", sensor_reading.lin_acc_y, "\t", sensor_reading.lin_acc_z)
        self.assertAlmostEqual(sensor_reading.lin_acc_z, -980.665, delta=0.1)

    pass
