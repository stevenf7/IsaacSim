import omni.kit.test
from omni.isaac.core.utils.stage import clear_stage, add_reference_to_stage, update_stage_async
from omni.isaac.core.utils.prims import create_prim
from omni.isaac.core.utils.nucleus import find_nucleus_server
import carb


class TestStage(omni.kit.test.AsyncTestCaseFailOnLogError):
    # Before running each test
    async def setUp(self):
        pass

    # After running each test
    async def tearDown(self):
        pass

    async def test_clear_stage(self):
        prim = create_prim("/Test")
        self.assertTrue(prim.IsValid())
        result, nucleus_server = find_nucleus_server()
        if result is False:
            carb.log_error("Could not find nucleus server with /Isaac folder")
        asset_path = nucleus_server + "/Isaac/Robots/Franka/franka_alt_fingers.usd"
        robot = add_reference_to_stage(usd_path=asset_path, prim_path="/World/Franka_1")
        await update_stage_async()

        self.assertTrue(robot.IsValid())
        clear_stage()
        await update_stage_async()
        self.assertFalse(prim.IsValid())
        self.assertFalse(robot.IsValid())
        pass
