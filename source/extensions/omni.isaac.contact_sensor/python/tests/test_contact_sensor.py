# NOTE:
#   omni.kit.test - std python's unittest module with additional wrapping to add suport for async/await tests
#   For most things refer to unittest docs: https://docs.python.org/3/library/unittest.html
import omni.kit.test

import omni.kit.commands
import carb.tokens
import os
import asyncio
import numpy as np
from pxr import Gf, Usd, UsdGeom, UsdShade, UsdLux

# Import extension python module we are testing with absolute import path, as if we are external user (other extension)
from omni.isaac.contact_sensor import _contact_sensor
from omni.kit.builtin.commands.usd_commands import *

# Having a test class dervived from omni.kit.test.AsyncTestCase declared on the root of module will make it auto-discoverable by omni.kit.test
class TestContactSensor(omni.kit.test.AsyncTestCaseFailOnLogError):
    # Before running each test
    async def setUp(self):

        # This needs to be set so that kit updates match physics updates
        physics_rate = carb.settings.get_settings().get("/physics/timeStepsPerSecond")
        carb.settings.get_settings().set_int("/app/runLoops/main/rateLimitFrequency", int(physics_rate))

        self._cs = _contact_sensor.acquire_contact_sensor_interface()
        self._omni_pbr_data = os.path.abspath(
            carb.tokens.get_tokens_interface().resolve("${kit}/../../library/mdl/Base/OmniPBR.mdl")
        )
        ext_manager = omni.kit.app.get_app().get_extension_manager()
        ext_id = ext_manager.get_enabled_extension_id("omni.isaac.contact_sensor")
        self._extension_path = ext_manager.get_extension_path(ext_id)

        self.leg_paths = ["/Ant/Arm_{:02d}/Lower_Arm".format(i + 1) for i in range(4)]
        self.sensor_ofsets = [
            carb.Float3(40, 0, 0),
            carb.Float3(40, 0, 0),
            carb.Float3(40, 0, 0),
            carb.Float3(40, 0, 0),
        ]

        self.shoulder_joints = ["/Ant/Arm_{:02d}/Upper_Arm/shoulder_joint".format(i + 1) for i in range(4)]

        self.lower_joints = ["{}/lower_arm_joint".format(i) for i in self.leg_paths]
        self._sensor_handles = [0 for i in range(4)]

        await omni.usd.get_context().open_stage_async(self._extension_path + "/data/ant.usd")
        self._stage = omni.usd.get_context().get_stage()
        self._editor = omni.kit.editor.get_editor_interface()
        self._timeline = omni.timeline.get_timeline_interface()
        pass

    # After running each test
    async def tearDown(self):
        self._timeline.stop()
        pass

    async def simulate(self, seconds, steps_per_sec=60):
        for frame in range(int(steps_per_sec * seconds)):
            await omni.kit.app.get_app().next_update_async()

    def is_loading(self):
        time, message, loaded, loading = self._editor.get_current_renderer_status()
        return loading > 0

    async def test_add_sensors(self):

        # Add Contact Sensor
        props = _contact_sensor.SensorProperties()
        props.radius = 12  # Cover the entire leg tip
        props.minThreshold = 0
        props.maxThreshold = 1000000000000
        props.sensorPeriod = -1  # one reading per sim step

        for i in range(4):
            props.position = self.sensor_ofsets[i]
            self._sensor_handles[i] = self._cs.add_sensor_on_body(self.leg_paths[i], props)
            self.assertNotEqual(self._sensor_handles[i], _contact_sensor.INVALID_HANDLE)
        pass

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
        await self.simulate(1, steps_per_sec=1)  # simulate 1 step, ant should be in the air
        contacts_raw = self._cs.get_body_contact_raw_data(self.leg_paths[0])
        self.assertEqual(len(contacts_raw), 0)
        await self.simulate(0.5)  # simulate 30 steps, ant should touch ground
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
        await self.simulate(2.0)  # simulate long enough that physx stops sending persistent contact raw data
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
        props.radius = 12  # Cover the entire leg tip
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
        props.sensorPeriod = 1 / 100
        # Sensors will be placed in the middle of capsule, so ground contact should always read zero
        for i in range(4):
            props.position = self.sensor_ofsets[i]
            self._sensor_handles[i] = self._cs.add_sensor_on_body(self.leg_paths[i], props)
            self.assertNotEqual(self._sensor_handles[i], _contact_sensor.INVALID_HANDLE)

        readings = []
        self._timeline.play()
        for i in range(61):  # Simulate for one second
            await omni.kit.app.get_app().next_update_async()
            contacts_raw = self._cs.get_body_contact_raw_data(self.leg_paths[0])
            sensor_reading = self._cs.get_sensor_readings(self._sensor_handles[0])
            readings = readings + sensor_reading.tolist()
        self.assertEqual(len(readings), 101)
