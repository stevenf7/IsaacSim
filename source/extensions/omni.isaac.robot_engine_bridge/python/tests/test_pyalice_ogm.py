# NOTE:
#   omni.kit.test - std python's unittest module with additional wrapping to add suport for async/await tests
#   For most things refer to unittest docs: https://docs.python.org/3/library/unittest.html
import omni.kit.test

import omni.kit.usd
import carb.tokens
import gc

# Import extension python module we are testing with absolute import path, as if we are external user (other extension)
from omni.isaac.dynamic_control import _dynamic_control

from omni.isaac.utils.scripts.nucleus_utils import find_nucleus_server
from .common import PyaliceApp, create_application, simulate
from pxr import Gf, UsdGeom, UsdPhysics, Sdf
from omni.physx.scripts import utils

# Having a test class dervived from omni.kit.test.AsyncTestCase declared on the root of module will make it auto-discoverable by omni.kit.test
class TestREBPyaliceOccupancyGridMap(omni.kit.test.AsyncTestCase):
    # Before running each test
    async def setUp(self):
        await omni.usd.get_context().new_stage_async()
        context = omni.usd.get_context()
        self._stage = context.get_stage()
        self._timeline = omni.timeline.get_timeline_interface()
        self._usd_context = omni.usd.get_context()
        self._dc = _dynamic_control.acquire_dynamic_control_interface()

        ext_manager = omni.kit.app.get_app().get_extension_manager()
        ext_id = ext_manager.get_enabled_extension_id("omni.isaac.robot_engine_bridge")
        self._reb_extension_path = ext_manager.get_extension_path(ext_id)
        ext_id = ext_manager.get_enabled_extension_id("omni.isaac.dynamic_control")
        self._dc_extension_path = ext_manager.get_extension_path(ext_id)

        self._asset_path = self._reb_extension_path

        result, nucleus_server = find_nucleus_server()
        if result is False:
            carb.log_error("Could not find nucleus server with /Isaac folder")
            return
        self._nucleus_path = nucleus_server + "/Isaac"

        self.assertTrue(create_application()[1])
        pass

    # After running each test
    async def tearDown(self):
        self.assertTrue(omni.kit.commands.execute("DestroyRobotEngineBridgeApplicationCommand")[1])
        gc.collect()
        pass

    def add_cube(self, path, size, offset):

        cubeGeom = UsdGeom.Cube.Define(self._stage, path)
        cubePrim = self._stage.GetPrimAtPath(path)

        cubeGeom.CreateSizeAttr(size)
        cubeGeom.AddTranslateOp().Set(offset)
        utils.setCollider(cubePrim)

        return cubeGeom

    def create_scene(self):
        UsdPhysics.Scene.Define(self._stage, Sdf.Path("/World/physicsScene"))
        self.add_cube("/cube_1", 100, (100, 0, 0))
        self.add_cube("/cube_2", 100, (100, 200, 0))
        self.add_cube("/cube_3", 100, (-150, -150, 0))

    async def test_component(self):
        result, prim = omni.kit.commands.execute(
            "CreateRobotEngineBridgeOccupancyGridMapCommand",
            path="/REB_OccupancyGridMap",
            parent=None,
            output_component="output",
            output_channel="occupancy_map",
            parent_prim_rel=None,
            offset=Gf.Vec3f(0, 0, 0),
            cell_size=0.1,
            degrees_per_ray=5,
            surface_offset=0.02,
            occupancy_threshold=1.0,
            max_rays=1000000,
            map_size=Gf.Vec2i(256, 256),
            debug_draw=False,
            occupied_value=1.0,
            unoccupied_value=0.0,
            unknown_value=0.5,
        )
        self.create_scene()
        self._timeline.play()
        await simulate(0.1)

    async def test_occupancy_grid_map(self):

        result, prim = omni.kit.commands.execute(
            "CreateRobotEngineBridgeOccupancyGridMapCommand",
            path="/REB_OccupancyGridMap",
            parent=None,
            output_component="output",
            output_channel="occupancy_map",
            parent_prim_rel=None,
            offset=Gf.Vec3f(0, 0, 0),
            cell_size=0.05,
            degrees_per_ray=5,
            surface_offset=0.02,
            occupancy_threshold=1.0,
            max_rays=1000000,
            map_size=Gf.Vec2i(80, 80),
            debug_draw=False,
            occupied_value=1.0,
            unoccupied_value=0.0,
            unknown_value=0.5,
        )
        self.create_scene()
        test_app = PyaliceApp()

        test_app.app.load(
            filename=self._reb_extension_path + "/data/config/navsim_tcp.subgraph.json", prefix="simulation"
        )

        test_app.start()

        self._timeline.play()
        await simulate(0.1)
        msg = test_app.app.receive("simulation.interface", "output", "occupancy_map")
        buffer = msg.tensor
        # print("TENSOR", omap)
        self.assertEqual(buffer[0, 79], 0.5)
        self.assertEqual(buffer[5, 75], 0.5)
        self.assertEqual(buffer[10, 59], 1.0)
        self.assertEqual(buffer[50, 20], 1.0)
        self.assertEqual(buffer[75, 29], 1.0)
        self.assertEqual(buffer[40, 40], 0.0)
        self.assertEqual(buffer[75, 20], 0.5)
        self._timeline.stop()
        test_app.stop()
        test_app = None
