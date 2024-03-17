# Copyright (c) 2018-2024, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#


from pathlib import Path

import omni.graph.core as og
import omni.ui as ui
import omni.usd
from omni.isaac.core.utils.stage import get_next_free_path
from omni.isaac.ui.callbacks import on_open_IDE_clicked
from omni.isaac.ui.style import get_style
from omni.isaac.ui.widgets import ParamWidget, SelectPrimWidget
from omni.kit.window.extensions import SimpleCheckBox
from pxr import OmniGraphSchema


class Ros2ClockGraph:
    def __init__(self):
        self._og_path = "/Graph/ROS_Clock"

    def make_graph(self):
        self._timeline = omni.timeline.get_timeline_interface()
        self._timeline.stop()

        keys = og.Controller.Keys
        (graph, nodes, _, _) = og.Controller.edit(
            {"graph_path": self._og_path, "evaluator_name": "execution"},
            {
                keys.CREATE_NODES: [
                    ("OnPlaybackTick", "omni.graph.action.OnPlaybackTick"),
                    ("ReadSimTime", "omni.isaac.core_nodes.IsaacReadSimulationTime"),
                    ("PublishClock", "omni.isaac.ros2_bridge.ROS2PublishClock"),
                    ("Context", "omni.isaac.ros2_bridge.ROS2Context"),
                ],
                keys.CONNECT: [
                    ("OnPlaybackTick.outputs:tick", "PublishClock.inputs:execIn"),
                    ("Context.outputs:context", "PublishClock.inputs:context"),
                    ("ReadSimTime.outputs:simulationTime", "PublishClock.inputs:timeStamp"),
                ],
                keys.SET_VALUES: [
                    ("ReadSimTime.inputs:resetOnStop", True),
                ],
            },
        )

    def create_clock_graph(self):
        default_og_path = "/Graph/ROS_Clock"
        og_path_def = ParamWidget.FieldDef(
            name="og_path", label="Graph Path", type=ui.StringField, default=default_og_path
        )

        self._window = ui.Window("Parameters", width=300, height=120)
        with self._window.frame:
            with ui.VStack(spacing=4):
                self.og_path_input = ParamWidget(field_def=og_path_def)
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

        self.make_graph()
        self._window.visible = False

    def _on_cancel(self):
        self._window.visible = False


class Ros2JointStatesGraph:
    def __init__(self):
        self._og_path = "/Graph/ROS_JointStates"
        self._art_root_path = ""
        self._pub_topic = "/joint_states"
        self._sub_topic = "/cmd"
        self._existing_graph = False
        self._publisher = False
        self._subscriber = False
        self._sub_move_robot = True  # does subscriber feeds into an articulation node to move the robot

    def make_graph(self):
        self._timeline = omni.timeline.get_timeline_interface()
        self._timeline.stop()

        keys = og.Controller.Keys

        # if starting from a new graph, start it with just a tick,context, and sim_time node, the rest is the same for adding to exsiting graph
        if not self._existing_graph:
            self._og_path = get_next_free_path(self._og_path, "")
            (graph_handle, nodes, _, _) = og.Controller.edit(
                {"graph_path": self._og_path, "evaluator_name": "execution"},
                {
                    keys.CREATE_NODES: [
                        ("OnPlaybackTick", "omni.graph.action.OnPlaybackTick"),
                        ("Context", "omni.isaac.ros2_bridge.ROS2Context"),
                        ("ReadSimTime", "omni.isaac.core_nodes.IsaacReadSimulationTime"),
                    ],
                    keys.SET_VALUES: [
                        ("ReadSimTime.inputs:resetOnStop", True),
                    ],
                },
            )
        else:
            # make sure the "existing" graph exist
            stage = omni.usd.get_context().get_stage()
            og_prim = stage.GetPrimAtPath(self._og_path)
            if og_prim.IsValid() and og_prim.IsA(OmniGraphSchema.OmniGraph):
                graph_handle = og.get_graph_by_path(self._og_path)
            else:
                print(f"{self._og_path} is not an existing graph, check the og path")
                return

        # to an existin graph
        # traverse through the graph
        all_nodes = graph_handle.get_nodes()
        js_pub_node_name = "PublisherJointState"
        js_sub_node_name = "SubscriberJointState"
        art_node_name = "ArticulationController"
        tick_node = None
        context_node = None
        sim_time_node = None
        for node in all_nodes:
            node_path = node.get_prim_path()
            node_type = node.get_type_name()
            if node_type == "omni.graph.action.OnPlaybackTick" or node_type == "omni.graph.action.OnTick":
                tick_node = node_path
            elif node_type == "omni.isaac.ros2_bridge.ROS2Context":
                context_node = node_path
            elif node_type == "omni.isaac.core_nodes.IsaacReadSimulationTime":
                sim_time_node = node_path
            elif node_type == "omni.isaac.ros2_bridge.ROS2PublishJointState":
                # if there already exist a js pub node, add a new one with a different name
                js_pub_node_path = get_next_free_path(node_path, "")
                js_pub_node_name = Path(js_pub_node_path).name
            elif node_type == "omni.isaac.ros2_bridge.ROS2SubscribeJointState":
                # if there already exist a js sub node, add a new one with a different name
                js_sub_node_path = get_next_free_path(node_path, "")
                js_sub_node_name = Path(js_sub_node_path).name
            elif node_type == "omni.isaac.core_nodes.IsaacArticulationController":
                print("already has an articulation controller node, CREATING A NEW ARTICULATION NODE")
                art_node = get_next_free_path(node_path, "")
                art_node_name = Path(art_node).name

        if self._publisher:
            og.Controller.edit(
                graph_handle,
                {
                    keys.CREATE_NODES: [
                        (js_pub_node_name, "omni.isaac.ros2_bridge.ROS2PublishJointState"),
                    ],
                    keys.SET_VALUES: [
                        (js_pub_node_name + ".inputs:targetPrim", self._art_root_path),
                        (js_pub_node_name + ".inputs:topicName", self._pub_topic),
                    ],
                },
            )

            if tick_node:
                og.Controller.connect(
                    og.Controller.attribute(tick_node + ".outputs:tick"),
                    og.Controller.attribute(self._og_path + "/" + js_pub_node_name + ".inputs:execIn"),
                )
            if context_node:
                og.Controller.connect(
                    og.Controller.attribute(context_node + ".outputs:context"),
                    og.Controller.attribute(self._og_path + "/" + js_pub_node_name + ".inputs:context"),
                )
            if sim_time_node:
                og.Controller.connect(
                    og.Controller.attribute(sim_time_node + ".outputs:simulationTime"),
                    og.Controller.attribute(self._og_path + "/" + js_pub_node_name + ".inputs:timeStamp"),
                )

        if self._subscriber:
            og.Controller.edit(
                graph_handle,
                {
                    keys.CREATE_NODES: [
                        (js_sub_node_name, "omni.isaac.ros2_bridge.ROS2SubscribeJointState"),
                    ],
                    keys.SET_VALUES: [
                        (js_sub_node_name + ".inputs:topicName", self._sub_topic),
                    ],
                },
            )

            if tick_node:
                og.Controller.connect(
                    og.Controller.attribute(tick_node + ".outputs:tick"),
                    og.Controller.attribute(self._og_path + "/" + js_sub_node_name + ".inputs:execIn"),
                )
            if context_node:
                og.Controller.connect(
                    og.Controller.attribute(context_node + ".outputs:context"),
                    og.Controller.attribute(self._og_path + "/" + js_sub_node_name + ".inputs:context"),
                )

            if self._sub_move_robot:
                og.Controller.edit(
                    graph_handle,
                    {
                        keys.CREATE_NODES: [
                            (art_node_name, "omni.isaac.core_nodes.IsaacArticulationController"),
                        ],
                        keys.SET_VALUES: [
                            (art_node_name + ".inputs:targetPrim", self._art_root_path),
                        ],
                        keys.CONNECT: [
                            (
                                self._og_path + "/" + js_sub_node_name + ".outputs:execOut",
                                self._og_path + "/" + art_node_name + ".inputs:execIn",
                            ),
                            (
                                self._og_path + "/" + js_sub_node_name + ".outputs:positionCommand",
                                self._og_path + "/" + art_node_name + ".inputs:positionCommand",
                            ),
                            (
                                self._og_path + "/" + js_sub_node_name + ".outputs:velocityCommand",
                                self._og_path + "/" + art_node_name + ".inputs:velocityCommand",
                            ),
                            (
                                self._og_path + "/" + js_sub_node_name + ".outputs:effortCommand",
                                self._og_path + "/" + art_node_name + ".inputs:effortCommand",
                            ),
                            (
                                self._og_path + "/" + js_sub_node_name + ".outputs:jointNames",
                                self._og_path + "/" + art_node_name + ".inputs:jointNames",
                            ),
                        ],
                    },
                )

    def create_jointstates_graph(self):

        og_path_def = ParamWidget.FieldDef(
            name="og_path", label="Graph Path", type=ui.StringField, default=self._og_path
        )
        pub_topic_def = ParamWidget.FieldDef(
            name="pub topic", label="Publisher Topic", type=ui.StringField, default=self._pub_topic
        )
        sub_topic_def = ParamWidget.FieldDef(
            name="sub topic", label="Subscriber Topic", type=ui.StringField, default=self._sub_topic
        )
        self._window = ui.Window("Parameters", width=450, height=300)
        with self._window.frame:
            with ui.VStack(spacing=4):
                with ui.HStack():
                    ui.Label("Add to an existing graph?", width=ui.Percent(30))
                    cb = ui.SimpleBoolModel(default_value=self._existing_graph)
                    SimpleCheckBox(self._existing_graph, self._on_use_existing_graph, model=cb)
                self.og_path_input = ParamWidget(field_def=og_path_def)
                self.art_root_input = SelectPrimWidget(label="Articulation Root", default=self._art_root_path)
                ui.Spacer(height=5)
                with ui.HStack():
                    ui.Label("Publisher", width=ui.Percent(15))
                    cb = ui.SimpleBoolModel(default_value=self._publisher)
                    SimpleCheckBox(self._publisher, self._on_pub_graph, model=cb)
                    ui.Spacer(width=ui.Percent(5))
                    self.pub_topic_input = ParamWidget(field_def=pub_topic_def)
                    ui.Spacer(width=ui.Percent(20))
                with ui.HStack():
                    ui.Label("Subscriber", width=ui.Percent(15))
                    cb = ui.SimpleBoolModel(default_value=self._subscriber)
                    SimpleCheckBox(self._subscriber, self._on_sub_graph, model=cb)
                    ui.Spacer(width=ui.Percent(5))
                    self.sub_topic_input = ParamWidget(field_def=sub_topic_def)
                    ui.Label("Move Robot?", width=ui.Percent(15))
                    cb = ui.SimpleBoolModel(default_value=self._sub_move_robot)
                    SimpleCheckBox(self._sub_move_robot, self._on_sub_move_robot, model=cb)
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
        self._pub_topic = self.pub_topic_input.get_value()
        self._sub_topic = self.sub_topic_input.get_value()

        self.make_graph()
        self._window.visible = False

    def _on_cancel(self):
        self._window.visible = False

    def _on_use_existing_graph(self, check_state):
        self._existing_graph = check_state
        if check_state:
            print("adding to existing graph")

    def _on_pub_graph(self, check_state):
        self._publisher = check_state

    def _on_sub_graph(self, check_state):
        self._subscriber = check_state

    def _on_sub_move_robot(self, check_state):
        self._sub_move_robot = check_state


class Ros2TfGraph:
    def __init__(self):
        self._og_path = "/Graph/ROS_Publisher_TF"
        self._art_root_path = ""
        self._topic_name = "/tf"
        self._existing_graph = False


class Ros2OdometryGraph:
    def __init__(self):
        self._og_path = "/Graph/ROS_Publisher_Odometry"
        self._art_root_path = ""
        self._topic_name = "/odom"
        self._existing_graph = False
