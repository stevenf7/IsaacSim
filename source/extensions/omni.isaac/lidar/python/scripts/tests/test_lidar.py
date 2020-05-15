import omni.kit.test

# Import extension python module we are testing with absolute import path, as if we are external user (other extension)
from omni.isaac.lidar import _lidar
from pxr import Usd, UsdGeom, UsdLux, Sdf, Gf, PhysicsSchema, PhysicsSchemaTools
import omni.isaac.LidarSchema as LidarSchema
import asyncio
import inspect

# import pxr
# import pkgutil
# import os.path, pkgutil

# Having a test class dervived from omni.kit.test.AsyncTestCase declared on the root of module will make it auto-discoverable by omni.kit.test
class TestLidar(omni.kit.test.AsyncTestCaseFailOnLogError):
    # Before running each test
    async def setUp(self):
        self._lidar = _lidar.acquire_lidar_interface()

        await omni.kit.asyncapi.new_stage()

    # After running each test
    async def tearDown(self):
        pass

    def add_lidar(self, lidarPath):
        stage = omni.usd.get_context().get_stage()

        lidar = LidarSchema.Lidar.Define(stage, Sdf.Path(lidarPath))
        lidar.CreateHorizontalFovAttr().Set(360.0)
        lidar.CreateVerticalFovAttr().Set(30.0)
        lidar.CreateRotationRateAttr().Set(20.0)
        lidar.CreateHorizontalResolutionAttr().Set(0.4)
        lidar.CreateVerticalResolutionAttr().Set(4.0)
        lidar.CreateMinRangeAttr().Set(0.4)
        lidar.CreateMaxRangeAttr().Set(100.0)
        lidar.CreateHighLodAttr().Set(True)
        lidar.CreateDrawLidarPointsAttr().Set(True)

        return lidar

    def add_cube(self, path, size, offset):
        stage = omni.usd.get_context().get_stage()

        cubeGeom = UsdGeom.Cube.Define(stage, path)
        cubePrim = stage.GetPrimAtPath(path)

        cubeGeom.CreateSizeAttr(size)
        cubeGeom.AddTranslateOp().Set(offset)

        physicsAPI = PhysicsSchema.PhysicsAPI.Apply(cubePrim)

        physicsAPI.CreateBodyTypeAttr("rigid")

        velocityAPI = PhysicsSchema.VelocityAPI.Apply(cubePrim)
        velocityAPI.CreateVelocityAttr().Set((0.0, 0.0, 0.0))
        velocityAPI.CreateAngularVelocityAttr().Set((0.0, 0.0, 0.0))

        densityAPI = PhysicsSchema.MassAPI.Apply(cubePrim)

        collisionAPI = PhysicsSchema.CollisionAPI.Apply(cubePrim)
        collisionAPI.CreatePhysicsMaterialRel()
        collisionAPI.CreateCollisionGroupRel()
        if cubePrim.IsA(UsdGeom.Mesh):
            collisionAPI.CreateApproximationShapeAttr().Set("convexHull")

        return cubeGeom

    # Tests a static lidar with a cube in front of it
    async def test_static_lidar(self):
        await omni.kit.asyncapi.new_stage()
        stage = omni.usd.get_context().get_stage()
        # set up axis to z
        UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
        UsdGeom.SetStageMetersPerUnit(stage, 0.01)

        # light
        sphereLight = UsdLux.SphereLight.Define(stage, Sdf.Path("/World/SphereLight"))
        sphereLight.CreateRadiusAttr(150)
        sphereLight.CreateIntensityAttr(30000)
        sphereLight.AddTranslateOp().Set(Gf.Vec3f(650.0, 0.0, 1150.0))

        # Physics scene
        scene = PhysicsSchema.PhysicsScene.Define(stage, Sdf.Path("/World/physicsScene"))
        scene.CreateGravityAttr().Set(Gf.Vec3f(0.0, 0.0, -1000.0))

        # Plane
        PhysicsSchemaTools.addGroundPlane(stage, "/World/groundPlane", "Z", 1500.0, Gf.Vec3f(0.0), Gf.Vec3f(0.5))

        # Add a cube
        cubePath = "/World/Cube"
        cubeGeom = self.add_cube(cubePath, 100.0, Gf.Vec3f(-200.0, 0.0, 50.0))

        # Add lidar
        lidarPath = "/World/Lidar"
        lidar = self.add_lidar(lidarPath)

        lidar.GetRotationRateAttr().Set(0.0)
        lidar.GetHighLodAttr().Set(False)
        lidar.AddTranslateOp().Set(Gf.Vec3f(0.0, 0.0, 25.0))

        # Run for a second
        editor = omni.kit.editor.get_editor_interface()
        editor.play()
        await asyncio.sleep(1)
        editor.pause()

        # Get depth, and check that we hit the cube in front, and hit nothing in back
        depth = self._lidar.get_depth_data(lidarPath)

        self.assertLess(depth[0, 0], 2000)
        self.assertEqual(depth[450, 0], 65535)

        editor.stop()

    # Tests a lidar on a falling cube, with a cube in front of it after it lands
    async def test_dynamic_lidar(self):
        await omni.kit.asyncapi.new_stage()
        stage = omni.usd.get_context().get_stage()

        # set up axis to z
        UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
        UsdGeom.SetStageMetersPerUnit(stage, 0.01)

        # light
        sphereLight = UsdLux.SphereLight.Define(stage, Sdf.Path("/World/SphereLight"))
        sphereLight.CreateRadiusAttr(150)
        sphereLight.CreateIntensityAttr(30000)
        sphereLight.AddTranslateOp().Set(Gf.Vec3f(650.0, 0.0, 1150.0))

        # Physics scene
        scene = PhysicsSchema.PhysicsScene.Define(stage, Sdf.Path("/World/physicsScene"))
        scene.CreateGravityAttr().Set(Gf.Vec3f(0.0, 0.0, -1000.0))

        # Plane
        PhysicsSchemaTools.addGroundPlane(stage, "/World/groundPlane", "Z", 1500.0, Gf.Vec3f(0.0), Gf.Vec3f(0.5))

        # Add a cube
        cubePath = "/World/Cube"
        cubeGeom = self.add_cube(cubePath, 100.0, Gf.Vec3f(-200.0, 0.0, 50.0))

        # Add falling cube
        cubePath2 = "/World/Cube2"
        cubeGeom2 = self.add_cube(cubePath2, 50.0, Gf.Vec3f(0.0, 0.0, 250.0))

        # Add lidar
        lidarPath = "/World/Cube2/Lidar"
        lidar = self.add_lidar(lidarPath)

        lidar.GetRotationRateAttr().Set(0.0)
        lidar.GetHighLodAttr().Set(False)
        lidar.AddTranslateOp().Set(Gf.Vec3f(0.0, 0.0, 50.0))

        # Run for two seconds
        editor = omni.kit.editor.get_editor_interface()
        editor.play()
        await asyncio.sleep(2)
        editor.pause()

        # Get depth, and check that we hit the cube in front, and hit nothing in back
        depth = self._lidar.get_depth_data(lidarPath)
        self.assertLess(depth[0, 0], 2000)
        self.assertEqual(depth[450, 0], 65535)
        editor.stop()
