# NOTE:
#   omni.kit.test - std python's unittest module with additional wrapping to add suport for async/await tests
#   For most things refer to unittest docs: https://docs.python.org/3/library/unittest.html
import omni.kit.test

import omni.kit.usd
import carb.tokens
import gc

# Import extension python module we are testing with absolute import path, as if we are external user (other extension)
from omni.isaac.robot_engine_bridge import _robot_engine_bridge
from omni.isaac.dynamic_control import _dynamic_control

from omni.isaac.utils.scripts.test_utils import load_test_file
from omni.isaac.utils.scripts.nucleus_utils import find_nucleus_server
from .common import PyaliceApp, VehicleControl, create_application, simulate


# Having a test class dervived from omni.kit.test.AsyncTestCase declared on the root of module will make it auto-discoverable by omni.kit.test
class TestREBPyaliceVehicle(omni.kit.test.AsyncTestCase):
    # Before running each test
    async def setUp(self):
        await omni.usd.get_context().new_stage_async()
        self._timeline = omni.timeline.get_timeline_interface()
        self._usd_context = omni.usd.get_context()
        self._dc = _dynamic_control.acquire_dynamic_control_interface()
        self._re_bridge = _robot_engine_bridge.acquire_robot_engine_bridge_interface()

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

        create_application(self._re_bridge)
        pass

    # After running each test
    async def tearDown(self):
        self._re_bridge.destroy_application()
        gc.collect()
        pass

    # Test diffbase component that was loaded from usd
    async def test_basic_vehicle(self):
        (result, error) = await load_test_file(self._nucleus_path + "/Samples/Isaac_SDK/Robots/Basic_Vehicle_REB.usd")
        # Make sure the stage loaded
        self.assertTrue(result)

        self._timeline.play()
        # settle the robot
        await simulate(1)

        test_app = PyaliceApp()
        test_app.app.load(
            filename=self._reb_extension_path + "/data/config/navsim_tcp.subgraph.json", prefix="simulation"
        )
        sim_in = test_app.app.nodes["simulation.interface"]["input"]
        sim_out = test_app.app.nodes["simulation.interface"]["output"]

        control = test_app.app.add("controller").add(VehicleControl, name="VehicleControl")
        control.config.accelerator = 2.0
        control.config.steering = 0.0
        test_app.app.connect(control, "cmd", sim_in, "vehicle_command")
        test_app.start()
        # TODO: Check chassis linear velocity
        await simulate(10)
        # TODO: Compute analytical values to compare against
        control.config.accelerator = 0.0
        control.config.steering = 1.0
        await simulate(3)
        control.config.accelerator = 0.0
        control.config.steering = -1.0
        await simulate(3)

        # print(lin_vel, ang_vel)
        self._timeline.stop()
        test_app.stop()
        test_app = None
        self._re_bridge.destroy_application()
        pass
