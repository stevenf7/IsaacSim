# NOTE:
#   omni.kit.test - std python's unittest module with additional wrapping to add suport for async/await tests
#   For most things refer to unittest docs: https://docs.python.org/3/library/unittest.html
import omni.kit.test

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

        ext_manager = omni.kit.app.get_app().get_extension_manager()
        ext_id = ext_manager.get_enabled_extension_id("omni.isaac.urdf")
        self._extension_path = ext_manager.get_extension_path(ext_id)
        await omni.kit.app.get_app().next_update_async()
        pass

    # After running each test
    async def tearDown(self):
        # _urdf.release_urdf_interface(self._urdf_interface)
        await omni.kit.app.get_app().next_update_async()
        pass

    # Tests to make sure visual mesh names are incremented
    async def test_urdf_mesh_naming(self):
        await omni.usd.get_context().new_stage_async()
        urdf_path = os.path.abspath(self._extension_path + "/data/urdf/tests/test_names.urdf")

        stage = omni.usd.get_context().get_stage()

        import_config = _urdf.ImportConfig()
        import_config.merge_fixed_joints = True
        root_path, filename = os.path.split(os.path.abspath(urdf_path))
        imported_robot = self._urdf_interface.parse_urdf(root_path, filename, import_config)
        self._urdf_interface.import_robot(root_path, filename, imported_robot, import_config)
        prim = stage.GetPrimAtPath("/test_names/cube/visuals")
        prim_range = prim.GetChildren()
        # There should be a total of 6 visual meshes after import
        self.assertEqual(len(prim_range), 6)

    # basic urdf test: joints and links are imported correctly
    async def test_urdf_basic(self):
        await omni.usd.get_context().new_stage_async()
        urdf_path = os.path.abspath(self._extension_path + "/data/urdf/tests/test_basic.urdf")
        stage = omni.usd.get_context().get_stage()
        import_config = _urdf.ImportConfig()
        import_config.import_inertia_tensor = True
        root_path, filename = os.path.split(os.path.abspath(urdf_path))
        imported_robot = self._urdf_interface.parse_urdf(root_path, filename, import_config)
        self._urdf_interface.import_robot(root_path, filename, imported_robot, import_config)

        prim = stage.GetPrimAtPath("/test_basic")
        self.assertNotEqual(prim.GetPath(), Sdf.Path.emptyPath)

        # make sure the joints exist
        rootJoint = stage.GetPrimAtPath("/test_basic/rootJoint")
        self.assertNotEqual(rootJoint.GetPath(), Sdf.Path.emptyPath)

        wristJoint = stage.GetPrimAtPath("/test_basic/link_2/wrist_joint")
        self.assertNotEqual(wristJoint.GetPath(), Sdf.Path.emptyPath)
        self.assertEqual(wristJoint.GetTypeName(), "PhysicsRevoluteJoint")

        fingerJoint = stage.GetPrimAtPath("/test_basic/palm_link/finger_1_joint")
        self.assertNotEqual(fingerJoint.GetPath(), Sdf.Path.emptyPath)
        self.assertEqual(fingerJoint.GetTypeName(), "PhysicsPrismaticJoint")
        self.assertAlmostEqual(fingerJoint.GetAttribute("physics:upperLimit").Get(), 8)

        fingerLink = stage.GetPrimAtPath("/test_basic/finger_link_2")
        self.assertAlmostEqual(fingerLink.GetAttribute("physics:diagonalInertia").Get()[0], 20000.0)
        self.assertAlmostEqual(fingerLink.GetAttribute("physics:mass").Get(), 3)

        # Start Simulation and wait
        self._timeline.play()
        await omni.kit.app.get_app().next_update_async()
        await asyncio.sleep(1.0)
        # nothing crashes
        self._timeline.stop()
        pass

    # advanced urdf test: test for all the categories of inputs that an urdf can hold
    async def test_urdf_advanced(self):
        await omni.usd.get_context().new_stage_async()
        urdf_path = os.path.abspath(self._extension_path + "/data/urdf/tests/test_advanced.urdf")
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
        self.assertAlmostEqual(elbowPrim.GetAttribute("physxJoint:jointFriction").Get(), 0.1)
        self.assertAlmostEqual(elbowPrim.GetAttribute("drive:angular:physics:damping").Get(), 0.1)

        # check position of a link
        joint_pos = elbowPrim.GetAttribute("physics:localPos0").Get()
        self.assertTrue(Gf.IsClose(joint_pos, Gf.Vec3f(0, 0, 40), 1e-5))

        # Start Simulation and wait
        self._timeline.play()
        await omni.kit.app.get_app().next_update_async()
        await asyncio.sleep(1.0)
        # nothing crashes
        self._timeline.stop()
        pass

    # test for importing urdf where fixed joints are merged
    async def test_urdf_merge_joints(self):
        await omni.usd.get_context().new_stage_async()
        urdf_path = os.path.abspath(self._extension_path + "/data/urdf/tests/test_merge_joints.urdf")

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

    async def test_urdf_mtl(self):
        await omni.usd.get_context().new_stage_async()
        urdf_path = os.path.abspath(self._extension_path + "/data/urdf/tests/test_mtl.urdf")

        stage = omni.usd.get_context().get_stage()

        import_config = _urdf.ImportConfig()
        root_path, filename = os.path.split(os.path.abspath(urdf_path))
        imported_robot = self._urdf_interface.parse_urdf(root_path, filename, import_config)
        self._urdf_interface.import_robot(root_path, filename, imported_robot, import_config)

        mesh = stage.GetPrimAtPath("/test_mtl/cube/visuals/material_1")
        self.assertNotEqual(mesh.GetPath(), Sdf.Path.emptyPath)
        mat, rel = UsdShade.MaterialBindingAPI(mesh).ComputeBoundMaterial()
        shader = UsdShade.Shader(stage.GetPrimAtPath(mat.GetPath().pathString + "/Shader"))
        self.assertTrue(Gf.IsClose(shader.GetInput("diffuseColor").Get(), Gf.Vec3f(0.8, 0.0, 0), 1e-5))

    async def test_urdf_carter(self):
        await omni.usd.get_context().new_stage_async()
        urdf_path = os.path.abspath(self._extension_path + "/data/urdf/robots/carter/urdf/carter.urdf")
        stage = omni.usd.get_context().get_stage()
        import_config = _urdf.ImportConfig()
        import_config.merge_fixed_joints = False
        root_path, filename = os.path.split(os.path.abspath(urdf_path))
        imported_robot = self._urdf_interface.parse_urdf(root_path, filename, import_config)
        self._urdf_interface.import_robot(root_path, filename, imported_robot, import_config)
        # TODO add checks here

    async def test_urdf_franka(self):
        await omni.usd.get_context().new_stage_async()
        urdf_path = os.path.abspath(
            self._extension_path + "/data/urdf/robots/franka_description/robots/panda_arm_hand.urdf"
        )
        stage = omni.usd.get_context().get_stage()
        import_config = _urdf.ImportConfig()
        root_path, filename = os.path.split(os.path.abspath(urdf_path))
        imported_robot = self._urdf_interface.parse_urdf(root_path, filename, import_config)
        self._urdf_interface.import_robot(root_path, filename, imported_robot, import_config)
        # TODO add checks here'

    async def test_urdf_ur10(self):
        await omni.usd.get_context().new_stage_async()
        urdf_path = os.path.abspath(self._extension_path + "/data/urdf/robots/ur10/urdf/ur10_base.urdf")
        stage = omni.usd.get_context().get_stage()
        import_config = _urdf.ImportConfig()
        root_path, filename = os.path.split(os.path.abspath(urdf_path))
        imported_robot = self._urdf_interface.parse_urdf(root_path, filename, import_config)
        self._urdf_interface.import_robot(root_path, filename, imported_robot, import_config)
        # TODO add checks here'

    async def test_urdf_kaya(self):
        await omni.usd.get_context().new_stage_async()
        urdf_path = os.path.abspath(self._extension_path + "/data/urdf/robots/kaya/urdf/kaya.urdf")
        stage = omni.usd.get_context().get_stage()
        import_config = _urdf.ImportConfig()
        import_config.merge_fixed_joints = False
        root_path, filename = os.path.split(os.path.abspath(urdf_path))
        imported_robot = self._urdf_interface.parse_urdf(root_path, filename, import_config)
        self._urdf_interface.import_robot(root_path, filename, imported_robot, import_config)
        # TODO add checks here

    async def test_missing(self):
        await omni.usd.get_context().new_stage_async()
        urdf_path = os.path.abspath(self._extension_path + "/data/urdf/tests/test_missing.urdf")

        stage = omni.usd.get_context().get_stage()

        import_config = _urdf.ImportConfig()
        root_path, filename = os.path.split(os.path.abspath(urdf_path))
        imported_robot = self._urdf_interface.parse_urdf(root_path, filename, import_config)
        self._urdf_interface.import_robot(root_path, filename, imported_robot, import_config)
