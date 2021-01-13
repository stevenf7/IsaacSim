import omni.kit.editor
import omni.kit.commands
import omni.kit.ui
from pxr import Gf


class RobotEngineBridgeMenu:
    def __init__(self):
        menu_items = [
            ("Differential Base", self._add_differential_base),
            ("Holonomic Base", self._add_holonomic_base),
            ("Vehicle", self._add_vehicle),
            ("Joint Control", self._add_joint_control),
            ("Scissor Lift", self._add_scissor_lift_simulator),
            ("Surface Gripper", self._add_surface_gripper),
            ("Two Finger Gripper", self._add_twofinger_gripper),
            ("Rigid Body Sink", self._add_rigid_body_sink),
            ("Teleport", self._add_teleport),
            ("Scenario From Message", self._add_scenario_from_message),
            ("Camera", self._add_camera),
            ("Lidar", self._add_lidar),
            ("Occupancy Grid Map", self._add_occupancy_grid_map),
            ("Contact Monitor", self._add_contact_monitor),
            ("Polyline Visualizer", self._add_polyline_visualizer),
        ]

        self._menus = []
        for item in menu_items:
            self._menus.append(omni.kit.ui.get_editor_menu().add_item(f"Create/Isaac/Robot Engine/{item[0]}", item[1]))

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
            "CreateRobotEngineBridgeDifferentialBaseCommand",
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
            "CreateRobotEngineBridgeHolonomicBaseCommand",
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
            "CreateRobotEngineBridgeVehicleCommand",
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
            "CreateRobotEngineBridgeJointControlCommand",
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
            "CreateRobotEngineBridgeScissorLiftCommand",
            path="/REB_ScissorLift",
            parent=self._get_stage_and_path(),
            input_component="input",
            input_channel="lift_command",
            output_component="output",
            output_channel="lift_state",
            articulation_prim_rel=None,
            lift_joint_name="lift_joint",
        )
        pass

    def _add_surface_gripper(self, *args, **kwargs):
        result, prim = omni.kit.commands.execute(
            "CreateRobotEngineBridgeSurfaceGripperCommand",
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
            "CreateRobotEngineBridgeTwoFingerGripperCommand",
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
            "CreateRobotEngineBridgeRigidBodySinkCommand",
            path="/REB_RigidBodySink",
            parent=self._get_stage_and_path(),
            output_component="output",
            output_channel="bodies",
            rigid_body_prims_rel=None,
        )

        pass

    def _add_teleport(self, *args, **kwargs):
        result, prim = omni.kit.commands.execute(
            "CreateRobotEngineBridgeTeleportCommand",
            path="/REB_Teleport",
            parent=self._get_stage_and_path(),
            input_component="input",
            input_channel="teleport",
        )

        pass

    def _add_scenario_from_message(self, *args, **kwargs):
        result, prim = omni.kit.commands.execute(
            "CreateRobotEngineBridgeScenarioFromMessageCommand",
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
            "CreateRobotEngineBridgeCameraCommand",
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
            "CreateRobotEngineBridgeLidarCommand",
            path="/REB_Lidar",
            parent=self._get_stage_and_path(),
            output_component="output",
            output_channel="rangescan",
            lidar_prim_rel=None,
        )

        pass

    def _add_occupancy_grid_map(self, *args, **kwargs):
        result, prim = omni.kit.commands.execute(
            "CreateRobotEngineBridgeOccupancyGridMapCommand",
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

    def _add_contact_monitor(self, *args, **kwargs):
        result, prim = omni.kit.commands.execute(
            "CreateRobotEngineBridgeContactMonitorCommand",
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
            "CreateRobotEngineBridgePolylineVisualizerCommand",
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

    def shutdown(self):
        self._menus = None
