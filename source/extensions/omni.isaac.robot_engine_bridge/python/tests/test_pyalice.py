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


# Having a test class dervived from omni.kit.test.AsyncTestCase declared on the root of module will make it auto-discoverable by omni.kit.test
class TestREBPyalice(omni.kit.test.AsyncTestCase):
    # Before running each test
    async def setUp(self):
        await omni.usd.get_context().new_stage_async()
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

    async def test_pyalice_init(self):
        self._timeline.play()

        test_app = PyaliceApp()
        test_app.app.load_module("sight")

        test_app.start()

        await simulate(2)
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
    #     await simulate(2.0)
    #     self._timeline.stop()

    #     test_app.stop()
    #     pass

    # async def test_polyline_visualizer(self):
    #     result, prim = omni.kit.commands.execute(
    #         "CreateRobotEngineBridgePolylineVisualizerCommand",
    #         path="/REB_PolylineVisualizer",
    #         parent=get_selected_path(),
    #         input_component="input",
    #         input_channel="plan",
    #         parent_prim_rel=None,
    #         width=0.1,
    #         color=Gf.Vec4f(1.0, 1.0, 1.0, 1.0),
    #         offset=Gf.Vec3f(0, 0, 0),
    #     )

    #     test_app = PyaliceApp()

    #     test_app.app.load(
    #         filename=self._reb_extension_path + "/data/config/navsim_tcp.subgraph.json", prefix="simulation"
    #     )
    #     sim_input = test_app.app.nodes["simulation.interface"]["input"]

    #     test_app.app.load_module("sight")
    #     test_app.app.load_module("message_generators")

    #     plan2 = test_app.app.add("generation").add(test_app.app.registry.isaac.message_generators.Plan2Generator)
    #     plan2.config.waypoints = [
    #         [0.0, 0.0, 0.0],
    #         [0.0, 1.0, 0.0],
    #         [1.57, 2.0, 0.0],
    #         [1.57, 2.0, 1.0],
    #         [0.0, 2.0, 2.0],
    #         [0.0, 3.0, 2.0],
    #         [0.0, 4.0, 2.0],
    #     ]
    #     plan2.config.new_message_threshold = [0.0, 0.0]
    #     plan2.config.tick_period = "10Hz"

    #     test_app.app.load_module("viewers")
    #     viewer = test_app.app.add("viewers").add(test_app.app.registry.isaac.viewers.Plan2Viewer)
    #     viewer.config.size = 0.5
    #     viewer.config.color = [118, 185, 0, 255]

    #     test_app.app.connect(plan2, "plan", viewer, "plan")
    #     test_app.app.connect(plan2, "plan", sim_input, "plan")

    #     kit_frontend = test_app.app.add("kit_frontend").add(test_app.app.registry.isaac.sight.SightTunnel)
    #     kit_frontend.config.edges = [
    #         {"source": "viewers/Plan2Viewer/plan", "target": "simulation.interface/input/sight_plan"}
    #     ]

    #     test_app.start()

    #     self._timeline.play()
    #     await simulate(1)
    #     self._timeline.stop()
    #     test_app.stop()
    #     test_app = None
