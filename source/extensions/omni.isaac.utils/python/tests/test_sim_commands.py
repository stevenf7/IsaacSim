# NOTE:
#   omni.kit.test - std python's unittest module with additional wrapping to add suport for async/await tests
#   For most things refer to unittest docs: https://docs.python.org/3/library/unittest.html
import omni.kit.test
import omni.kit.usd
import gc
import carb

# Import extension python module we are testing with absolute import path, as if we are external user (other extension)
import omni.kit.commands
from omni.isaac.utils.scripts.nucleus_utils import find_nucleus_server

from pxr import Gf


# Having a test class dervived from omni.kit.test.AsyncTestCase declared on the root of module will make it auto-discoverable by omni.kit.test
class TestIsaacSimCommands(omni.kit.test.AsyncTestCase):
    # Before running each test
    async def setUp(self):
        await omni.usd.get_context().new_stage_async()
        self._timeline = omni.timeline.get_timeline_interface()
        self._stage = omni.usd.get_context().get_stage()

        result, nucleus_server = find_nucleus_server()
        if result is False:
            carb.log_error("Could not find nucleus server with /Isaac folder")
            return
        self._nucleus_path = nucleus_server + "/Isaac"

        pass

    # After running each test
    async def tearDown(self):
        await omni.kit.app.get_app().next_update_async()
        self._stage = None
        self._timeline = None
        gc.collect()
        pass

    async def test_spawn_command(self):
        articulation_usd = self._nucleus_path + "/Robots/Franka/franka.usd"
        static_usd = self._nucleus_path + "/Props/KLT_Bin/small_KLT.usd"
        physics_usd = self._nucleus_path + "/Props/Blocks/basic_block.usd"

        omni.kit.commands.execute(
            "IsaacSimSpawnPrim", usd_path=articulation_usd, prim_path="/franka", translation=(100, 100, 0)
        )
        omni.kit.commands.execute(
            "IsaacSimSpawnPrim", usd_path=static_usd, prim_path="/klt", translation=(-100, 100, 0)
        )
        omni.kit.commands.execute(
            "IsaacSimSpawnPrim", usd_path=physics_usd, prim_path="/block", translation=(100, -100, 0)
        )

    async def test_teleport_command(self):
        articulation_usd = self._nucleus_path + "/Robots/Franka/franka.usd"
        omni.kit.commands.execute(
            "IsaacSimSpawnPrim", usd_path=articulation_usd, prim_path="/franka", translation=(0, 0, 0)
        )
        omni.kit.commands.execute("IsaacSimTeleportPrim", prim_path="/franka", translation=(-100, -100, 0))

    async def test_destroy_command(self):
        articulation_usd = self._nucleus_path + "/Robots/Franka/franka.usd"
        omni.kit.commands.execute("IsaacSimSpawnPrim", usd_path=articulation_usd, prim_path="/franka")
        await omni.kit.app.get_app().next_update_async()
        omni.kit.commands.execute("IsaacSimDestroyPrim", prim_path="/franka")
