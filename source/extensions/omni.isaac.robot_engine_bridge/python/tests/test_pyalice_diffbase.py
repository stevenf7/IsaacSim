# NOTE:
#   omni.kit.test - std python's unittest module with additional wrapping to add suport for async/await tests
#   For most things refer to unittest docs: https://docs.python.org/3/library/unittest.html
import omni.kit.test

import omni.kit.usd
import carb.tokens
import numpy as np
import gc

# Import extension python module we are testing with absolute import path, as if we are external user (other extension)
from omni.isaac.robot_engine_bridge import _robot_engine_bridge
from omni.isaac.dynamic_control import _dynamic_control

from omni.isaac.utils.scripts.test_utils import load_test_file
from omni.isaac.utils.scripts.nucleus_utils import find_nucleus_server
from .common import PyaliceApp, ConstantDiffBaseControl, BodyMonitor, get_selected_path, create_application, simulate


# Having a test class dervived from omni.kit.test.AsyncTestCase declared on the root of module will make it auto-discoverable by omni.kit.test
class TestREBPyaliceDiffbase(omni.kit.test.AsyncTestCase):
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
    async def test_diffbase_carter(self):
        (result, error) = await load_test_file(self._nucleus_path + "/Samples/Isaac_SDK/Robots/Carter_REB.usd")
        # Make sure the stage loaded
        self.assertTrue(result)

        self._timeline.play()
        # settle the robot
        await simulate(1)
        art = self._dc.get_articulation("/Carter")
        self.assertNotEqual(art, _dynamic_control.INVALID_HANDLE)
        root_body_ptr = self._dc.get_articulation_root_body(art)

        test_app = PyaliceApp()
        test_app.app.load(
            filename=self._reb_extension_path + "/data/config/navsim_tcp.subgraph.json", prefix="simulation"
        )
        sim_in = test_app.app.nodes["simulation.interface"]["input"]
        sim_out = test_app.app.nodes["simulation.interface"]["output"]

        control = test_app.app.add("controller").add(ConstantDiffBaseControl, name="ConstantDiffBaseControl")
        # Convert the velocity to cm/s
        control.config.linear = 0.5
        control.config.rotation = 0.0
        test_app.app.connect(control, "cmd", sim_in, "base_command")
        monitor = test_app.app.add("monitor").add(BodyMonitor, name="BodyMonitor")
        monitor.config.linear_target = control.config.linear
        monitor.config.angular_target = control.config.rotation
        monitor.config.check = False
        test_app.app.connect(sim_out, "bodies", monitor, "bodies")
        test_app.app.connect(sim_out, "base_state", monitor, "state")
        test_app.start()
        # Run test for 2 seconds, check the linear velocity
        await simulate(2)

        lin_vel = self._dc.get_rigid_body_linear_velocity(root_body_ptr)
        self.assertAlmostEqual(
            control.config.linear, np.linalg.norm([lin_vel.x, lin_vel.y, lin_vel.z]) / 100.0, delta=0.2
        )
        self.assertEqual(monitor.config.check, True)

        control.config.linear = 0.0
        await simulate(2)

        lin_vel = self._dc.get_rigid_body_linear_velocity(root_body_ptr)
        self.assertAlmostEqual(
            control.config.linear, np.linalg.norm([lin_vel.x, lin_vel.y, lin_vel.z]) / 100.0, delta=0.2
        )

        control.config.rotation = 1.0
        monitor.config.linear_target = control.config.linear
        monitor.config.angular_target = control.config.rotation
        monitor.config.check = False
        await simulate(4)
        ang_vel = self._dc.get_rigid_body_angular_velocity(root_body_ptr)
        self.assertAlmostEqual(control.config.rotation, ang_vel[2], delta=0.2)
        self.assertEqual(monitor.config.check, True)
        # print(lin_vel, ang_vel)
        self._timeline.stop()
        test_app.stop()
        test_app = None
        self._re_bridge.destroy_application()
        pass

    # Creating a REB diffbase component from scratch
    async def test_diffbase_str(self):
        (result, error) = await load_test_file(self._nucleus_path + "/Robots/STR/STR_V4_Physics_Caster_Sensors.usda")

        # (result, error) = await load_test_file(self._dc_extension_path + "/data/usd/robots/str/str_physics.usd")
        # Make sure the stage loaded
        self.assertTrue(result)
        result, prim = omni.kit.commands.execute(
            "CreateRobotEngineBridgeDifferentialBaseCommand",
            path="/REB_DifferentialBase",
            parent=get_selected_path(),
            input_component="input",
            input_channel="base_command",
            output_component="output",
            output_channel="base_state",
            chassis_prim_rel=["/STR_V4"],
            left_wheel_joint_name="left_wheel_joint",
            right_wheel_joint_name="right_wheel_joint",
            robot_front=(1, 0, 0),
            wheel_radius=0.08,
            wheel_base=0.28963,
            max_speed=(2.0, 4.0),
            time_without_command=0.2,
            acceleration_smoothing=1.0,
        )

        self._timeline.play()
        await omni.kit.app.get_app().next_update_async()
        art = self._dc.get_articulation("/STR_V4")
        self.assertNotEqual(art, _dynamic_control.INVALID_HANDLE)
        root_body_ptr = self._dc.get_articulation_root_body(art)

        test_app = PyaliceApp()
        test_app.app.load(
            filename=self._reb_extension_path + "/data/config/navsim_tcp.subgraph.json", prefix="simulation"
        )
        sim_in = test_app.app.nodes["simulation.interface"]["input"]

        control = test_app.app.add("controller").add(ConstantDiffBaseControl, name="ConstantDiffBaseControl")
        # Convert the velocity to cm/s
        control.config.linear = 0.5
        control.config.rotation = 0.0
        test_app.app.connect(control, "cmd", sim_in, "base_command")
        test_app.start()
        # Run test for a while
        await simulate(3)

        lin_vel = self._dc.get_rigid_body_linear_velocity(root_body_ptr)
        self.assertAlmostEqual(
            control.config.linear, np.linalg.norm([lin_vel.x, lin_vel.y, lin_vel.z]) / 100.0, delta=0.2
        )

        control.config.linear = 0.0
        await simulate(1)
        print(lin_vel)
        control.config.rotation = 1.0
        await simulate(4)
        ang_vel = self._dc.get_rigid_body_angular_velocity(root_body_ptr)
        print(ang_vel)
        self.assertAlmostEqual(control.config.rotation, ang_vel[2], delta=0.2)
        self._timeline.stop()
        test_app.stop()
        test_app = None

        pass
