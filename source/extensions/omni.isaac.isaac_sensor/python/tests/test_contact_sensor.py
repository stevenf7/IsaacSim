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
from pxr import UsdGeom, Gf, UsdPhysics, PhysxSchema

# Import extension python module we are testing with absolute import path, as if we are external user (other extension)
from omni.isaac.isaac_sensor import _isaac_sensor
from omni.isaac.core.utils.physics import simulate_async
from omni.isaac.core.utils.extensions import get_extension_path_from_name

import omni.isaac.IsaacSensorSchema as sensorSchema

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


def create_physics_scene(stage, gravity=9.81):
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


class TestContactSensor(omni.kit.test.AsyncTestCase):
    # Before running each test
    async def setUp(self):
        # This needs to be set so that kit updates match physics updates
        self._physics_rate = 60
        carb.settings.get_settings().set_bool("/app/runLoops/main/rateLimitEnabled", True)
        carb.settings.get_settings().set_int("/app/runLoops/main/rateLimitFrequency", int(self._physics_rate))
        carb.settings.get_settings().set_int("/persistent/simulation/minFrameRate", int(self._physics_rate))

        self._cs = _isaac_sensor.acquire_contact_sensor_interface()

        self._extension_path = get_extension_path_from_name("omni.isaac.isaac_sensor")

        self.leg_paths = ["/Ant/Arm_{:02d}/Lower_Arm".format(i + 1) for i in range(4)]

        # sensor offset from the center of the leg, have to consider parent scaling.
        self.sensor_offsets = [Gf.Vec3d(40, 0, 0), Gf.Vec3d(40, 0, 0), Gf.Vec3d(40, 0, 0), Gf.Vec3d(40, 0, 0)]

        # colors for the sensor visualization (r,g,b,a)
        self.color = [(1, 0, 0, 1), (0, 1, 0, 1), (0, 0, 1, 1), (1, 1, 0, 1)]

        self.shoulder_joints = ["/Ant/Arm_{:02d}/Upper_Arm/shoulder_joint".format(i + 1) for i in range(4)]

        self.lower_joints = ["{}/lower_arm_joint".format(i) for i in self.leg_paths]
        self._sensor_handles = [0 for i in range(4)]

        await omni.usd.get_context().open_stage_async(self._extension_path + "/data/ant.usd")
        self._stage = omni.usd.get_context().get_stage()
        self._timeline = omni.timeline.get_timeline_interface()
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
                "IsaacSensorCreateContactSensor",
                path="/sensor",
                parent=self.leg_paths[i],
                min_threshold=0,
                max_threshold=10000000,
                color=self.color[i],
                radius=0.12,
                sensor_period=-1,
                offset=self.sensor_offsets[i],
                visualize=True,
            )
            self.sensorGeoms.append(sensor)
            self.assertTrue(result)
        pass

    # test plan:
    # move the ground to -10, simulate 10 steps, test for no contact
    # move the ground to -0.78, simulate 60 steps, test for contact
    # test raw contact value, z-normal ~ 1.0
    # move teh ground to -15, simulate 30 steps, test for no contact
    async def test_lost_contacts(self):
        await self.test_add_sensor_prim()
        xform = UsdGeom.Xformable(self._stage.GetPrimAtPath("/World/GroundPlane"))
        xform_op = xform.GetOrderedXformOps()[0]
        xform_op.Set(Gf.Vec3d(0, 0, -10))

        await omni.kit.app.get_app().next_update_async()
        self._timeline.play()
        await simulate_async(0.1)  # simulate 0.1 s
        contacts_raw = self._cs.get_contact_sensor_raw_data(self.leg_paths[0] + "/sensor")
        self.assertEqual(len(contacts_raw), 0)

        xform = UsdGeom.Xformable(self._stage.GetPrimAtPath("/World/GroundPlane"))
        xform_op = xform.GetOrderedXformOps()[0]
        xform_op.Set(Gf.Vec3d(0, 0, -0.78))
        await simulate_async(1)  # simulate 60 steps, ant should touch ground
        contacts_raw = self._cs.get_contact_sensor_raw_data(self.leg_paths[0] + "/sensor")
        self.assertEqual(len(contacts_raw), 1)

        c = contacts_raw[0]
        body0 = self._cs.decode_body_name(c["body0"])
        body1 = self._cs.decode_body_name(c["body1"])
        if not (body0 == self.leg_paths[0] or body1 == self.leg_paths[0]):
            self.fail("Raw contact does not contain queried body {} ({},{})".format(self.leg_paths[0], body0, body1))
        self.assertAlmostEqual(1.0, c["normal"]["z"], delta=6)
        print(c)

        # move the ground to lose the contacts
        xform = UsdGeom.Xformable(self._stage.GetPrimAtPath("/World/GroundPlane"))
        xform_op = xform.GetOrderedXformOps()[0]
        xform_op.Set(Gf.Vec3d(0, 0, -15))
        await simulate_async(0.5)
        contacts_raw = self._cs.get_contact_sensor_raw_data(self.leg_paths[0] + "/sensor")
        self.assertEqual(len(contacts_raw), 0)

    async def test_get_raw_data(self):
        await self.test_add_sensor_prim()
        await omni.kit.app.get_app().next_update_async()
        self._timeline.play()
        await simulate_async(1)  # simulate 60 steps, ant should touch ground
        contacts_raw = self._cs.get_contact_sensor_raw_data(self.leg_paths[0] + "/sensor")
        self.assertEqual(len(contacts_raw), 1)

        c = contacts_raw[0]
        body0 = self._cs.decode_body_name(c["body0"])
        body1 = self._cs.decode_body_name(c["body1"])
        if not (body0 == self.leg_paths[0] or body1 == self.leg_paths[0]):
            self.fail("Raw contact does not contain queried body {} ({},{})".format(self.leg_paths[0], body0, body1))
        self.assertAlmostEqual(1.0, c["normal"]["z"], delta=6)
        print(c)

    async def test_persistent_raw_data(self):
        await self.test_add_sensor_prim()
        self._timeline.play()
        await simulate_async(2.0)  # simulate long enough that physx stops sending persistent contact raw data
        contacts_raw = self._cs.get_contact_sensor_raw_data(self.leg_paths[0] + "/sensor")
        self.assertEqual(len(contacts_raw), 1)

        c = contacts_raw[0]
        body0 = self._cs.decode_body_name(c["body0"])
        body1 = self._cs.decode_body_name(c["body1"])
        if not (body0 == self.leg_paths[0] or body1 == self.leg_paths[0]):
            self.fail("Raw contact does not contain queried body {} ({},{})".format(self.leg_paths[0], body0, body1))
        self.assertAlmostEqual(1.0, c["normal"]["z"], delta=6)
        print(c)

    async def test_get_sensor_readings(self):
        await self.test_add_sensor_prim()
        await omni.kit.app.get_app().next_update_async()
        self._timeline.play()

        await simulate_async(1.0)
        for i in range(120):
            await omni.kit.app.get_app().next_update_async()
            contacts_raw = self._cs.get_contact_sensor_raw_data(self.leg_paths[0] + "/sensor")
            sensor_reading = self._cs.get_sensor_readings(self.leg_paths[0] + "/sensor")
            self.assertTrue(len(sensor_reading) >= 1)
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
                print(str(sensor_reading["value"]))
                self.assertAlmostEqual(force, sensor_reading["value"], 2)
            else:
                # No contact, reading should be zero
                self.assertEqual(sensor_reading["value"], 0)
        pass

    async def test_delayed_get_sensor_readings(self):
        await self.test_add_sensor_prim()
        await omni.kit.app.get_app().next_update_async()
        self._timeline.play()
        await simulate_async(1.0)

        for i in range(120):
            await omni.kit.app.get_app().next_update_async()

        contacts_raw = self._cs.get_contact_sensor_raw_data(self.leg_paths[0] + "/sensor")
        sensor_reading = self._cs.get_sensor_readings(self.leg_paths[0] + "/sensor")
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
        cube_prim = add_cube(self._stage, "/cube", 1, (2, 2, 0), physics=True)
        mass = 10
        massAPI = UsdPhysics.MassAPI.Apply(cube_prim)
        massAPI.CreateMassAttr(mass)

        # create fully body sensor (radius -1)
        result, sensor = omni.kit.commands.execute(
            "IsaacSensorCreateContactSensor",
            path="/sensor",
            parent="/cube",
            min_threshold=0,
            max_threshold=10000000,
            color=(1, 1, 1, 1),
            radius=-1,
            sensor_period=-1,
            visualize=True,
        )
        self.assertTrue(result)

        # need this sync to add the cube into the physics engine
        await omni.kit.app.get_app().next_update_async()
        self._timeline.play()
        await simulate_async(1.5)
        await omni.kit.app.get_app().next_update_async()

        sensor_reading = self._cs.get_sensor_readings("/cube/sensor")
        self.assertEqual(len(sensor_reading), 1)
        sensor_reading = sensor_reading[0]
        self.assertAlmostEqual(sensor_reading["value"], mass * 9.81, 1)
        pass

    async def test_get_sensor_sim_reading(self):
        await self.test_add_sensor_prim()
        self._timeline.play()
        await simulate_async(1.0)
        for i in range(120):
            await omni.kit.app.get_app().next_update_async()
            contacts_raw = self._cs.get_contact_sensor_raw_data(self.leg_paths[0] + "/sensor")
            sensor_reading = self._cs.get_sensor_sim_reading(self.leg_paths[0] + "/sensor")
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
        self.sensorGeoms = []

        # create 4 sensors at the center of the leg
        for i in range(4):
            result, sensor = omni.kit.commands.execute(
                "IsaacSensorCreateContactSensor",
                path="/sensor",
                parent=self.leg_paths[i],
                min_threshold=0,
                max_threshold=10000000,
                color=self.color[i],
                radius=0.12,
                sensor_period=-1,
                offset=Gf.Vec3f(0, 0, 0),
                visualize=True,
            )
            self.sensorGeoms.append(sensor)
            self.assertTrue(result)

        await omni.kit.app.get_app().next_update_async()
        self._timeline.play()
        await simulate_async(1)

        for i in range(40):
            await omni.kit.app.get_app().next_update_async()
            sensor_reading = self._cs.get_sensor_readings(self.leg_paths[0] + "/sensor")
            self.assertEqual(len(sensor_reading), 1)
            sensor_reading = sensor_reading[0]
            self.assertEqual(sensor_reading["value"], 0)
        pass

    async def test_sensor_period(self):
        # create four sensors that run at 120hz
        for i in range(4):
            result, sensor = omni.kit.commands.execute(
                "IsaacSensorCreateContactSensor",
                path="/sensor",
                parent=self.leg_paths[i],
                min_threshold=0,
                max_threshold=10000000,
                color=self.color[i],
                radius=0.12,
                sensor_period=1.0 / 120.0,
                offset=self.sensor_offsets[i],
                visualize=True,
            )
            self.assertTrue(result)

        await omni.kit.app.get_app().next_update_async()
        self._timeline.play()
        # give it some time to reach the ground first
        await simulate_async(1.5)
        await omni.kit.app.get_app().next_update_async()
        readings = []

        for i in range(60):  # Simulate for one second
            await omni.kit.app.get_app().next_update_async()
            raw = self._cs.get_contact_sensor_raw_data(self.leg_paths[0] + "/sensor")
            print(str(raw))
            sensor_reading = self._cs.get_sensor_readings(self.leg_paths[0] + "/sensor")
            print(str(sensor_reading))
            sensor_sim = self._cs.get_sensor_sim_reading(self.leg_paths[0] + "/sensor")
            print(str(sensor_sim.value))
            readings = readings + sensor_reading.tolist()

        # tolerance +-1 reading (119, 120, 121 will be accepted)
        print(len(readings))
        self.assertTrue(abs(len(readings) - 120) <= 1)
        pass

    async def test_cubes_not_touching_restart(self):
        print("before cube add")

        cube_prim = add_cube(self._stage, "/cube", 1, (2, 2, 10), physics=True)
        cube_prim2 = add_cube(self._stage, "/cube2", 1, (5, 2, 10), physics=True)

        mass = 10
        massAPI = UsdPhysics.MassAPI.Apply(cube_prim)
        massAPI = UsdPhysics.MassAPI.Apply(cube_prim2)
        massAPI.CreateMassAttr(mass)

        print("before contact sensor create")

        # create fully body sensor (radius -1)
        result, sensor = omni.kit.commands.execute(
            "IsaacSensorCreateContactSensor",
            path="/sensor",
            parent="/cube",
            min_threshold=0,
            max_threshold=10000000,
            color=(1, 1, 1, 1),
            radius=-1,
            sensor_period=-1,
            visualize=True,
        )
        self.assertTrue(result)

        print("before refresh")

        # need this sync to add the cube into the physics engine
        await omni.kit.app.get_app().next_update_async()

        print("before play")
        self._timeline.play()

        print("before loop")
        for i in range(30):  # Simulate for one second
            await omni.kit.app.get_app().next_update_async()
            print("before reading")
            sensor_reading = self._cs.get_sensor_readings("/cube/sensor")
            print("sensor reading: " + str(sensor_reading))
            sensor_sim = self._cs.get_sensor_sim_reading("/cube/sensor")
            print("sensor sim: " + str(sensor_sim))

        self._timeline.stop()
        await omni.kit.app.get_app().next_update_async()
        await omni.kit.app.get_app().next_update_async()
        self._timeline.play()
        print("TIMELINE RESTARTED")

        for i in range(30):  # Simulate for one second
            await omni.kit.app.get_app().next_update_async()
            sensor_reading = self._cs.get_sensor_readings("/cube/sensor")
            print("sensor reading: " + str(sensor_reading))
            sensor_sim = self._cs.get_sensor_sim_reading("/cube/sensor")
            print("sensor sim: " + str(sensor_sim))

        pass

    async def test_cubes_not_touching_then_touching_restart(self):
        cube_prim = add_cube(self._stage, "/cube", 1, (2, 2, 10), physics=True)
        cube_prim2 = add_cube(self._stage, "/cube2", 1, (5, 2, 10), physics=True)

        mass = 10
        massAPI = UsdPhysics.MassAPI.Apply(cube_prim)
        massAPI = UsdPhysics.MassAPI.Apply(cube_prim2)
        massAPI.CreateMassAttr(mass)

        # create fully body sensor (radius -1)
        result, sensor = omni.kit.commands.execute(
            "IsaacSensorCreateContactSensor",
            path="/sensor",
            parent="/cube",
            min_threshold=0,
            max_threshold=10000000,
            color=(1, 1, 1, 1),
            radius=-1,
            sensor_period=-1,
            visualize=True,
        )
        self.assertTrue(result)

        # need this sync to add the cube into the physics engine
        await omni.kit.app.get_app().next_update_async()
        self._timeline.play()

        for i in range(30):  # Simulate for one second
            await omni.kit.app.get_app().next_update_async()
            sensor_reading = self._cs.get_sensor_readings("/cube/sensor")
            print("sensor reading: " + str(sensor_reading))
            sensor_sim = self._cs.get_sensor_sim_reading("/cube/sensor")
            print("sensor sim: " + str(sensor_sim))

        self._timeline.stop()
        await omni.kit.app.get_app().next_update_async()

        cube_prim3 = add_cube(self._stage, "/cube3", 1, (2, 3, 0), physics=True)
        massAPI = UsdPhysics.MassAPI.Apply(cube_prim3)
        await omni.kit.app.get_app().next_update_async()
        await omni.kit.app.get_app().next_update_async()

        self._timeline.play()
        print("TIMELINE RESTARTED")
        for i in range(30):  # Simulate for one second

            await omni.kit.app.get_app().next_update_async()
            sensor_reading = self._cs.get_sensor_readings("/cube/sensor")
            print("sensor reading: " + str(sensor_reading))
            sensor_sim = self._cs.get_sensor_sim_reading("/cube/sensor")
            print("sensor sim: " + str(sensor_sim))

        pass

    async def test_cubes_touching_restart(self):
        cube_prim = add_cube(self._stage, "/cube", 1, (2, 2, 0), physics=True)
        cube_prim2 = add_cube(self._stage, "/cube2", 1, (2, 3, 0), physics=True)

        mass = 10
        massAPI = UsdPhysics.MassAPI.Apply(cube_prim)
        massAPI = UsdPhysics.MassAPI.Apply(cube_prim2)
        massAPI.CreateMassAttr(mass)

        # create fully body sensor (radius -1)
        result, sensor = omni.kit.commands.execute(
            "IsaacSensorCreateContactSensor",
            path="/sensor",
            parent="/cube",
            min_threshold=0,
            max_threshold=10000000,
            color=(1, 1, 1, 1),
            radius=-1,
            sensor_period=-1,
            visualize=True,
        )
        self.assertTrue(result)

        # need this sync to add the cube into the physics engine
        await omni.kit.app.get_app().next_update_async()
        self._timeline.play()

        for i in range(30):  # Simulate for one second
            await omni.kit.app.get_app().next_update_async()
            sensor_reading = self._cs.get_sensor_readings("/cube/sensor")
            print("sensor reading: " + str(sensor_reading))
            # sensor_sim = self._cs.get_sensor_sim_reading("/cube/sensor")
            # print("sensor sim: " + str(sensor_sim))

        self._timeline.stop()
        await omni.kit.app.get_app().next_update_async()
        await omni.kit.app.get_app().next_update_async()
        self._timeline.play()
        print("TIMELINE RESTARTED")
        for i in range(30):  # Simulate for one second

            await omni.kit.app.get_app().next_update_async()
            sensor_reading = self._cs.get_sensor_readings("/cube/sensor")
            print("sensor reading: " + str(sensor_reading))
            # sensor_sim = self._cs.get_sensor_sim_reading("/cube/sensor")
            # print("sensor sim: " + str(sensor_sim))

        pass

    async def test_cubes_touching_then_not_touching_restart(self):
        cube_prim = add_cube(self._stage, "/cube", 1, (2, 2, 0), physics=True)
        cube_prim2 = add_cube(self._stage, "/cube2", 1, (2, 3, 0), physics=True)

        mass = 10
        massAPI = UsdPhysics.MassAPI.Apply(cube_prim)
        massAPI = UsdPhysics.MassAPI.Apply(cube_prim2)
        massAPI.CreateMassAttr(mass)

        # create fully body sensor (radius -1)
        result, sensor = omni.kit.commands.execute(
            "IsaacSensorCreateContactSensor",
            path="/sensor",
            parent="/cube",
            min_threshold=0,
            max_threshold=10000000,
            color=(1, 1, 1, 1),
            radius=-1,
            sensor_period=-1,
            visualize=True,
        )

        self.assertTrue(result)

        # need this sync to add the cube into the physics engine
        await omni.kit.app.get_app().next_update_async()
        print("next update fail")

        self._timeline.play()
        print("timeline play fail")

        for i in range(30):  # Simulate for one second
            await omni.kit.app.get_app().next_update_async()
            sensor_reading = self._cs.get_sensor_readings("/cube/sensor")

            print("sensor reading: " + str(sensor_reading))
            # sensor_sim = self._cs.get_sensor_sim_reading("/cube/sensor")
            # print("sensor sim: " + str(sensor_sim))

        self._timeline.stop()
        await omni.kit.app.get_app().next_update_async()

        omni.kit.commands.execute("IsaacSimDestroyPrim", prim_path="/cube2")

        await omni.kit.app.get_app().next_update_async()

        self._timeline.play()
        print("TIMELINE RESTARTED")
        for i in range(30):  # Simulate for one second

            await omni.kit.app.get_app().next_update_async()
            sensor_reading = self._cs.get_sensor_readings("/cube/sensor")
            print("sensor reading: " + str(sensor_reading))
        #           sensor_sim = self._cs.get_sensor_sim_reading("/cube/sensor")
        #            print("sensor sim: " + str(sensor_sim))

        pass
