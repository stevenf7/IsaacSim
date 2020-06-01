import carb
import omni.kit.editor
import omni.kit.commands
import omni.kit.ui
from pxr import Usd, UsdGeom, Sdf, Gf, Tf

import omni.isaac.RosBridgeSchema as ROSSchema


ADD_ROS_CLOCK = "Create/Isaac/ROS/Clock"
ADD_ROS_CAMERA = "Create/Isaac/ROS/Camera"
ADD_ROS_JOINT_STATE = "Create/Isaac/ROS/Joint State"
ADD_ROS_LIDAR = "Create/Isaac/ROS/Lidar"
ADD_ROS_POSE_TREE = "Create/Isaac/ROS/Pose Tree"
ADD_ROS_SINK = "Create/Isaac/ROS/Sink"
ADD_ROS_TELEPORT = "Create/Isaac/ROS/Teleport"


class RosBridgeMenu:
    def __init__(self):
        self._usd_context = omni.usd.get_context()
        self._menus = []

        editor_menu = omni.kit.ui.get_editor_menu()
        self._menus.append(editor_menu.add_item(ADD_ROS_CLOCK, self._on_scene_menu_click))
        self._menus.append(editor_menu.add_item(ADD_ROS_CAMERA, self._on_scene_menu_click))
        self._menus.append(editor_menu.add_item(ADD_ROS_JOINT_STATE, self._on_scene_menu_click))
        self._menus.append(editor_menu.add_item(ADD_ROS_LIDAR, self._on_scene_menu_click))
        self._menus.append(editor_menu.add_item(ADD_ROS_POSE_TREE, self._on_scene_menu_click))
        # self._menus.append(editor_menu.add_item(ADD_ROS_SINK, self._on_scene_menu_click))
        # self._menus.append(editor_menu.add_item(ADD_ROS_TELEPORT, self._on_scene_menu_click))

    def setup_base_prim(self, prim):
        prim.CreateRosNodePrefixAttr("")
        prim.CreateEnabledAttr(True)

    def get_path(self, name):
        selectedPrims = self._usd_context.get_selection().get_selected_prim_paths()
        # upAxis = UsdGeom.GetStageUpAxis(stage)
        # scaleFactor = getUnitScaleFactor(stage)
        if len(selectedPrims) > 0:
            curr_prim = selectedPrims[-1]
        else:
            curr_prim = None

        if curr_prim:
            return omni.kit.utils.get_stage_next_free_path(self._stage, curr_prim + name, False)
        else:
            return omni.kit.utils.get_stage_next_free_path(self._stage, name, True)

    def add_camera(self):
        prim = ROSSchema.RosCamera.Define(self._stage, self.get_path("/ROS_Camera"))
        self.setup_base_prim(prim)
        prim.CreateCameraInfoPubTopicAttr("/camera_info")
        prim.CreateRgbPubTopicAttr("/rgb")
        prim.CreateDepthPubTopicAttr("/depth")
        prim.CreateFrameIdAttr("/sim_camera")

        prim.CreateRgbEnabledAttr(False)
        prim.CreateDepthEnabledAttr(False)
        prim.CreateQueueSizeAttr(10)
        pass

    def add_clock(self):
        prim = ROSSchema.RosClock.Define(self._stage, self.get_path("/ROS_Clock"))
        self.setup_base_prim(prim)
        prim.CreateClockPubTopicAttr("/clock")
        prim.CreateSimTimeAttr(True)
        prim.CreateQueueSizeAttr(0)
        pass

    def add_joint_state(self):
        prim = ROSSchema.RosJointState.Define(self._stage, self.get_path("/ROS_JointState"))
        self.setup_base_prim(prim)
        prim.CreateJointStatePubTopicAttr("/joint_state")
        prim.CreateJointStateSubTopicAttr("/joint_command")
        prim.CreateArticulationPrimRel()
        prim.CreateQueueSizeAttr(0)
        pass

    def add_lidar(self):
        prim = ROSSchema.RosLidar.Define(self._stage, self.get_path("/ROS_Lidar"))
        self.setup_base_prim(prim)
        prim.CreateLaserScanPubTopicAttr("/laser_scan")
        prim.CreateLidarPrimRel()
        prim.CreateFrameIdAttr("/sim_lidar")
        prim.CreateQueueSizeAttr(0)
        pass

    def add_pose_tree(self):
        prim = ROSSchema.RosPoseTree.Define(self._stage, self.get_path("/ROS_PoseTree"))
        self.setup_base_prim(prim)
        prim.CreatePoseTreePubTopicAttr("/tf")
        prim.CreateTargetPrimsRel()
        prim.CreateQueueSizeAttr(0)

        pass

    def add_sink(self):
        prim = ROSSchema.RosSink.Define(self._stage, self.get_path("/ROS_Sink"))
        self.setup_base_prim(prim)
        prim.CreatePosePubTopicAttr("/body_pos")
        prim.CreateVelPubTopicAttr("/body_vel")
        prim.CreateAccPubTopicAttr("/body_acc")

        prim.CreateTargetPrimsRel()
        prim.CreateQueueSizeAttr(0)

        pass

    def add_teleport(self):
        prim = ROSSchema.RosTeleport.Define(self._stage, self.get_path("/ROS_Teleport"))
        self.setup_base_prim(prim)
        prim.CreatePoseSubTopicAttr("/teleport_pos")
        prim.CreateTeleportPrimsRel()
        prim.CreateQueueSizeAttr(0)

        pass

    def _on_scene_menu_click(self, menu, value):
        self._stage = self._usd_context.get_stage()

        if menu == ADD_ROS_CLOCK:
            self.add_clock()
        elif menu == ADD_ROS_CAMERA:
            self.add_camera()
        elif menu == ADD_ROS_JOINT_STATE:
            self.add_joint_state()
        elif menu == ADD_ROS_LIDAR:
            self.add_lidar()
        elif menu == ADD_ROS_POSE_TREE:
            self.add_pose_tree()
        # elif menu == ADD_ROS_SINK:
        #     self.add_sink()
        # elif menu == ADD_ROS_TELEPORT:
        #     self.add_teleport()

    def shutdown(self):
        self._menus = None
