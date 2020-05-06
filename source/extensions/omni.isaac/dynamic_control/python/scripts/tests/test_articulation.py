# NOTE:
#   omni.kit.test - std python's unittest module with additional wrapping to add suport for async/await tests
#   For most things refer to unittest docs: https://docs.python.org/3/library/unittest.html
import omni.kit.test
import omni.kit.asyncapi
import carb.tokens
import os
import asyncio

# Import extension python module we are testing with absolute import path, as if we are external user (other extension)
from omni.isaac.dynamic_control import _dynamic_control
from omni.isaac.utils.scripts.test_utils import load_test_file

# Having a test class dervived from omni.kit.test.AsyncTestCase declared on the root of module will make it auto-discoverable by omni.kit.test
class TestArticulation(omni.kit.test.AsyncTestCaseFailOnLogError):
    # Before running each test
    async def setUp(self):
        self._dc = _dynamic_control.acquire_dynamic_control_interface()

        pass

    # After running each test
    async def tearDown(self):
        pass

    # Actual test, notice it is "async" function, so "await" can be used if needed
    async def test_articulation_load(self):
        (result, error) = await load_test_file("assets/robots/franka/franka.usd")
        # Make sure the stage loaded
        self.assertTrue(result)
        # Start Simulation and wait
        editor = omni.kit.editor.get_editor_interface()
        editor.play()
        await asyncio.sleep(0.125)
        obj_type = self._dc.peek_object_type("/panda")
        self.assertEqual(obj_type, _dynamic_control.ObjectType.OBJECT_ARTICULATION)

        art = self._dc.get_articulation("/panda")
        self.assertNotEqual(art, _dynamic_control.INVALID_HANDLE)

        pass

        # Actual test, notice it is "async" function, so "await" can be used if needed

    async def test_articulation_teleport(self):
        (result, error) = await load_test_file("assets/robots/franka/franka.usd")
        # Make sure the stage loaded
        self.assertTrue(result)
        # Start Simulation and wait
        editor = omni.kit.editor.get_editor_interface()
        editor.play()
        await asyncio.sleep(0.125)
        obj_type = self._dc.peek_object_type("/panda")
        self.assertEqual(obj_type, _dynamic_control.ObjectType.OBJECT_ARTICULATION)

        art = self._dc.get_articulation("/panda")
        self.assertNotEqual(art, _dynamic_control.INVALID_HANDLE)

        # root_body = self._dc.get_articulation_root_body(art)
        # new_pose = _dynamic_control.Transform((1.0, 2.0, 3.0), (0.1, 0.2, 0.3, 0.4))
        # self._dc.set_rigid_body_pose(root_body, new_pose)
        # print("POSE:", self._dc.get_rigid_body_pose(root_body).p)

        pass
