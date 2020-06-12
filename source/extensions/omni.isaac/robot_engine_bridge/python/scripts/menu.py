import carb
import omni.kit.editor
import omni.kit.commands
import omni.kit.ui
from pxr import Usd, UsdGeom, Sdf, Gf, Tf

import omni.isaac.RobotEngineBridgeSchema as REBSchema


ADD_DIFFERENTIALBASE_SCENE_MENU_ITEM = "Create/Isaac/Robot Engine/Differential Base"
ADD_HOLONOMICBASE_SCENE_MENU_ITEM = "Create/Isaac/Robot Engine/Holonomic Base"
ADD_JOINTCONTROL_SCENE_MENU_ITEM = "Create/Isaac/Robot Engine/Joint Control"
ADD_SCISSORLIFT_SCENE_MENU_ITEM = "Create/Isaac/Robot Engine/Scissor Lift"
ADD_SURFACEGRIPPER_SCENE_MENU_ITEM = "Create/Isaac/Robot Engine/Surface Gripper"
ADD_TWOFINGERGRIPPER_SCENE_MENU_ITEM = "Create/Isaac/Robot Engine/Two Finger Gripper"
ADD_RIGIDBODYSINK_SCENE_MENU_ITEM = "Create/Isaac/Robot Engine/Rigid Body Sink"
ADD_TELEPORT_SCENE_MENU_ITEM = "Create/Isaac/Robot Engine/Teleport"
ADD_SCENARIOFROMMESSAGE_SCENE_MENU_ITEM = "Create/Isaac/Robot Engine/Scenario From Message"
ADD_LIDAR_SCENE_MENU_ITEM = "Create/Isaac/Robot Engine/Lidar"
ADD_CAMERA_SCENE_MENU_ITEM = "Create/Isaac/Robot Engine/Camera"
ADD_CONTACTMONITOR_SCENE_MENU_ITEM = "Create/Isaac/Robot Engine/Contact Monitor"


class RobotEngineBridgeMenu:
    def __init__(self):
        self._usd_context = omni.usd.get_context()
        self._menus = []

        editor_menu = omni.kit.ui.get_editor_menu()

        # add
        # self._menus.append(editor_menu.add_item(ADD_BRIDGE_NODE_MENU_ITEM, self._on_scene_menu_click))
        self._menus.append(editor_menu.add_item(ADD_DIFFERENTIALBASE_SCENE_MENU_ITEM, self._on_scene_menu_click))
        self._menus.append(editor_menu.add_item(ADD_HOLONOMICBASE_SCENE_MENU_ITEM, self._on_scene_menu_click))
        self._menus.append(editor_menu.add_item(ADD_JOINTCONTROL_SCENE_MENU_ITEM, self._on_scene_menu_click))
        self._menus.append(editor_menu.add_item(ADD_SCISSORLIFT_SCENE_MENU_ITEM, self._on_scene_menu_click))
        self._menus.append(editor_menu.add_item(ADD_SURFACEGRIPPER_SCENE_MENU_ITEM, self._on_scene_menu_click))
        self._menus.append(editor_menu.add_item(ADD_TWOFINGERGRIPPER_SCENE_MENU_ITEM, self._on_scene_menu_click))
        self._menus.append(editor_menu.add_item(ADD_RIGIDBODYSINK_SCENE_MENU_ITEM, self._on_scene_menu_click))
        self._menus.append(editor_menu.add_item(ADD_TELEPORT_SCENE_MENU_ITEM, self._on_scene_menu_click))
        self._menus.append(editor_menu.add_item(ADD_SCENARIOFROMMESSAGE_SCENE_MENU_ITEM, self._on_scene_menu_click))
        self._menus.append(editor_menu.add_item(ADD_LIDAR_SCENE_MENU_ITEM, self._on_scene_menu_click))
        self._menus.append(editor_menu.add_item(ADD_CAMERA_SCENE_MENU_ITEM, self._on_scene_menu_click))
        self._menus.append(editor_menu.add_item(ADD_CONTACTMONITOR_SCENE_MENU_ITEM, self._on_scene_menu_click))

    def setup_base_prim(self, prim):
        prim.CreateNodeNameAttr("interface")
        prim.CreateEnabledAttr(True)

    def add_differential_base(self, parent=None):
        if parent:
            path = omni.kit.utils.get_stage_next_free_path(self._stage, parent + "/REB_DifferentialBase", False)
        else:
            path = omni.kit.utils.get_stage_next_free_path(self._stage, "/REB_DifferentialBase", True)

        prim = REBSchema.RobotEngineDifferentialBase.Define(self._stage, path)
        self.setup_base_prim(prim)

        prim.CreateInputComponentAttr("input")
        prim.CreateInputChannelAttr("base_command")

        prim.CreateOutputComponentAttr("output")
        prim.CreateOutputChannelAttr("base_state")

        prim.CreateChassisPrimRel()
        prim.CreateLeftWheelJointNameAttr("")
        prim.CreateRightWheelJointNameAttr("")

        prim.CreateRobotFrontAttr((1, 0, 0))
        prim.CreateMaxSpeedAttr((1.5, 1.0))
        prim.CreateMaxTimeWithoutCommandAttr(0.2)
        prim.CreateMaxMotorTorqueAttr(10)
        prim.CreateUseProportionalDriverAttr(True)

        prim.CreateProportionalGainAttr(100)
        prim.CreateBrakeTorqueAttr(100)
        prim.CreateAccelerationSmoothingAttr(1.0)
        pass

    def add_holonomic_base(self, parent=None):
        if parent:
            path = omni.kit.utils.get_stage_next_free_path(self._stage, parent + "/REB_HolonomicBase", False)
        else:
            path = omni.kit.utils.get_stage_next_free_path(self._stage, "/REB_HolonomicBase", True)

        prim = REBSchema.RobotEngineHolonomicBase.Define(self._stage, path)
        self.setup_base_prim(prim)

        prim.CreateInputComponentAttr("input")
        prim.CreateInputChannelAttr("base_command")

        prim.CreateOutputComponentAttr("output")
        prim.CreateOutputChannelAttr("base_state")

        prim.CreateArticulationPrimRel()
        prim.CreateWheel1JointNameAttr("")
        prim.CreateWheel2JointNameAttr("")
        prim.CreateWheel3JointNameAttr("")

        # prim.CreateRobotFrontAttr((1, 0, 0))
        prim.CreateWheelRadiusAttr(0.04)
        prim.CreateWheelBaseAttr(0.125)
        prim.CreateMaxSpeedAttr((1.5, 1.0))
        prim.CreateMaxTimeWithoutCommandAttr(0.2)
        prim.CreateMaxMotorTorqueAttr(10)
        prim.CreateUseProportionalDriverAttr(True)

        prim.CreateProportionalGainAttr(100)
        prim.CreateBrakeTorqueAttr(100)
        prim.CreateAccelerationSmoothingAttr(1.0)
        pass

    def add_joint_control(self, parent=None):
        if parent:
            path = omni.kit.utils.get_stage_next_free_path(self._stage, parent + "/REB_JointControl", False)
        else:
            path = omni.kit.utils.get_stage_next_free_path(self._stage, "/REB_JointControl", True)

        prim = REBSchema.RobotEngineJointControl.Define(self._stage, path)
        self.setup_base_prim(prim)

        prim.CreateInputComponentAttr("input")
        prim.CreateInputChannelAttr("joint_position")

        prim.CreateOutputComponentAttr("output")
        prim.CreateOutputChannelAttr("joint_state")

        prim.CreateArticulationPrimRel()
        pass

    def add_scissor_lift_simulator(self, parent=None):
        if parent:
            path = omni.kit.utils.get_stage_next_free_path(self._stage, parent + "/REB_ScissorLiftSimulator", False)
        else:
            path = omni.kit.utils.get_stage_next_free_path(self._stage, "/REB_ScissorLiftSimulator", True)

        prim = REBSchema.RobotEngineScissorLift.Define(self._stage, path)
        self.setup_base_prim(prim)

        prim.CreateInputComponentAttr("input")
        prim.CreateInputChannelAttr("lift_command")

        prim.CreateOutputComponentAttr("output")
        prim.CreateOutputChannelAttr("lift_state")

        prim.CreateArticulationPrimRel()
        prim.CreateLiftJointNameAttr("lift_joint")

        pass

    def add_surface_gripper(self, parent=None):
        if parent:
            path = omni.kit.utils.get_stage_next_free_path(self._stage, parent + "/REB_SurfaceGripper", False)
        else:
            path = omni.kit.utils.get_stage_next_free_path(self._stage, "/REB_SurfaceGripper", True)

        prim = REBSchema.RobotEngineSurfaceGripper.Define(self._stage, path)
        self.setup_base_prim(prim)

        prim.CreateInputComponentAttr("input")
        prim.CreateInputChannelAttr("io_command")

        prim.CreateOutputComponentAttr("output")
        prim.CreateOutputChannelAttr("io_state")

        prim.CreateD6JointPrimRel()
        prim.CreateParentPrimRel()

        prim.CreateGripperEntityAttr("gripper")

        prim.CreateGripThresholdAttr(1)
        prim.CreateForceLimitAttr(1e10)
        prim.CreateTorqueLimitAttr(1e10)
        prim.CreateBendAngleAttr(0)
        prim.CreateStiffnessAttr(1e10)
        prim.CreateDampingAttr(1e3)
        prim.CreateOffsetPositionAttr(Gf.Vec3f(0, 0, 0))
        prim.CreateOffsetRotationAttr(Gf.Quatf(1.0))

        pass

    def add_twofinger_gripper(self, parent=None):
        if parent:
            path = omni.kit.utils.get_stage_next_free_path(self._stage, parent + "/REB_TwoFingerGripper", False)
        else:
            path = omni.kit.utils.get_stage_next_free_path(self._stage, "/REB_TwoFingerGripper", True)

        prim = REBSchema.RobotEngineTwoFingerGripper.Define(self._stage, path)
        self.setup_base_prim(prim)

        prim.CreateInputComponentAttr("input")
        prim.CreateInputChannelAttr("io_command")

        prim.CreateOutputComponentAttr("output")
        prim.CreateOutputChannelAttr("io_state")

        prim.CreateArticulationPrimRel()
        prim.CreateLeftFingerJointAttr("left_finger")
        prim.CreateRightFingerJointAttr("right_finger")
        prim.CreateGripperEntityAttr("gripper")

        prim.CreateClosedDistanceAttr(0)
        prim.CreateOpenDistanceAttr(0.04)

        pass

    def add_rigid_body_sink(self, parent=None):
        if parent:
            path = omni.kit.utils.get_stage_next_free_path(self._stage, parent + "/REB_RigidBodiesSink", False)
        else:
            path = omni.kit.utils.get_stage_next_free_path(self._stage, "/REB_RigidBodiesSink", True)

        prim = REBSchema.RobotEngineRigidBodySink.Define(self._stage, path)
        self.setup_base_prim(prim)
        prim.CreateOutputComponentAttr("output")
        prim.CreateOutputChannelAttr("bodies")
        prim.CreateRigidBodyPrimsRel()

        pass

    def add_teleport(self, parent=None):
        if parent:
            path = omni.kit.utils.get_stage_next_free_path(self._stage, parent + "/REB_Teleport", False)
        else:
            path = omni.kit.utils.get_stage_next_free_path(self._stage, "/REB_Teleport", True)

        prim = REBSchema.RobotEngineTeleport.Define(self._stage, path)
        self.setup_base_prim(prim)
        prim.CreateInputComponentAttr("input")
        prim.CreateInputChannelAttr("teleport")
        prim.CreateTeleportPrimsRel()

        pass

    def add_scenario_from_message(self, parent=None):
        if parent:
            path = omni.kit.utils.get_stage_next_free_path(self._stage, parent + "/REB_ScenarioFromMessage", False)
        else:
            path = omni.kit.utils.get_stage_next_free_path(self._stage, "/REB_ScenarioFromMessage", True)

        prim = REBSchema.RobotEngineScenarioFromMessage.Define(self._stage, path)
        self.setup_base_prim(prim)
        prim.CreateInputComponentAttr("input")
        prim.CreateInputChannelAttr("scenario_actors")

        prim.CreateTeleportInputComponentAttr("input")
        prim.CreateTeleportInputChannelAttr("teleport")

        prim.CreateRigidBodySinkOutputComponentAttr("output")
        prim.CreateRigidBodySinkOutputChannelAttr("bodies")

        pass

    def add_camera(self, parent=None):
        if parent:
            path = omni.kit.utils.get_stage_next_free_path(self._stage, parent + "/REB_Camera", False)
        else:
            path = omni.kit.utils.get_stage_next_free_path(self._stage, "/REB_Camera", True)

        prim = REBSchema.RobotEngineCamera.Define(self._stage, path)
        self.setup_base_prim(prim)
        prim.CreateRgbOutputComponentAttr("output")
        prim.CreateRgbOutputChannelAttr("color")

        prim.CreateDepthOutputComponentAttr("output")
        prim.CreateDepthOutputChannelAttr("depth")

        prim.CreateSegmentationOutputComponentAttr("output")
        prim.CreateSegmentationOutputChannelAttr("segmentation")

        prim.CreateBoundingBox2DOutputComponentAttr("output")
        prim.CreateBoundingBox2DOutputChannelAttr("bbox")
        prim.CreateBoundingBox2DClassListAttr("")

        prim.CreateRgbEnabledAttr(True)
        prim.CreateDepthEnabledAttr(False)
        prim.CreateSegmentationEnabledAttr(False)
        prim.CreateBoundingBox2DEnabledAttr(False)

        pass

    def add_lidar(self, parent=None):
        if parent:
            path = omni.kit.utils.get_stage_next_free_path(self._stage, parent + "/REB_Lidar", False)
        else:
            path = omni.kit.utils.get_stage_next_free_path(self._stage, "/REB_Lidar", True)

        prim = REBSchema.RobotEngineLidar.Define(self._stage, path)
        self.setup_base_prim(prim)
        prim.CreateOutputComponentAttr("output")
        prim.CreateOutputChannelAttr("rangescan")
        prim.CreateLidarPrimRel()
        pass

    def add_contact_monitor(self, parent=None):
        if parent:
            path = omni.kit.utils.get_stage_next_free_path(self._stage, parent + "/REB_ContactMonitor", False)
        else:
            path = omni.kit.utils.get_stage_next_free_path(self._stage, "/REB_ContactMonitor", True)

        prim = REBSchema.RobotEngineContactMonitor.Define(self._stage, path)
        self.setup_base_prim(prim)
        prim.CreateOutputComponentAttr("output")
        prim.CreateOutputChannelAttr("collision")
        prim.CreateTargetPrimRel()
        prim.CreateIgnoredPrimsRel()
        prim.CreateForceThresholdAttr(1000.0)
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
        elif menu == ADD_HOLONOMICBASE_SCENE_MENU_ITEM:
            self.add_holonomic_base(curr_prim)
        elif menu == ADD_JOINTCONTROL_SCENE_MENU_ITEM:
            self.add_joint_control(curr_prim)
        elif menu == ADD_SCISSORLIFT_SCENE_MENU_ITEM:
            self.add_scissor_lift_simulator(curr_prim)
        elif menu == ADD_SURFACEGRIPPER_SCENE_MENU_ITEM:
            self.add_surface_gripper(curr_prim)
        elif menu == ADD_TWOFINGERGRIPPER_SCENE_MENU_ITEM:
            self.add_twofinger_gripper(curr_prim)
        elif menu == ADD_RIGIDBODYSINK_SCENE_MENU_ITEM:
            self.add_rigid_body_sink(curr_prim)
        elif menu == ADD_TELEPORT_SCENE_MENU_ITEM:
            self.add_teleport(curr_prim)
        elif menu == ADD_SCENARIOFROMMESSAGE_SCENE_MENU_ITEM:
            self.add_scenario_from_message(curr_prim)
        elif menu == ADD_LIDAR_SCENE_MENU_ITEM:
            self.add_lidar(curr_prim)
        elif menu == ADD_CAMERA_SCENE_MENU_ITEM:
            self.add_camera(curr_prim)
        elif menu == ADD_CONTACTMONITOR_SCENE_MENU_ITEM:
            self.add_contact_monitor(curr_prim)

    def shutdown(self):
        self._menus = None
