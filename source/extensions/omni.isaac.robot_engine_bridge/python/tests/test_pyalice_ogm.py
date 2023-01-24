# Copyright (c) 2018-2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

# NOTE:
#   omni.kit.test - std python's unittest module with additional wrapping to add suport for async/await tests
#   For most things refer to unittest docs: https://docs.python.org/3/library/unittest.html
import omni.kit.test

import omni.kit.usd
import carb.tokens
import gc
import asyncio

# Import extension python module we are testing with absolute import path, as if we are external user (other extension)
from omni.isaac.dynamic_control import _dynamic_control

from omni.isaac.core.utils.nucleus import get_assets_root_path
from .common import PyaliceApp, create_application, add_cube, create_physics_scene
from omni.isaac.core.utils.physics import simulate_async
from pxr import Gf

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

        self._asset_path = self._reb_extension_path

        self._assets_root_path = get_assets_root_path()
        if self._assets_root_path is None:
            carb.log_error("Could not find Isaac Sim assets folder")
            return

        self.assertTrue(create_application()[1])
        pass

    # After running each test
    async def tearDown(self):
        self.assertTrue(omni.kit.commands.execute("RobotEngineBridgeDestroyApplication")[1])
        while omni.usd.get_context().get_stage_loading_status()[2] > 0:
            print("tearDown, assets still loading, waiting to finish...")
            await asyncio.sleep(1.0)
        gc.collect()
        pass

    def create_scene(self):
        create_physics_scene(self._stage)
        add_cube(self._stage, "/cube_1", 100, (100, 0, 0))
        add_cube(self._stage, "/cube_2", 100, (100, 200, 0))
        add_cube(self._stage, "/cube_3", 100, (-150, -150, 0))

    async def test_component(self):
        result, prim = omni.kit.commands.execute(
            "RobotEngineBridgeCreateOccupancyGridMap",
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
        await simulate_async(0.1)

    async def test_occupancy_grid_map(self):

        result, prim = omni.kit.commands.execute(
            "RobotEngineBridgeCreateOccupancyGridMap",
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
        await simulate_async(0.1)
        msg = test_app.app.receive("simulation.interface", "output", "occupancy_map")
        buffer = msg.tensor
        # print("TENSOR", omap)
        self.assertEqual(buffer[0, 79], 1.0)
        self.assertEqual(buffer[5, 75], 1.0)
        self.assertEqual(buffer[10, 59], 1.0)
        self.assertEqual(buffer[50, 20], 1.0)
        self.assertEqual(buffer[75, 29], 1.0)
        self.assertEqual(buffer[40, 40], 0.0)
        self.assertEqual(buffer[75, 20], 1.0)
        self._timeline.stop()
        test_app.stop()
        test_app = None
