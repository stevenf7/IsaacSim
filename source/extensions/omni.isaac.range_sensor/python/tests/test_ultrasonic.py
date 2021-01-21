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


# Having a test class dervived from omni.kit.test.AsyncTestCase declared on the root of module will make it auto-discoverable by omni.kit.test
class TestUltrasonic(omni.kit.test.AsyncTestCaseFailOnLogError):
    # Before running each test
    async def setUp(self):
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

    def add_ultrasonic(self, ultrasonicPath):

        ultrasonic = RangeSensorSchema.Ultrasonic.Define(self._stage, Sdf.Path(ultrasonicPath))
        ultrasonic.CreateHorizontalFovAttr().Set(20.0)
        ultrasonic.CreateVerticalFovAttr().Set(10.0)
        ultrasonic.CreateHorizontalResolutionAttr().Set(0.4)
        ultrasonic.CreateVerticalResolutionAttr().Set(0.8)
        ultrasonic.CreateMinRangeAttr().Set(0.4)
        ultrasonic.CreateMaxRangeAttr().Set(2.0)
        ultrasonic.CreateDrawPointsAttr().Set(True)

        xform = UsdGeom.Xformable(ultrasonic)
        xform_op = xform.AddXformOp(UsdGeom.XformOp.TypeTransform, UsdGeom.XformOp.PrecisionDouble, "")

        return ultrasonic

    def add_cube(self, path, size, offset):

        cubeGeom = UsdGeom.Cube.Define(self._stage, path)
        cubePrim = self._stage.GetPrimAtPath(path)
        cubeGeom.CreateSizeAttr(size)
        cubeGeom.AddTranslateOp().Set(offset)
        utils.setRigidBody(cubePrim, "convexHull", False)

        return cubePrim

    # Tests a static ultrasonic with a cube in front of it
    async def test_static_ultrasonic(self):
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

        # Add ultrasonic
        ultrasonicPath = "/World/Ultrasonic"
        ultrasonic = self.add_ultrasonic(ultrasonicPath)

        ultrasonic.AddTranslateOp().Set(Gf.Vec3f(8.0, 0.0, 2.0))

        # run for 12s @ 500Hz
        steps_per_sec = 500
        seconds = 3
        self._timeline.play()
        for frame in range(steps_per_sec * seconds):
            await omni.kit.app.get_app().next_update_async()
            emitter_idx = 3
            depth = self._ultrasonic.get_depth_data(ultrasonicPath, emitter_idx)
            lin_depth = self._ultrasonic.get_linear_depth_data(ultrasonicPath, emitter_idx)
            intensity = self._ultrasonic.get_intensity_data(ultrasonicPath, emitter_idx)
            envelope = self._ultrasonic.get_envelope(ultrasonicPath, emitter_idx)

        envelope_arr = self._ultrasonic.get_envelope_array(ultrasonicPath)

        # move box then confirm that the envelopes have changed
        cubePrim.GetAttribute("xformOp:translate").Set(Gf.Vec3f(20.0, 220.0, 0.0))
        for frame in range(steps_per_sec * seconds):
            await omni.kit.app.get_app().next_update_async()
            emitter_idx = 3
            depth2 = self._ultrasonic.get_depth_data(ultrasonicPath, emitter_idx)
            lin_depth2 = self._ultrasonic.get_linear_depth_data(ultrasonicPath, emitter_idx)

        envelope_arr2 = self._ultrasonic.get_envelope_array(ultrasonicPath)
        res = envelope_arr - envelope_arr2
        self.assertFalse(res[0].any())
        self.assertTrue(res[10].any())
        self.assertTrue(res[11].any())
        self._timeline.stop()
