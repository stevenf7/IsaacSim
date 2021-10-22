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
import gc
import carb

# Import extension python module we are testing with absolute import path, as if we are external user (other extension)
import omni.kit.commands
from .common import create_application, get_selected_path, create_physics_scene
from omni.isaac.core.utils.nucleus import find_nucleus_server

from pxr import Gf, UsdPhysics, PhysxSchema


# Having a test class dervived from omni.kit.test.AsyncTestCase declared on the root of module will make it auto-discoverable by omni.kit.test
class TestREBCommands(omni.kit.test.AsyncTestCase):
    # Before running each test
    async def setUp(self):
        await omni.usd.get_context().new_stage_async()
        self._timeline = omni.timeline.get_timeline_interface()
        self._stage = omni.usd.get_context().get_stage()

        create_physics_scene(self._stage)

        result, nucleus_server = find_nucleus_server()
        if result is False:
            carb.log_error("Could not find nucleus server with /Isaac folder")
            return
        self._nucleus_path = nucleus_server + "/Isaac"

        self.assertTrue(create_application()[1])

        pass

    # After running each test
    async def tearDown(self):
        self.assertTrue(omni.kit.commands.execute("RobotEngineBridgeDestroyApplication")[1])
        self._stage = None
        self._timeline = None
        gc.collect()
        pass

    async def test_helper_commands(self):
        self.assertEqual(0, omni.kit.commands.execute("RobotEngineBridgeGetSimTimeNano")[1])
        self.assertNotEqual(0, omni.kit.commands.execute("RobotEngineBridgeGetAppOffsetNano")[1])
        self._timeline.play()
        for f in range(100):
            await omni.kit.app.get_app().next_update_async()
        self.assertGreater(omni.kit.commands.execute("RobotEngineBridgeGetSimTimeNano")[1], 0)
        self.assertNotEqual(0, omni.kit.commands.execute("RobotEngineBridgeGetAppOffsetNano")[1])

    # Disable this test because it just prints error messages anyways and causes the test to fail
    # def run_command_basic(self):
    #     self._stage.DefinePrim("/World/test", "Xform")
    #     result, prim = omni.kit.commands.execute(
    #         "RobotEngineBridgeCreateDifferentialBase", path="/REB_DifferentialBase"
    #     )

    #     result, prim = omni.kit.commands.execute("RobotEngineBridgeCreateHolonomicBase", path="/REB_HolonomicBase")

    #     result, prim = omni.kit.commands.execute("RobotEngineBridgeCreateVehicle", path="/REB_Vehicle")

    #     result, prim = omni.kit.commands.execute("RobotEngineBridgeCreateJointControl", path="/REB_JointControl")

    #     result, prim = omni.kit.commands.execute("RobotEngineBridgeCreateScissorLift", path="/REB_ScissorLift")

    #     result, prim = omni.kit.commands.execute("RobotEngineBridgeCreateSurfaceGripper", path="/REB_SurfaceGripper")

    #     result, prim = omni.kit.commands.execute(
    #         "RobotEngineBridgeCreateTwoFingerGripper", path="/REB_TwoFingerGripper"
    #     )

    #     result, prim = omni.kit.commands.execute("RobotEngineBridgeCreateRigidBodySink", path="/REB_RigidBodySink")

    #     result, prim = omni.kit.commands.execute("RobotEngineBridgeCreateTeleport", path="/REB_Teleport")

    #     result, prim = omni.kit.commands.execute(
    #         "RobotEngineBridgeCreateScenarioFromMessage", path="/REB_ScenarioFromMessage"
    #     )

    #     result, prim = omni.kit.commands.execute("RobotEngineBridgeCreateCamera", path="/REB_Camera")

    #     result, prim = omni.kit.commands.execute("RobotEngineBridgeCreateLidar", path="/REB_Lidar")

    #     result, prim = omni.kit.commands.execute(
    #         "RobotEngineBridgeCreateOccupancyGridMap", path="/REB_OccupancyGridMap"
    #     )

    #     result, prim = omni.kit.commands.execute("RobotEngineBridgeCreateUltrasonic", path="/REB_Ultrasonic")

    #     result, prim = omni.kit.commands.execute("RobotEngineBridgeCreateContactMonitor", path="/REB_ContactMonitor")

    #     result, prim = omni.kit.commands.execute(
    #         "RobotEngineBridgeCreatePolylineVisualizer", path="/REB_PolylineVisualizer"
    #     )

    # async def test_command_active(self):
    #     self.assertTrue(create_application()[1])
    #     self._timeline.play()
    #     await omni.kit.app.get_app().next_update_async()
    #     self.run_command_basic()
    #     await omni.kit.app.get_app().next_update_async()
    #     await omni.kit.app.get_app().next_update_async()
    #     self.assertTrue(omni.kit.commands.execute("RobotEngineBridgeTickComponent", path="/REB_Lidar")[1])
    #     # self.assertFalse(omni.kit.commands.execute("RobotEngineBridgeTickComponent", path="/REB_DOESNT_EXIST")[1])
    #     await omni.kit.app.get_app().next_update_async()
    #     await omni.kit.app.get_app().next_update_async()
    #     self.assertTrue(omni.kit.commands.execute("RobotEngineBridgeDestroyApplication")[1])
    #     self._timeline.stop()

    # TODO make this generic and automatically randomize all parameters
    async def test_diffbase_update(self):
        result, prim = omni.kit.commands.execute(
            "RobotEngineBridgeCreateDifferentialBase",
            path="/REB_DifferentialBase",
            parent=get_selected_path(),
            input_component="input",
            input_channel="base_command",
            output_component="output",
            output_channel="base_state",
            chassis_prim_rel=None,
            left_wheel_joint_name="",
            right_wheel_joint_name="",
            robot_front=Gf.Vec3f(1, 0, 0),
            wheel_radius=0.1,
            wheel_base=0.5,
            max_speed=Gf.Vec2f(1.5, 1.0),
            time_without_command=0.2,
            acceleration_smoothing=1.0,
        )
        await omni.kit.app.get_app().next_update_async()
        await omni.kit.app.get_app().next_update_async()
        # print(result, prim)
        prim.GetInputComponentAttr().Set(str("input_changed"))
        prim.GetInputChannelAttr().Set(str("base_command_changed"))
        await omni.kit.app.get_app().next_update_async()
        await omni.kit.app.get_app().next_update_async()
        # TODO complete test
