import omni.kit.commands
import omni.isaac.RosBridgeSchema as ROSSchema
from pxr import Gf
import carb


def get_path(stage, path: str, parent=None) -> str:
    if parent:
        path = omni.usd.get_stage_next_free_path(stage, parent + path, False)
    else:
        path = omni.usd.get_stage_next_free_path(stage, path, True)
    return path


def setup_base_prim(prim, enabled):
    prim.CreateRosNodePrefixAttr("")
    prim.CreateEnabledAttr(enabled)


# this command is used to create each REB prim, it also handles undo so that each individual prim command doesn't have to
class RosBridgeCreatePrim(omni.kit.commands.Command):
    def __init__(self, path: str, parent: str, enabled: bool, scehma_type):
        self._path = path
        self._parent = parent
        self._scehma_type = scehma_type
        self._prim_path = None
        self._enabled = enabled
        pass

    def do(self):
        self._stage = omni.usd.get_context().get_stage()
        # make prim path unique
        self._prim_path = get_path(self._stage, self._path, self._parent)
        self._prim = self._scehma_type.Define(self._stage, self._prim_path)
        setup_base_prim(self._prim, self._enabled)
        return self._prim

    def undo(self):
        if self._prim_path is not None:
            return self._stage.RemovePrim(self._prim_path)


class ROSBridgeCreateClock(omni.kit.commands.Command):
    def __init__(
        self,
        path: str = "/ROS_Clock",
        parent=None,
        enabled: bool = True,
        queue_size: int = 10,
        clock_topic: str = "/clock",
    ):
        # condensed way to copy all input arguments into self with an underscore prefix
        for name, value in vars().items():
            if name != "self":
                setattr(self, f"_{name}", value)
        self._prim = None
        pass

    def do(self) -> bool:
        success, self._prim = omni.kit.commands.execute(
            "RosBridgeCreatePrim",
            path=self._path,
            parent=self._parent,
            enabled=self._enabled,
            scehma_type=ROSSchema.RosClock,
        )
        if success and self._prim:
            self._prim.CreateClockPubTopicAttr(self._clock_topic)
            self._prim.CreateQueueSizeAttr(self._queue_size)
        return self._prim

    def undo(self):
        pass


class ROSBridgeCreateCamera(omni.kit.commands.Command):
    def __init__(
        self,
        path: str = "/ROS_Camera",
        parent=None,
        enabled: bool = True,
        queue_size: int = 10,
        frame_id: str = "sim_camera",
        camera_info_topic: str = "/camera_info",
        rgb_enabled: bool = True,
        rgb_topic: str = "/rgb",
        depth_enabled: bool = False,
        depth_topic: str = "/depth",
        segmentation_enabled: bool = False,
        semantic_topic: str = "/semantic",
        instance_topic: str = "/instance",
        label_topic: str = "/label",
        bbox2d_enabled: bool = False,
        bbox2d_topic: str = "/bbox_2d",
        bbox3d_enabled: bool = False,
        bbox3d_topic: str = "/bbox_3d",
        camera_prim_rel=None,
        resolution: Gf.Vec2i = Gf.Vec2i(1280, 720),
    ):
        # condensed way to copy all input arguments into self with an underscore prefix
        for name, value in vars().items():
            if name != "self":
                setattr(self, f"_{name}", value)
        self._prim = None
        pass

    def do(self) -> bool:
        success, self._prim = omni.kit.commands.execute(
            "RosBridgeCreatePrim",
            path=self._path,
            parent=self._parent,
            enabled=self._enabled,
            scehma_type=ROSSchema.RosCamera,
        )
        if success and self._prim:
            rel_paths = self._prim.CreateCameraPrimRel()
            if self._camera_prim_rel is not None:
                if len(self._camera_prim_rel) == 1:
                    rel_paths.AddTarget(self._camera_prim_rel[0])
                else:
                    carb.log_warn("only one camera prim rel target can be specified")
            self._prim.CreateResolutionAttr(self._resolution)

            self._prim.CreateCameraInfoPubTopicAttr(self._camera_info_topic)
            self._prim.CreateRgbPubTopicAttr(self._rgb_topic)
            self._prim.CreateDepthPubTopicAttr(self._depth_topic)
            self._prim.CreateFrameIdAttr(self._frame_id)
            self._prim.CreateSemanticPubTopicAttr(self._semantic_topic)
            self._prim.CreateInstancePubTopicAttr(self._instance_topic)
            self._prim.CreateLabelPubTopicAttr(self._label_topic)
            self._prim.CreateBoundingBox2DPubTopicAttr(self._bbox2d_topic)
            self._prim.CreateBoundingBox3DPubTopicAttr(self._bbox3d_topic)

            self._prim.CreateBoundingBox2DClassListAttr("")
            self._prim.CreateBoundingBox3DClassListAttr("")

            self._prim.CreateRgbEnabledAttr(self._rgb_enabled)
            self._prim.CreateDepthEnabledAttr(self._depth_enabled)
            self._prim.CreateSegmentationEnabledAttr(self._segmentation_enabled)
            self._prim.CreateBoundingBox2DEnabledAttr(self._bbox2d_enabled)
            self._prim.CreateBoundingBox3DEnabledAttr(self._bbox3d_enabled)
            self._prim.CreateQueueSizeAttr(self._queue_size)
        return self._prim

    def undo(self):
        pass


class ROSBridgeCreateJointState(omni.kit.commands.Command):
    def __init__(
        self,
        path: str = "/ROS_JointState",
        parent=None,
        enabled: bool = True,
        queue_size: int = 0,
        state_topic: str = "/joint_states",
        command_topic: str = "/joint_command",
        articulation_prim_rel=None,
    ):
        # condensed way to copy all input arguments into self with an underscore prefix
        for name, value in vars().items():
            if name != "self":
                setattr(self, f"_{name}", value)
        self._prim = None
        pass

    def do(self) -> bool:
        success, self._prim = omni.kit.commands.execute(
            "RosBridgeCreatePrim",
            path=self._path,
            parent=self._parent,
            enabled=self._enabled,
            scehma_type=ROSSchema.RosJointState,
        )
        if success and self._prim:
            self._prim.CreateJointStatePubTopicAttr(self._state_topic)
            self._prim.CreateJointStateSubTopicAttr(self._command_topic)
            rel_paths = self._prim.CreateArticulationPrimRel()
            if self._articulation_prim_rel is not None:
                if len(self._articulation_prim_rel) == 1:
                    rel_paths.AddTarget(self._articulation_prim_rel[0])
                else:
                    carb.log_warn("only one articulation prim rel target can be specified")
            self._prim.CreateQueueSizeAttr(self._queue_size)
        return self._prim

    def undo(self):
        pass


class ROSBridgeCreateLidar(omni.kit.commands.Command):
    def __init__(
        self,
        path: str = "/ROS_Lidar",
        parent=None,
        enabled: bool = True,
        queue_size: int = 10,
        frame_id: str = "sim_lidar",
        laser_scan_topic: str = "/laser_scan",
        point_cloud_enabled: bool = False,
        point_cloud_topic: str = "/point_cloud",
        lidar_prim_rel=None,
    ):
        # condensed way to copy all input arguments into self with an underscore prefix
        for name, value in vars().items():
            if name != "self":
                setattr(self, f"_{name}", value)
        self._prim = None
        pass

    def do(self) -> bool:
        success, self._prim = omni.kit.commands.execute(
            "RosBridgeCreatePrim",
            path=self._path,
            parent=self._parent,
            enabled=self._enabled,
            scehma_type=ROSSchema.RosLidar,
        )
        if success and self._prim:
            self._prim.CreateLaserScanPubTopicAttr(self._laser_scan_topic)
            rel_paths = self._prim.CreateLidarPrimRel()
            if self._lidar_prim_rel is not None:
                if len(self._lidar_prim_rel) == 1:
                    rel_paths.AddTarget(self._lidar_prim_rel[0])
                else:
                    carb.log_warn("only one lidar prim rel target can be specified")
            self._prim.CreateFrameIdAttr(self._frame_id)
            self._prim.CreatePointCloudPubTopicAttr(self._point_cloud_topic)
            self._prim.CreatePointCloudEnabledAttr(self._point_cloud_enabled)

            self._prim.CreateQueueSizeAttr(self._queue_size)
        return self._prim

    def undo(self):
        pass


class ROSBridgeCreatePoseTree(omni.kit.commands.Command):
    def __init__(
        self,
        path: str = "/ROS_PoseTree",
        parent=None,
        enabled: bool = True,
        queue_size: int = 0,
        topic: str = "/tf",
        target_prims_rel=None,
    ):
        # condensed way to copy all input arguments into self with an underscore prefix
        for name, value in vars().items():
            if name != "self":
                setattr(self, f"_{name}", value)
        self._prim = None
        pass

    def do(self) -> bool:
        success, self._prim = omni.kit.commands.execute(
            "RosBridgeCreatePrim",
            path=self._path,
            parent=self._parent,
            enabled=self._enabled,
            scehma_type=ROSSchema.RosPoseTree,
        )
        if success and self._prim:
            self._prim.CreatePoseTreePubTopicAttr(self._topic)
            target_paths = self._prim.CreateTargetPrimsRel()
            if self._target_prims_rel is not None:
                for path in self._target_prims_rel:
                    target_paths.AddTarget(path)
            self._prim.CreateQueueSizeAttr(self._queue_size)
        return self._prim

    def undo(self):
        pass


class ROSBridgeCreateTeleport(omni.kit.commands.Command):
    def __init__(
        self,
        path: str = "/ROS_Teleport",
        parent=None,
        enabled: bool = True,
        service_topic: str = "/teleport_pos",
        teleport_prims_rel=None,
    ):
        # condensed way to copy all input arguments into self with an underscore prefix
        for name, value in vars().items():
            if name != "self":
                setattr(self, f"_{name}", value)
        self._prim = None
        pass

    def do(self) -> bool:
        success, self._prim = omni.kit.commands.execute(
            "RosBridgeCreatePrim",
            path=self._path,
            parent=self._parent,
            enabled=self._enabled,
            scehma_type=ROSSchema.RosTeleport,
        )
        if success and self._prim:
            self._prim.CreatePoseSrvTopicAttr(self._service_topic)
            rel_paths = self._prim.CreateTeleportPrimsRel()
            if self._teleport_prims_rel is not None:
                for path in self._teleport_prims_rel:
                    rel_paths.AddTarget(path)
        return self._prim

    def undo(self):
        pass


class ROSBridgeCreateSurfaceGripper(omni.kit.commands.Command):
    def __init__(
        self,
        path: str = "/ROS_SurfaceGripper",
        parent=None,
        enabled: bool = True,
        queue_size: int = 0,
        state_topic: str = "/gripper_state",
        command_topic: str = "/gripper_command",
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
        self._prim = None
        pass

    def do(self) -> bool:
        success, self._prim = omni.kit.commands.execute(
            "RosBridgeCreatePrim",
            path=self._path,
            parent=self._parent,
            enabled=self._enabled,
            scehma_type=ROSSchema.RosSurfaceGripper,
        )
        if success and self._prim:
            self._prim.CreateSurfaceGripperPubTopicAttr(self._state_topic)
            self._prim.CreateSurfaceGripperSubTopicAttr(self._command_topic)
            self._prim.CreateQueueSizeAttr(self._queue_size)
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
        pass


class ROSBridgeCreateDifferentialBase(omni.kit.commands.Command):
    def __init__(
        self,
        path: str = "/ROS_DifferentialBase",
        parent=None,
        enabled: bool = True,
        queue_size: int = 0,
        chassis_prim_rel=None,
        left_wheel_joint_name: str = "",
        right_wheel_joint_name: str = "",
        robot_front: Gf.Vec2f = Gf.Vec3f(1, 0, 0),
        wheel_radius: float = 0.1,
        wheel_base: float = 0.5,
        max_speed: Gf.Vec2f = Gf.Vec2f(1.5, 1.0),
        time_without_command: float = 0.2,
        acceleration_smoothing: float = 1.0,
        state_topic: str = "/odom",
        command_topic: str = "/cmd_vel",
        odom_frame_id: str = "odom",
        base_frame_id: str = "base_link",
    ):
        # condensed way to copy all input arguments into self with an underscore prefix
        for name, value in vars().items():
            if name != "self":
                setattr(self, f"_{name}", value)
        self._prim = None
        pass

    def do(self) -> bool:
        success, self._prim = omni.kit.commands.execute(
            "RosBridgeCreatePrim",
            path=self._path,
            parent=self._parent,
            enabled=self._enabled,
            scehma_type=ROSSchema.RosDifferentialBase,
        )
        if success and self._prim:
            self._prim.CreateStatePubTopicAttr(self._state_topic)
            self._prim.CreateCommandSubTopicAttr(self._command_topic)
            self._prim.CreateQueueSizeAttr(self._queue_size)
            self._prim.CreateOdomFrameIdAttr(self._odom_frame_id)
            self._prim.CreateBaseFrameIdAttr(self._base_frame_id)
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
        pass


omni.kit.commands.register_all_commands_in_module(__name__)
