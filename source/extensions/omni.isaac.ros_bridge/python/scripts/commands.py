import omni.kit.commands
import omni.isaac.RosBridgeSchema as ROSSchema
from pxr import Gf


def get_path(stage, path: str, parent=None) -> str:
    if parent:
        path = omni.usd.get_stage_next_free_path(stage, parent + path, False)
    else:
        path = omni.usd.get_stage_next_free_path(stage, path, True)
    return path


def setup_base_prim(prim):
    prim.CreateRosNodePrefixAttr("")
    prim.CreateEnabledAttr(True)


# this command is used to create each REB prim, it also handles undo so that each individual prim command doesn't have to
class CreateROSBridgePrimCommand(omni.kit.commands.Command):
    def __init__(self, path: str, parent: str, scehma_type):
        self._path = path
        self._parent = parent
        self._scehma_type = scehma_type
        self._prim_path = None
        pass

    def do(self):
        self._stage = omni.usd.get_context().get_stage()
        # make prim path unique
        self._prim_path = get_path(self._stage, self._path, self._parent)
        self._prim = self._scehma_type.Define(self._stage, self._prim_path)
        setup_base_prim(self._prim)
        return self._prim

    def undo(self):
        if self._prim_path is not None:
            return self._stage.RemovePrim(self._prim_path)


class CreateROSBridgeClockCommand(omni.kit.commands.Command):
    def __init__(self, path: str = "/ROS_Clock", parent=None):
        # condensed way to copy all input arguments into self with an underscore prefix
        for name, value in vars().items():
            if name != "self":
                setattr(self, f"_{name}", value)
        self._prim = None
        pass

    def do(self) -> bool:
        success, self._prim = omni.kit.commands.execute(
            "CreateROSBridgePrimCommand", path=self._path, parent=self._parent, scehma_type=ROSSchema.RosClock
        )
        if success and self._prim:
            self._prim.CreateClockPubTopicAttr("/clock")
            self._prim.CreateQueueSizeAttr(0)
        return self._prim

    def undo(self):
        pass


class CreateROSBridgeCameraCommand(omni.kit.commands.Command):
    def __init__(
        self, path: str = "/ROS_Camera", parent=None, camera_prim_rel=None, use_existing_viewport: bool = True
    ):
        # condensed way to copy all input arguments into self with an underscore prefix
        for name, value in vars().items():
            if name != "self":
                setattr(self, f"_{name}", value)
        self._prim = None
        pass

    def do(self) -> bool:
        success, self._prim = omni.kit.commands.execute(
            "CreateROSBridgePrimCommand", path=self._path, parent=self._parent, scehma_type=ROSSchema.RosCamera
        )
        if success and self._prim:
            rel_paths = self._prim.CreateCameraPrimRel()
            if self._camera_prim_rel is not None:
                if len(self._camera_prim_rel) == 1:
                    rel_paths.AddTarget(self._camera_prim_rel[0])
                else:
                    carb.log_warn("only one camera prim rel target can be specified")
            self._prim.CreateUseExistingViewportAttr(self._use_existing_viewport)

            self._prim.CreateCameraInfoPubTopicAttr("/camera_info")
            self._prim.CreateRgbPubTopicAttr("/rgb")
            self._prim.CreateDepthPubTopicAttr("/depth")
            self._prim.CreateFrameIdAttr("/sim_camera")
            self._prim.CreateSemanticPubTopicAttr("/semantic")
            self._prim.CreateInstancePubTopicAttr("/instance")
            self._prim.CreateLabelPubTopicAttr("/label")
            self._prim.CreateBoundingBox2DPubTopicAttr("/bbox_2d")
            self._prim.CreateBoundingBox3DPubTopicAttr("/bbox_3d")

            self._prim.CreateBoundingBox2DClassListAttr("")
            self._prim.CreateBoundingBox3DClassListAttr("")

            self._prim.CreateRgbEnabledAttr(False)
            self._prim.CreateDepthEnabledAttr(False)
            self._prim.CreateSegmentationEnabledAttr(False)
            self._prim.CreateBoundingBox2DEnabledAttr(False)
            self._prim.CreateBoundingBox3DEnabledAttr(False)
            self._prim.CreateQueueSizeAttr(10)
        return self._prim

    def undo(self):
        pass


class CreateROSBridgeJointStateCommand(omni.kit.commands.Command):
    def __init__(self, path: str = "/ROS_JointState", parent=None):
        # condensed way to copy all input arguments into self with an underscore prefix
        for name, value in vars().items():
            if name != "self":
                setattr(self, f"_{name}", value)
        self._prim = None
        pass

    def do(self) -> bool:
        success, self._prim = omni.kit.commands.execute(
            "CreateROSBridgePrimCommand", path=self._path, parent=self._parent, scehma_type=ROSSchema.RosJointState
        )
        if success and self._prim:
            self._prim.CreateJointStatePubTopicAttr("/joint_state")
            self._prim.CreateJointStateSubTopicAttr("/joint_command")
            self._prim.CreateArticulationPrimRel()
            self._prim.CreateQueueSizeAttr(0)
        return self._prim

    def undo(self):
        pass


class CreateROSBridgeLidarCommand(omni.kit.commands.Command):
    def __init__(self, path: str = "/ROS_Lidar", parent=None):
        # condensed way to copy all input arguments into self with an underscore prefix
        for name, value in vars().items():
            if name != "self":
                setattr(self, f"_{name}", value)
        self._prim = None
        pass

    def do(self) -> bool:
        success, self._prim = omni.kit.commands.execute(
            "CreateROSBridgePrimCommand", path=self._path, parent=self._parent, scehma_type=ROSSchema.RosLidar
        )
        if success and self._prim:
            self._prim.CreateLaserScanPubTopicAttr("/laser_scan")
            self._prim.CreateLidarPrimRel()
            self._prim.CreateFrameIdAttr("/sim_lidar")
            self._prim.CreatePointCloudPubTopicAttr("/point_cloud")
            self._prim.CreatePointCloudEnabledAttr(False)

            self._prim.CreateQueueSizeAttr(0)
        return self._prim

    def undo(self):
        pass


class CreateROSBridgePoseTreeCommand(omni.kit.commands.Command):
    def __init__(self, path: str = "/ROS_PoseTree", parent=None):
        # condensed way to copy all input arguments into self with an underscore prefix
        for name, value in vars().items():
            if name != "self":
                setattr(self, f"_{name}", value)
        self._prim = None
        pass

    def do(self) -> bool:
        success, self._prim = omni.kit.commands.execute(
            "CreateROSBridgePrimCommand", path=self._path, parent=self._parent, scehma_type=ROSSchema.RosPoseTree
        )
        if success and self._prim:
            self._prim.CreatePoseTreePubTopicAttr("/tf")
            self._prim.CreateTargetPrimsRel()
            self._prim.CreateQueueSizeAttr(0)
        return self._prim

    def undo(self):
        pass


class CreateROSBridgeTeleportCommand(omni.kit.commands.Command):
    def __init__(self, path: str = "/ROS_Teleport", parent=None):
        # condensed way to copy all input arguments into self with an underscore prefix
        for name, value in vars().items():
            if name != "self":
                setattr(self, f"_{name}", value)
        self._prim = None
        pass

    def do(self) -> bool:
        success, self._prim = omni.kit.commands.execute(
            "CreateROSBridgePrimCommand", path=self._path, parent=self._parent, scehma_type=ROSSchema.RosTeleport
        )
        if success and self._prim:
            self._prim.CreatePoseSrvTopicAttr("/teleport_pos")
            self._prim.CreateTeleportPrimsRel()
        return self._prim

    def undo(self):
        pass


class CreateROSBridgeSurfaceGripperCommand(omni.kit.commands.Command):
    def __init__(
        self,
        path: str = "/ROS_SurfaceGripper",
        parent=None,
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
            "CreateROSBridgePrimCommand", path=self._path, parent=self._parent, scehma_type=ROSSchema.RosSurfaceGripper
        )
        if success and self._prim:
            self._prim.CreateSurfaceGripperPubTopicAttr("/gripper_state")
            self._prim.CreateSurfaceGripperSubTopicAttr("/gripper_command")
            self._prim.CreateQueueSizeAttr(0)
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


omni.kit.commands.register_all_commands_in_module(__name__)
