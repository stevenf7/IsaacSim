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
class TestREBPyaliceCamera(omni.kit.test.AsyncTestCase):
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

    def add_camera(self, cameraPath):

        result, camera_prim = omni.kit.commands.execute(
            "CreateRobotEngineBridgeCameraCommand",
            path=cameraPath,
            parent=None,
            rgb_output_component="output",
            rgb_output_channel="color",
            depth_output_component="output",
            depth_output_channel="depth",
            segmentation_output_component="output",
            segmentation_output_channel="segmentation",
            bbox2d_output_component="output",
            bbox2d_output_channel="bbox",
            bbox2d_class_list="",
            bbox3d_output_component="output",
            bbox3d_output_channel="bbox3d",
            bbox3d_class_list="",
            rgb_enabled=True,
            depth_enabled=False,
            segmentaion_enabled=False,
            bbox2d_enabled=False,
            bbox3d_enabled=False,
            camera_prim_rel=None,
            use_existing_viewport=False,
            resolution=Gf.Vec2i(800, 600),
        )

        return camera_prim

    async def test_camera(self):

        self.add_camera("/REB_Camera")
        test_app = PyaliceApp()

        test_app.app.load(
            filename=self._reb_extension_path + "/data/config/navsim_tcp.subgraph.json", prefix="simulation"
        )

        test_app.start()

        self._timeline.play()
        await simulate(2.0)
        msg = test_app.app.receive("simulation.interface", "output", "color")
        buffer = msg.tensor
        self.assertTupleEqual(buffer.shape, (600, 800, 3))
        self._timeline.stop()
        test_app.stop()
        test_app = None
