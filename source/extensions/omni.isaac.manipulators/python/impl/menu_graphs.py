# Copyright (c) 2018-2024, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
import os

import numpy as np
import omni.graph.core as og
import omni.ui as ui
import omni.usd
from omni.isaac.core.utils.stage import get_next_free_path
from omni.isaac.ui.callbacks import on_open_IDE_clicked
from omni.isaac.ui.style import get_style
from omni.isaac.ui.widgets import ParamWidget, SelectPrimWidget
from omni.kit.window.extensions import SimpleCheckBox
from pxr import Usd, UsdPhysics


class ArticulationPositionGraph:
    def __init__(self):
        self._og_path = ""
        self._art_root_path = ""
        self._num_dofs = None
        self._joint_names = []
        self._default_pos = []

    def make_graph(self):
        keys = og.Controller.Keys
        og.Controller.edit(
            {"graph_path": self._og_path, "evaluator_name": "execution"},
            {
                keys.CREATE_NODES: [
                    ("OnPlaybackTick", "omni.graph.action.OnPlaybackTick"),
                    ("JointCommandArray", "omni.graph.nodes.ConstructArray"),
                    ("ArticulationController", "omni.isaac.core_nodes.IsaacArticulationController"),
                    ("JointNameArray", "omni.graph.nodes.ConstructArray"),
                ],
                keys.SET_VALUES: [
                    ("JointCommandArray.inputs:arrayType", "double[]"),
                    ("JointCommandArray.inputs:arraySize", self._num_dofs),
                    ("ArticulationController.inputs:targetPrim", self._art_root_path),
                    ("JointNameArray.inputs:arrayType", "token[]"),
                    ("JointNameArray.inputs:arraySize", self._num_dofs),
                ],
                keys.CONNECT: [
                    ("OnPlaybackTick.outputs:tick", "ArticulationController.inputs:execIn"),
                    ("JointCommandArray.outputs:array", "ArticulationController.inputs:positionCommand"),
                    ("JointNameArray.outputs:array", "ArticulationController.inputs:jointNames"),
                ],
            },
        )

        for i in range(1, self._num_dofs):
            og.Controller.create_attribute(
                self._og_path + "/JointCommandArray",
                "inputs:input" + str(i),
                og.Type(og.BaseDataType.DOUBLE, 1, 0, og.AttributeRole.NONE),
                og.AttributePortType.ATTRIBUTE_PORT_TYPE_INPUT,
            )
            og.Controller.create_attribute(
                self._og_path + "/JointNameArray",
                "inputs:input" + str(i),
                og.Type(og.BaseDataType.TOKEN, 1, 0, og.AttributeRole.NONE),
                og.AttributePortType.ATTRIBUTE_PORT_TYPE_INPUT,
            )

        for i in range(self._num_dofs):
            og.Controller.attribute(self._og_path + "/JointCommandArray.inputs:input" + str(i)).set(
                self._default_pos[i]
            )
            og.Controller.attribute(self._og_path + "/JointNameArray.inputs:input" + str(i)).set(self._joint_names[i])

        og.Controller.node(self._og_path + "/JointCommandArray")

    def create_articulation_controller_graph(self):
        default_og_path = "/Graphs/articulation_position_controller"
        og_path = get_next_free_path(default_og_path, "")
        og_path_def = ParamWidget.FieldDef(name="og_path", label="Graph Path", type=ui.StringField, default=og_path)

        instructions = "Add Articulation root and then Press 'OK' to create graph. \n\n To move the joints, highlight the JointCommandArray on the stage tree under /World/Graphs/articulation_position_controller{_n} (after pressed 'OK'), \n\n Start simulation by pressing 'play', then change the joint angles in the Property Manager Tab -> Raw USD Properties"
        ## populate the popup window
        self._art_window = ui.Window("Parameters", width=500, height=450)
        with self._art_window.frame:
            with ui.VStack(spacing=4):
                ui.Label(
                    "REQUIRED",
                    style_type_name_override="Label.Label",
                    height=40,
                    style={"font_size": 18, "color": 0xFFA8A8A8},
                )
                self.art_root_input = SelectPrimWidget(label="Articulation Root", default=self._art_root_path)
                self.og_path_input = ParamWidget(field_def=og_path_def)
                ui.Spacer(height=2)
                ui.Line(style={"color": 0x338A8777}, width=ui.Fraction(1), height=2)
                with ui.HStack():
                    ui.Label(
                        "Instructions:",
                        style_type_name_override="Label::label",
                        word_wrap=True,
                        width=ui.Percent(20),
                        alignment=ui.Alignment.LEFT_TOP,
                    )
                    with ui.ScrollingFrame(
                        height=180,
                        style_type_name_override="ScrollingFrame",
                        alignment=ui.Alignment.LEFT_TOP,
                        horizontal_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_AS_NEEDED,
                        vertical_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_ALWAYS_ON,
                    ):
                        with ui.ZStack(style={"ZStack": {"margin": 10}}):
                            ui.Rectangle()
                            ui.Label(
                                instructions,
                                style_type_name_override="Label::label",
                                word_wrap=True,
                                alignment=ui.Alignment.LEFT_TOP,
                            )

                ui.Line(style={"color": 0x338A8777}, width=ui.Fraction(1), height=2)
                ui.Spacer(height=2)
                with ui.HStack():
                    ui.Spacer(width=ui.Percent(10))
                    ui.Button("OK", height=40, width=ui.Percent(30), clicked_fn=self._on_ok)
                    ui.Spacer(width=ui.Percent(20))
                    ui.Button("Cancel", height=40, width=ui.Percent(30), clicked_fn=self._on_cancel)
                    ui.Spacer(width=ui.Percent(10))
                with ui.Frame(height=30):
                    with ui.HStack():
                        ui.Label("Python Script for Graph Generation", width=ui.Percent(30))
                        ui.Button(
                            name="IconButton",
                            width=24,
                            height=24,
                            clicked_fn=lambda: on_open_IDE_clicked("", __file__),
                            style=get_style()["IconButton.Image::OpenConfig"],
                        )

    def _on_ok(self):
        self._og_path = self.og_path_input.get_value()
        self._art_root_path = self.art_root_input.get_value()

        PI = 3.1415926535
        # if the art_root_path is an articulation root, get the number of dof automatically
        stage = omni.usd.get_context().get_stage()
        current_prim = stage.GetPrimAtPath(self._art_root_path)
        self._joint_names = []
        self._default_pos = []
        if current_prim.HasAPI(UsdPhysics.ArticulationRootAPI):
            for prim in Usd.PrimRange(current_prim, Usd.TraverseInstanceProxies()):
                if prim.IsA(UsdPhysics.RevoluteJoint):
                    self._joint_names.append(os.path.basename(prim.GetPath().pathString))
                    joint_drive = UsdPhysics.DriveAPI.Get(prim, "angular")
                    default_pos_deg = joint_drive.GetTargetPositionAttr().Get()
                    self._default_pos.append(
                        default_pos_deg * PI / 180
                    )  # USD property is in degrees, PhysX (articulation controller) is in radians
                elif prim.IsA(UsdPhysics.PrismaticJoint):
                    self._joint_names.append(os.path.basename(prim.GetPath().pathString))
                    joint_drive = UsdPhysics.DriveAPI.Get(prim, "linear")
                    self._default_pos.append(joint_drive.GetTargetPositionAttr().Get())

        self._num_dofs = len(self._joint_names)
        self.make_graph()
        self._art_window.visible = False

    def _on_cancel(self):
        self._art_window.visible = False


class ArticulationVelocityGraph:
    def __init__(self):
        self._og_path = ""
        self._art_root_path = ""
        self._num_dofs = None
        self._joint_names = []
        self._default_vel = []

    def make_graph(self):
        keys = og.Controller.Keys
        og.Controller.edit(
            {"graph_path": self._og_path, "evaluator_name": "execution"},
            {
                keys.CREATE_NODES: [
                    ("OnPlaybackTick", "omni.graph.action.OnPlaybackTick"),
                    ("JointCommandArray", "omni.graph.nodes.ConstructArray"),
                    ("ArticulationController", "omni.isaac.core_nodes.IsaacArticulationController"),
                    ("JointNameArray", "omni.graph.nodes.ConstructArray"),
                ],
                keys.SET_VALUES: [
                    ("JointCommandArray.inputs:arrayType", "double[]"),
                    ("JointCommandArray.inputs:arraySize", self._num_dofs),
                    ("ArticulationController.inputs:targetPrim", self._art_root_path),
                    ("JointNameArray.inputs:arrayType", "token[]"),
                    ("JointNameArray.inputs:arraySize", self._num_dofs),
                ],
                keys.CONNECT: [
                    ("OnPlaybackTick.outputs:tick", "ArticulationController.inputs:execIn"),
                    ("JointCommandArray.outputs:array", "ArticulationController.inputs:velocityCommand"),
                    ("JointNameArray.outputs:array", "ArticulationController.inputs:jointNames"),
                ],
            },
        )

        for i in range(1, self._num_dofs):
            og.Controller.create_attribute(
                self._og_path + "/JointCommandArray",
                "inputs:input" + str(i),
                og.Type(og.BaseDataType.DOUBLE, 1, 0, og.AttributeRole.NONE),
                og.AttributePortType.ATTRIBUTE_PORT_TYPE_INPUT,
            )
            og.Controller.create_attribute(
                self._og_path + "/JointNameArray",
                "inputs:input" + str(i),
                og.Type(og.BaseDataType.TOKEN, 1, 0, og.AttributeRole.NONE),
                og.AttributePortType.ATTRIBUTE_PORT_TYPE_INPUT,
            )

        for j in range(self._num_dofs):
            og.Controller.attribute(self._og_path + "/JointCommandArray.inputs:input" + str(j)).set(
                self._default_vel[j]
            )
            og.Controller.attribute(self._og_path + "/JointNameArray.inputs:input" + str(j)).set(self._joint_names[j])

        og.Controller.node(self._og_path + "/JointCommandArray")

    def create_articulation_controller_graph(self):
        default_og_path = "/Graphs/articulation_velocity_controller"
        og_path = get_next_free_path(default_og_path, "")
        og_path_def = ParamWidget.FieldDef(name="og_path", label="Graph Path", type=ui.StringField, default=og_path)

        instructions = "Add Articulation root and then Press 'OK' to create graph. \n\n To move the joints, highlight the JointCommandArray on the stage tree under /World/Graphs/articulation_velocity_controller{_n} (after pressed 'OK'), \n\n Start simulation by pressing 'play', then change the joint angles in the Property Manager Tab -> Raw USD Properties"
        ## populate the popup window
        self._art_window = ui.Window("Parameters", width=500, height=450)
        with self._art_window.frame:
            with ui.VStack(spacing=4):
                ui.Label(
                    "REQUIRED",
                    style_type_name_override="Label.Label",
                    height=40,
                    style={"font_size": 18, "color": 0xFFA8A8A8},
                )
                self.art_root_input = SelectPrimWidget(label="Articulation Root", default=self._art_root_path)
                self.og_path_input = ParamWidget(field_def=og_path_def)
                ui.Spacer(height=2)
                ui.Line(style={"color": 0x338A8777}, width=ui.Fraction(1), height=2)
                with ui.HStack():
                    ui.Label(
                        "Instructions:",
                        style_type_name_override="Label::label",
                        word_wrap=True,
                        width=ui.Percent(20),
                        alignment=ui.Alignment.LEFT_TOP,
                    )
                    with ui.ScrollingFrame(
                        height=180,
                        style_type_name_override="ScrollingFrame",
                        alignment=ui.Alignment.LEFT_TOP,
                        horizontal_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_AS_NEEDED,
                        vertical_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_ALWAYS_ON,
                    ):
                        with ui.ZStack(style={"ZStack": {"margin": 10}}):
                            ui.Rectangle()
                            ui.Label(
                                instructions,
                                style_type_name_override="Label::label",
                                word_wrap=True,
                                alignment=ui.Alignment.LEFT_TOP,
                            )

                ui.Line(style={"color": 0x338A8777}, width=ui.Fraction(1), height=2)
                ui.Spacer(height=2)
                with ui.HStack():
                    ui.Spacer(width=ui.Percent(10))
                    ui.Button("OK", height=40, width=ui.Percent(30), clicked_fn=self._on_ok)
                    ui.Spacer(width=ui.Percent(20))
                    ui.Button("Cancel", height=40, width=ui.Percent(30), clicked_fn=self._on_cancel)
                    ui.Spacer(width=ui.Percent(10))
                with ui.Frame(height=30):
                    with ui.HStack():
                        ui.Label("Python Script for Graph Generation", width=ui.Percent(30))
                        ui.Button(
                            name="IconButton",
                            width=24,
                            height=24,
                            clicked_fn=lambda: on_open_IDE_clicked("", __file__),
                            style=get_style()["IconButton.Image::OpenConfig"],
                        )

    def _on_ok(self):
        self._og_path = self.og_path_input.get_value()
        self._art_root_path = self.art_root_input.get_value()

        PI = 3.1415926535
        # if the art_root_path is an articulation root, get the number of dof automatically
        stage = omni.usd.get_context().get_stage()
        current_prim = stage.GetPrimAtPath(self._art_root_path)
        self._joint_names = []
        self._default_vel = []
        if current_prim.HasAPI(UsdPhysics.ArticulationRootAPI):
            for prim in Usd.PrimRange(current_prim, Usd.TraverseInstanceProxies()):
                if prim.IsA(UsdPhysics.RevoluteJoint) and prim.HasAPI(UsdPhysics.DriveAPI):
                    self._joint_names.append(os.path.basename(prim.GetPath().pathString))
                    joint_drive = UsdPhysics.DriveAPI.Get(prim, "angular")
                    default_vel_deg = joint_drive.GetTargetVelocityAttr().Get()
                    self._default_vel.append(
                        default_vel_deg * PI / 180
                    )  # USD property is in degrees, PhysX (articulation controller) is in radians
                elif prim.IsA(UsdPhysics.PrismaticJoint) and prim.HasAPI(UsdPhysics.DriveAPI):
                    self._joint_names.append(os.path.basename(prim.GetPath().pathString))
                    joint_drive = UsdPhysics.DriveAPI.Get(prim, "linear")
                    self._default_vel.append(joint_drive.GetTargetVelocityAttr().Get())

        self._num_dofs = len(self._joint_names)
        print(self._num_dofs)
        self.make_graph()
        self._art_window.visible = False

    def _on_cancel(self):
        self._art_window.visible = False


class GripperGraph:
    def __init__(self):

        self._og_path = ""
        self._art_root_path = ""
        self._gripper_root_path = ""
        self._use_keyboard = False
        self._dof_actuation = None
        self._joint_names = ""
        self._open_position = None
        self._close_position = None
        self._speed = None

    def make_graph(self):
        controller = og.Controller()
        keys = controller.Keys
        (graph, _, _, _) = og.Controller.edit(
            {"graph_path": self._og_path, "evaluator_name": "execution"},
            {
                keys.CREATE_NODES: [
                    ("GripperController", "omni.isaac.manipulators.IsaacGripperController"),
                    ("OnTick", "omni.graph.action.OnTick"),
                    ("OpenPositionArray", "omni.graph.nodes.ConstructArray"),
                    ("ClosePositionArray", "omni.graph.nodes.ConstructArray"),
                    ("GripperSpeedArray", "omni.graph.nodes.ConstructArray"),
                    ("OpenJointLimit", "omni.graph.nodes.ConstantDouble"),
                    ("CloseJointLimit", "omni.graph.nodes.ConstantDouble"),
                    ("Speed", "omni.graph.nodes.ConstantDouble"),
                ],
                keys.SET_VALUES: [
                    ("OnTick.inputs:onlyPlayback", True),  # only tick when simulator is playing
                    ("GripperController.inputs:articulationRootPrim", self._art_root_path),
                    ("GripperController.inputs:gripperPrim", self._gripper_root_path),
                    ("Speed.inputs:value", self._speed),
                    ("OpenJointLimit.inputs:value", self._open_position),
                    ("CloseJointLimit.inputs:value", self._close_position),
                ],
                keys.CONNECT: [
                    ("OnTick.outputs:tick", "GripperController.inputs:execIn"),
                    ("OpenJointLimit.inputs:value", "OpenPositionArray.inputs:input0"),
                    ("CloseJointLimit.inputs:value", "ClosePositionArray.inputs:input0"),
                    ("Speed.inputs:value", "GripperSpeedArray.inputs:input0"),
                    ("OpenPositionArray.outputs:array", "GripperController.inputs:openPosition"),
                    ("ClosePositionArray.outputs:array", "GripperController.inputs:closePosition"),
                    ("GripperSpeedArray.outputs:array", "GripperController.inputs:gripperSpeed"),
                ],
            },
        )

        # if user put in joint names:
        if self._joint_names:
            n_joints = len(self._joint_names)

            # create an array node to collect joint names
            (_, [joint_names_node], _, _) = controller.edit(
                graph,
                {
                    keys.CREATE_NODES: [("ArrayJointNames", "omni.graph.nodes.ConstructArray")],
                    keys.SET_VALUES: [
                        ("ArrayJointNames.inputs:arrayType", "token[]"),
                        ("ArrayJointNames.inputs:arraySize", n_joints),
                    ],
                },
            )
            controller.connect(
                controller.attribute(self._og_path + "/ArrayJointNames.outputs:array"),
                controller.attribute(self._og_path + "/GripperController.inputs:jointNames"),
            )
            # create the matching number of inputs in array node and input token nodes
            for i in range(n_joints):
                node_name = "JointName" + str(i)
                joint_name = self._joint_names[i]
                controller.create_node((node_name, graph), "omni.graph.nodes.ConstantToken")
                controller.attribute(self._og_path + "/" + node_name + ".inputs:value").set(joint_name)
                if i > 0:
                    joint_names_node.create_attribute(
                        "input" + str(i),
                        og.Type(og.BaseDataType.TOKEN),
                        og.AttributePortType.ATTRIBUTE_PORT_TYPE_INPUT,
                    )

                # make connections to arrayNames node
                controller.connect(
                    og.Controller.attribute(self._og_path + "/JointName" + str(i) + ".inputs:value"),
                    og.Controller.attribute(self._og_path + "/ArrayJointNames.inputs:input" + str(i)),
                )
        else:
            print("defaulting to move all joints in the robot")

        if self._use_keyboard:
            print("using keyboard input to open/close gripper")
            og.Controller.edit(
                graph,
                {
                    keys.CREATE_NODES: [
                        ("Open", "omni.graph.action.OnKeyboardInput"),
                        ("Close", "omni.graph.action.OnKeyboardInput"),
                        ("Stop", "omni.graph.action.OnKeyboardInput"),
                    ],
                    keys.SET_VALUES: [
                        ("Open.inputs:keyIn", "O"),
                        ("Close.inputs:keyIn", "C"),
                        ("Stop.inputs:keyIn", "N"),
                    ],
                },
            )

            controller.connect(
                og.Controller.attribute(self._og_path + "/Open.outputs:pressed"),
                og.Controller.attribute(self._og_path + "/GripperController.inputs:open"),
            )

            controller.connect(
                og.Controller.attribute(self._og_path + "/Close.outputs:pressed"),
                og.Controller.attribute(self._og_path + "/GripperController.inputs:close"),
            )

            controller.connect(
                og.Controller.attribute(self._og_path + "/Stop.outputs:pressed"),
                og.Controller.attribute(self._og_path + "/GripperController.inputs:stop"),
            )

    def create_gripper_controller_graph(self):
        default_og_path = "/Graphs/gripper_controller"
        og_path = get_next_free_path(default_og_path, "")
        og_path_def = ParamWidget.FieldDef(name="og_path", label="Graph Path", type=ui.StringField, default=og_path)

        speed_def = ParamWidget.FieldDef(
            name="gripper_speed", label="Gripper Speed (distance per frame)", type=ui.FloatField, default=self._speed
        )
        joint_names_def = ParamWidget.FieldDef(
            name="joint_names", label="Gripper Joint Names", type=ui.StringField, default=self._joint_names
        )
        open_position_def = ParamWidget.FieldDef(
            name="open_position", label="Open Position Limit", type=ui.FloatField, default=self._open_position
        )
        close_position_def = ParamWidget.FieldDef(
            name="close_position", label="Close Position Limit", type=ui.FloatField, default=self._close_position
        )

        ## populate the popup window
        self._window = ui.Window("Parameters", width=400, height=550)
        with self._window.frame:
            with ui.VStack(spacing=4):
                ui.Label(
                    "REQUIRED",
                    style_type_name_override="Label.Label",
                    height=40,
                    style={"font_size": 18, "color": 0xFFA8A8A8},
                )
                self.art_root_input = SelectPrimWidget(label="Articulation Root", default=self._art_root_path)
                self.gripper_root_input = SelectPrimWidget(label="Gripper Root Prim", default=self._gripper_root_path)
                self.og_path_input = ParamWidget(field_def=og_path_def)
                self.speed_input = ParamWidget(field_def=speed_def)
                ui.Spacer(height=2)
                ui.Label(
                    "If not all actuated joints are gripper joints, list all gripper joint names separated by a comma",
                    height=30,
                    width=ui.Percent(80),
                    style_type_name_override="Label.Label",
                    style={"font_size": 12, "color": 0xFFA8A8A8},
                    word_wrap=True,
                )
                self.joint_names_input = ParamWidget(field_def=joint_names_def)
                ui.Spacer(height=2)

                ui.Line(style={"color": 0x338A8777}, width=ui.Fraction(1), height=2)
                ui.Label(
                    "OPTIONAL (Default to joint limits if not given)",
                    height=30,
                    style_type_name_override="Label.Label",
                    style={"font_size": 18, "color": 0xFFA8A8A8},
                )
                ui.Label(
                    "Only uniform joint limit (and speed) are supported in this popup, update the generated omnigraph if need finger-specific joint limits/speed",
                    height=30,
                    width=ui.Percent(80),
                    style_type_name_override="Label.Label",
                    style={"font_size": 12, "color": 0xFFA8A8A8},
                    word_wrap=True,
                )
                self.open_position_input = ParamWidget(field_def=open_position_def)
                self.close_position_input = ParamWidget(field_def=close_position_def)
                ui.Spacer(height=5)
                ui.Line(style={"color": 0x338A8777}, width=ui.Fraction(1), height=2)
                with ui.HStack():
                    ui.Label("Use Keyboard Control", width=ui.Percent(30))
                    cb = ui.SimpleBoolModel(default_value=self._use_keyboard)
                    SimpleCheckBox(self._use_keyboard, self._on_checked_box, model=cb)
                with ui.HStack():
                    ui.Spacer(width=ui.Percent(10))
                    ui.Button("OK", height=40, width=ui.Percent(30), clicked_fn=self._on_ok)
                    ui.Spacer(width=ui.Percent(20))
                    ui.Button("Cancel", height=40, width=ui.Percent(30), clicked_fn=self._on_cancel)
                    ui.Spacer(width=ui.Percent(10))
                with ui.Frame(height=30):
                    with ui.HStack():
                        ui.Label("Python Script for Graph Generation", width=ui.Percent(30))
                        ui.Button(
                            name="IconButton",
                            width=24,
                            height=24,
                            clicked_fn=lambda: on_open_IDE_clicked("", __file__),
                            style=get_style()["IconButton.Image::OpenConfig"],
                        )

    def _on_ok(self):
        self._og_path = self.og_path_input.get_value()
        self._art_root_path = self.art_root_input.get_value()
        self._gripper_root_path = self.gripper_root_input.get_value()

        self._speed = self.speed_input.get_value()
        self._open_position = self.open_position_input.get_value()
        self._close_position = self.close_position_input.get_value()
        self._joint_names = self.joint_names_input.get_value()

        self._parameter_checks()
        self.make_graph()
        self._window.visible = False

    def _on_cancel(self):
        self._window.visible = False

    def _on_checked_box(self, check_state):
        self._use_keyboard = check_state
        print(f"using keyboard set to {self._use_keyboard}\n O-open, C-close, N-stop")

    def _parameter_checks(self):
        # turn joint names from tokens to a list
        self._joint_names = [item.strip() for item in self._joint_names.split(",")]
        print(f"joint names {self._joint_names}, dof: {len(self._joint_names)}")
