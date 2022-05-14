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

# Import extension python module we are testing with absolute import path, as if we are external user (other extension)
import omni.kit.commands
from .common import get_selected_path

from pxr import Gf


# Having a test class dervived from omni.kit.test.AsyncTestCase declared on the root of module will make it auto-discoverable by omni.kit.test
class TestREBMenuCommands(omni.kit.test.AsyncTestCaseFailOnLogError):
    # Before running each test
    async def setUp(self):
        await omni.usd.get_context().new_stage_async()
        self._timeline = omni.timeline.get_timeline_interface()
        self._stage = omni.usd.get_context().get_stage()
        pass

    # After running each test
    async def tearDown(self):
        self._stage = None
        self._timeline = None
        gc.collect()
        pass

    # Run all commands
    async def test_command_basic(self):
        self._stage.DefinePrim("/World/test", "Xform")
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

        result, prim = omni.kit.commands.execute(
            "RobotEngineBridgeCreateHolonomicBase",
            path="/REB_HolonomicBase",
            parent=get_selected_path(),
            input_component="input",
            input_channel="base_command",
            output_component="output",
            output_channel="base_state",
            articulation_prim_rel=None,
            wheel_1_joint_name="",
            wheel_2_joint_name="",
            wheel_3_joint_name="",
            robot_front=Gf.Vec3f(1, 0, 0),
            wheel_radius=0.04,
            wheel_base=0.125,
            max_speed=Gf.Vec2f(1.5, 1.0),
            time_without_command=0.2,
            acceleration_smoothing=1.0,
        )

        result, prim = omni.kit.commands.execute(
            "RobotEngineBridgeCreateVehicle",
            path="/REB_Vehicle",
            parent=get_selected_path(),
            input_component="input",
            input_channel="vehicle_command",
            output_component="output",
            output_channel="vehicle_state",
            vehicle_prim_rel=None,
        )

        result, prim = omni.kit.commands.execute(
            "RobotEngineBridgeCreateJointControl",
            path="/REB_JointControl",
            parent=get_selected_path(),
            input_component="input",
            input_channel="joint_position",
            output_component="output",
            output_channel="joint_state",
            articulation_prim_rel=None,
        )

        result, prim = omni.kit.commands.execute(
            "RobotEngineBridgeCreateScissorLift",
            path="/REB_ScissorLift",
            parent=get_selected_path(),
            input_component="input",
            input_channel="lift_command",
            output_component="output",
            output_channel="lift_state",
            articulation_prim_rel=None,
            lift_joint_name="lift_joint",
        )

        result, prim = omni.kit.commands.execute(
            "RobotEngineBridgeCreateSurfaceGripper",
            path="/REB_SurfaceGripper",
            parent=get_selected_path(),
            input_component="input",
            input_channel="io_command",
            output_component="output",
            output_channel="io_state",
            d6_joint_prim_rel=None,
            parent_prim_rel=["/World/test"],
            gripper_entity="gripper",
            grip_threshold=1,
            force_limit=1e10,
            torque_limit=1e10,
            bend_angle=0,
            stiffness=1e10,
            damping=1e3,
            offset_position=Gf.Vec3f(0, 0, 0),
            offset_rotation=Gf.Quatf(1.0),
        )

        result, prim = omni.kit.commands.execute(
            "RobotEngineBridgeCreateTwoFingerGripper",
            path="/REB_TwoFingerGripper",
            parent=get_selected_path(),
            input_component="input",
            input_channel="io_command",
            output_component="output",
            output_channel="io_state",
            articulation_prim_rel=None,
            left_finger_joint="left_finger",
            right_finger_joint="right_finger",
            gripper_entity="gripper",
            closed_distance=0,
            open_distance=0.04,
        )

        result, prim = omni.kit.commands.execute(
            "RobotEngineBridgeCreateRigidBodySink",
            path="/REB_RigidBodySink",
            parent=get_selected_path(),
            output_component="output",
            output_channel="bodies",
            rigid_body_prims_rel=None,
        )

        result, prim = omni.kit.commands.execute(
            "RobotEngineBridgeCreateTeleport",
            path="/REB_Teleport",
            parent=get_selected_path(),
            input_component="input",
            input_channel="teleport",
        )

        result, prim = omni.kit.commands.execute(
            "RobotEngineBridgeCreateScenarioFromMessage",
            path="/REB_ScenarioFromMessage",
            parent=get_selected_path(),
            input_component="input",
            input_channel="scenario_actors",
            teleport_input_component="input",
            teleport_input_channel="teleport",
            rigid_body_sink_output_component="output",
            rigid_body_sink_output_channel="bodies",
        )

        result, prim = omni.kit.commands.execute(
            "RobotEngineBridgeCreateCamera",
            path="/REB_Camera",
            parent=get_selected_path(),
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
        )

        result, prim = omni.kit.commands.execute(
            "RobotEngineBridgeCreateLidar",
            path="/REB_Lidar",
            parent=get_selected_path(),
            output_component="output",
            output_channel="rangescan",
            lidar_prim_rel=None,
        )

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
            map_size=Gf.Vec2i(32, 32),
            debug_draw=False,
            occupied_value=1.0,
            unoccupied_value=0.0,
            unknown_value=0.5,
        )

        result, prim = omni.kit.commands.execute(
            "RobotEngineBridgeCreateUltrasonic",
            path="/REB_Ultrasonic",
            parent=get_selected_path(),
            output_component="output",
            output_channel="uss_envelopes",
            ultrasonic_prim_rel=None,
        )

        result, prim = omni.kit.commands.execute(
            "RobotEngineBridgeCreateContactMonitor",
            path="/REB_ContactMonitor",
            parent=get_selected_path(),
            output_component="output",
            output_channel="collision",
            target_prim_rel=None,
            ignored_prims_rel=None,
            force_threshold=1000.0,
        )

        result, prim = omni.kit.commands.execute(
            "RobotEngineBridgeCreatePolylineVisualizer",
            path="/REB_PolylineVisualizer",
            parent=get_selected_path(),
            input_component="input",
            input_channel="sight_plan",
            parent_prim_rel=None,
            width=0.1,
            color=Gf.Vec4f(1.0, 1.0, 1.0, 1.0),
            offset=Gf.Vec3f(0, 0, 0),
        )
