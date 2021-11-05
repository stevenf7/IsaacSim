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
import numpy as np
from pxr import UsdGeom, Gf, UsdPhysics

# Import extension python module we are testing with absolute import path, as if we are external user (other extension)
from omni.isaac.contact_sensor import _contact_sensor
from omni.isaac.core.utils.physics import simulate_async
from omni.isaac.core.utils.extensions import get_extension_path_from_name

# Having a test class dervived from omni.kit.test.AsyncTestCase declared on the root of module will make it auto-discoverable by omni.kit.test


def add_cube(stage, path, size, offset, physics=False):
    cubeGeom = UsdGeom.Cube.Define(stage, path)
    cubePrim = stage.GetPrimAtPath(path)

    cubeGeom.CreateSizeAttr(size)
    cubeGeom.AddTranslateOp().Set(offset)
    if physics:
        rigid_api = UsdPhysics.RigidBodyAPI.Apply(cubePrim)
        rigid_api.CreateRigidBodyEnabledAttr(True)

    UsdPhysics.CollisionAPI.Apply(cubePrim)

    return cubePrim


def create_physics_scene(stage, gravity=981):
    from pxr import UsdPhysics, PhysxSchema, Gf

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


class TestContactSensor(omni.kit.test.AsyncTestCaseFailOnLogError):
    # Before running each test
    async def setUp(self):

        # This needs to be set so that kit updates match physics updates
        self._physics_rate = 60
        carb.settings.get_settings().set_bool("/app/runLoops/main/rateLimitEnabled", True)
        carb.settings.get_settings().set_int("/app/runLoops/main/rateLimitFrequency", int(self._physics_rate))
        carb.settings.get_settings().set_int("/persistent/simulation/minFrameRate", int(self._physics_rate))

        self._cs = _contact_sensor.acquire_contact_sensor_interface()

        self._extension_path = get_extension_path_from_name("omni.isaac.contact_sensor")

        self.leg_paths = ["/Ant/Arm_{:02d}/Lower_Arm".format(i + 1) for i in range(4)]
        self.sensor_ofsets = [
            carb.Float3(0.40, 0, 0),
            carb.Float3(0.40, 0, 0),
            carb.Float3(0.40, 0, 0),
            carb.Float3(0.40, 0, 0),
        ]

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

        # Add Contact Sensor
        props = _contact_sensor.SensorProperties()
        props.radius = 0.12  # Cover the entire leg tip
        props.minThreshold = 0
        props.maxThreshold = 1000000000000
        props.sensorPeriod = -1  # one reading per sim step

        for i in range(4):
            props.position = self.sensor_ofsets[i]
            self._sensor_handles[i] = self._cs.add_sensor_on_body(self.leg_paths[i], props)
            self.assertNotEqual(self._sensor_handles[i], _contact_sensor.INVALID_HANDLE)
        pass

    async def test_lost_contacts(self):
        await self.test_add_sensors()
        self._timeline.play()
        await simulate_async(1, steps_per_sec=1)  # simulate 1 step, ant should be in the air
        contacts_raw = self._cs.get_body_contact_raw_data(self.leg_paths[0])
        self.assertEqual(len(contacts_raw), 0)
        await simulate_async(0.5)  # simulate 30 steps, ant should touch ground
        contacts_raw = self._cs.get_body_contact_raw_data(self.leg_paths[0])
        self.assertEqual(len(contacts_raw), 1)
        c = contacts_raw[0]
        body0 = self._cs.decode_body_name(c["body0"])
        body1 = self._cs.decode_body_name(c["body1"])
        if not (body0 == self.leg_paths[0] or body1 == self.leg_paths[0]):
            self.fail("Raw contact does not contain queried body {} ({},{})".format(self.leg_paths[0], body0, body1))
        self.assertAlmostEqual(1.0, c["normal"]["z"], delta=6)
        print(c)

        # move the ground to 15 lose the contacts
        xform = UsdGeom.Xformable(self._stage.GetPrimAtPath("/World/GroundPlane"))
        # xform.ClearXformOpOrder()
        xform_op = xform.GetOrderedXformOps()[0]
        xform_op.Set(Gf.Vec3d(0, 0, 15))
        await simulate_async(0.5)
        contacts_raw = self._cs.get_body_contact_raw_data(self.leg_paths[0])
        self.assertEqual(len(contacts_raw), 0)

    async def test_remove_sensor(self):
        await self.test_add_sensors()
        self.assertTrue(self._cs.remove_sensor(self._sensor_handles[0]))
        pass

    async def test_get_num_sensors_on_body(self):
        await self.test_add_sensors()
        n_sensors = self._cs.get_num_sensors_on_body(self.leg_paths[0])
        self.assertEqual(n_sensors, 1)
        pass

    async def test_get_sensors_on_body(self):
        await self.test_add_sensors()
        sensors = self._cs.get_sensors_on_body(self.leg_paths[0])
        self.assertEqual(len(sensors), 1)
        self.assertEqual(sensors[0], self._sensor_handles[0])
        pass

    async def test_get_raw_data(self):
        await self.test_add_sensors()
        self._timeline.play()
        await simulate_async(1, steps_per_sec=1)  # simulate 1 step, ant should be in the air
        contacts_raw = self._cs.get_body_contact_raw_data(self.leg_paths[0])
        self.assertEqual(len(contacts_raw), 0)
        await simulate_async(0.5)  # simulate 30 steps, ant should touch ground
        contacts_raw = self._cs.get_body_contact_raw_data(self.leg_paths[0])
        self.assertEqual(len(contacts_raw), 1)
        c = contacts_raw[0]
        body0 = self._cs.decode_body_name(c["body0"])
        body1 = self._cs.decode_body_name(c["body1"])
        if not (body0 == self.leg_paths[0] or body1 == self.leg_paths[0]):
            self.fail("Raw contact does not contain queried body {} ({},{})".format(self.leg_paths[0], body0, body1))
        self.assertAlmostEqual(1.0, c["normal"]["z"], delta=6)
        print(c)

    async def test_persistent_raw_data(self):
        await self.test_add_sensors()
        self._timeline.play()
        await simulate_async(2.0)  # simulate long enough that physx stops sending persistent contact raw data
        contacts_raw = self._cs.get_body_contact_raw_data(self.leg_paths[0])
        self.assertEqual(len(contacts_raw), 1)
        c = contacts_raw[0]
        body0 = self._cs.decode_body_name(c["body0"])
        body1 = self._cs.decode_body_name(c["body1"])
        if not (body0 == self.leg_paths[0] or body1 == self.leg_paths[0]):
            self.fail("Raw contact does not contain queried body {} ({},{})".format(self.leg_paths[0], body0, body1))
        self.assertAlmostEqual(1.0, c["normal"]["z"], delta=6)
        print(c)

    async def test_get_sensor_readings(self):
        await self.test_add_sensors()
        self._timeline.play()
        for i in range(120):
            await omni.kit.app.get_app().next_update_async()
            contacts_raw = self._cs.get_body_contact_raw_data(self.leg_paths[0])
            sensor_reading = self._cs.get_sensor_readings(self._sensor_handles[0])
            self.assertEqual(len(sensor_reading), 1)
            sensor_reading = sensor_reading[0]
            if len((contacts_raw)):
                # there is a contact, compute force from impulse, compare to sensor reading
                force = (
                    np.linalg.norm(
                        [
                            contacts_raw[0]["impulse"]["x"],
                            contacts_raw[0]["impulse"]["y"],
                            contacts_raw[0]["impulse"]["z"],
                        ]
                    )
                    * 60.0
                )  # dt is 1/60
                self.assertAlmostEqual(force, sensor_reading["value"], 2)
            else:
                # No contact, reading should be zero
                self.assertEqual(sensor_reading["value"], 0)
        pass

    async def test_delayed_get_sensor_readings(self):
        await self.test_add_sensors()
        self._timeline.play()
        for i in range(120):
            await omni.kit.app.get_app().next_update_async()
        contacts_raw = self._cs.get_body_contact_raw_data(self.leg_paths[0])
        sensor_reading = self._cs.get_sensor_readings(self._sensor_handles[0])
        self.assertEqual(len(sensor_reading), 1)
        sensor_reading = sensor_reading[0]
        if len((contacts_raw)):
            # there is a contact, compute force from impulse, compare to sensor reading
            force = (
                np.linalg.norm(
                    [contacts_raw[0]["impulse"]["x"], contacts_raw[0]["impulse"]["y"], contacts_raw[0]["impulse"]["z"]]
                )
                * 60.0
            )  # dt is 1/60
            self.assertAlmostEqual(force, sensor_reading["value"], 2)
        else:
            # No contact, reading should be zero
            self.assertEqual(sensor_reading["value"], 0)
        pass

    async def test_compare_sensor_force_to_mass(self):

        cube_prim = add_cube(self._stage, "/cube", 1, (10, 10, 2), physics=True)
        mass = 10
        massAPI = UsdPhysics.MassAPI.Apply(cube_prim)
        massAPI.CreateMassAttr(mass)

        props = _contact_sensor.SensorProperties()
        props.radius = -1  # Cover the entire leg tip
        props.minThreshold = 0
        props.maxThreshold = 1000000000000
        props.sensorPeriod = -1  # one reading per sim step
        sensor = self._cs.add_sensor_on_body("/cube", props)

        self._timeline.play()
        await simulate_async(1.5)
        await omni.kit.app.get_app().next_update_async()
        sensor_reading = self._cs.get_sensor_readings(sensor)
        self.assertEqual(len(sensor_reading), 1)
        sensor_reading = sensor_reading[0]
        self.assertAlmostEqual(sensor_reading["value"], mass * 9.81, 1)
        pass

    async def test_get_sensor_sim_reading(self):
        await self.test_add_sensors()
        self._timeline.play()
        for i in range(120):
            await omni.kit.app.get_app().next_update_async()
            contacts_raw = self._cs.get_body_contact_raw_data(self.leg_paths[0])
            sensor_reading = self._cs.get_sensor_sim_reading(self._sensor_handles[0])
            if len((contacts_raw)):
                # there is a contact, compute force from impulse, compare to sensor reading
                force = (
                    np.linalg.norm(
                        [
                            contacts_raw[0]["impulse"]["x"],
                            contacts_raw[0]["impulse"]["y"],
                            contacts_raw[0]["impulse"]["z"],
                        ]
                    )
                    * 60.0
                )  # dt is 1/60
                self.assertAlmostEqual(force, sensor_reading.value, 2)
            else:
                # No contact, reading should be zero
                self.assertEqual(sensor_reading.value, 0)
        pass

    async def test_contact_outside_range(self):
        # Add Contact Sensor
        props = _contact_sensor.SensorProperties()
        props.radius = 0.12  # Cover the entire leg tip
        props.minThreshold = 0
        props.maxThreshold = 1000000000000
        props.sensorPeriod = -1  # one reading per sim step

        # Sensors will be placed in the middle of capsule, so ground contact should always read zero
        for i in range(4):
            props.position = carb.Float3(0, 0, 0)
            self._sensor_handles[i] = self._cs.add_sensor_on_body(self.leg_paths[i], props)
            self.assertNotEqual(self._sensor_handles[i], _contact_sensor.INVALID_HANDLE)

        self._timeline.play()
        for i in range(40):
            await omni.kit.app.get_app().next_update_async()
            contacts_raw = self._cs.get_body_contact_raw_data(self.leg_paths[0])
            sensor_reading = self._cs.get_sensor_readings(self._sensor_handles[0])
            self.assertEqual(len(sensor_reading), 1)
            sensor_reading = sensor_reading[0]
            self.assertEqual(sensor_reading["value"], 0)

    pass

    async def test_sensor_period(self):
        # Add Contact Sensor
        props = _contact_sensor.SensorProperties()
        props.radius = 12  # Cover the entire leg tip
        props.minThreshold = 0
        props.maxThreshold = 1000000000000
        props.sensorPeriod = 1.0 / 100.0
        # Sensors will be placed in the middle of capsule, so ground contact should always read zero
        for i in range(4):
            props.position = self.sensor_ofsets[i]
            self._sensor_handles[i] = self._cs.add_sensor_on_body(self.leg_paths[i], props)
            self.assertNotEqual(self._sensor_handles[i], _contact_sensor.INVALID_HANDLE)

        readings = []
        self._timeline.play()
        for i in range(60):  # Simulate for one second
            await omni.kit.app.get_app().next_update_async()
            contacts_raw = self._cs.get_body_contact_raw_data(self.leg_paths[0])
            sensor_reading = self._cs.get_sensor_readings(self._sensor_handles[0])
            readings = readings + sensor_reading.tolist()
        self.assertEqual(len(readings), 101)
