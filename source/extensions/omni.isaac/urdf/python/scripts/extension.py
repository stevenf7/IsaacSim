import os
import omni.ext
import omni.kit.commands
import omni.kit.editor
import omni.ui as ui
import carb.tokens
import asyncio
import textwrap
from .link_model import *

from .. import _urdf
from pxr import UsdGeom
from omni.isaac.utils.scripts.filebrowser import *

EXTENSION_NAME = "URDF Importer"


def on_filter_item(item: FileBrowserItem) -> bool:
    if not item or item.is_folder:
        return True
    _, ext = os.path.splitext(item.path)
    if ext.lower() in [".urdf"]:
        return True
    else:
        return False


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
        self._rgb_byte_provider = None
        self._rgb_image_provider = None
        self._robot_graph_im = None

        self._file_window = omni.ui.Window("Open URDF File", width=600, height=400, visible=False)
        with self._file_window.frame:
            with ui.VStack():
                self._filebrowser = FileBrowserWidget(
                    "Omniverse",
                    layout=LAYOUT_SINGLE_PANE_SLIM,
                    allow_multi_selection=False,
                    show_grid_view=False,
                    tree_root_visible=False,
                    mouse_double_clicked_fn=self._on_double_pressed,
                    filter_fn=on_filter_item,
                )

                ui.Button("Open File", clicked_fn=self._on_open_selected, height=0)

        with self._window.frame:
            with ui.ScrollingFrame(
                horizontal_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_ALWAYS_OFF,
                vertical_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_ALWAYS_OFF,
            ):
                with ui.HStack():
                    with ui.VStack(width=ui.Percent(30), height=0):
                        ui.Button("Parse URDF", clicked_fn=self._parse_urdf)
                        ui.Button("Load Robot", clicked_fn=self._load_robot)
                        ui.Label("Parser Settings (Set before Parsing URDF):")
                        ui.Line(height=5)
                        with ui.HStack():
                            ui.Label(
                                "Merge Fixed Joints",
                                tooltip="Check this box to skip adding articulation on fixed joints",
                            )
                            model = ui.CheckBox().model
                            model.add_value_changed_fn(
                                lambda m, config=self.config: config.set_merge_fixed_joints(m.get_value_as_bool())
                            )
                            model.set_value(False)
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
                        ui.Label("Parser Defaults:")
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
                            ui.Label(
                                "Joint Drive Strength:",
                                tooltip="Corresponds to stiffness for position or damping for velocity",
                            )
                            model = ui.FloatField().model
                            model.add_value_changed_fn(
                                lambda m, config=self.config: config.set_default_drive_strength(m.get_value_as_float())
                            )
                            model.set_value(100000)
                        ui.Line(height=5)
                        ui.Spacer(height=15)
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
                        with ui.HStack():
                            ui.Label("Create Physics Scene", tooltip="If true, creates a default physics scene")
                            model = ui.CheckBox().model
                            model.add_value_changed_fn(
                                lambda m, config=self.config: config.set_create_physics_scene(m.get_value_as_bool())
                            )
                            model.set_value(True)
                        ui.Spacer(height=5)
                        with ui.HStack():
                            ui.Label(
                                "Make Default Prim",
                                tooltip="If true, makes imported robot the default prim for the stage",
                            )
                            model = ui.CheckBox().model
                            model.add_value_changed_fn(
                                lambda m, config=self.config: config.set_make_default_prim(m.get_value_as_bool())
                            )
                            model.set_value(True)
                        # ui.Spacer(height=5)

                        # with ui.HStack():
                        #     ui.Label("Up Axis:")
                        #     self.models["up_axis"] = ui.MultiFloatField(0.0, 0.0, 1.0)
                        #     self.models["up_axis"].model.add_item_changed_fn(
                        #         lambda m, n, config=self.config: config.set_up_vector(
                        #             m.get_item_value_model(m.get_item_children()[0]).get_value_as_float(),
                        #             m.get_item_value_model(m.get_item_children()[1]).get_value_as_float(),
                        #             m.get_item_value_model(m.get_item_children()[2]).get_value_as_float(),
                        #         )
                        #     )
                        ui.Spacer(height=5)
                        with ui.HStack():
                            ui.Label("Stage Units Per Meter:")
                            self.models["scale"] = ui.FloatField(enabled=True)
                            self.models["scale"].model.add_value_changed_fn(
                                lambda m, config=self.config: config.set_distance_scale(m.get_value_as_float())
                            )
                    self._frame = ui.Frame()

        stage = self._usd_context.get_stage()
        if stage:
            if UsdGeom.GetStageUpAxis(stage) == UsdGeom.Tokens.y:
                # self.models["up_axis"].model.get_item_value_model(
                #     self.models["up_axis"].model.get_item_children()[0]
                # ).set_value(0)
                # self.models["up_axis"].model.get_item_value_model(
                #     self.models["up_axis"].model.get_item_children()[1]
                # ).set_value(1)
                # self.models["up_axis"].model.get_item_value_model(
                #     self.models["up_axis"].model.get_item_children()[2]
                # ).set_value(0)
                self.config.set_up_vector(0, 1, 0)
            if UsdGeom.GetStageUpAxis(stage) == UsdGeom.Tokens.z:
                # self.models["up_axis"].model.get_item_value_model(
                #     self.models["up_axis"].model.get_item_children()[0]
                # ).set_value(0)
                # self.models["up_axis"].model.get_item_value_model(
                #     self.models["up_axis"].model.get_item_children()[1]
                # ).set_value(0)
                # self.models["up_axis"].model.get_item_value_model(
                #     self.models["up_axis"].model.get_item_children()[2]
                # ).set_value(1)
                self.config.set_up_vector(0, 0, 1)
            units_per_meter = 1.0 / UsdGeom.GetStageMetersPerUnit(stage)
            self.models["scale"].model.set_value(units_per_meter)

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

    def _generate_robot_image(self, robot, vertical=True):
        from graphviz import Graph

        im = None
        robot_tree = self._urdf_interface.get_kinematic_chain(robot)

        robot_graph = Graph("robot_graph", strict=True, engine="dot")
        robot_graph.attr(splines="ortho")
        if vertical:
            robot_graph.attr(rankdir="TB")
        else:
            robot_graph.attr(rankdir="LR")

        robot_graph.attr(packMode="node")
        with robot_graph.subgraph(name="cluster_legend") as legend_graph:
            legend_graph.attr(label="legend")
            legend_graph.node("legend_fixed", "Fixed", color="red", shape="rect", margin="0", height="0")
            legend_graph.node("legend_revolute", "Revolute", color="green", shape="rect", margin="0", height="0")
            legend_graph.node("legend_prismatic", "Prismatic", color="blue", shape="rect", margin="0", height="0")
            legend_graph.node("legend_continuous", "Continuous", color="orange", shape="rect", margin="0", height="0")

        try:
            from PIL import Image
            import io

            self._create_graphviz_tree(robot_tree, robot, robot_graph)
            buffer = io.BytesIO(robot_graph.pipe(format="png"))
            buffer.seek(0)
            im = Image.open(buffer)
            im.thumbnail([min(im.size[0], 3000), min(im.size[1], 3000)], Image.ANTIALIAS)
            # im.show()
            im = im.convert("RGBA")  # needed sometimes as image can change to RGB without this
        except Exception as e:
            im = None
            print("Error: ", e, ", graph generation disabled")
        return im

    def _create_ui(self, robot):

        self._link_delegate = RobotDelegate()
        self._robot_model = RobotListModel(robot)
        self._rgb_byte_provider = None
        self._rgb_image_provider = None
        self._robot_graph_im = self._generate_robot_image(robot, vertical=True)
        with self._frame:
            with ui.HStack():
                with ui.ScrollingFrame():
                    ui.TreeView(self._robot_model, root_visible=False, delegate=self._link_delegate)
                if self._robot_graph_im is not None:
                    with ui.VStack():
                        with ui.ScrollingFrame():
                            self._rgb_byte_provider = omni.ui.ByteImageProvider()
                            self._rgb_image_provider = omni.ui.ImageWithProvider(
                                self._rgb_byte_provider,
                                width=self._robot_graph_im.size[0],
                                height=self._robot_graph_im.size[1],
                                fill_policy=ui.IwpFillPolicy.IWP_PRESERVE_ASPECT_FIT,
                            )

                            self._rgb_byte_provider.set_data(
                                list(self._robot_graph_im.tobytes("raw", "RGBA")),
                                [int(self._robot_graph_im.size[0]), int(self._robot_graph_im.size[1])],
                            )

                        def scale_image(scale):
                            self._rgb_image_provider.width = ui.Length(scale[0])
                            self._rgb_image_provider.height = ui.Length(scale[1])

                        def update_image(vertical=True):
                            self._robot_graph_im = self._generate_robot_image(robot, vertical=vertical)
                            # if im is not None:
                            self._rgb_byte_provider.set_data(
                                list(self._robot_graph_im.tobytes("raw", "RGBA")),
                                [int(self._robot_graph_im.size[0]), int(self._robot_graph_im.size[1])],
                            )
                            scale_image([int(self._robot_graph_im.size[0]), int(self._robot_graph_im.size[1])])

                        with ui.HStack(height=0):
                            ui.Label("Scale: ", width=0)
                            model = ui.FloatDrag(min=0.1, height=0).model
                            model.set_value(1.0)
                            model.add_value_changed_fn(
                                lambda m: (
                                    scale_image(
                                        (
                                            int(self._robot_graph_im.size[0] * m.get_value_as_float()),
                                            int(self._robot_graph_im.size[1] * m.get_value_as_float()),
                                        )
                                    )
                                )
                            )
                        with ui.HStack(height=0):
                            ui.Label("Layout Orientation: ", width=0)
                            model = ui.ComboBox(1, "Horizontal", "Vertical").model
                            model.add_item_changed_fn(lambda m, i: (update_image(m.get_item_value_model().as_int)))

    def _on_double_pressed(self, button: ui.Button, item: FileBrowserItem):
        if item and not item.is_folder:
            self._file_window.visible = False
            self._select_picked_folder_callback(item.path)

    def _on_open_selected(self):
        if self._filebrowser:
            item = self._filebrowser.get_selections()[0]
        if item and not item.is_folder:
            self._file_window.visible = False
            self._select_picked_folder_callback(item.path)

    def _select_picked_folder_callback(self, path):
        if not path.startswith("omniverse:"):
            self.root_path, self.filename = os.path.split(os.path.abspath(path))
            self._imported_robot = self._urdf_interface.parse_urdf(self.root_path, self.filename, self.config)
            self._create_ui(self._imported_robot)
        else:
            print("Omniverse Paths not Supported, Only local paths can be imported")

    def _parse_urdf(self):
        if self.models["clean_stage"].model.get_value_as_bool():
            asyncio.ensure_future(omni.kit.asyncapi.new_stage())
        import psutil

        partitions = psutil.disk_partitions()
        for p in partitions:
            if any(x in p.fstype for x in ["ext3", "ext4", "fuseblk", "NTFS", "removable", "fixed"]):
                mountpoint = p.mountpoint.strip("\\")
                self._filebrowser.add_model_as_subtree(FileSystemModel(mountpoint, mountpoint))
        data_dir = os.path.abspath(carb.tokens.get_tokens_interface().resolve("${app}/../data/urdf"))
        self._filebrowser.add_model_as_subtree(FileSystemModel("Built In URDFs", data_dir))
        if len(self._filebrowser.get_selections()):
            item = self._filebrowser.get_selections()[0]
            item.parent.populated = False
        else:
            item = self._filebrowser._models.root
            item.populated = False
        self._filebrowser.refresh_ui(None)
        self._file_window.visible = True

    def _load_robot(self):
        self._urdf_interface.import_robot(self.root_path, self.filename, self._imported_robot, self.config)

    def on_shutdown(self):
        if self._filebrowser:
            self._filebrowser._mouse_double_clicked_fn = None
            self._filebrowser._filter_fn = None
            self._filebrowser = None
        if self._file_window:
            self._file_window = None
        if self._window:
            self._window = None
        _urdf.release_urdf_interface(self._urdf_interface)
