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
from typing_extensions import Protocol
import omni.kit.test

import omni.kit.usd
import carb.tokens
import gc

# Import extension python module we are testing with absolute import path, as if we are external user (other extension)
from omni.isaac.dynamic_control import _dynamic_control

from omni.isaac.core.utils.nucleus import get_assets_root_path
from .common import PyaliceApp, create_application
from omni.isaac.core.utils.physics import simulate_async
from pxr import Gf

# Having a test class dervived from omni.kit.test.AsyncTestCase declared on the root of module will make it auto-discoverable by omni.kit.test
class TestREBPyalice(omni.kit.test.AsyncTestCase):
    # Before running each test
    async def setUp(self):
        await omni.usd.get_context().new_stage_async()
        self._timeline = omni.timeline.get_timeline_interface()
        self._usd_context = omni.usd.get_context()

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
        gc.collect()
        pass

    async def test_pyalice_init(self):
        self._timeline.play()

        test_app = PyaliceApp()
        test_app.app.load_module("sight")

        test_app.start()

        await simulate_async(2)
        self._timeline.stop()

        test_app.stop()
        pass

    # TODO: modify test so it returns true if we were able to connect
    # async def test_pyalice_connect(self):
    #     # Base create destroy test

    #     test_app = PyaliceApp()
    #     test_app.app.load_module("sight")

    #     test_app.start()

    #     self._timeline.play()
    #     await simulate_async(2.0)
    #     self._timeline.stop()

    #     test_app.stop()
    #     pass

    # TODO add checks for this test
    async def test_polyline_visualizer_2d(self):
        result, prim = omni.kit.commands.execute(
            "RobotEngineBridgeCreatePolylineVisualizer",
            path="/REB_PolylineVisualizer",
            parent=None,
            input_component="input",
            input_channel="sight_plan",
            parent_prim_rel=None,
            width=0.1,
            color=Gf.Vec4f(1.0, 1.0, 1.0, 1.0),
            offset=Gf.Vec3f(0, 0, 0),
        )

        test_app = PyaliceApp()

        test_app.app.load(
            filename=self._reb_extension_path + "/data/config/navsim_tcp.subgraph.json", prefix="simulation"
        )
        sim_input = test_app.app.nodes["simulation.interface"]["input"]

        test_app.app.load_module("sight")
        test_app.app.load_module("message_generators")

        plan2 = test_app.app.add("generation").add(test_app.app.registry.isaac.message_generators.Plan2Generator)
        plan2.config.waypoints = [
            [0.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [1.57, 2.0, 0.0],
            [1.57, 2.0, 1.0],
            [0.0, 2.0, 2.0],
            [0.0, 3.0, 2.0],
            [0.0, 4.0, 2.0],
        ]
        plan2.config.new_message_threshold = [0.0, 0.0]
        plan2.config.tick_period = "10Hz"

        test_app.app.load_module("viewers")
        viewer = test_app.app.add("viewers").add(test_app.app.registry.isaac.viewers.Plan2Viewer)
        viewer.config.size = 0.5
        viewer.config.color = [255, 0, 0, 255]

        test_app.app.connect(plan2, "plan", viewer, "plan")
        test_app.app.connect(plan2, "plan", sim_input, "plan")

        kit_frontend = test_app.app.add("kit_frontend").add(test_app.app.registry.isaac.sight.SightTunnel)
        kit_frontend.config.edges = [
            {"source": "viewers/Plan2Viewer/plan", "target": "simulation.interface/input/sight_plan"}
        ]

        test_app.start()

        self._timeline.play()
        await simulate_async(1.0)
        viewer.config.size = 0.5
        viewer.config.color = [255, 0, 0, 255]
        await simulate_async(1.0)
        viewer.config.size = 0.0
        viewer.config.color = [0, 255, 0, 255]
        await simulate_async(1.0)
        viewer.config.size = 1.0
        viewer.config.color = [0, 0, 255, 255]
        await simulate_async(1.0)
        viewer.config.size = 1.0
        viewer.config.color = [0, 0, 255, 0]
        await simulate_async(1.0)
        self._timeline.stop()
        test_app.stop()
        test_app = None

    async def test_polyline_visualizer_3d(self):
        result, prim = omni.kit.commands.execute(
            "RobotEngineBridgeCreatePolylineVisualizer",
            path="/REB_PolylineVisualizer",
            parent=None,
            input_component="input",
            input_channel="sight_plan",
            parent_prim_rel=None,
            width=0.1,
            color=Gf.Vec4f(1.0, 1.0, 1.0, 1.0),
            offset=Gf.Vec3f(0, 0, 0),
        )

        test_app = PyaliceApp()

        test_app.app.load(
            filename=self._reb_extension_path + "/data/config/navsim_tcp.subgraph.json", prefix="simulation"
        )
        sim_input = test_app.app.nodes["simulation.interface"]["input"]

        test_app.app.load_module("sight")
        test_app.app.load_module("message_generators")

        polyline2 = test_app.app.add("generation").add(
            test_app.app.registry.isaac.message_generators.Polyline2Generator
        )
        polyline2.config.prototype = [[0.0, 0.0], [0.0, 1.0], [1.0, 1.0], [1.0, 0.0]]
        polyline2.config.new_message_threshold = [0.0, 0.0]
        polyline2.config.tick_period = "10Hz"

        test_app.app.load_module("viewers")
        viewer = test_app.app.add("viewers").add(test_app.app.registry.isaac.viewers.Polyline2Viewer)
        viewer.config.size = 0.5
        viewer.config.color = [255, 0, 0, 255]

        test_app.app.connect(polyline2, "polyline", viewer, "polyline")
        test_app.app.connect(polyline2, "polyline", sim_input, "polyline")

        kit_frontend = test_app.app.add("kit_frontend").add(test_app.app.registry.isaac.sight.SightTunnel)
        kit_frontend.config.edges = [
            {"source": "viewers/Polyline2Viewer/polyline", "target": "simulation.interface/input/sight_plan"}
        ]

        test_app.start()

        self._timeline.play()
        await simulate_async(1.0)
        viewer.config.size = 0.5
        viewer.config.polyline_color = [255, 0, 0, 255]
        await simulate_async(1.0)
        viewer.config.size = 0.0
        viewer.config.polyline_color = [0, 255, 0, 255]
        await simulate_async(1.0)
        viewer.config.size = 1.0
        viewer.config.polyline_color = [0, 0, 255, 255]
        await simulate_async(1.0)
        viewer.config.size = 1.0
        viewer.config.polyline_color = [0, 0, 255, 0]
        await simulate_async(1.0)
        self._timeline.stop()
        test_app.stop()
        test_app = None
