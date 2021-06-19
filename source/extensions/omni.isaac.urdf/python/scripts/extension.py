# Copyright (c) 2018-2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

import os
import omni.ext
import omni.ui as ui
import weakref
import gc
import carb
import asyncio

from omni.kit.menu.utils import add_menu_items, remove_menu_items, MenuItemDescription
from omni.kit.window.filepicker import FilePickerDialog
from omni.kit.window.content_browser import get_content_window

from .link_model import *
from omni.isaac.urdf import _urdf
from pxr import UsdGeom


EXTENSION_NAME = "URDF Importer"


def is_urdf_file(path: str):
    _, ext = os.path.splitext(path.lower())
    return ext in [".urdf", ".URDF"]


def on_filter_item(item) -> bool:
    if not item or item.is_folder:
        return not (item.name == "Omniverse" or item.path.startswith("omniverse:"))
    return is_urdf_file(item.path)


def on_filter_folder(item) -> bool:
    if item and item.is_folder:
        return True
    else:
        return False


class Extension(omni.ext.IExt):
    def on_startup(self, ext_id):

        self._urdf_interface = _urdf.acquire_urdf_interface()
        self._usd_context = omni.usd.get_context()
        self._window = omni.ui.Window(
            EXTENSION_NAME, width=600, height=400, visible=False, dockPreference=ui.DockPreference.LEFT_BOTTOM
        )
        self._window.deferred_dock_in("Console", omni.ui.DockPolicy.DO_NOTHING)
        self._window.set_visibility_changed_fn(self._on_window)
        self._menu_items = [
            MenuItemDescription(name=EXTENSION_NAME, onclick_fn=lambda a=weakref.proxy(self): a._menu_callback())
        ]
        add_menu_items(self._menu_items, "Isaac Utils")
        self._file_picker = None

        self._models = {}
        self._config = _urdf.ImportConfig()
        self._root_path = None
        self._filepicker = None
        self._content_browser = None
        self._extension_path = omni.kit.app.get_app().get_extension_manager().get_extension_path(ext_id)
        self._imported_robot = None

        self._content_browser = get_content_window()
        self._content_browser.toggle_bookmark_from_path(
            "Built In URDF Files", (self._extension_path + "/data/urdf"), True
        )
        self._init_context_menu()

    def build_ui(self):

        with self._window.frame:
            with ui.ScrollingFrame(horizontal_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_ALWAYS_OFF):
                with ui.HStack(spacing=4):
                    with ui.VStack(height=0):
                        with ui.CollapsableFrame("Parser Settings"):
                            with ui.VStack(height=0, spacing=4):
                                ui.Line(height=5)
                                with ui.HStack():
                                    ui.Label(
                                        "Merge Fixed Joints",
                                        tooltip="Check this box to skip adding articulation on fixed joints",
                                    )
                                    model = ui.CheckBox().model
                                    model.add_value_changed_fn(
                                        lambda m, config=self._config: config.set_merge_fixed_joints(
                                            m.get_value_as_bool()
                                        )
                                    )
                                    model.set_value(False)

                                # with ui.HStack():
                                #     ui.Label(
                                #         "Flip Visuals",
                                #         tooltip="Enable this if URDF visuals are Y up and not Z up. Visual meshes are flipped Y->Z up true.",
                                #     )
                                #     model = ui.CheckBox().model
                                #     model.add_value_changed_fn(
                                #         lambda m, config=self._config: config.set_flip_visuals(m.get_value_as_bool())
                                #     )
                                #     model.set_value(False)

                                with ui.HStack():
                                    ui.Label(
                                        "Import Inertia Tensor",
                                        tooltip="If True, inertia will be loaded from urdf, if the urdf does not specify inertia tensor, identity will be used and scaled by the scaling factor. If false physx will compute automatically",
                                    )
                                    ui.CheckBox().model.add_value_changed_fn(
                                        lambda m, config=self._config: config.set_import_inertia_tensor(
                                            m.get_value_as_bool()
                                        )
                                    )

                                with ui.HStack():
                                    ui.Label(
                                        "Link Density:",
                                        tooltip="[kg/m^3] If a link doesn't have mass, use this density as backup, A density of 0.0 results in the physics engine automatically computing density as well",
                                    )
                                    model = ui.FloatField().model
                                    model.add_value_changed_fn(
                                        lambda m, config=self._config: config.set_density(m.get_value_as_float())
                                    )
                                    model.set_value(0)

                                with ui.HStack():
                                    ui.Label("Joint Drive Type:")
                                    model = ui.ComboBox(1, "None", "Position", "Velocity").model
                                    model.add_item_changed_fn(
                                        lambda m, i, config=self._config: config.set_default_drive_type(
                                            m.get_item_value_model().as_int
                                        )
                                    )

                                with ui.HStack():
                                    ui.Label(
                                        "Joint Drive Strength:",
                                        tooltip="Corresponds to stiffness for position or damping for velocity",
                                    )
                                    model = ui.FloatField().model
                                    model.add_value_changed_fn(
                                        lambda m, config=self._config: config.set_default_drive_strength(
                                            m.get_value_as_float()
                                        )
                                    )
                                    model.set_value(100000)
                        ui.Button(
                            "Select and Parse URDF", tooltip="Select a urdf to parse", clicked_fn=self._parse_urdf
                        )
                        ui.Button(
                            "Show Parsed Data",
                            tooltip="Shows the materials, joints and links parsed from the selected urdf",
                            clicked_fn=self._show_parsed,
                        )
                    with ui.VStack(height=0, spacing=2):
                        with ui.CollapsableFrame("Importer Settings"):
                            with ui.VStack(height=0, spacing=4):
                                ui.Line(height=5)
                                with ui.HStack():
                                    ui.Label("Clean Stage", tooltip="Check this box to load URDF on a clean stage")
                                    self._models["clean_stage"] = ui.CheckBox()
                                    self._models["clean_stage"].model.set_value(False)

                                with ui.HStack():
                                    ui.Label(
                                        "Convex Decomposition",
                                        tooltip="If true, non-convex meshes will be decomposed into convex collision shapes, if false a convex hull will be used.",
                                    )
                                    model = ui.CheckBox().model
                                    model.add_value_changed_fn(
                                        lambda m, config=self._config: config.set_convex_decomp(m.get_value_as_bool())
                                    )
                                    model.set_value(False)

                                with ui.HStack():
                                    ui.Label(
                                        "Fix Base Link",
                                        tooltip="If true, enables the fix base property on the root of the articulation.",
                                    )
                                    model = ui.CheckBox().model
                                    model.add_value_changed_fn(
                                        lambda m, config=self._config: config.set_fix_base(m.get_value_as_bool())
                                    )
                                    model.set_value(True)

                                with ui.HStack():
                                    ui.Label(
                                        "Self Collision",
                                        tooltip="If true, allows self intersection between links in the robot, can cause instability if collision meshes between links are self intersecting",
                                    )
                                    model = ui.CheckBox().model
                                    model.add_value_changed_fn(
                                        lambda m, config=self._config: config.set_self_collision(m.get_value_as_bool())
                                    )
                                    model.set_value(False)

                                with ui.HStack():
                                    ui.Label("Create Physics Scene", tooltip="If true, creates a default physics scene")
                                    model = ui.CheckBox().model
                                    model.add_value_changed_fn(
                                        lambda m, config=self._config: config.set_create_physics_scene(
                                            m.get_value_as_bool()
                                        )
                                    )
                                    model.set_value(True)

                                with ui.HStack():
                                    ui.Label(
                                        "Make Default Prim",
                                        tooltip="If true, makes imported robot the default prim for the stage",
                                    )
                                    model = ui.CheckBox().model
                                    model.add_value_changed_fn(
                                        lambda m, config=self._config: config.set_make_default_prim(
                                            m.get_value_as_bool()
                                        )
                                    )
                                    model.set_value(True)
                                with ui.HStack():
                                    ui.Label("Stage Units Per Meter:")
                                    self._models["scale"] = ui.FloatField(enabled=True)
                                    self._models["scale"].model.add_value_changed_fn(
                                        lambda m, config=self._config: config.set_distance_scale(m.get_value_as_float())
                                    )
                        self._models["load_robot_btn"] = ui.Button(
                            "Import Robot To Stage",
                            tooltip="Import the parsed urdf into the stage as usd",
                            clicked_fn=self._load_robot,
                        )
                        self._models["load_robot_btn"].enabled = False

        stage = self._usd_context.get_stage()
        if stage:
            if UsdGeom.GetStageUpAxis(stage) == UsdGeom.Tokens.y:
                self._config.set_up_vector(0, 1, 0)
            if UsdGeom.GetStageUpAxis(stage) == UsdGeom.Tokens.z:
                self._config.set_up_vector(0, 0, 1)
            units_per_meter = 1.0 / UsdGeom.GetStageMetersPerUnit(stage)
            self._models["scale"].model.set_value(units_per_meter)

    def _menu_callback(self):
        self._window.visible = not self._window.visible

    def _on_window(self, visible):
        if self._window.visible:
            self.build_ui()
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
                self._config.set_up_vector(0, 1, 0)
            if UsdGeom.GetStageUpAxis(stage) == UsdGeom.Tokens.z:
                self._config.set_up_vector(0, 0, 1)
            units_per_meter = 1.0 / UsdGeom.GetStageMetersPerUnit(stage)
            self._models["scale"].model.set_value(units_per_meter)

    def _refresh_filebrowser(self):
        parent = None
        selection_name = None
        if len(self._filebrowser.get_selections()):
            parent = self._filebrowser.get_selections()[0].parent
            selection_name = self._filebrowser.get_selections()[0].name

        self._filebrowser.refresh_ui(parent)
        if selection_name:
            selection = [child for child in parent.children.values() if child.name == selection_name]
            if len(selection):
                self._filebrowser.select_and_center(selection[0])

    def _show_parsed(self):
        if self._imported_robot is not None:
            self._tree_window = ui.Window("Parsed URDF Data", width=500, height=400, flags=ui.WINDOW_FLAGS_MODAL)
            self._link_delegate = RobotDelegate()
            self._robot_model = RobotListModel(self._imported_robot)
            self._rgb_byte_provider = None
            self._rgb_image_provider = None
            # self._robot_graph_im = self._generate_robot_image(robot, vertical=True)
            with self._tree_window.frame:
                with ui.HStack():
                    with ui.CollapsableFrame():
                        ui.TreeView(self._robot_model, root_visible=False, delegate=self._link_delegate)

    def _select_picked_folder_callback(self, path):
        if not path.startswith("omniverse:"):
            self._root_path, self.filename = os.path.split(os.path.abspath(path))
            self._imported_robot = self._urdf_interface.parse_urdf(self._root_path, self.filename, self._config)
            self._models["load_robot_btn"].enabled = True
        else:
            print("Omniverse Paths not Supported, Only local paths can be imported")

    def _parse_urdf(self):
        self._filepicker = FilePickerDialog(
            "Import URDF",
            allow_multi_selection=False,
            apply_button_label="Import",
            click_apply_handler=lambda filename, path, c=weakref.proxy(self): c._select_picked_file_callback(
                self._filepicker, filename, path
            ),
            click_cancel_handler=lambda a, b, c=weakref.proxy(self): c._filepicker.hide(),
            item_filter_fn=on_filter_item,
            enable_versioning_pane=True,
        )

        self._filepicker.toggle_bookmark_from_path("Built In URDF Files", (self._extension_path + "/data/urdf"), True)
        self._filepicker.show()

    def _load_robot(self):
        if self._root_path:
            self._imported_robot = self._urdf_interface.parse_urdf(self._root_path, self.filename, self._config)

            async def import_with_clean_stage():
                await omni.usd.get_context().new_stage_async()
                await omni.kit.app.get_app().next_update_async()
                self._urdf_interface.import_robot(self._root_path, self.filename, self._imported_robot, self._config)
                await omni.kit.app.get_app().next_update_async()

            if self._models["clean_stage"].model.get_value_as_bool():
                asyncio.ensure_future(import_with_clean_stage())
            else:
                self._urdf_interface.import_robot(self._root_path, self.filename, self._imported_robot, self._config)

    def _parse_and_import(self, path=None):
        self._root_path, self.filename = os.path.split(os.path.abspath(path))
        self._imported_robot = self._urdf_interface.parse_urdf(self._root_path, self.filename, self._config)
        self._urdf_interface.import_robot(self._root_path, self.filename, self._imported_robot, self._config)

    def _select_picked_file_callback(self, dialog: FilePickerDialog, filename=None, path=None):
        print(filename, path)
        if not path.startswith("omniverse://"):
            self._root_path = path
            self.filename = filename
            if self._root_path and self.filename:

                self._imported_robot = self._urdf_interface.parse_urdf(self._root_path, self.filename, self._config)
                self._models["load_robot_btn"].enabled = True
            else:
                carb.log_error("path and filename not specified")
        else:
            self._root_path = ""
            self.filename = ""
            carb.log_error("Only Local Paths supported")
        dialog.hide()

    def _init_context_menu(self):
        if self._content_browser:
            self._context_menu = self._content_browser.add_context_menu(
                "Convert URDF to USD", "upload.svg", lambda menu, path: self._parse_and_import(path=path), is_urdf_file
            )

    def on_shutdown(self):
        if self._content_browser:
            self._content_browser.toggle_bookmark_from_path(
                "Built In URDF Files", (self._extension_path + "/data/urdf"), False
            )
            self._content_browser.delete_context_menu("Convert URDF to USD")
            self._content_browser = None
        if self._filepicker:
            self._filepicker.toggle_bookmark_from_path(
                "Built In URDF Files", (self._extension_path + "/data/urdf"), False
            )
            self._filepicker.destroy()
            self._filepicker = None

        remove_menu_items(self._menu_items, "Isaac Utils")
        if self._window:
            self._window = None
        gc.collect()
