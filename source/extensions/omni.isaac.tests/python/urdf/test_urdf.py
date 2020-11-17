# NOTE:
#   omni.kit.test - std python's unittest module with additional wrapping to add suport for async/await tests
#   For most things refer to unittest docs: https://docs.python.org/3/library/unittest.html
import omni.kit.test
import omni.kit.asyncapi
import carb.tokens
import os
from pxr import Sdf, Gf, UsdShade
import asyncio

# Import extension python module we are testing with absolute import path, as if we are external user (other extension)
from omni.isaac.urdf import _urdf


# Having a test class dervived from omni.kit.test.AsyncTestCase declared on the root of module will make it auto-discoverable by omni.kit.test
class TestUrdf(omni.kit.test.AsyncTestCaseFailOnLogError):
    # Before running each test
    async def setUp(self):
        self._urdf_interface = _urdf.acquire_urdf_interface()
        self._timeline = omni.timeline.get_timeline_interface()
        pass

    # After running each test
    async def tearDown(self):
        # _urdf.release_urdf_interface(self._urdf_interface)
        pass

    # basic urdf test: joints and links are imported correctly
    async def test_urdf_basic(self):
        await omni.kit.asyncapi.new_stage()
        urdf_path = os.path.abspath(
            carb.tokens.get_tokens_interface().resolve("${app}/../data/urdf/tests/test_basic.urdf")
        )
        print("Setting up stage, importing urdf data")
        stage = omni.usd.get_context().get_stage()
        import_config = _urdf.ImportConfig()
        import_config.import_inertia_tensor = True
        root_path, filename = os.path.split(os.path.abspath(urdf_path))
        imported_robot = self._urdf_interface.parse_urdf(root_path, filename, import_config)
        self._urdf_interface.import_robot(root_path, filename, imported_robot, import_config)

        print("check object exist")
        prim = stage.GetPrimAtPath("/test_basic")
        self.assertNotEqual(prim.GetPath(), Sdf.Path.emptyPath)

        print("check different types of joints are imported")
        # make sure the joints exist
        rootJoint = stage.GetPrimAtPath("/test_basic/rootJoint")
        self.assertNotEqual(rootJoint.GetPath(), Sdf.Path.emptyPath)

        wristJoint = stage.GetPrimAtPath("/test_basic/link_2/wrist_joint")
        self.assertNotEqual(wristJoint.GetPath(), Sdf.Path.emptyPath)
        self.assertEqual(wristJoint.GetTypeName(), "RevolutePhysicsJoint")

        fingerJoint = stage.GetPrimAtPath("/test_basic/palm_link/finger_1_joint")
        self.assertNotEqual(fingerJoint.GetPath(), Sdf.Path.emptyPath)
        self.assertEqual(fingerJoint.GetTypeName(), "PrismaticPhysicsJoint")
        self.assertAlmostEqual(fingerJoint.GetAttribute("upperLimit").Get(), 8)

        fingerLink = stage.GetPrimAtPath("/test_basic/finger_link_2")
        self.assertAlmostEqual(fingerLink.GetAttribute("diagonalInertia").Get()[0], 20000.0)
        self.assertAlmostEqual(fingerLink.GetAttribute("mass").Get(), 3)

        # Start Simulation and wait
        self._timeline.play()
        await omni.kit.asyncapi.next_update()
        await asyncio.sleep(1.0)
        # nothing crashes
        self._timeline.stop()
        pass

    # advanced urdf test: test for all the categories of inputs that an urdf can hold
    async def test_urdf_advanced(self):
        await omni.kit.asyncapi.new_stage()
        urdf_path = os.path.abspath(
            carb.tokens.get_tokens_interface().resolve("${app}/../data/urdf/tests/test_advanced.urdf")
        )
        print("Setting up stage, importing urdf data")
        stage = omni.usd.get_context().get_stage()

        # enable merging fixed joints
        import_config = _urdf.ImportConfig()
        import_config.merge_fixed_joints = True
        root_path, filename = os.path.split(os.path.abspath(urdf_path))
        imported_robot = self._urdf_interface.parse_urdf(root_path, filename, import_config)
        self._urdf_interface.import_robot(root_path, filename, imported_robot, import_config)

        # check if object is there
        prim = stage.GetPrimAtPath("/test_advanced")
        self.assertNotEqual(prim.GetPath(), Sdf.Path.emptyPath)

        # check color are imported
        mesh = stage.GetPrimAtPath("/test_advanced/link_1/visuals")
        self.assertNotEqual(mesh.GetPath(), Sdf.Path.emptyPath)
        mat, rel = UsdShade.MaterialBindingAPI(mesh).ComputeBoundMaterial()
        shader = UsdShade.Shader(stage.GetPrimAtPath(mat.GetPath().pathString + "/Shader"))
        self.assertTrue(Gf.IsClose(shader.GetInput("diffuseColor").Get(), Gf.Vec3f(0, 0.8, 0), 1e-5))

        # check joint properties
        elbowPrim = stage.GetPrimAtPath("/test_advanced/link_1/elbow_joint")
        self.assertNotEqual(elbowPrim.GetPath(), Sdf.Path.emptyPath)
        self.assertAlmostEqual(elbowPrim.GetAttribute("jointFriction").Get(), 0.1)
        self.assertAlmostEqual(elbowPrim.GetAttribute("drive:angular:damping").Get(), 0.1)

        # check position of a link
        joint_pos = elbowPrim.GetAttribute("localPos0").Get()
        self.assertTrue(Gf.IsClose(joint_pos, Gf.Vec3f(0, 0, 40), 1e-5))

        # Start Simulation and wait
        self._timeline.play()
        await omni.kit.asyncapi.next_update()
        await asyncio.sleep(1.0)
        # nothing crashes
        self._timeline.stop()
        pass

    # test for importing urdf where fixed joints are merged
    async def test_urdf_merge_joints(self):
        await omni.kit.asyncapi.new_stage()
        urdf_path = os.path.abspath(
            carb.tokens.get_tokens_interface().resolve("${app}/../data/urdf/tests/test_merge_joints.urdf")
        )
        print("Setting up stage, importing urdf data")
        stage = omni.usd.get_context().get_stage()

        # enable merging fixed joints
        import_config = _urdf.ImportConfig()
        import_config.merge_fixed_joints = True
        root_path, filename = os.path.split(os.path.abspath(urdf_path))
        imported_robot = self._urdf_interface.parse_urdf(root_path, filename, import_config)
        self._urdf_interface.import_robot(root_path, filename, imported_robot, import_config)

        # the merged link shouldn't be there
        prim = stage.GetPrimAtPath("/test_merge_joints/link_2")
        self.assertEqual(prim.GetPath(), Sdf.Path.emptyPath)

        pass
