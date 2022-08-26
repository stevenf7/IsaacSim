# Copyright (c) 2018-2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

import omni.kit.commands
from pxr import Gf
import weakref
import omni.kit.menu.utils
from omni.kit.menu.utils import add_menu_items, remove_menu_items, MenuItemDescription


class RobotEngineBridgeMenu:
    def __init__(self):
        menu_items = [
            MenuItemDescription(
                name="Differential Base", onclick_fn=lambda a=weakref.proxy(self): a._add_differential_base()
            ),
            MenuItemDescription(
                name="Holonomic Base", onclick_fn=lambda a=weakref.proxy(self): a._add_holonomic_base()
            ),
            MenuItemDescription(name="Vehicle", onclick_fn=lambda a=weakref.proxy(self): a._add_vehicle()),
            MenuItemDescription(name="Joint Control", onclick_fn=lambda a=weakref.proxy(self): a._add_joint_control()),
            MenuItemDescription(
                name="Scissor Lift", onclick_fn=lambda a=weakref.proxy(self): a._add_scissor_lift_simulator()
            ),
            MenuItemDescription(
                name="Surface Gripper", onclick_fn=lambda a=weakref.proxy(self): a._add_surface_gripper()
            ),
            MenuItemDescription(
                name="Two Finger Gripper", onclick_fn=lambda a=weakref.proxy(self): a._add_twofinger_gripper()
            ),
            MenuItemDescription(
                name="Rigid Body Sink", onclick_fn=lambda a=weakref.proxy(self): a._add_rigid_body_sink()
            ),
            MenuItemDescription(name="Teleport", onclick_fn=lambda a=weakref.proxy(self): a._add_teleport()),
            MenuItemDescription(
                name="Scenario From Message", onclick_fn=lambda a=weakref.proxy(self): a._add_scenario_from_message()
            ),
            MenuItemDescription(name="Camera", onclick_fn=lambda a=weakref.proxy(self): a._add_camera()),
            MenuItemDescription(name="Lidar", onclick_fn=lambda a=weakref.proxy(self): a._add_lidar()),
            MenuItemDescription(
                name="Occupancy Grid Map", onclick_fn=lambda a=weakref.proxy(self): a._add_occupancy_grid_map()
            ),
            MenuItemDescription(name="Ultrasonic", onclick_fn=lambda a=weakref.proxy(self): a._add_ultrasonic()),
            MenuItemDescription(
                name="Contact Monitor", onclick_fn=lambda a=weakref.proxy(self): a._add_contact_monitor()
            ),
            MenuItemDescription(
                name="Polyline Visualizer", onclick_fn=lambda a=weakref.proxy(self): a._add_polyline_visualizer()
            ),
            MenuItemDescription(name="Simulation Command", onclick_fn=lambda a=weakref.proxy(self): a._add_command()),
            MenuItemDescription(name="Pose Tree", onclick_fn=lambda a=weakref.proxy(self): a._add_pose_tree()),
        ]

        self._menu_items = [
            MenuItemDescription(
                name="Isaac", glyph="plug.svg", sub_menu=[MenuItemDescription(name="Isaac SDK", sub_menu=menu_items)]
            )
        ]
        add_menu_items(self._menu_items, "Create")

    def _get_stage_and_path(self):
        self._stage = omni.usd.get_context().get_stage()
        selectedPrims = omni.usd.get_context().get_selection().get_selected_prim_paths()

        if len(selectedPrims) > 0:
            curr_prim = selectedPrims[-1]
        else:
            curr_prim = None
        return curr_prim

    def _add_differential_base(self, *args, **kwargs):
        result, prim = omni.kit.commands.execute(
            "RobotEngineBridgeCreateDifferentialBase",
            path="/REB_DifferentialBase",
            parent=self._get_stage_and_path(),
            input_component="input",
            input_channel="base_command",
            output_component="output",
            output_channel="base_state",
            chassis_prim_rel=None,
            left_wheel_joint_name="",
            right_wheel_joint_name="",
            robot_front=(1, 0, 0),
            wheel_radius=0.1,
            wheel_base=0.5,
            max_speed=(1.5, 1.0),
            time_without_command=0.2,
            acceleration_smoothing=1.0,
        )

        pass

    def _add_holonomic_base(self, *args, **kwargs):
        result, prim = omni.kit.commands.execute(
            "RobotEngineBridgeCreateHolonomicBase",
            path="/REB_HolonomicBase",
            parent=self._get_stage_and_path(),
            input_component="input",
            input_channel="base_command",
            output_component="output",
            output_channel="base_state",
            articulation_prim_rel=None,
            wheel_1_joint_name="",
            wheel_2_joint_name="",
            wheel_3_joint_name="",
            robot_front=(1, 0, 0),
            wheel_radius=0.04,
            wheel_base=0.125,
            max_speed=(1.5, 1.0),
            time_without_command=0.2,
            acceleration_smoothing=1.0,
        )
        pass

    def _add_vehicle(self, *args, **kwargs):
        result, prim = omni.kit.commands.execute(
            "RobotEngineBridgeCreateVehicle",
            path="/REB_Vehicle",
            parent=self._get_stage_and_path(),
            input_component="input",
            input_channel="vehicle_command",
            output_component="output",
            output_channel="vehicle_state",
            vehicle_prim_rel=None,
        )
        pass

    def _add_joint_control(self, *args, **kwargs):
        result, prim = omni.kit.commands.execute(
            "RobotEngineBridgeCreateJointControl",
            path="/REB_JointControl",
            parent=self._get_stage_and_path(),
            input_component="input",
            input_channel="joint_position",
            output_component="output",
            output_channel="joint_state",
            articulation_prim_rel=None,
        )
        pass

    def _add_scissor_lift_simulator(self, *args, **kwargs):
        result, prim = omni.kit.commands.execute(
            "RobotEngineBridgeCreateScissorLift",
            path="/REB_ScissorLift",
            parent=self._get_stage_and_path(),
            input_component="input",
            input_channel="lift_command",
            output_component="output",
            output_channel="lift_state",
            articulation_prim_rel=None,
            lift_joint_name="lift_joint",
            lift_speed=0.02,
        )
        pass

    def _add_surface_gripper(self, *args, **kwargs):
        result, prim = omni.kit.commands.execute(
            "RobotEngineBridgeCreateSurfaceGripper",
            path="/REB_SurfaceGripper",
            parent=self._get_stage_and_path(),
            input_component="input",
            input_channel="io_command",
            output_component="output",
            output_channel="io_state",
            d6_joint_prim_rel=None,
            parent_prim_rel=None,
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
        pass

    def _add_twofinger_gripper(self, *args, **kwargs):
        result, prim = omni.kit.commands.execute(
            "RobotEngineBridgeCreateTwoFingerGripper",
            path="/REB_TwoFingerGripper",
            parent=self._get_stage_and_path(),
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

        pass

    def _add_rigid_body_sink(self, *args, **kwargs):
        result, prim = omni.kit.commands.execute(
            "RobotEngineBridgeCreateRigidBodySink",
            path="/REB_RigidBodySink",
            parent=self._get_stage_and_path(),
            output_component="output",
            output_channel="bodies",
            rigid_body_prims_rel=None,
        )

        pass

    def _add_teleport(self, *args, **kwargs):
        result, prim = omni.kit.commands.execute(
            "RobotEngineBridgeCreateTeleport",
            path="/REB_Teleport",
            parent=self._get_stage_and_path(),
            input_component="input",
            input_channel="teleport",
        )

        pass

    def _add_scenario_from_message(self, *args, **kwargs):
        result, prim = omni.kit.commands.execute(
            "RobotEngineBridgeCreateScenarioFromMessage",
            path="/REB_ScenarioFromMessage",
            parent=self._get_stage_and_path(),
            input_component="input",
            input_channel="scenario_actors",
            teleport_input_component="input",
            teleport_input_channel="teleport",
            rigid_body_sink_output_component="output",
            rigid_body_sink_output_channel="bodies",
        )

        pass

    def _add_camera(self, *args, **kwargs):
        result, prim = omni.kit.commands.execute(
            "RobotEngineBridgeCreateCamera",
            path="/REB_Camera",
            parent=self._get_stage_and_path(),
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

        pass

    def _add_lidar(self, *args, **kwargs):
        result, prim = omni.kit.commands.execute(
            "RobotEngineBridgeCreateLidar",
            path="/REB_Lidar",
            parent=self._get_stage_and_path(),
            output_component="output",
            output_channel="rangescan",
            lidar_prim_rel=None,
        )

        pass

    def _add_occupancy_grid_map(self, *args, **kwargs):
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

        pass

    def _add_ultrasonic(self, *args, **kwargs):
        result, prim = omni.kit.commands.execute(
            "RobotEngineBridgeCreateUltrasonic",
            path="/REB_Ultrasonic",
            parent=self._get_stage_and_path(),
            output_component="output",
            output_channel="uss_envelopes",
            ultrasonic_prim_rel=None,
        )

        pass

    def _add_contact_monitor(self, *args, **kwargs):
        result, prim = omni.kit.commands.execute(
            "RobotEngineBridgeCreateContactMonitor",
            path="/REB_ContactMonitor",
            parent=self._get_stage_and_path(),
            output_component="output",
            output_channel="collision",
            target_prim_rel=None,
            ignored_prims_rel=None,
            force_threshold=1000.0,
        )

        pass

    def _add_polyline_visualizer(self, *args, **kwargs):
        result, prim = omni.kit.commands.execute(
            "RobotEngineBridgeCreatePolylineVisualizer",
            path="/REB_PolylineVisualizer",
            parent=self._get_stage_and_path(),
            input_component="input",
            input_channel="sight_plan",
            parent_prim_rel=None,
            width=0.1,
            color=Gf.Vec4f(1.0, 1.0, 1.0, 1.0),
            offset=Gf.Vec3f(0, 0, 0),
        )
        pass

    def _add_command(self, *args, **kwargs):
        result, prim = omni.kit.commands.execute(
            "RobotEngineBridgeCreateCommand",
            path="/REB_Command",
            parent=self._get_stage_and_path(),
            input_component="command",
            input_channel="input",
        )
        pass

    def _add_pose_tree(self, *args, **kwargs):
        result, prim = omni.kit.commands.execute(
            "RobotEngineBridgeCreatePoseTree",
            path="/REB_PoseTree",
            parent=self._get_stage_and_path(),
            node_name="interface",
            output_component="output",
            output_channel="pose_tree",
            prims_rel=None,
            depth_limits=[],
            prim_regex="",
        )
        pass

    def shutdown(self):
        remove_menu_items(self._menu_items, "Create")
        self._menus = None
