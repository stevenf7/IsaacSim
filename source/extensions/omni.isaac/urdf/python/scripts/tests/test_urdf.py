# NOTE:
#   omni.kit.test - std python's unittest module with additional wrapping to add suport for async/await tests
#   For most things refer to unittest docs: https://docs.python.org/3/library/unittest.html
import omni.kit.test
import omni.kit.asyncapi
import carb.tokens
import os
from pxr import Sdf
import asyncio

# Import extension python module we are testing with absolute import path, as if we are external user (other extension)
from omni.isaac.urdf import _urdf


# Having a test class dervived from omni.kit.test.AsyncTestCase declared on the root of module will make it auto-discoverable by omni.kit.test
class TestUrdf(omni.kit.test.AsyncTestCaseFailOnLogError):
    # Before running each test
    async def setUp(self):
        print("Starting URDF Importer")
        self._urdf_interface = _urdf.acquire_urdf_interface()
        pass

    # After running each test
    async def tearDown(self):
        print("Shutting down URDF importer")
        # _urdf.release_urdf_interface(self._urdf_interface)
        pass

    # basic urdf test: joints and links are imported correctly
    async def test_urdf_basic(self):
        urdf_path = os.path.abspath(
            carb.tokens.get_tokens_interface().resolve("${app}/../data/urdf/tests/test_basic.urdf")
        )
        print("Setting up stage, importing urdf data")
        stage = omni.usd.get_context().get_stage()
        self._urdf_interface.importUrdf(urdf_path)

        print("check object exist")
        prim = stage.GetPrimAtPath("/test_basic")
        self.assertNotEqual(prim.GetPath(), Sdf.Path.emptyPath)

        print("check links are imported")
        linkPrim = stage.GetPrimAtPath("/test_basic/base_link/box_0")
        self.assertNotEqual(linkPrim.GetPath(), Sdf.Path.emptyPath)

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
        self.assertAlmostEqual(fingerJoint.GetAttribute("upperLimit").Get(), 0.08)
        # Start Simulation and wait
        editor = omni.kit.editor.get_editor_interface()
        editor.play()
        await asyncio.sleep(1.0)
        # nothing crashes
        editor.stop()
        pass

    # advanced urdf test: test for all the categories of inputs that an urdf can hold
    async def test_urdf_advanced(self):
        urdf_path = os.path.abspath(
            carb.tokens.get_tokens_interface().resolve("${app}/../data/urdf/tests/test_advanced.urdf")
        )
        print("Setting up stage, importing urdf data")
        stage = omni.usd.get_context().get_stage()

        # enable merging fixed joints
        self._urdf_interface.merge_fixed_joints(True)
        self._urdf_interface.importUrdf(urdf_path)

        # check if object is there
        prim = stage.GetPrimAtPath("/test_advanced")
        self.assertNotEqual(prim.GetPath(), Sdf.Path.emptyPath)

        # linkPrim = stage.GetPrimAtPath("/test_advanced/link_1")
        # TODO: self.assertEqual(round(linkPrim.GetAttribute('mass').Get()),10)

        materialShader = stage.GetPrimAtPath("/test_advanced/link_1/cylinder/_0Shader")
        self.assertNotEqual(materialShader.GetPath(), Sdf.Path.emptyPath)

        elbowPrim = stage.GetPrimAtPath("/test_advanced/link_1/elbow_joint")
        self.assertNotEqual(elbowPrim.GetPath(), Sdf.Path.emptyPath)
        self.assertAlmostEqual(elbowPrim.GetAttribute("jointFriction").Get(), 0.1)
        self.assertAlmostEqual(elbowPrim.GetAttribute("drive:angular:damping").Get(), 1.0)

        # TODO: print(materialShader.GetAttribute('inputs:diffuseColor').Get())
        # TODO: self.assertEqual(elbowJoint.GetAttribute("localPos0").Get())
        # TODO: check sensor attachment (camera)

        # Start Simulation and wait
        editor = omni.kit.editor.get_editor_interface()
        editor.play()
        await asyncio.sleep(1.0)
        # nothing crashes
        editor.stop()
        pass

    # test for importing urdf where fixed joints are merged
    async def test_urdf_merge_joints(self):
        urdf_path = os.path.abspath(
            carb.tokens.get_tokens_interface().resolve("${app}/../data/urdf/tests/test_merge_joints.urdf")
        )
        print("Setting up stage, importing urdf data")
        stage = omni.usd.get_context().get_stage()

        # enable merging fixed joints
        self._urdf_interface.merge_fixed_joints(True)
        self._urdf_interface.importUrdf(urdf_path)

        # the merged link shouldn't be there
        prim = stage.GetPrimAtPath("/test_merge_joints/link_2")
        self.assertEqual(prim.GetPath(), Sdf.Path.emptyPath)
        pass
