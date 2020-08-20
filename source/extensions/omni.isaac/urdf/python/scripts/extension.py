import os
import omni.ext
import omni.kit.commands
import omni.kit.editor
import omni.ui as ui
import carb.tokens
import asyncio
import textwrap
from .link_model import *

omni.kit.pipapi.install("graphviz")
# from .test_model import *
from graphviz import Graph
from graphviz import Digraph
from .. import _urdf
from pxr import UsdGeom
from PIL import Image, ImageDraw
import io

EXTENSION_NAME = "URDF Importer"

tooltip_style = {"Tooltip": {"background_color": 0xFF444444, "border_width": 2, "border_radius": 5}}


def robot_block(color, label):
    with ui.ZStack():
        ui.Rectangle(style={"background_color": color})
        with ui.HStack():
            ui.Spacer(width=2)
            ui.Label(label, alignment=ui.Alignment.CENTER, style={"color": 0xFF000000}, width=0)
            ui.Spacer(width=2)


def create_tooltip():
    with ui.VStack(width=200, style=tooltip_style):
        with ui.HStack():
            ui.Label("Fancy tooltip", width=150)
            ui.IntField().model.set_value(12)
        ui.Line(height=2, style={"color": 0xFFFFFFFF})
        with ui.HStack():
            ui.Label("Anything is possible", width=150)
            ui.StringField().model.set_value("you bet")
        image_source = "resources/desktop-icons/omniverse_512.png"
        ui.Image(image_source, width=200, height=200, alignment=ui.Alignment.CENTER, style={"margin": 0})


class Extension(omni.ext.IExt):
    def on_startup(self):
        self._urdf_interface = _urdf.acquire_urdf_interface()
        self._usd_context = omni.usd.get_context()
        menu_path = f"Window/Isaac/{EXTENSION_NAME}"
        self._window = omni.ui.Window(EXTENSION_NAME, width=600, height=400, visible=False)
        self._menu_entry = omni.kit.ui.get_editor_menu().add_item(f"Window/Isaac/URDF Importer", self._menu_callback)
        self._file_picker = None
        self.models = {}
        self.config = _urdf.ImportConfig()

        with self._window.frame:
            with ui.ScrollingFrame(
                horizontal_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_ALWAYS_OFF,
                vertical_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_ALWAYS_OFF,
            ):
                self._hstack = ui.HStack()
                with self._hstack:
                    with ui.VStack(width=ui.Percent(30)):
                        ui.Button("Parse URDF", clicked_fn=self._parse_urdf)
                        ui.Button("Load Robot", clicked_fn=self._load_robot)
                        ui.Label("Parser Settings:")
                        ui.Line(height=5)
                        with ui.HStack():
                            ui.Label(
                                "Merge Fixed Joints",
                                tooltip="Check this box to skip adding articulation on fixed joints",
                            )
                            ui.CheckBox().model.add_value_changed_fn(
                                lambda m, config=self.config: config.set_merge_fixed_joints(m.get_value_as_bool())
                            )
                        ui.Spacer(height=5)
                        with ui.HStack():
                            ui.Label(
                                "Import Inertia Tensor",
                                tooltip="If True, inertia will be loaded from urdf, if the urdf does not specify inertia tensor, identity will be used and scaled by the scaling factor. If false physx will compute automatically",
                            )
                            ui.CheckBox().model.add_value_changed_fn(
                                lambda m, config=self.config: config.set_import_inertia_tensor(m.get_value_as_bool())
                            )
                        ui.Spacer(height=5)
                        ui.Label("Importer Settings:")
                        ui.Line(height=5)
                        with ui.HStack():
                            ui.Label("Clean Stage", tooltip="Check this box to load URDF on a clean stage")
                            self.models["clean_stage"] = ui.CheckBox()
                            self.models["clean_stage"].model.set_value(False)
                        ui.Spacer(height=5)
                        with ui.HStack():
                            ui.Label(
                                "Convex Decomposition",
                                tooltip="If true, non-convex meshes will be decomposed into convex collision shapes, if false a convex hull will be used.",
                            )
                            model = ui.CheckBox().model
                            model.add_value_changed_fn(
                                lambda m, config=self.config: config.set_convex_decomp(m.get_value_as_bool())
                            )
                            model.set_value(False)
                        ui.Spacer(height=5)
                        with ui.HStack():
                            ui.Label(
                                "Fix Base Link",
                                tooltip="If true, enables the fix base property on the root of the articulation.",
                            )
                            model = ui.CheckBox().model
                            model.add_value_changed_fn(
                                lambda m, config=self.config: config.set_fix_base(m.get_value_as_bool())
                            )
                            model.set_value(True)
                        ui.Spacer(height=5)
                        with ui.HStack():
                            ui.Label(
                                "Self Collision",
                                tooltip="If true, allows self intersection between links in the robot, can cause instability if collision meshes between links are self intersecting",
                            )
                            model = ui.CheckBox().model
                            model.add_value_changed_fn(
                                lambda m, config=self.config: config.set_self_collision(m.get_value_as_bool())
                            )
                            model.set_value(False)
                        ui.Spacer(height=5)
                        ui.Label("Importer Defaults:")
                        ui.Line(height=5)
                        with ui.HStack():
                            ui.Label(
                                "Link Density:",
                                tooltip="[kg/m^3] If a link doesn't have mass, use this density as backup",
                            )
                            model = ui.FloatField().model
                            model.add_value_changed_fn(
                                lambda m, config=self.config: config.set_density(m.get_value_as_float())
                            )
                            model.set_value(1000)
                        ui.Spacer(height=5)
                        with ui.HStack():
                            ui.Label("Joint Drive Type:")
                            model = ui.ComboBox(1, "None", "Position", "Velocity").model
                            model.add_item_changed_fn(
                                lambda m, i, config=self.config: config.set_default_drive_type(
                                    m.get_item_value_model().as_int
                                )
                            )
                        ui.Spacer(height=5)
                        with ui.HStack():
                            ui.Label("Joint Drive Stiffness:")
                            model = ui.FloatField().model
                            model.add_value_changed_fn(
                                lambda m, config=self.config: config.set_default_drive_stiffness(m.get_value_as_float())
                            )
                            model.set_value(100000)
                        ui.Line(height=5)
                        with ui.HStack():
                            ui.Label("Up Axis:")
                            self.models["up_axis"] = ui.MultiFloatField(0.0, 0.0, 1.0)
                            self.models["up_axis"].model.add_item_changed_fn(
                                lambda m, n, config=self.config: config.set_up_vector(
                                    m.get_item_value_model(m.get_item_children()[0]).get_value_as_float(),
                                    m.get_item_value_model(m.get_item_children()[1]).get_value_as_float(),
                                    m.get_item_value_model(m.get_item_children()[2]).get_value_as_float(),
                                )
                            )
                        ui.Spacer(height=5)
                        with ui.HStack():
                            ui.Label("Stage Units Per Meter:")
                            self.models["scale"] = ui.FloatField(enabled=True)
                            self.models["scale"].model.add_value_changed_fn(
                                lambda m, config=self.config: config.set_distance_scale(m.get_value_as_float())
                            )

        stage = self._usd_context.get_stage()
        if stage:
            if UsdGeom.GetStageUpAxis(stage) == UsdGeom.Tokens.y:
                self.models["up_axis"].model.get_item_value_model(
                    self.models["up_axis"].model.get_item_children()[0]
                ).set_value(0)
                self.models["up_axis"].model.get_item_value_model(
                    self.models["up_axis"].model.get_item_children()[1]
                ).set_value(1)
                self.models["up_axis"].model.get_item_value_model(
                    self.models["up_axis"].model.get_item_children()[2]
                ).set_value(0)
            if UsdGeom.GetStageUpAxis(stage) == UsdGeom.Tokens.z:
                self.models["up_axis"].model.get_item_value_model(
                    self.models["up_axis"].model.get_item_children()[0]
                ).set_value(0)
                self.models["up_axis"].model.get_item_value_model(
                    self.models["up_axis"].model.get_item_children()[1]
                ).set_value(0)
                self.models["up_axis"].model.get_item_value_model(
                    self.models["up_axis"].model.get_item_children()[2]
                ).set_value(1)
            units_per_meter = 1.0 / UsdGeom.GetStageMetersPerUnit(stage)
            self.models["scale"].model.set_value(units_per_meter)

        # self._select_picked_folder_callback(
        #     "/home/hmazhar/repos/omni_isaac_sim/_build/linux-x86_64/release/data/urdf/robots/kaya/urdf/kaya.urdf"
        # )
        self._file_picker = None

    def _menu_callback(self, name, visible):
        self._window.visible = not self._window.visible
        if self._window.visible:

            self._events = self._usd_context.get_stage_event_stream()
            self._stage_event_sub = self._events.create_subscription_to_pop(
                self._on_stage_event, name="urdf importer stage event"
            )
        else:
            self._events = None
            self._stage_event_sub = None

    def _on_stage_event(self, event):
        print(event)
        stage = self._usd_context.get_stage()
        if stage:
            if UsdGeom.GetStageUpAxis(stage) == UsdGeom.Tokens.y:
                self.models["up_axis"].model.get_item_value_model(
                    self.models["up_axis"].model.get_item_children()[0]
                ).set_value(0)
                self.models["up_axis"].model.get_item_value_model(
                    self.models["up_axis"].model.get_item_children()[1]
                ).set_value(1)
                self.models["up_axis"].model.get_item_value_model(
                    self.models["up_axis"].model.get_item_children()[2]
                ).set_value(0)
            if UsdGeom.GetStageUpAxis(stage) == UsdGeom.Tokens.z:
                self.models["up_axis"].model.get_item_value_model(
                    self.models["up_axis"].model.get_item_children()[0]
                ).set_value(0)
                self.models["up_axis"].model.get_item_value_model(
                    self.models["up_axis"].model.get_item_children()[1]
                ).set_value(0)
                self.models["up_axis"].model.get_item_value_model(
                    self.models["up_axis"].model.get_item_children()[2]
                ).set_value(1)
            units_per_meter = 1.0 / UsdGeom.GetStageMetersPerUnit(stage)
            self.models["scale"].model.set_value(units_per_meter)

    def _print_robot(self):
        for key, value in self._imported_robot.materials.items():
            print(value.color.r, value.color.g, value.color.b)

    def _create_graphviz_tree(self, tree_item, robot, graph):
        if not tree_item:
            return
        if isinstance(tree_item, list):
            for item in tree_item:
                joint = robot.joints[item["A_joint"]]
                color = "red"
                if joint.type == omni.isaac.urdf._urdf.UrdfJointType.JOINT_REVOLUTE:
                    color = "green"
                if joint.type == omni.isaac.urdf._urdf.UrdfJointType.JOINT_PRISMATIC:
                    color = "blue"
                if joint.type == omni.isaac.urdf._urdf.UrdfJointType.JOINT_CONTINUOUS:
                    color = "orange"
                graph.node(item["B_link"], textwrap.fill(item["B_link"], 20), style="filled", shape="rect")
                graph.edge(
                    item["A_link"], item["B_link"], textwrap.fill(item["A_joint"], 20), color=color, penwidth=str(5)
                )
                self._create_graphviz_tree(item["B_node"], robot, graph)
        else:
            graph.node("Root", style="filled", shape="doublecircle")
            graph.node(tree_item["B_link"], style="filled", shape="rect")
            graph.edge("Root", tree_item["B_link"], tree_item["A_joint"], color="red", penwidth=str(5))
            self._create_graphviz_tree(tree_item["B_node"], robot, graph)

    def _create_robot_parser(self, robot):

        self._link_delegate = RobotDelegate()
        self.robot_model = RobotListModel(robot)
        import pprint

        robot_tree = self._urdf_interface.get_kinematic_chain(robot)
        robot_graph = Graph("robot_graph", strict=True, engine="dot")
        robot_graph.attr(rankdir="TB", splines="ortho")
        robot_graph.attr(packMode="node")
        with robot_graph.subgraph(name="cluster_legend") as legend_graph:
            legend_graph.attr(label="legend")
            legend_graph.node("legend_fixed", "Fixed", color="red", shape="rect", margin="0", height="0")
            legend_graph.node("legend_revolute", "Revolute", color="green", shape="rect", margin="0", height="0")
            legend_graph.node("legend_prismatic", "Prismatic", color="blue", shape="rect", margin="0", height="0")
            legend_graph.node("legend_continuous", "Continuous", color="orange", shape="rect", margin="0", height="0")

        im = None
        try:
            self._create_graphviz_tree(robot_tree, robot, robot_graph)
            buffer = io.BytesIO(robot_graph.pipe(format="png"))
            buffer.seek(0)
            im = Image.open(buffer)
            im.thumbnail([min(im.size[0], 3000), min(im.size[1], 3000)], Image.ANTIALIAS)
            # im.show()
            im = im.convert("RGBA")  # needed sometimes image changes to RGB without this
            print([im.size[0], im.size[1]])
        except Exception as e:
            im = None
            print("Error: ", e, ", graph generation disabled")
        with self._hstack:
            with ui.ScrollingFrame(horizontal_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_ALWAYS_OFF):
                ui.TreeView(self.robot_model, root_visible=False, delegate=self._link_delegate)
            if im is not None:
                with ui.ScrollingFrame():
                    self._rgb_byte_provider = omni.ui.ByteImageProvider()
                    self._rgb_byte_provider.set_data(list(im.tobytes("raw", "RGBA")), [im.size[0], im.size[1]])
                    omni.ui.ImageWithProvider(self._rgb_byte_provider, width=im.size[0], height=im.size[1])

    def _select_picked_folder_callback(self, path):
        if not path.startswith("omniverse:"):

            self.root_path, self.filename = os.path.split(os.path.abspath(path))
            self._imported_robot = self._urdf_interface.parse_urdf(self.root_path, self.filename, self.config)
            self._create_robot_parser(self._imported_robot)
        else:
            print("Omniverse Paths not Supported, Only local paths can be imported")

    def _parse_urdf(self):
        if self.models["clean_stage"].model.get_value_as_bool():
            asyncio.ensure_future(omni.kit.asyncapi.new_stage())

        self._filepicker = omni.kit.ui.FilePicker("Select URDF File", file_type=omni.kit.ui.FileDialogSelectType.FILE)
        self._filepicker.set_file_selected_fn(self._select_picked_folder_callback)
        self._filepicker.add_filter("URDF Files (*.urdf)", r".*.urdf$")
        data_dir = os.path.abspath(carb.tokens.get_tokens_interface().resolve("${app}/../data/urdf"))
        self._filepicker.set_current_directory(data_dir)
        self._filepicker.show()

    def _load_robot(self):
        self._urdf_interface.import_robot(self.root_path, self.filename, self._imported_robot, self.config)

    def on_shutdown(self):
        print("Shutting down URDF Extension")
        if self._file_picker is not None:
            self._file_picker.set_file_selected_fn(None)
            self._file_picker.set_dialog_cancelled_fn(None)
        _urdf.release_urdf_interface(self._urdf_interface)
