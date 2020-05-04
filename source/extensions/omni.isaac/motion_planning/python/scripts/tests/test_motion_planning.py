# NOTE:
#   omni.kit.test - std python's unittest module with additional wrapping to add suport for async/await tests
#   For most things refer to unittest docs: https://docs.python.org/3/library/unittest.html
import omni.kit.test
import omni.kit.asyncapi
import carb.tokens
import os
import asyncio

# Import extension python module we are testing with absolute import path, as if we are external user (other extension)
from omni.isaac.motion_planning import _motion_planning
from omni.isaac.utils.scripts.test_utils import load_test_file

# Having a test class dervived from omni.kit.test.AsyncTestCase declared on the root of module will make it auto-discoverable by omni.kit.test
class TestMotionPlanning(omni.kit.test.AsyncTestCaseFailOnLogError):
    # Before running each test
    async def setUp(self):
        self._mp = _motion_planning.acquire_motion_planning_interface()
        self._rmp_data = os.path.abspath(
            carb.tokens.get_tokens_interface().resolve(
                "${app}/../exts/omni.isaac.motion_planning/resources/lula/lula_franka"
            )
        )
        pass

    # After running each test
    async def tearDown(self):
        pass

    # Actual test, notice it is "async" function, so "await" can be used if needed
    async def test_motion_planning(self):
        (result, error) = await load_test_file("assets/robots/franka/franka.usd")
        # Make sure the stage loaded
        self.assertTrue(result)

        stage = omni.usd.get_context().get_stage()
        prim = stage.GetPrimAtPath("/panda")
        # make sure the prim exists
        self.assertNotEqual(str(prim.GetPath()), "")
        # Start Simulation and wait
        editor = omni.kit.editor.get_editor_interface()
        editor.play()
        await asyncio.sleep(0.125)
        # Create RMP for franka
        rmp_handle = self._mp.registerRmp(
            self._rmp_data + "/urdf/lula_franka_gen.urdf",
            self._rmp_data + "/config/robot_descriptor.yaml",
            self._rmp_data + "/config/franka_rmpflow_common.yaml",
            prim.GetPath().pathString,
            "right_gripper",
            True,
        )
        self.assertNotEqual(rmp_handle, 0)
        pass
