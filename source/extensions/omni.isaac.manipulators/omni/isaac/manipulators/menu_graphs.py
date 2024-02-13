# Copyright (c) 2018-2024, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
import os

import omni.graph.core as og
import omni.ui as ui
import omni.usd
from omni.isaac.core.utils.stage import get_next_free_path
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
        og_path = get_next_free_path(default_og_path)
        og_path_def = ParamWidget.FieldDef(name="og_path", label="graph path", type=ui.StringField, default=og_path)

        instructions = "Add Articulation root and then Press 'OK' to create graph. \n\n To move the joints, highlight the JointCommandArray on the stage tree under /World/Graphs/articulation_position_controller{_n} (after pressed 'OK'), \n\n Start simulation by pressing 'play', then change the joint angles in the Property Manager Tab -> Raw USD Properties"
        ## populate the popup window
        self._art_window = ui.Window("Parameters", width=500, height=0)
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
        og_path = get_next_free_path(default_og_path)
        og_path_def = ParamWidget.FieldDef(name="og_path", label="graph path", type=ui.StringField, default=og_path)

        instructions = "Add Articulation root and then Press 'OK' to create graph. \n\n To move the joints, highlight the JointCommandArray on the stage tree under /World/Graphs/articulation_velocity_controller{_n} (after pressed 'OK'), \n\n Start simulation by pressing 'play', then change the joint angles in the Property Manager Tab -> Raw USD Properties"
        ## populate the popup window
        self._art_window = ui.Window("Parameters", width=500, height=0)
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
        self._og_path = "/Graphs/gripper_controller_graph"
        self._art_root_path = ""
        self._gripper_root_path = ""
        self._use_keyboard = False
        self._joint_names = ""
        self._open_position = None
        self._close_position = None
        self._speed = None

    def make_graph(self):
        keys = og.Controller.Keys
        og.Controller.edit(
            {"graph_path": self._graph_path, "evaluator_name": "execution"},
            {
                keys.CREATE_NODES: [
                    ("GripperController", "omni.isaac.examples_nodes.IsaacGripperController"),
                    ("OnTick", "omni.graph.action.OnTick"),
                    ("Open", "omni.graph.action.OnKeyboardInput"),
                    ("Close", "omni.graph.action.OnKeyboardInput"),
                    ("Stop", "omni.graph.action.OnKeyboardInput"),
                    ("JointNamesArray", "omni.graph.nodes.ConstructArray"),  # need user input
                    ("OpenPositionArray", "omni.graph.nodes.ConstructArray"),  # by default no output connection
                    ("ClosePositionArray", "omni.graph.nodes.ConstructArray"),  # by default no output connection
                    ("GripperSpeedArray", "omni.graph.nodes.ConstructArray"),
                    ("OpenJointLimit", "omni.graph.nodes.ConstantDouble"),
                    ("CloseJointLimit", "omni.graph.nodes.ConstantDouble"),
                    ("Speed", "omni.graph.nodes.ConstantDouble"),  # need user input
                    ("JointName_1", "omni.graph.nodes.ConstantToken"),
                    ("JointName_2", "omni.graph.nodes.ConstantToken"),
                ],
                keys.SET_VALUES: [
                    ("Open.inputs:keyIn", "A"),
                    ("Close.inputs:keyIn", "C"),
                    ("Stop.inputs:keyIn", "B"),
                    ("OnTick.inputs:onlyPlayback", True),  # only tick when simulator is playing
                    ("JointNamesArray.inputs:arraySize", 2),
                    ("JointNamesArray.inputs:arrayType", "token[]"),
                ],
                keys.CREATE_ATTRIBUTES: [
                    ("JointNamesArray.inputs:input1", "token"),
                ],
                keys.CONNECT: [
                    ("OnTick.outputs:tick", "GripperController.inputs:execIn"),
                    ("Open.outputs:pressed", "GripperController.inputs:open"),
                    ("Close.outputs:pressed", "GripperController.inputs:close"),
                    ("Stop.outputs:pressed", "GripperController.inputs:stop"),
                    ("JointName_1.inputs:value", "JointNamesArray.inputs:input0"),
                    ("JointName_2.inputs:value", "JointNamesArray.inputs:input1"),
                    ("JointNamesArray.outputs:array", "GripperController.inputs:jointNames"),
                    ("OpenJointLimit.inputs:value", "OpenPositionArray.inputs:input0"),
                    ("CloseJointLimit.inputs:value", "ClosePositionArray.inputs:input0"),
                    ("OpenPositionArray.outputs:array", "GripperController.inputs:openPosition"),
                    ("ClosePositionArray.outputs:array", "GripperController.inputs:closePosition"),
                    ("Speed.inputs:value", "GripperSpeedArray.inputs:input0"),
                    ("GripperSpeedArray.outputs:array", "GripperController.inputs:gripperSpeed"),
                ],
            },
        )
        print("new gripper controller graph generated at path ", self._graph_path)
        pass

    def create_gripper_controller_grpah(self):
        pass

    def _on_ok(self):
        pass

    def _on_cancel(self):
        pass

    def _on_checked_box(self, check_state):
        self._use_keyboard = check_state
