# Copyright (c) 2018-2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

import omni.kit.commands
import omni.kit.utils
import omni.isaac.RobotEngineBridgeSchema as REBSchema
import carb
from pxr import Gf
from omni.isaac.core.utils.stage import get_next_free_path


def setup_publisher(prim, component: str, channel: str):
    prim.CreateOutputComponentAttr(component)
    prim.CreateOutputChannelAttr(channel)


def setup_receiver(prim, component: str, channel: str):
    prim.CreateInputComponentAttr(component)
    prim.CreateInputChannelAttr(channel)


# this command is used to create each REB prim, it also handles undo so that each individual prim command doesn't have to
class RobotEngineBridgeCreatePrim(omni.kit.commands.Command):
    def __init__(self, path: str, parent: str, scehma_type, enabled: bool = True, node_name: str = "interface"):
        for name, value in vars().items():
            if name != "self":
                setattr(self, f"_{name}", value)

        self._prim_path = None
        pass

    def do(self):
        self._stage = omni.usd.get_context().get_stage()
        # make prim path unique
        self._prim_path = get_next_free_path(self._path, self._parent)
        self._prim = self._scehma_type.Define(self._stage, self._prim_path)
        self._prim.CreateNodeNameAttr(self._node_name)
        self._prim.CreateEnabledAttr(self._enabled)
        self._prim.CreateTimeOffsetAttr(0.0)
        return self._prim

    def undo(self):
        if self._prim_path is not None:
            return self._stage.RemovePrim(self._prim_path)


class RobotEngineBridgeCreateDifferentialBase(omni.kit.commands.Command):
    def __init__(
        self,
        path: str = "/REB_DifferentialBase",
        parent=None,
        enabled: bool = True,
        input_component: str = "input",
        input_channel: str = "base_command",
        output_component: str = "output",
        output_channel: str = "base_state",
        chassis_prim_rel=None,
        left_wheel_joint_name: str = "",
        right_wheel_joint_name: str = "",
        robot_front: Gf.Vec2f = Gf.Vec3f(1, 0, 0),
        wheel_radius: float = 0.1,
        wheel_base: float = 0.5,
        max_speed: Gf.Vec2f = Gf.Vec2f(1.5, 1.0),
        time_without_command: float = 0.2,
        acceleration_smoothing: float = 1.0,
    ):
        # condensed way to copy all input arguments into self with an underscore prefix
        for name, value in vars().items():
            if name != "self":
                setattr(self, f"_{name}", value)
        self._prim = None
        pass

    def do(self):
        success, self._prim = omni.kit.commands.execute(
            "RobotEngineBridgeCreatePrim",
            path=self._path,
            parent=self._parent,
            enabled=self._enabled,
            scehma_type=REBSchema.RobotEngineDifferentialBase,
        )
        if success and self._prim:

            setup_receiver(self._prim, self._input_component, self._input_channel)
            setup_publisher(self._prim, self._output_component, self._output_channel)

            rel_paths = self._prim.CreateChassisPrimRel()
            if self._chassis_prim_rel is not None:
                if len(self._chassis_prim_rel) == 1:
                    rel_paths.AddTarget(self._chassis_prim_rel[0])
                else:
                    carb.log_warn("only one chassis prim rel target can be specified")

            self._prim.CreateLeftWheelJointNameAttr(self._left_wheel_joint_name)
            self._prim.CreateRightWheelJointNameAttr(self._right_wheel_joint_name)

            self._prim.CreateRobotFrontAttr(self._robot_front)
            self._prim.CreateWheelRadiusAttr(self._wheel_radius)
            self._prim.CreateWheelBaseAttr(self._wheel_base)
            self._prim.CreateMaxSpeedAttr(self._max_speed)
            self._prim.CreateMaxTimeWithoutCommandAttr(self._time_without_command)
            self._prim.CreateAccelerationSmoothingAttr(self._acceleration_smoothing)

        return self._prim

    def undo(self):
        # undo must be defined even if empty
        pass


class RobotEngineBridgeCreateHolonomicBase(omni.kit.commands.Command):
    def __init__(
        self,
        path: str = "/REB_HolonomicBase",
        parent=None,
        enabled: bool = True,
        input_component: str = "input",
        input_channel: str = "base_command",
        output_component: str = "output",
        output_channel: str = "base_state",
        articulation_prim_rel=None,
        wheel_1_joint_name: str = "",
        wheel_2_joint_name: str = "",
        wheel_3_joint_name: str = "",
        robot_front: Gf.Vec3f = Gf.Vec3f(1, 0, 0),
        wheel_radius: float = 0.1,
        wheel_base: float = 0.5,
        max_speed: Gf.Vec2f = Gf.Vec2f(1.5, 1.0),
        time_without_command: float = 0.2,
        acceleration_smoothing: float = 1.0,
    ):
        # condensed way to copy all input arguments into self with an underscore prefix
        for name, value in vars().items():
            if name != "self":
                setattr(self, f"_{name}", value)
        pass

    def do(self):
        success, self._prim = omni.kit.commands.execute(
            "RobotEngineBridgeCreatePrim",
            path=self._path,
            parent=self._parent,
            enabled=self._enabled,
            scehma_type=REBSchema.RobotEngineHolonomicBase,
        )
        if success and self._prim:
            setup_receiver(self._prim, self._input_component, self._input_channel)
            setup_publisher(self._prim, self._output_component, self._output_channel)

            rel_paths = self._prim.CreateArticulationPrimRel()
            if self._articulation_prim_rel is not None:
                if len(self._articulation_prim_rel) == 1:
                    rel_paths.AddTarget(self._articulation_prim_rel[0])
                else:
                    carb.log_warn("only one articulation prim rel target can be specified")

            self._prim.CreateWheel1JointNameAttr(self._wheel_1_joint_name)
            self._prim.CreateWheel2JointNameAttr(self._wheel_2_joint_name)
            self._prim.CreateWheel3JointNameAttr(self._wheel_3_joint_name)

            self._prim.CreateRobotFrontAttr(self._robot_front)
            self._prim.CreateWheelRadiusAttr(self._wheel_radius)
            self._prim.CreateWheelBaseAttr(self._wheel_base)
            self._prim.CreateMaxSpeedAttr(self._max_speed)
            self._prim.CreateMaxTimeWithoutCommandAttr(self._time_without_command)
            self._prim.CreateAccelerationSmoothingAttr(self._acceleration_smoothing)

        return self._prim

    def undo(self):
        # undo must be defined even if empty
        pass


class RobotEngineBridgeCreateVehicle(omni.kit.commands.Command):
    def __init__(
        self,
        path: str = "/REB_Vehicle",
        parent=None,
        enabled: bool = True,
        input_component: str = "input",
        input_channel: str = "vehicle_command",
        output_component: str = "output",
        output_channel: str = "vehicle_state",
        vehicle_prim_rel=None,
        history_length=100,
        use_pid=False,
        controller_pid_values=(1, 1, 1),
    ):
        # condensed way to copy all input arguments into self with an underscore prefix
        for name, value in vars().items():
            if name != "self":
                setattr(self, f"_{name}", value)
        pass

    def do(self):
        success, self._prim = omni.kit.commands.execute(
            "RobotEngineBridgeCreatePrim",
            path=self._path,
            parent=self._parent,
            enabled=self._enabled,
            scehma_type=REBSchema.RobotEngineVehicle,
        )
        if success and self._prim:
            setup_receiver(self._prim, self._input_component, self._input_channel)
            setup_publisher(self._prim, self._output_component, self._output_channel)

            rel_paths = self._prim.CreateVehiclePrimRel()
            if self._vehicle_prim_rel is not None:
                if len(self._vehicle_prim_rel) == 1:
                    rel_paths.AddTarget(self._vehicle_prim_rel[0])
                else:
                    carb.log_warn("only one vehicle prim rel target can be specified")
            self._prim.CreateHistoryLengthAttr(self._history_length)
            self._prim.CreateUsePIDAttr(self._use_pid)
            self._prim.CreateControllerPIDValuesAttr(self._controller_pid_values)
        return self._prim

    def undo(self):
        # undo must be defined even if empty
        pass


class RobotEngineBridgeCreateJointControl(omni.kit.commands.Command):
    def __init__(
        self,
        path: str = "/REB_JointControl",
        parent=None,
        enabled: bool = True,
        input_component: str = "input",
        input_channel: str = "joint_position",
        output_component: str = "output",
        output_channel: str = "joint_state",
        articulation_prim_rel=None,
    ):
        # condensed way to copy all input arguments into self with an underscore prefix
        for name, value in vars().items():
            if name != "self":
                setattr(self, f"_{name}", value)
        pass

    def do(self):
        success, self._prim = omni.kit.commands.execute(
            "RobotEngineBridgeCreatePrim",
            path=self._path,
            parent=self._parent,
            enabled=self._enabled,
            scehma_type=REBSchema.RobotEngineJointControl,
        )
        if success and self._prim:
            setup_receiver(self._prim, self._input_component, self._input_channel)
            setup_publisher(self._prim, self._output_component, self._output_channel)

            rel_paths = self._prim.CreateArticulationPrimRel()
            if self._articulation_prim_rel is not None:
                if len(self._articulation_prim_rel) == 1:
                    rel_paths.AddTarget(self._articulation_prim_rel[0])
                else:
                    carb.log_warn("only one articulation prim rel target can be specified")

        return self._prim

    def undo(self):
        # undo must be defined even if empty
        pass


class RobotEngineBridgeCreateScissorLift(omni.kit.commands.Command):
    def __init__(
        self,
        path: str = "/REB_ScissorLift",
        parent=None,
        enabled: bool = True,
        input_component: str = "input",
        input_channel: str = "joint_position",
        output_component: str = "output",
        output_channel: str = "joint_state",
        articulation_prim_rel=None,
        lift_joint_name: str = "lift_joint",
        lift_speed: float = 0.02,
    ):
        # condensed way to copy all input arguments into self with an underscore prefix
        for name, value in vars().items():
            if name != "self":
                setattr(self, f"_{name}", value)
        pass

    def do(self):
        success, self._prim = omni.kit.commands.execute(
            "RobotEngineBridgeCreatePrim",
            path=self._path,
            parent=self._parent,
            enabled=self._enabled,
            scehma_type=REBSchema.RobotEngineScissorLift,
        )
        if success and self._prim:

            setup_receiver(self._prim, self._input_component, self._input_channel)
            setup_publisher(self._prim, self._output_component, self._output_channel)
            rel_paths = self._prim.CreateArticulationPrimRel()
            if self._articulation_prim_rel is not None:
                if len(self._articulation_prim_rel) == 1:
                    rel_paths.AddTarget(self._articulation_prim_rel[0])
                else:
                    carb.log_warn("only one articulation prim rel target can be specified")
            self._prim.CreateLiftJointNameAttr(self._lift_joint_name)
            self._prim.CreateLiftSpeedAttr(self._lift_speed)

        return self._prim

    def undo(self):
        # undo must be defined even if empty
        pass


class RobotEngineBridgeCreateSurfaceGripper(omni.kit.commands.Command):
    def __init__(
        self,
        path: str = "/REB_SurfaceGripper",
        parent=None,
        enabled: bool = True,
        input_component: str = "input",
        input_channel: str = "io_command",
        output_component: str = "output",
        output_channel: str = "io_state",
        d6_joint_prim_rel=None,
        parent_prim_rel=None,
        gripper_entity: str = "gripper",
        grip_threshold: float = 1,
        force_limit: float = 1e10,
        torque_limit: float = 1e10,
        bend_angle: float = 0,
        stiffness: float = 1e10,
        damping: float = 1e3,
        offset_position: Gf.Vec3f = Gf.Vec3f(0, 0, 0),
        offset_rotation: Gf.Quatf = Gf.Quatf(1.0),
    ):
        # condensed way to copy all input arguments into self with an underscore prefix
        for name, value in vars().items():
            if name != "self":
                setattr(self, f"_{name}", value)
        pass

    def do(self):
        success, self._prim = omni.kit.commands.execute(
            "RobotEngineBridgeCreatePrim",
            path=self._path,
            parent=self._parent,
            enabled=self._enabled,
            scehma_type=REBSchema.RobotEngineSurfaceGripper,
        )
        if success and self._prim:
            setup_receiver(self._prim, self._input_component, self._input_channel)
            setup_publisher(self._prim, self._output_component, self._output_channel)
            d6_rel_paths = self._prim.CreateD6JointPrimRel()
            if self._d6_joint_prim_rel is not None:
                if len(self._d6_joint_prim_rel) == 1:
                    d6_rel_paths.AddTarget(self._d6_joint_prim_rel[0])
                else:
                    carb.log_warn("only one d6 prim rel target can be specified")

            parent_rel_paths = self._prim.CreateParentPrimRel()
            if self._parent_prim_rel is not None:
                if len(self._parent_prim_rel) == 1:
                    parent_rel_paths.AddTarget(self._parent_prim_rel[0])
                else:
                    carb.log_warn("only one parent prim rel target can be specified")

            self._prim.CreateGripperEntityAttr(self._gripper_entity)

            self._prim.CreateGripThresholdAttr(self._grip_threshold)
            self._prim.CreateForceLimitAttr(self._force_limit)
            self._prim.CreateTorqueLimitAttr(self._torque_limit)
            self._prim.CreateBendAngleAttr(self._bend_angle)
            self._prim.CreateStiffnessAttr(self._stiffness)
            self._prim.CreateDampingAttr(self._damping)
            self._prim.CreateOffsetPositionAttr(self._offset_position)
            self._prim.CreateOffsetRotationAttr(self._offset_rotation)

        return self._prim

    def undo(self):
        # undo must be defined even if empty
        pass


class RobotEngineBridgeCreateTwoFingerGripper(omni.kit.commands.Command):
    def __init__(
        self,
        path: str = "/REB_TwoFingerGripper",
        parent=None,
        enabled: bool = True,
        input_component: str = "input",
        input_channel: str = "io_command",
        output_component: str = "output",
        output_channel: str = "io_state",
        articulation_prim_rel=None,
        left_finger_joint: str = "left_finger",
        right_finger_joint: str = "right_finger",
        gripper_entity: str = "gripper",
        closed_distance: float = 0,
        open_distance: float = 0.04,
    ):
        # condensed way to copy all input arguments into self with an underscore prefix
        for name, value in vars().items():
            if name != "self":
                setattr(self, f"_{name}", value)
        pass

    def do(self):
        success, self._prim = omni.kit.commands.execute(
            "RobotEngineBridgeCreatePrim",
            path=self._path,
            parent=self._parent,
            enabled=self._enabled,
            scehma_type=REBSchema.RobotEngineTwoFingerGripper,
        )
        if success and self._prim:
            setup_receiver(self._prim, self._input_component, self._input_channel)
            setup_publisher(self._prim, self._output_component, self._output_channel)
            rel_paths = self._prim.CreateArticulationPrimRel()
            if self._articulation_prim_rel is not None:
                if len(self._articulation_prim_rel) == 1:
                    rel_paths.AddTarget(self._articulation_prim_rel[0])
                else:
                    carb.log_warn("only one articulation prim rel target can be specified")
            self._prim.CreateLeftFingerJointAttr(self._left_finger_joint)
            self._prim.CreateRightFingerJointAttr(self._right_finger_joint)
            self._prim.CreateGripperEntityAttr(self._gripper_entity)
            self._prim.CreateClosedDistanceAttr(self._closed_distance)
            self._prim.CreateOpenDistanceAttr(self._open_distance)
        return self._prim

    def undo(self):
        # undo must be defined even if empty
        pass


class RobotEngineBridgeCreateRigidBodySink(omni.kit.commands.Command):
    def __init__(
        self,
        path: str = "/REB_RigidBodySink",
        parent=None,
        enabled: bool = True,
        output_component: str = "output",
        output_channel: str = "bodies",
        rigid_body_prims_rel=None,
    ):
        # condensed way to copy all input arguments into self with an underscore prefix
        for name, value in vars().items():
            if name != "self":
                setattr(self, f"_{name}", value)
        pass

    def do(self):
        success, self._prim = omni.kit.commands.execute(
            "RobotEngineBridgeCreatePrim",
            path=self._path,
            parent=self._parent,
            enabled=self._enabled,
            scehma_type=REBSchema.RobotEngineRigidBodySink,
        )
        if success and self._prim:
            setup_publisher(self._prim, self._output_component, self._output_channel)
            rel_paths = self._prim.CreateRigidBodyPrimsRel()
            if self._rigid_body_prims_rel is not None:
                for path in self._rigid_body_prims_rel:
                    rel_paths.AddTarget(path)
        return self._prim

    def undo(self):
        # undo must be defined even if empty
        pass


class RobotEngineBridgeCreateTeleport(omni.kit.commands.Command):
    def __init__(
        self,
        path: str = "/REB_Teleport",
        parent=None,
        enabled: bool = True,
        input_component: str = "input",
        input_channel: str = "teleport",
        teleport_prims_rel=None,
    ):
        # condensed way to copy all input arguments into self with an underscore prefix
        for name, value in vars().items():
            if name != "self":
                setattr(self, f"_{name}", value)
        pass

    def do(self):
        success, self._prim = omni.kit.commands.execute(
            "RobotEngineBridgeCreatePrim",
            path=self._path,
            parent=self._parent,
            enabled=self._enabled,
            scehma_type=REBSchema.RobotEngineTeleport,
        )
        if success and self._prim:
            setup_receiver(self._prim, self._input_component, self._input_channel)
            rel_paths = self._prim.CreateTeleportPrimsRel()
            if self._teleport_prims_rel is not None:
                for path in self._teleport_prims_rel:
                    rel_paths.AddTarget(path)
        return self._prim

    def undo(self):
        # undo must be defined even if empty
        pass


class RobotEngineBridgeCreateScenarioFromMessage(omni.kit.commands.Command):
    def __init__(
        self,
        path: str = "/REB_ScenarioFromMessage",
        parent=None,
        enabled: bool = True,
        input_component: str = "input",
        input_channel: str = "scenario_actors",
        teleport_input_component: str = "input",
        teleport_input_channel: str = "teleport",
        rigid_body_sink_output_component: str = "output",
        rigid_body_sink_output_channel: str = "bodies",
    ):
        # condensed way to copy all input arguments into self with an underscore prefix
        for name, value in vars().items():
            if name != "self":
                setattr(self, f"_{name}", value)
        pass

    def do(self):
        success, self._prim = omni.kit.commands.execute(
            "RobotEngineBridgeCreatePrim",
            path=self._path,
            parent=self._parent,
            enabled=self._enabled,
            scehma_type=REBSchema.RobotEngineScenarioFromMessage,
        )
        if success and self._prim:
            setup_receiver(self._prim, self._input_component, self._input_channel)

            self._prim.CreateTeleportInputComponentAttr(self._teleport_input_component)
            self._prim.CreateTeleportInputChannelAttr(self._teleport_input_channel)

            self._prim.CreateRigidBodySinkOutputComponentAttr(self._rigid_body_sink_output_component)
            self._prim.CreateRigidBodySinkOutputChannelAttr(self._rigid_body_sink_output_channel)
        return self._prim

    def undo(self):
        # undo must be defined even if empty
        pass


class RobotEngineBridgeCreateCamera(omni.kit.commands.Command):
    def __init__(
        self,
        path: str = "/REB_Camera",
        parent=None,
        enabled: bool = True,
        rgb_output_component: str = "output",
        rgb_output_channel: str = "color",
        depth_output_component: str = "output",
        depth_output_channel: str = "depth",
        segmentation_output_component: str = "output",
        segmentation_output_channel: str = "segmentation",
        bbox2d_output_component: str = "output",
        bbox2d_output_channel: str = "bbox",
        bbox2d_class_list: str = "",
        bbox3d_output_component: str = "output",
        bbox3d_output_channel: str = "bbox3d",
        bbox3d_class_list: str = "",
        rgb_enabled: bool = True,
        depth_enabled: bool = False,
        segmentaion_enabled: bool = False,
        bbox2d_enabled: bool = False,
        bbox3d_enabled: bool = False,
        camera_prim_rel=None,
        resolution: Gf.Vec2i = Gf.Vec2i(1280, 720),
    ):
        # condensed way to copy all input arguments into self with an underscore prefix
        for name, value in vars().items():
            if name != "self":
                setattr(self, f"_{name}", value)
        pass

    def do(self):
        success, self._prim = omni.kit.commands.execute(
            "RobotEngineBridgeCreatePrim",
            path=self._path,
            parent=self._parent,
            enabled=self._enabled,
            scehma_type=REBSchema.RobotEngineCamera,
        )
        if success and self._prim:
            rel_paths = self._prim.CreateCameraPrimRel()
            if self._camera_prim_rel is not None:
                if len(self._camera_prim_rel) == 1:
                    rel_paths.AddTarget(self._camera_prim_rel[0])
                else:
                    carb.log_warn("only one camera prim rel target can be specified")
            self._prim.CreateResolutionAttr(self._resolution)

            self._prim.CreateRgbOutputComponentAttr(self._rgb_output_component)
            self._prim.CreateRgbOutputChannelAttr(self._rgb_output_channel)

            self._prim.CreateDepthOutputComponentAttr(self._depth_output_component)
            self._prim.CreateDepthOutputChannelAttr(self._depth_output_channel)

            self._prim.CreateSegmentationOutputComponentAttr(self._segmentation_output_component)
            self._prim.CreateSegmentationOutputChannelAttr(self._segmentation_output_channel)

            self._prim.CreateBoundingBox2DOutputComponentAttr(self._bbox2d_output_component)
            self._prim.CreateBoundingBox2DOutputChannelAttr(self._bbox2d_output_channel)
            self._prim.CreateBoundingBox2DClassListAttr(self._bbox2d_class_list)

            self._prim.CreateBoundingBox3DOutputComponentAttr(self._bbox3d_output_component)
            self._prim.CreateBoundingBox3DOutputChannelAttr(self._bbox3d_output_channel)
            self._prim.CreateBoundingBox3DClassListAttr(self._bbox3d_class_list)

            self._prim.CreateRgbEnabledAttr(self._rgb_enabled)
            self._prim.CreateDepthEnabledAttr(self._depth_enabled)
            self._prim.CreateSegmentationEnabledAttr(self._segmentaion_enabled)
            self._prim.CreateBoundingBox2DEnabledAttr(self._bbox2d_enabled)
            self._prim.CreateBoundingBox3DEnabledAttr(self._bbox3d_enabled)

        return self._prim

    def undo(self):
        # undo must be defined even if empty
        pass


class RobotEngineBridgeCreateLidar(omni.kit.commands.Command):
    def __init__(
        self,
        path: str = "/REB_Lidar",
        parent=None,
        enabled: bool = True,
        output_component: str = "output",
        output_channel: str = "rangescan",
        lidar_prim_rel=None,
    ):
        # condensed way to copy all input arguments into self with an underscore prefix
        for name, value in vars().items():
            if name != "self":
                setattr(self, f"_{name}", value)
        pass

    def do(self):
        success, self._prim = omni.kit.commands.execute(
            "RobotEngineBridgeCreatePrim",
            path=self._path,
            parent=self._parent,
            enabled=self._enabled,
            scehma_type=REBSchema.RobotEngineLidar,
        )
        if success and self._prim:
            setup_publisher(self._prim, self._output_component, self._output_channel)
            rel_paths = self._prim.CreateLidarPrimRel()
            if self._lidar_prim_rel is not None:
                if len(self._lidar_prim_rel) == 1:
                    rel_paths.AddTarget(self._lidar_prim_rel[0])
                else:
                    carb.log_warn("only one lidar prim rel target can be specified")
        return self._prim

    def undo(self):
        # undo must be defined even if empty
        pass


class RobotEngineBridgeCreateOccupancyGridMap(omni.kit.commands.Command):
    def __init__(
        self,
        path: str = "/REB_OccupancyGridMap",
        parent=None,
        enabled: bool = True,
        output_component: str = "output",
        output_channel: str = "occupancy_map",
        parent_prim_rel=None,
        offset: Gf.Vec3f = Gf.Vec3f(0, 0, 0),
        cell_size: float = 0.1,
        degrees_per_ray: float = 5,
        surface_offset: float = 0.02,
        occupancy_threshold: float = 1.0,
        max_rays: int = 1000000,
        map_size: Gf.Vec2i = Gf.Vec2i(32, 32),
        debug_draw: bool = False,
        occupied_value: float = 1.0,
        unoccupied_value: float = 0.0,
        unknown_value: float = 0.5,
    ):
        # condensed way to copy all input arguments into self with an underscore prefix
        for name, value in vars().items():
            if name != "self":
                setattr(self, f"_{name}", value)
        pass

    def do(self):
        success, self._prim = omni.kit.commands.execute(
            "RobotEngineBridgeCreatePrim",
            path=self._path,
            parent=self._parent,
            enabled=self._enabled,
            scehma_type=REBSchema.RobotEngineOccupancyGridMap,
        )
        if success and self._prim:
            setup_publisher(self._prim, self._output_component, self._output_channel)
            rel_paths = self._prim.CreateParentPrimRel()
            if self._parent_prim_rel is not None:
                if len(self._parent_prim_rel) == 1:
                    rel_paths.AddTarget(self._parent_prim_rel[0])
                else:
                    carb.log_warn("only one parent prim rel target can be specified")
            self._prim.CreateOffsetAttr(self._offset)
            self._prim.CreateCellSizeAttr(self._cell_size)
            self._prim.CreateDegreesPerRayAttr(self._degrees_per_ray)
            self._prim.CreateSurfaceOffsetAttr(self._surface_offset)
            self._prim.CreateOccupancyThresholdAttr(self._occupancy_threshold)
            self._prim.CreateMaxRaysAttr(self._max_rays)
            self._prim.CreateMapSizeAttr(self._map_size)
            self._prim.CreateDebugDrawAttr(self._debug_draw)

            self._prim.CreateOccupiedValueAttr(self._occupied_value)
            self._prim.CreateUnoccupiedValueAttr(self._unoccupied_value)
            self._prim.CreateUnknownValueAttr(self._unknown_value)
        return self._prim

    def undo(self):
        # undo must be defined even if empty
        pass


class RobotEngineBridgeCreateUltrasonic(omni.kit.commands.Command):
    def __init__(
        self,
        path: str = "/REB_Ultrasonic",
        parent=None,
        enabled: bool = True,
        output_component: str = "output",
        output_channel: str = "uss_envelopes",
        ultrasonic_prim_rel=None,
    ):
        # condensed way to copy all input arguments into self with an underscore prefix
        for name, value in vars().items():
            if name != "self":
                setattr(self, f"_{name}", value)
        pass

    def do(self):
        success, self._prim = omni.kit.commands.execute(
            "RobotEngineBridgeCreatePrim",
            path=self._path,
            parent=self._parent,
            enabled=self._enabled,
            scehma_type=REBSchema.RobotEngineUltrasonic,
        )
        if success and self._prim:
            setup_publisher(self._prim, self._output_component, self._output_channel)
            rel_paths = self._prim.CreateUltrasonicPrimRel()
            if self._ultrasonic_prim_rel is not None:
                if len(self._ultrasonic_prim_rel) == 1:
                    rel_paths.AddTarget(self._ultrasonic_prim_rel[0])
                else:
                    carb.log_warn("only one ultrasonic prim rel target can be specified")
        return self._prim

    def undo(self):
        # undo must be defined even if empty
        pass


class RobotEngineBridgeCreateContactMonitor(omni.kit.commands.Command):
    def __init__(
        self,
        path: str = "/REB_ContactMonitor",
        parent=None,
        enabled: bool = True,
        output_component: str = "output",
        output_channel: str = "collision",
        target_prim_rel=None,
        ignored_prims_rel=None,
        force_threshold: float = 1000.0,
    ):
        # condensed way to copy all input arguments into self with an underscore prefix
        for name, value in vars().items():
            if name != "self":
                setattr(self, f"_{name}", value)
        pass

    def do(self):
        success, self._prim = omni.kit.commands.execute(
            "RobotEngineBridgeCreatePrim",
            path=self._path,
            parent=self._parent,
            enabled=self._enabled,
            scehma_type=REBSchema.RobotEngineContactMonitor,
        )
        if success and self._prim:
            setup_publisher(self._prim, self._output_component, self._output_channel)
            target_paths = self._prim.CreateTargetPrimRel()
            if self._target_prim_rel is not None:
                if len(self._target_prim_rel) == 1:
                    target_paths.AddTarget(self._target_prim_rel[0])
                else:
                    carb.log_warn("only one target prim rel target can be specified")
            ignored_paths = self._prim.CreateIgnoredPrimsRel()
            if self._ignored_prims_rel is not None:
                for path in self._ignored_prims_rel:
                    ignored_paths.AddTarget(path)
            self._prim.CreateForceThresholdAttr(self._force_threshold)
        return self._prim

    def undo(self):
        # undo must be defined even if empty
        pass


class RobotEngineBridgeCreatePolylineVisualizer(omni.kit.commands.Command):
    def __init__(
        self,
        path: str = "/REB_PolylineVisualizer",
        parent=None,
        enabled: bool = True,
        input_component: str = "input",
        input_channel: str = "sight_plan",
        parent_prim_rel=None,
        width: float = 0.1,
        color: Gf.Vec4f = Gf.Vec4f(1.0, 1.0, 1.0, 1.0),
        offset: Gf.Vec3f = Gf.Vec3f(0, 0, 0),
    ):
        # condensed way to copy all input arguments into self with an underscore prefix
        for name, value in vars().items():
            if name != "self":
                setattr(self, f"_{name}", value)
        pass

    def do(self):
        success, self._prim = omni.kit.commands.execute(
            "RobotEngineBridgeCreatePrim",
            path=self._path,
            parent=self._parent,
            enabled=self._enabled,
            scehma_type=REBSchema.RobotEnginePolylineVisualizer,
        )
        if success and self._prim:
            setup_receiver(self._prim, self._input_component, self._input_channel)

            parent_path = self._prim.CreateParentPrimRel()
            if self._parent_prim_rel is not None:
                if len(self._parent_prim_rel) == 1:
                    parent_path.AddTarget(self._parent_prim_rel[0])
                else:
                    carb.log_warn("only one parent prim rel target can be specified")
            self._prim.CreateWidthAttr(self._width)
            self._prim.CreateColorAttr().Set(self._color)
            self._prim.CreateOffsetAttr().Set(self._offset)
        return self._prim

    def undo(self):
        # undo must be defined even if empty
        pass


class RobotEngineBridgeCreateCommand(omni.kit.commands.Command):
    def __init__(
        self,
        path: str = "/REB_Command",
        parent=None,
        enabled: bool = True,
        input_component: str = "command",
        input_channel: str = "input",
    ):
        # condensed way to copy all input arguments into self with an underscore prefix
        for name, value in vars().items():
            if name != "self":
                setattr(self, f"_{name}", value)
        pass

    def do(self):
        success, self._prim = omni.kit.commands.execute(
            "RobotEngineBridgeCreatePrim",
            path=self._path,
            parent=self._parent,
            enabled=self._enabled,
            scehma_type=REBSchema.RobotEngineCommand,
        )
        if success and self._prim:
            setup_receiver(self._prim, self._input_component, self._input_channel)
        return self._prim

    def undo(self):
        # undo must be defined even if empty
        pass


class RobotEngineBridgeCreatePoseTree(omni.kit.commands.Command):
    def __init__(
        self,
        path: str = "/REB_PoseTree",
        parent=None,
        enabled: bool = True,
        node_name: str = "interface",
        output_component: str = "output",
        output_channel: str = "pose_tree",
        prims_rel: [] = None,
        depth_limits: [int] = [],
        prim_regex: str = "",
    ):
        # condensed way to copy all input arguments into self with an underscore prefix
        for name, value in vars().items():
            if name != "self":
                setattr(self, f"_{name}", value)
        pass

    def do(self):
        success, self._prim = omni.kit.commands.execute(
            "RobotEngineBridgeCreatePrim",
            path=self._path,
            parent=self._parent,
            enabled=self._enabled,
            scehma_type=REBSchema.RobotEnginePoseTree,
        )
        if success and self._prim:
            setup_publisher(self._prim, self._output_component, self._output_channel)

            prim_paths = self._prim.CreatePrimsRel()
            if self._prims_rel is not None:
                for path in self._prims_rel:
                    prim_paths.AddTarget(path)

            self._prim.CreateDepthLimitsAttr().Set(self._depth_limits)
            self._prim.CreatePrimRegexAttr().Set(self._prim_regex)
        return self._prim

    def undo(self):
        # undo must be defined even if empty
        pass


omni.kit.commands.register_all_commands_in_module(__name__)
