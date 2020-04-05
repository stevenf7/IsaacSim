import carb
import omni.kit.editor
import omni.kit.commands
import omni.kit.ui
from pxr import Usd, UsdGeom, Sdf, Gf, Tf

ADD_DIFFERENTIALBASE_SCENE_MENU_ITEM = "Create/Isaac/Robot Engine/Differential Base"
ADD_JOINTCONTROL_SCENE_MENU_ITEM = "Create/Isaac/Robot Engine/Joint Control"
ADD_SCISSORLIFT_SCENE_MENU_ITEM = "Create/Isaac/Robot Engine/Scissor Lift"
ADD_SURFACEGRIPPER_SCENE_MENU_ITEM = "Create/Isaac/Robot Engine/Surface Gripper"
ADD_SCENARIOFROMMESSAGE_SCENE_MENU_ITEM = "Create/Isaac/Robot Engine/Scenario From Message"
ADD_RIGIDBODYSINK_SCENE_MENU_ITEM = "Create/Isaac/Robot Engine/Rigid Body Sink"
ADD_LIDAR_SCENE_MENU_ITEM = "Create/Isaac/Robot Engine/Lidar"
ADD_CAMERA_SCENE_MENU_ITEM = "Create/Isaac/Robot Engine/Camera"


class RobotEngineBridgeMenu:
    def __init__(self):
        self._usd_context = omni.usd.get_context()
        self._menus = []

        editor_menu = omni.kit.ui.get_editor_menu()

        # add
        # self._menus.append(editor_menu.add_item(ADD_BRIDGE_NODE_MENU_ITEM, self._on_scene_menu_click))
        self._menus.append(editor_menu.add_item(ADD_DIFFERENTIALBASE_SCENE_MENU_ITEM, self._on_scene_menu_click))
        self._menus.append(editor_menu.add_item(ADD_JOINTCONTROL_SCENE_MENU_ITEM, self._on_scene_menu_click))
        self._menus.append(editor_menu.add_item(ADD_SCISSORLIFT_SCENE_MENU_ITEM, self._on_scene_menu_click))
        self._menus.append(editor_menu.add_item(ADD_SURFACEGRIPPER_SCENE_MENU_ITEM, self._on_scene_menu_click))
        self._menus.append(editor_menu.add_item(ADD_SCENARIOFROMMESSAGE_SCENE_MENU_ITEM, self._on_scene_menu_click))
        self._menus.append(editor_menu.add_item(ADD_RIGIDBODYSINK_SCENE_MENU_ITEM, self._on_scene_menu_click))
        self._menus.append(editor_menu.add_item(ADD_LIDAR_SCENE_MENU_ITEM, self._on_scene_menu_click))
        self._menus.append(editor_menu.add_item(ADD_CAMERA_SCENE_MENU_ITEM, self._on_scene_menu_click))

    def add_differential_base(self, parent=None):
        if parent:
            path = omni.kit.utils.get_stage_next_free_path(self._stage, parent + "/DifferentialBaseSimulator", False)
        else:
            path = omni.kit.utils.get_stage_next_free_path(self._stage, "/DifferentialBaseSimulator", True)

        prim = self._stage.DefinePrim(path, "RobotEngine_DifferentialBaseSimulator")
        prim.CreateAttribute("nodeName", Sdf.ValueTypeNames.String).Set(str("interface"))

        prim.CreateAttribute("inputComponent", Sdf.ValueTypeNames.String).Set(str("input"))
        prim.CreateAttribute("commandChannelName", Sdf.ValueTypeNames.String).Set(str("base_command"))
        prim.CreateAttribute("outputComponent", Sdf.ValueTypeNames.String).Set(str("output"))
        prim.CreateAttribute("stateChannelName", Sdf.ValueTypeNames.String).Set(str("base_state"))

        prim.CreateAttribute("chassisPath", Sdf.ValueTypeNames.String)
        prim.CreateAttribute("leftWheelName", Sdf.ValueTypeNames.String)
        prim.CreateAttribute("rightWheelName", Sdf.ValueTypeNames.String)

        prim.CreateAttribute("robotFront", Sdf.ValueTypeNames.Double3).Set((1, 0, 0))
        prim.CreateAttribute("maxSpeed", Sdf.ValueTypeNames.Double2).Set((1.5, 1.0))
        prim.CreateAttribute("maxMotorTorque", Sdf.ValueTypeNames.Float).Set(float(10.0))
        prim.CreateAttribute("proportionalGain", Sdf.ValueTypeNames.Float).Set(float(100.0))
        prim.CreateAttribute("brakeTorque", Sdf.ValueTypeNames.Float).Set(float(100.0))
        prim.CreateAttribute("accelerationSmoothing", Sdf.ValueTypeNames.Float).Set(float(1.0))
        prim.CreateAttribute("useProprotionalDriver", Sdf.ValueTypeNames.Bool).Set(bool(True))
        pass

    def add_joint_control(self, parent=None):
        if parent:
            path = omni.kit.utils.get_stage_next_free_path(self._stage, parent + "/JointControl", False)
        else:
            path = omni.kit.utils.get_stage_next_free_path(self._stage, "/JointControl", True)

        prim = self._stage.DefinePrim(path, "RobotEngine_JointControl")
        prim.CreateAttribute("nodeName", Sdf.ValueTypeNames.String).Set(str("interface"))

        prim.CreateAttribute("inputComponent", Sdf.ValueTypeNames.String).Set(str("input"))
        prim.CreateAttribute("outputComponent", Sdf.ValueTypeNames.String).Set(str("output"))
        prim.CreateAttribute("jointControlChannelName", Sdf.ValueTypeNames.String).Set(str("joint_position"))
        prim.CreateAttribute("jointStateChannelName", Sdf.ValueTypeNames.String).Set(str("joint_state"))
        prim.CreateAttribute("articulationPath", Sdf.ValueTypeNames.String).Set(str("/"))
        pass

    def add_scissor_lift_simulator(self, parent=None):
        if parent:
            path = omni.kit.utils.get_stage_next_free_path(self._stage, parent + "/ScissorLiftSimulator", False)
        else:
            path = omni.kit.utils.get_stage_next_free_path(self._stage, "/ScissorLiftSimulator", True)

        prim = self._stage.DefinePrim(path, "RobotEngine_ScissorLiftSimulator")
        prim.CreateAttribute("nodeName", Sdf.ValueTypeNames.String).Set(str("interface"))

        prim.CreateAttribute("inputComponent", Sdf.ValueTypeNames.String).Set(str("input"))
        prim.CreateAttribute("outputComponent", Sdf.ValueTypeNames.String).Set(str("output"))
        prim.CreateAttribute("commandChannelName", Sdf.ValueTypeNames.String).Set(str("lift_command"))
        prim.CreateAttribute("stateChannelName", Sdf.ValueTypeNames.String).Set(str("lift_state"))
        prim.CreateAttribute("liftJointName", Sdf.ValueTypeNames.String).Set(str("lift_joint"))
        prim.CreateAttribute("articulationPath", Sdf.ValueTypeNames.String).Set(str("/"))
        pass

    def add_surface_gripper(self, parent=None):
        if parent:
            path = omni.kit.utils.get_stage_next_free_path(self._stage, parent + "/SurfaceGripper", False)
        else:
            path = omni.kit.utils.get_stage_next_free_path(self._stage, "/SurfaceGripper", True)

        prim = self._stage.DefinePrim(path, "RobotEngine_SurfaceGripper")

        prim.CreateAttribute("nodeName", Sdf.ValueTypeNames.String).Set(str("interface"))
        prim.CreateAttribute("inputComponent", Sdf.ValueTypeNames.String).Set(str("input"))
        prim.CreateAttribute("outputComponent", Sdf.ValueTypeNames.String).Set(str("output"))

        prim.CreateAttribute("gripperControlChannelName", Sdf.ValueTypeNames.String).Set(str("io_command"))
        prim.CreateAttribute("gripperStateChannelName", Sdf.ValueTypeNames.String).Set(str("io_state"))
        prim.CreateAttribute("d6JointPath", Sdf.ValueTypeNames.String).Set(str("/"))
        prim.CreateAttribute("parentPath", Sdf.ValueTypeNames.String).Set(str("/"))
        prim.CreateAttribute("gripThreshold", Sdf.ValueTypeNames.Float).Set(float(1))
        prim.CreateAttribute("forceLimit", Sdf.ValueTypeNames.Float).Set(float(1e7))
        prim.CreateAttribute("offsetPosition", Sdf.ValueTypeNames.Float3).Set(Gf.Vec3f(0, 0, 0))
        prim.CreateAttribute("offsetRotation", Sdf.ValueTypeNames.Quatf).Set(Gf.Quatf(1.0))
        pass

    def add_scenario_from_message(self, parent=None):
        if parent:
            path = omni.kit.utils.get_stage_next_free_path(self._stage, parent + "/ScenarioFromMessage", False)
        else:
            path = omni.kit.utils.get_stage_next_free_path(self._stage, "/ScenarioFromMessage", True)

        prim = self._stage.DefinePrim(path, "RobotEngine_ScenarioFromMessage")
        prim.CreateAttribute("nodeName", Sdf.ValueTypeNames.String).Set(str("interface"))

        prim.CreateAttribute("inputComponent", Sdf.ValueTypeNames.String).Set(str("input"))
        prim.CreateAttribute("requestChannelName", Sdf.ValueTypeNames.String).Set(str("scenario_actors"))

        prim.CreateAttribute("teleportInputComponent", Sdf.ValueTypeNames.String).Set(str("input"))
        prim.CreateAttribute("teleportChannelName", Sdf.ValueTypeNames.String).Set(str("teleport"))

        prim.CreateAttribute("rigidBodyOutputComponent", Sdf.ValueTypeNames.String).Set(str("output"))
        prim.CreateAttribute("rigidBodyChannelName", Sdf.ValueTypeNames.String).Set(str("bodies"))
        pass

    def add_rigid_body_sink(self, parent=None):
        if parent:
            path = omni.kit.utils.get_stage_next_free_path(self._stage, parent + "/RigidBodiesSink", False)
        else:
            path = omni.kit.utils.get_stage_next_free_path(self._stage, "/RigidBodiesSink", True)

        prim = self._stage.DefinePrim(path, "RobotEngine_RigidBodiesSink")
        prim.CreateAttribute("nodeName", Sdf.ValueTypeNames.String).Set(str("interface"))

        prim.CreateAttribute("rigidBodyOutputComponent", Sdf.ValueTypeNames.String).Set(str("output"))
        prim.CreateAttribute("rigidBodyChannelName", Sdf.ValueTypeNames.String).Set(str("bodies"))
        prim.CreateAttribute("rigidBodyPrimPaths", Sdf.ValueTypeNames.String).Set(str(""))
        pass

    def add_lidar(self, parent=None):
        if parent:
            path = omni.kit.utils.get_stage_next_free_path(self._stage, parent + "/Lidar", False)
        else:
            path = omni.kit.utils.get_stage_next_free_path(self._stage, "/Lidar", True)

        prim = self._stage.DefinePrim(path, "RobotEngine_Lidar")
        prim.CreateAttribute("nodeName", Sdf.ValueTypeNames.String).Set(str("interface"))

        prim.CreateAttribute("outputComponent", Sdf.ValueTypeNames.String).Set(str("output"))
        prim.CreateAttribute("scanChannelName", Sdf.ValueTypeNames.String).Set(str("rangescan"))
        prim.CreateAttribute("lidarPath", Sdf.ValueTypeNames.String).Set(str("/"))
        pass

    def add_camera(self, parent=None):
        if parent:
            path = omni.kit.utils.get_stage_next_free_path(self._stage, parent + "/Camera", False)
        else:
            path = omni.kit.utils.get_stage_next_free_path(self._stage, "/Camera", True)

        prim = self._stage.DefinePrim(path, "RobotEngine_Camera")
        prim.CreateAttribute("nodeName", Sdf.ValueTypeNames.String).Set(str("interface"))

        prim.CreateAttribute("outputComponent", Sdf.ValueTypeNames.String).Set(str("output"))
        prim.CreateAttribute("channelName", Sdf.ValueTypeNames.String).Set(str("color"))
        prim.CreateAttribute("depthOutputComponent", Sdf.ValueTypeNames.String).Set(str("output"))
        prim.CreateAttribute("depthChannelName", Sdf.ValueTypeNames.String).Set(str("depth"))

        prim.CreateAttribute("enableRgb", Sdf.ValueTypeNames.Bool).Set(bool(False))
        prim.CreateAttribute("enableDepth", Sdf.ValueTypeNames.Bool).Set(bool(False))
        prim.CreateAttribute("enableSegmentation", Sdf.ValueTypeNames.Bool).Set(bool(False))
        pass

    def _on_scene_menu_click(self, menu, value):
        self._stage = self._usd_context.get_stage()
        selectedPrims = self._usd_context.get_selection().get_selected_prim_paths()
        # upAxis = UsdGeom.GetStageUpAxis(stage)
        # scaleFactor = getUnitScaleFactor(stage)
        if len(selectedPrims) > 0:
            curr_prim = selectedPrims[-1]
        else:
            curr_prim = None

        if menu == ADD_DIFFERENTIALBASE_SCENE_MENU_ITEM:
            self.add_differential_base(curr_prim)
        elif menu == ADD_JOINTCONTROL_SCENE_MENU_ITEM:
            self.add_joint_control(curr_prim)
        elif menu == ADD_SCISSORLIFT_SCENE_MENU_ITEM:
            self.add_scissor_lift_simulator(curr_prim)
        elif menu == ADD_SURFACEGRIPPER_SCENE_MENU_ITEM:
            self.add_surface_gripper(curr_prim)
        elif menu == ADD_SCENARIOFROMMESSAGE_SCENE_MENU_ITEM:
            self.add_scenario_from_message(curr_prim)
        elif menu == ADD_RIGIDBODYSINK_SCENE_MENU_ITEM:
            self.add_rigid_body_sink(curr_prim)
        elif menu == ADD_LIDAR_SCENE_MENU_ITEM:
            self.add_lidar(curr_prim)
        elif menu == ADD_CAMERA_SCENE_MENU_ITEM:
            self.add_camera(curr_prim)

    def shutdown(self):
        self._menus = None
