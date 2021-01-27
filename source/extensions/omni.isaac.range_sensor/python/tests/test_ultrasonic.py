import omni.kit.test
import omni.kit.commands

# Import extension python module we are testing with absolute import path, as if we are external user (other extension)
from omni.isaac.range_sensor import _range_sensor
from pxr import Usd, UsdGeom, UsdLux, Sdf, Gf, UsdPhysics
from omni.physx.scripts import utils
import omni.isaac.RangeSensorSchema as RangeSensorSchema
import asyncio
import numpy as np
import os
import carb.tokens


def get_data_file(file_name: str):
    if os.path.isabs(file_name):
        path_to_file = file_name
    else:
        path_to_file = os.path.abspath(
            os.path.join(carb.tokens.get_tokens_interface().resolve("${app}"), "..", "data", "usd", file_name)
        )
    return path_to_file


async def load_test_file(test_file_name: str):
    if not Usd.Stage.IsSupportedFile(test_file_name):
        raise ValueError("Only USD files can be loaded with this method")

    path_to_file = get_data_file(test_file_name)

    usd_context = omni.usd.get_context()
    usd_context.disable_save_to_recent_files()
    (result, error) = await omni.usd.get_context().open_stage_async(path_to_file)
    usd_context.enable_save_to_recent_files()
    return (result, error)


async def simulate(seconds, steps_per_sec=60):
    for frame in range(int(steps_per_sec * seconds)):
        await omni.kit.app.get_app().next_update_async()


# Having a test class dervived from omni.kit.test.AsyncTestCase declared on the root of module will make it auto-discoverable by omni.kit.test
class TestUltrasonic(omni.kit.test.AsyncTestCaseFailOnLogError):
    # Before running each test
    async def setUp(self):

        self._physics_rate = carb.settings.get_settings().get("/physics/timeStepsPerSecond")
        carb.settings.get_settings().set_bool("/app/runLoops/main/rateLimitEnabled", True)
        carb.settings.get_settings().set_int("/app/runLoops/main/rateLimitFrequency", int(self._physics_rate))
        carb.settings.get_settings().set_int("persistent/physics/maxNumSteps", int(1))

        self._ultrasonic = _range_sensor.acquire_ultrasonic_sensor_interface()
        self._timeline = omni.timeline.get_timeline_interface()
        await omni.usd.get_context().new_stage_async()
        self._stage = omni.usd.get_context().get_stage()

        # light
        sphereLight = UsdLux.SphereLight.Define(self._stage, Sdf.Path("/World/SphereLight"))
        sphereLight.CreateRadiusAttr(150)
        sphereLight.CreateIntensityAttr(30000)
        sphereLight.AddTranslateOp().Set(Gf.Vec3f(650.0, 0.0, 1150.0))

        # set up axis to z
        UsdGeom.SetStageUpAxis(self._stage, UsdGeom.Tokens.z)
        UsdGeom.SetStageMetersPerUnit(self._stage, 0.01)

        # Physics scene
        scene = UsdPhysics.Scene.Define(self._stage, Sdf.Path("/World/physicsScene"))
        scene.CreateGravityDirectionAttr().Set(Gf.Vec3f(0.0, 0.0, -1.0))
        scene.CreateGravityMagnitudeAttr().Set(981.0)

        ext_manager = omni.kit.app.get_app().get_extension_manager()
        ext_id = ext_manager.get_enabled_extension_id("omni.isaac.range_sensor")
        self._extension_path = ext_manager.get_extension_path(ext_id)

    # After running each test
    async def tearDown(self):
        self._timeline.stop()
        pass

    async def sweep_parameter(self, parameter, min_v, max_v, step):
        print(parameter.GetName())
        for value in np.arange(min_v, max_v, step):
            # print(value)
            parameter.Set(float(value))
            await omni.kit.app.get_app().next_update_async()
            await omni.kit.app.get_app().next_update_async()

    # Create a cube, set physics to False to make it static with collision only
    def add_cube(self, path, size, offset, physics=True):

        cubeGeom = UsdGeom.Cube.Define(self._stage, path)
        cubePrim = self._stage.GetPrimAtPath(path)
        cubeGeom.CreateSizeAttr(size)
        cubeGeom.AddTranslateOp().Set(offset)
        if physics:
            utils.setRigidBody(cubePrim, "convexHull", False)
        else:
            utils.setCollider(cubePrim)

        return cubePrim

    # Test to make sure that command can create emitter and array without any errors
    # Simulate and stop to make sure it doesn't crash
    async def test_command(self):

        result, emitter = omni.kit.commands.execute(
            "CreateRangeSensorUltrasonicEmitterCommand",
            path="/World/UltrasonicEmitter",
            per_ray_intensity=0.4,
            yaw_offset=0.0,
            firing_delay=0.0,
        )
        result, ultrasonic = omni.kit.commands.execute(
            "CreateRangeSensorUltrasonicArrayCommand",
            path="/World/UltrasonicArray",
            min_range=0.4,
            max_range=2.0,
            draw_points=True,
            draw_lines=True,
            horizontal_fov=20.0,
            vertical_fov=10.0,
            horizontal_resolution=0.4,
            vertical_resolution=0.8,
            pulse_duration=0.5,
            pulse_gap_delta=1.0,
            num_bins=224,
            emitter_prims=[emitter.GetPath()],
        )
        self.assertTrue(result)
        self._timeline.play()
        await simulate(0.5)
        self._timeline.stop()
        await simulate(0.1)
        self._timeline.play()
        await simulate(0.5)

    # Create two emitters, test to make sure that data from them is correct
    async def test_two_emitter(self):

        result, emitter0 = omni.kit.commands.execute(
            "CreateRangeSensorUltrasonicEmitterCommand",
            path="/World/UltrasonicEmitter0",
            per_ray_intensity=0.4,
            yaw_offset=0.0,
            firing_delay=0.1,
        )
        emitter0.GetPrim().GetAttribute("xformOp:translate").Set(Gf.Vec3d(0.0, 0.0, 0.0))
        # Rotate 90 degrees about z
        emitter0.GetPrim().GetAttribute("xformOp:rotateXYZ").Set(Gf.Vec3d(0, 0, 90))

        result, emitter1 = omni.kit.commands.execute(
            "CreateRangeSensorUltrasonicEmitterCommand",
            path="/World/UltrasonicEmitter1",
            per_ray_intensity=0.4,
            yaw_offset=0.0,
            firing_delay=0.2,
        )
        emitter1.GetPrim().GetAttribute("xformOp:translate").Set(Gf.Vec3d(0.0, 0.0, 0.0))

        result, ultrasonic = omni.kit.commands.execute(
            "CreateRangeSensorUltrasonicArrayCommand",
            path="/World/UltrasonicArray",
            min_range=0.4,
            max_range=2.0,
            draw_points=True,
            draw_lines=True,
            horizontal_fov=20.0,
            vertical_fov=10.0,
            horizontal_resolution=0.4,
            vertical_resolution=0.8,
            pulse_duration=0.1,
            pulse_gap_delta=0.3,
            num_bins=224,
            emitter_prims=[emitter0.GetPath(), emitter1.GetPath()],
        )
        self.assertTrue(result)

        self.add_cube("/World/Cube0", 25.0, Gf.Vec3f(0.0, 100.0, 0.0), physics=False)
        self.add_cube("/World/Cube1", 25.0, Gf.Vec3f(0.0, -90.0, 0.0), physics=False)
        self.add_cube("/World/Cube2", 25.0, Gf.Vec3f(80.0, 0.0, 0.0), physics=False)
        self.add_cube("/World/Cube3", 25.0, Gf.Vec3f(-70.0, 0.0, 0.0), physics=False)

        self._timeline.play()
        await simulate(2.0)
        # TODO test to make sure that the sensor is firing at correct times
        # TODO test to make sure that distances are correct
        depth = self._ultrasonic.get_linear_depth_data("/World/UltrasonicArray", 0)

    # TODO: Add test that makes emitter on dynamic object
    # TODO: Add test that changes a parameter on the array and the emitter to make sure USD updates are working

    # TODO: re-work the existing tests to make sure that they work
    # # ensures that envelope changes when cube is moved
    async def test_static_ultrasonic_moving_box(self):
        # Plane
        omni.kit.commands.execute(
            "AddGroundPlaneCommand",
            stage=self._stage,
            planePath="/World/groundPlane",
            axis="Z",
            size=1500.0,
            position=Gf.Vec3f(0),
            color=Gf.Vec3f(0.5),
        )

        # Add a cube
        cubePath = "/World/Cube"
        cubePrim = self.add_cube(cubePath, 25.0, Gf.Vec3f(0.0, -90.0, 0.0))

        emitter_poses = [
            (Gf.Quatd(0.951057, 0, 0, -0.309017), Gf.Vec3d(25, 0.0, 25)),
            (Gf.Quatd(0.987688, 0, 0, -0.156434), Gf.Vec3d(25, 50.0, 25)),
            (Gf.Quatd(0.987688, 0, 0, 0.156434), Gf.Vec3d(25, 100, 25)),
            (Gf.Quatd(0.951057, 0, 0, 0.309017), Gf.Vec3d(25, 150, 25)),
            (Gf.Quatd(-0.309017, 0, 0, 0.951056), Gf.Vec3d(-25, 0.0, 25)),
            (Gf.Quatd(-0.156435, 0, 0, 0.987688), Gf.Vec3d(-25, 50.0, 25)),
            (Gf.Quatd(0.156434, 0, 0, 0.987688), Gf.Vec3d(-25, 100, 25)),
            (Gf.Quatd(0.309017, 0, 0, 0.951057), Gf.Vec3d(-25, 150, 25)),
            (Gf.Quatd(0.760406, 0, 0, -0.649448), Gf.Vec3d(12.5, 0.0, 25)),
            (Gf.Quatd(0.649448, 0, 0, -0.760406), Gf.Vec3d(12.5, 0.0, 25)),
            (Gf.Quatd(0.760406, 0, 0, 0.649448), Gf.Vec3d(12.5, 150, 25)),
            (Gf.Quatd(0.649448, 0, 0, 0.760406), Gf.Vec3d(12.5, 150, 25)),
        ]

        emitters = []
        for pose in emitter_poses:
            result, emitter_prim = omni.kit.commands.execute(
                "CreateRangeSensorUltrasonicEmitterCommand",
                path="/World/UltrasonicEmitter",
                per_ray_intensity=0.4,
                yaw_offset=0.0,
                firing_delay=0.5,
            )
            emitter_prim.GetPrim().GetAttribute("xformOp:translate").Set(pose[1])
            emitter_prim.GetPrim().GetAttribute("xformOp:rotateXYZ").Set(
                Gf.Rotation(pose[0]).Decompose((1, 0, 0), (0, 1, 0), (0, 0, 1))
            )
            emitters.append(emitter_prim)
        emitter_paths = [emitter.GetPath() for emitter in emitters]

        # Add ultrasonic
        ultrasonicPath = "/World/UltrasonicArray"
        result, ultrasonic = omni.kit.commands.execute(
            "CreateRangeSensorUltrasonicArrayCommand",
            path=ultrasonicPath,
            min_range=0.4,
            max_range=2.0,
            draw_points=True,
            horizontal_fov=20.0,
            vertical_fov=10.0,
            horizontal_resolution=0.4,
            vertical_resolution=0.8,
            pulse_duration=0.5,
            pulse_gap_delta=1.0,
            num_bins=224,
            emitter_prims=emitter_paths,
        )

        # run for 12s @ 50Hz
        steps_per_sec = 50
        seconds = 3
        self._timeline.play()

        await simulate(seconds, steps_per_sec=steps_per_sec)
        envelope_arr = self._ultrasonic.get_envelope_array(ultrasonicPath)
        cubePrim.GetAttribute("xformOp:translate").Set(Gf.Vec3f(20.0, 220.0, 0.0))
        await simulate(seconds, steps_per_sec=steps_per_sec)
        envelope_arr2 = self._ultrasonic.get_envelope_array(ultrasonicPath)
        envelope_diff = envelope_arr - envelope_arr2
        self.assertFalse(envelope_diff[0].any())
        self.assertTrue(envelope_diff[10].any())
        self.assertTrue(envelope_diff[11].any())

    # # ensures that envelope changes when cube is moved progressively further away from sensor
    async def test_move_box_to_muliple_distances(self):
        # Plane
        omni.kit.commands.execute(
            "AddGroundPlaneCommand",
            stage=self._stage,
            planePath="/World/groundPlane",
            axis="Z",
            size=1500.0,
            position=Gf.Vec3f(0),
            color=Gf.Vec3f(0.5),
        )

        # Add a cube
        cubePath = "/World/Cube"
        cubePrim = self.add_cube(cubePath, 25.0, Gf.Vec3f(0.0, -90.0, 0.0))

        emitter_poses = [
            (Gf.Quatd(0.951057, 0, 0, -0.309017), Gf.Vec3d(25, 0.0, 25)),
            (Gf.Quatd(0.987688, 0, 0, -0.156434), Gf.Vec3d(25, 50.0, 25)),
            (Gf.Quatd(0.987688, 0, 0, 0.156434), Gf.Vec3d(25, 100, 25)),
            (Gf.Quatd(0.951057, 0, 0, 0.309017), Gf.Vec3d(25, 150, 25)),
            (Gf.Quatd(-0.309017, 0, 0, 0.951056), Gf.Vec3d(-25, 0.0, 25)),
            (Gf.Quatd(-0.156435, 0, 0, 0.987688), Gf.Vec3d(-25, 50.0, 25)),
            (Gf.Quatd(0.156434, 0, 0, 0.987688), Gf.Vec3d(-25, 100, 25)),
            (Gf.Quatd(0.309017, 0, 0, 0.951057), Gf.Vec3d(-25, 150, 25)),
            (Gf.Quatd(0.760406, 0, 0, -0.649448), Gf.Vec3d(12.5, 0.0, 25)),
            (Gf.Quatd(0.649448, 0, 0, -0.760406), Gf.Vec3d(12.5, 0.0, 25)),
            (Gf.Quatd(0.760406, 0, 0, 0.649448), Gf.Vec3d(12.5, 150, 25)),
            (Gf.Quatd(0.649448, 0, 0, 0.760406), Gf.Vec3d(12.5, 150, 25)),
        ]

        emitters = []
        for pose in emitter_poses:
            result, emitter_prim = omni.kit.commands.execute(
                "CreateRangeSensorUltrasonicEmitterCommand",
                path="/World/UltrasonicEmitter",
                per_ray_intensity=0.4,
                yaw_offset=0.0,
                firing_delay=0.5,
            )
            emitter_prim.GetPrim().GetAttribute("xformOp:translate").Set(pose[1])
            emitter_prim.GetPrim().GetAttribute("xformOp:rotateXYZ").Set(
                Gf.Rotation(pose[0]).Decompose((1, 0, 0), (0, 1, 0), (0, 0, 1))
            )
            emitters.append(emitter_prim)
        emitter_paths = [emitter.GetPath() for emitter in emitters]

        # Add ultrasonic
        ultrasonicPath = "/World/UltrasonicArray"
        result, ultrasonic = omni.kit.commands.execute(
            "CreateRangeSensorUltrasonicArrayCommand",
            path=ultrasonicPath,
            min_range=0.4,
            max_range=2.0,
            draw_points=True,
            horizontal_fov=20.0,
            vertical_fov=10.0,
            horizontal_resolution=0.4,
            vertical_resolution=0.8,
            pulse_duration=0.5,
            pulse_gap_delta=1.0,
            num_bins=224,
            emitter_prims=emitter_paths,
        )

        # run for 3s @ 50Hz
        steps_per_sec = 50
        seconds = 3
        self._timeline.play()
        await simulate(seconds, steps_per_sec=steps_per_sec)
        envelope_arr = self._ultrasonic.get_envelope_array(ultrasonicPath)
        self.assertTrue(np.allclose(envelope_arr[9][87:93], np.array([99.0, 140.0, 130.0, 59.0, 21.0, 1.0])))

        # move box then confirm that the envelopes have changed
        cubePrim.GetAttribute("xformOp:translate").Set(Gf.Vec3f(0.0, -120.0, 0.0))
        await simulate(seconds, steps_per_sec=steps_per_sec)
        envelope_arr2 = self._ultrasonic.get_envelope_array(ultrasonicPath)
        self.assertTrue(np.allclose(envelope_arr2[9][87:93], np.array([0.0, 0.0, 0.0, 0.0, 0.0, 0.0])))
        self.assertTrue(np.allclose(envelope_arr2[9][120:127], np.array([13.0, 81.0, 99.0, 96.0, 67.0, 19.0, 2.0])))

        # move box further and again confirm that the envelopes have changed
        cubePrim.GetAttribute("xformOp:translate").Set(Gf.Vec3f(0.0, -190.0, 0.0))
        await simulate(seconds, steps_per_sec=steps_per_sec)
        envelope_arr3 = self._ultrasonic.get_envelope_array(ultrasonicPath)
        self.assertTrue(np.allclose(envelope_arr3[9][120:127], np.array([0.0, 0.0, 0.0, 0.0, 25.0, 0.0, 0.0])))
        self.assertTrue(np.allclose(envelope_arr3[9][199:203], np.array([21.0, 49.0, 26.0, 4.0])))
