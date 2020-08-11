import os
import omni.ext
import omni.kit.commands
import omni.kit.editor
import omni.ui as ui
import carb.tokens
import asyncio
from .material_model import *
from .. import _urdf
from pxr import UsdGeom

EXTENSION_NAME = "URDF Importer"


class Extension(omni.ext.IExt):
    def on_startup(self):
        self._urdf_interface = _urdf.acquire_urdf_interface()
        self._usd_context = omni.usd.get_context()
        menu_path = f"Window/Isaac/{EXTENSION_NAME}"
        self._window = omni.ui.Window(EXTENSION_NAME, width=600, height=400, visible=False)
        self._menu_entry = omni.kit.ui.get_editor_menu().add_item(f"Window/Isaac/URDF Importer", self._menu_callback)
        self._file_picker = None
        self.models = {}
        with self._window.frame:
            with ui.VStack():
                with ui.HStack():
                    ui.Button("Parse URDF", clicked_fn=self._parse_urdf)
                    with ui.VStack(height=0):
                        ui.Label("Parser Settings:")
                        ui.Line(height=10)
                        with ui.HStack():
                            ui.Label(
                                "Merge Fixed Joints",
                                tooltip="Check this box to skip adding articulation on fixed joints",
                                width=ui.Percent(60),
                            )
                            self.models["merge_fixed"] = ui.CheckBox()
                        ui.Spacer(height=10)
                        with ui.HStack():
                            ui.Label(
                                "Import Inertia Tensor",
                                tooltip="If True, inertia will be loaded from urdf, if the urdf does not specify inertia tensor, identity will be used and scaled by the scaling factor. If false physx will compute automatically",
                                width=ui.Percent(60),
                            )
                            self.models["import_inertia"] = ui.CheckBox()
                        ui.Spacer(height=10)

                with ui.HStack():
                    ui.Button("Load Robot", clicked_fn=self._load_robot)
                    with ui.VStack(height=0):
                        ui.Label("Importer Settings:")
                        ui.Line(height=10)
                        with ui.HStack():
                            ui.Label(
                                "Clean Stage",
                                tooltip="Check this box to load URDF on a clean stage",
                                width=ui.Percent(60),
                            )
                            self.models["clean_stage"] = ui.CheckBox()
                            self.models["clean_stage"].model.set_value(True)
                        ui.Spacer(height=10)
                        with ui.HStack():
                            ui.Label(
                                "Enable Convex Decomposition",
                                tooltip="If true, non-convex meshes will be decomposed into convex collision shapes, if false a convex hull will be used.",
                                width=ui.Percent(60),
                            )
                            self.models["convex_decomp"] = ui.CheckBox()
                            self.models["convex_decomp"].model.set_value(True)
                        ui.Spacer(height=10)
                with ui.VStack(height=0):
                    with ui.HStack():
                        ui.Label("Current Stage Up Axis Used For Import:")
                        self.models["up_axis"] = ui.ComboBox(0, "Y", "Z", enabled=False)
                    with ui.HStack():
                        ui.Label("Current Stage Units Per Meter Used For Import:")
                        self.models["scale"] = ui.FloatDrag(enabled=False)

        stage = self._usd_context.get_stage()
        if stage:
            if UsdGeom.GetStageUpAxis(stage) == UsdGeom.Tokens.y:
                self.models["up_axis"].model.get_item_value_model(None).set_value(0)
            if UsdGeom.GetStageUpAxis(stage) == UsdGeom.Tokens.z:
                self.models["up_axis"].model.get_item_value_model(None).set_value(1)
            units_per_meter = 1.0 / UsdGeom.GetStageMetersPerUnit(stage)
            self.models["scale"].model.set_value(units_per_meter)
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
                self.models["up_axis"].model.get_item_value_model(None).set_value(0)
            if UsdGeom.GetStageUpAxis(stage) == UsdGeom.Tokens.z:
                self.models["up_axis"].model.get_item_value_model(None).set_value(1)

    def _print_robot(self):
        for key, value in self._imported_robot.materials.items():
            print(value.color.r, value.color.g, value.color.b)

    def _create_robot_parser(self, robot):
        self._robot_window = ui.Window("robot editor", width=600, height=200)
        self._tp_delegate = MaterialPropertiesDelegate()
        self._tp_model = MaterialPropertiesListModel(robot.materials)

        with self._robot_window.frame:
            with ui.VStack(height=ui.Percent(100)):
                with ui.CollapsableFrame("Material List", height=ui.Percent(100)):
                    with ui.ScrollingFrame(vertical_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_ALWAYS_ON):
                        self._tesselation_properties_list = ui.TreeView(
                            self._tp_model,
                            # style=self.tree_style,
                            delegate=self._tp_delegate,
                            header_visible=True,
                            # height=ui.Percent(100),
                            alignment=ui.Alignment.CENTER_TOP,
                        )
                ui.Button("Dump Robot", clicked_fn=self._print_robot)

    def _select_picked_folder_callback(self, path):
        if not path.startswith("omniverse:"):
            config = _urdf.ImportConfig()
            config.merge_fixed_joints = self.models["merge_fixed"].model.get_value_as_bool()
            config.enable_convex_decomp = self.models["convex_decomp"].model.get_value_as_bool()
            config.import_inertia_tensor = self.models["import_inertia"].model.get_value_as_bool()
            self.root_path, self.filename = os.path.split(os.path.abspath(path))
            self._imported_robot = self._urdf_interface.parse_urdf(self.root_path, self.filename, config)
            # self._create_robot_parser(self._imported_robot)
        else:
            print("Only local paths supported currently")

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
        config = _urdf.ImportConfig()
        config.merge_fixed_joints = self.models["merge_fixed"].model.get_value_as_bool()
        config.enable_convex_decomp = self.models["convex_decomp"].model.get_value_as_bool()
        config.import_inertia_tensor = self.models["import_inertia"].model.get_value_as_bool()

        self._urdf_interface.import_robot(self.root_path, self.filename, self._imported_robot, config)

    def on_shutdown(self):
        print("Shutting down URDF Extension")
        if self._file_picker is not None:
            self._file_picker.set_file_selected_fn(None)
            self._file_picker.set_dialog_cancelled_fn(None)
        _urdf.release_urdf_interface(self._urdf_interface)
