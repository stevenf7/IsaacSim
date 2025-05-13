import omni.graph.core as og
import omni.kit.test
from pxr import Sdf, UsdGeom


class TestGraphIsolation(omni.kit.test.AsyncTestCase):
    async def setUp(self):
        self._timeline = omni.timeline.get_timeline_interface()
        await omni.usd.get_context().new_stage_async()

    async def tearDown(self):
        self._timeline.stop()

    async def test_graph_evaluation_is_isolated(self):
        stage = omni.usd.get_context().get_stage()

        # Create two cubes
        for i in [1, 2]:
            stage.DefinePrim(f"/Cube{i}", "Cube")

        keys = og.Controller.Keys

        def make_graph(graph_path, cube_path):
            return og.Controller.edit(
                {"graph_path": graph_path, "evaluator_name": "execution"},
                {
                    keys.CREATE_NODES: [
                        ("on_playback_tick", "omni.graph.action.OnPlaybackTick"),
                        ("read_prim_attr", "omni.graph.nodes.ReadPrimAttribute"),
                        ("add", "omni.graph.nodes.Add"),
                        ("constant_float", "omni.graph.nodes.ConstantFloat"),
                        ("write_prim_attr", "omni.graph.nodes.WritePrimAttribute"),
                    ],
                    keys.CONNECT: [
                        ("on_playback_tick.outputs:tick", "write_prim_attr.inputs:execIn"),
                        ("read_prim_attr.outputs:value", "add.inputs:a"),
                        ("constant_float.inputs:value", "add.inputs:b"),
                        ("add.outputs:sum", "write_prim_attr.inputs:value"),
                    ],
                    keys.SET_VALUES: [
                        ("read_prim_attr.inputs:prim", Sdf.Path(cube_path)),
                        ("read_prim_attr.inputs:name", "size"),
                        ("write_prim_attr.inputs:prim", Sdf.Path(cube_path)),
                        ("write_prim_attr.inputs:name", "size"),
                        ("constant_float.inputs:value", 1.0),
                    ],
                },
            )

        make_graph("/Graph1", "/Cube1")
        make_graph("/Graph2", "/Cube2")

        # Force stage update once to initialize types
        await omni.kit.app.get_app().next_update_async()

        # Only evaluate Graph1
        og.Controller().evaluate_sync(graph_id="/Graph1")

        cube1_size = stage.GetAttributeAtPath("/Cube1.size").Get()
        cube2_size = stage.GetAttributeAtPath("/Cube2.size").Get()

        self.assertEqual(cube1_size, 2.0, "Cube1 should be incremented")
        self.assertEqual(cube2_size, 1.0, "Cube2 should remain unchanged")
