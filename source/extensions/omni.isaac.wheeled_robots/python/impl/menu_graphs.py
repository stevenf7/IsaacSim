# Copyright (c) 2018-2024, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

import omni.graph.core as og
import omni.ui as ui
from omni.isaac.core.utils.stage import get_next_free_path
from omni.isaac.ui.widgets import ParamWidget, SelectPrimWidget
from omni.kit.window.extensions import SimpleCheckBox


class DifferentialRobotGraph:
    def __init__(self):
        # have a place to save variables so there's default when creating new graphs in the same session
        self._og_path = "/Graphs/differential_controller_graph"
        self._art_root_path = ""
        self._wheel_radius = 0.0
        self._wheel_distance = 0.0
        self._left_joint_name = ""
        self._right_joint_name = ""
        self._left_joint_index = 0
        self._right_joint_index = 0
        self._use_keyboard = False

    def make_graph(self):
        keys = og.Controller.Keys
        (graph, nodes, _, _) = og.Controller.edit(
            {"graph_path": self._og_path, "evaluator_name": "execution"},
            {
                keys.CREATE_NODES: [
                    ("OnPlaybackTick", "omni.graph.action.OnPlaybackTick"),
                    ("DifferentialController", "omni.isaac.wheeled_robots.DifferentialController"),
                    ("ArticulationController", "omni.isaac.core_nodes.IsaacArticulationController"),
                ],
                keys.CONNECT: [
                    ("OnPlaybackTick.outputs:tick", "DifferentialController.inputs:execIn"),
                    ("OnPlaybackTick.outputs:tick", "ArticulationController.inputs:execIn"),
                    ("DifferentialController.outputs:velocityCommand", "ArticulationController.inputs:velocityCommand"),
                ],
                keys.SET_VALUES: [
                    ("ArticulationController.inputs:targetPrim", self._art_root_path),
                    ("DifferentialController.inputs:wheelRadius", self._wheel_radius),
                    ("DifferentialController.inputs:wheelDistance", self._wheel_distance),
                ],
            },
        )

        # if user input used joint indices
        # if user put int both index and names, index will take priority
        if self._left_joint_index and self._right_joint_index:
            print("using joint INDEX")
            og.Controller.edit(
                graph,
                {
                    keys.CREATE_NODES: [("ArrayNames", "omni.graph.nodes.ConstructArray")],
                    keys.CREATE_ATTRIBUTES: [
                        ("ArrayNames.inputs:input1", "int"),
                    ],
                    keys.SET_VALUES: [
                        ("ArrayNames.inputs:arrayType", "int[]"),
                        ("ArrayNames.inputs:input0", self._right_joint_index),
                        ("ArrayNames.inputs:input1", self._left_joint_index),
                        ("ArrayNames.inputs:arraySize", 2),
                    ],
                },
            )
            og.Controller.connect(
                og.Controller.attribute(self._og_path + "/ArrayNames.outputs:array"),
                og.Controller.attribute(self._og_path + "/ArticulationController.inputs:jointIndices"),
            )

        # if user input used joint names
        elif self._left_joint_name and self._right_joint_name:
            print("using joint NAMES")
            og.Controller.edit(
                graph,
                {
                    keys.CREATE_NODES: [("ArrayNames", "omni.graph.nodes.ConstructArray")],
                    keys.CREATE_ATTRIBUTES: [
                        ("ArrayNames.inputs:input1", "token"),
                    ],
                    keys.SET_VALUES: [
                        ("ArrayNames.inputs:arrayType", "token[]"),
                        ("ArrayNames.inputs:input0", self._right_joint_name),
                        ("ArrayNames.inputs:input1", self._left_joint_name),
                        ("ArrayNames.inputs:arraySize", 2),
                    ],
                },
            )
            og.Controller.connect(
                og.Controller.attribute(self._og_path + "/ArrayNames.outputs:array"),
                og.Controller.attribute(self._og_path + "/ArticulationController.inputs:jointNames"),
            )

        else:
            print("default to all joints in the articulation")

        if self._use_keyboard:
            print("adding WASD keyboard control")
            og.Controller.edit(
                graph,
                {
                    keys.CREATE_NODES: [
                        ("W", "omni.graph.nodes.ReadKeyboardState"),
                        ("A", "omni.graph.nodes.ReadKeyboardState"),
                        ("S", "omni.graph.nodes.ReadKeyboardState"),
                        ("D", "omni.graph.nodes.ReadKeyboardState"),
                        ("ToDoubleW", "omni.graph.nodes.ToDouble"),
                        ("ToDoubleA", "omni.graph.nodes.ToDouble"),
                        ("ToDoubleS", "omni.graph.nodes.ToDouble"),
                        ("ToDoubleD", "omni.graph.nodes.ToDouble"),
                        ("NegateLinear", "omni.graph.nodes.Multiply"),
                        ("NegateAngular", "omni.graph.nodes.Multiply"),
                        ("AddLinear", "omni.graph.nodes.Add"),
                        ("AddAngular", "omni.graph.nodes.Add"),
                        ("SpeedLinear", "omni.graph.nodes.Multiply"),
                        ("ScaleLinear", "omni.graph.nodes.ConstantDouble"),
                        ("SpeedAngular", "omni.graph.nodes.Multiply"),
                        ("ScaleAngular", "omni.graph.nodes.ConstantDouble"),
                        ("NegOne", "omni.graph.nodes.ConstantInt"),
                    ],
                    keys.SET_VALUES: [
                        ("W.inputs:key", "W"),
                        ("A.inputs:key", "A"),
                        ("S.inputs:key", "S"),
                        ("D.inputs:key", "D"),
                        ("NegOne.inputs:value", -1),
                        ("ScaleLinear.inputs:value", 5),
                        ("ScaleAngular.inputs:value", 6),
                    ],
                    keys.CONNECT: [
                        ("W.outputs:isPressed", "ToDoubleW.inputs:value"),
                        ("A.outputs:isPressed", "ToDoubleA.inputs:value"),
                        ("S.outputs:isPressed", "ToDoubleS.inputs:value"),
                        ("D.outputs:isPressed", "ToDoubleD.inputs:value"),
                        ("ToDoubleS.outputs:converted", "NegateLinear.inputs:a"),
                        ("NegOne.inputs:value", "NegateLinear.inputs:b"),
                        ("ToDoubleD.outputs:converted", "NegateAngular.inputs:a"),
                        ("NegOne.inputs:value", "NegateAngular.inputs:b"),
                        ("ToDoubleW.outputs:converted", "AddLinear.inputs:a"),
                        ("NegateLinear.outputs:product", "AddLinear.inputs:b"),
                        ("AddLinear.outputs:sum", "SpeedLinear.inputs:a"),
                        ("ScaleLinear.inputs:value", "SpeedLinear.inputs:b"),
                        ("ToDoubleA.outputs:converted", "AddAngular.inputs:a"),
                        ("NegateAngular.outputs:product", "AddAngular.inputs:b"),
                        ("AddAngular.outputs:sum", "SpeedAngular.inputs:a"),
                        ("ScaleAngular.inputs:value", "SpeedAngular.inputs:b"),
                    ],
                },
            )
            og.Controller.connect(
                og.Controller.attribute(self._og_path + "/SpeedLinear.outputs:product"),
                og.Controller.attribute(self._og_path + "/DifferentialController.inputs:linearVelocity"),
            )
            og.Controller.connect(
                og.Controller.attribute(self._og_path + "/SpeedAngular.outputs:product"),
                og.Controller.attribute(self._og_path + "/DifferentialController.inputs:angularVelocity"),
            )

    def create_differential_robot_graph(self):
        default_og_path = get_next_free_path(self._og_path)
        og_path_def = ParamWidget.FieldDef(
            name="og_path", label="graph path", type=ui.StringField, default=default_og_path
        )
        wheel_radius_def = ParamWidget.FieldDef(
            name="wheel_radius", label="wheel radius(cm)", type=ui.FloatField, default=self._wheel_radius
        )
        wheel_distance_def = ParamWidget.FieldDef(
            name="wheel_distance",
            label="distance between wheels (cm)",
            type=ui.FloatField,
            default=self._wheel_distance,
        )
        left_joint_name_def = ParamWidget.FieldDef(
            name="left_joint_name", label="Left Joint Name", type=ui.StringField, default=self._left_joint_name
        )
        right_joint_name_def = ParamWidget.FieldDef(
            name="right_joint_name", label="Right Joint Name", type=ui.StringField, default=self._right_joint_name
        )
        left_joint_index_def = ParamWidget.FieldDef(
            name="left_joint_index", label="Left Joint Index", type=ui.IntField, default=self._left_joint_index
        )
        right_joint_index_def = ParamWidget.FieldDef(
            name="right_joint_index", label="Right Joint Index", type=ui.IntField, default=self._right_joint_index
        )

        ## populate the popup window
        self._window = ui.Window("Parameters", width=400, height=450)
        with self._window.frame:
            with ui.VStack(spacing=4):
                ui.Label(
                    "REQUIRED",
                    style_type_name_override="Label.Label",
                    height=40,
                    style={"font_size": 18, "color": 0xFFA8A8A8},
                )
                self.art_root_input = SelectPrimWidget(label="Articulation Root", default=self._art_root_path)
                self.og_path_input = ParamWidget(field_def=og_path_def)
                self.wheel_radius_input = ParamWidget(field_def=wheel_radius_def)
                self.wheel_distance_input = ParamWidget(field_def=wheel_distance_def)
                ui.Spacer(height=2)

                ui.Line(style={"color": 0x338A8777}, width=ui.Fraction(1), height=2)
                ui.Label(
                    "If robot has more than two controllable joints:",
                    height=30,
                    style_type_name_override="Label.Label",
                    style={"font_size": 18, "color": 0xFFA8A8A8},
                )
                with ui.VStack(spacing=4):
                    self.right_joint_name_input = ParamWidget(field_def=right_joint_name_def)
                    self.left_joint_name_input = ParamWidget(field_def=left_joint_name_def)
                ui.Label("    OR", height=0)
                with ui.VStack(spacing=4):
                    self.right_joint_index_input = ParamWidget(field_def=right_joint_index_def)
                    self.left_joint_index_input = ParamWidget(field_def=left_joint_index_def)
                ui.Spacer(height=5)
                with ui.HStack():
                    ui.Label("Use Keyboard Control (WASD)", width=ui.Percent(30))
                    cb = ui.SimpleBoolModel(default_value=self._use_keyboard)
                    SimpleCheckBox(self._use_keyboard, self._on_checked_box, model=cb)
                with ui.HStack():
                    ui.Spacer(width=ui.Percent(10))
                    ui.Button("OK", height=40, width=ui.Percent(30), clicked_fn=self._on_ok)
                    ui.Spacer(width=ui.Percent(20))
                    ui.Button("Cancel", height=40, width=ui.Percent(30), clicked_fn=self._on_cancel)
                    ui.Spacer(width=ui.Percent(10))

    def _on_ok(self):
        self._og_path = self.og_path_input.get_value()
        self._art_root_path = self.art_root_input.get_value()
        self._wheel_radius = self.wheel_radius_input.get_value()
        self._wheel_distance = self.wheel_distance_input.get_value()
        self._right_joint_name = self.right_joint_name_input.get_value()
        self._left_joint_name = self.left_joint_name_input.get_value()
        self._right_joint_index = self.right_joint_index_input.get_value()
        self._left_joint_index = self.left_joint_index_input.get_value()

        self.make_graph()
        self._window.visible = False

    def _on_cancel(self):
        self._window.visible = False

    def _on_checked_box(self, check_state):
        self._use_keyboard = check_state
        print("use keyboard", self._use_keyboard)
