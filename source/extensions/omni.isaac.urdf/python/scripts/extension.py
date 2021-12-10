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
from pxr import Usd, UsdGeom, Sdf, UsdPhysics
from omni.client._omniclient import Result
import omni.client

from omni.isaac.ui.ui_utils import float_builder, dropdown_builder, btn_builder, cb_builder, str_builder


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
        result, self._config = omni.kit.commands.execute("URDFCreateImportConfig")
        self._filepicker = None
        self._last_folder = None
        self._content_browser = None
        self._extension_path = omni.kit.app.get_app().get_extension_manager().get_extension_path(ext_id)
        self._imported_robot = None

        # Set defaults
        self._config.set_merge_fixed_joints(False)
        self._config.set_convex_decomp(False)
        self._config.set_fix_base(True)
        self._config.set_import_inertia_tensor(False)
        self._config.set_distance_scale(100.0)
        self._config.set_density(0.0)
        self._config.set_default_drive_type(1)
        self._config.set_default_drive_strength(1e7)
        self._config.set_default_position_drive_damping(1e5)
        self._config.set_self_collision(False)
        self._config.set_up_vector(0, 0, 1)
        self._config.set_make_default_prim(True)
        self._config.set_create_physics_scene(True)

    def build_ui(self):
        with self._window.frame:
            with ui.VStack(spacing=20, height=0):
                with ui.HStack(spacing=10):
                    with ui.VStack(spacing=2, height=0):
                        cb_builder(
                            label="Merge Fixed Joints",
                            tooltip="Check this box to skip adding articulation on fixed joints",
                            on_clicked_fn=lambda m, config=self._config: config.set_merge_fixed_joints(m),
                        )
                        cb_builder(
                            "Fix Base Link",
                            tooltip="If true, enables the fix base property on the root of the articulation.",
                            default_val=True,
                            on_clicked_fn=lambda m, config=self._config: config.set_fix_base(m),
                        )
                        cb_builder(
                            "Import Inertia Tensor",
                            tooltip="If True, inertia will be loaded from urdf, if the urdf does not specify inertia tensor, identity will be used and scaled by the scaling factor. If false physx will compute automatically",
                            on_clicked_fn=lambda m, config=self._config: config.set_import_inertia_tensor(m),
                        )
                        self._models["scale"] = float_builder(
                            "Stage Units Per Meter",
                            default_val=100.0,
                            tooltip="[1.0 / stage_units] Set the distance units the robot is imported as, default is 100.0 corresponding to cm",
                        )
                        self._models["scale"].add_value_changed_fn(
                            lambda m, config=self._config: config.set_distance_scale(m.get_value_as_float())
                        )
                        self._models["density"] = float_builder(
                            "Link Density",
                            default_val=0.0,
                            tooltip="[kg/stage_units^3] If a link doesn't have mass, use this density as backup, A density of 0.0 results in the physics engine automatically computing a default density",
                        )
                        self._models["density"].add_value_changed_fn(
                            lambda m, config=self._config: config.set_density(m.get_value_as_float())
                        )
                        dropdown_builder(
                            "Joint Drive Type",
                            items=["None", "Position", "Velocity"],
                            default_val=1,
                            on_clicked_fn=lambda i, config=self._config: config.set_default_drive_type(
                                0 if i == "None" else (1 if i == "Position" else 2)
                            ),
                            tooltip="Set the default drive configuration, None: stiffness and damping are zero, Position/Velocity: use default specified below.",
                        )
                        self._models["drive_strength"] = float_builder(
                            "Joint Drive Strength",
                            default_val=1e7,
                            tooltip="Corresponds to stiffness for position or damping for velocity, set to -1 to prevent this value from getting used",
                        )
                        self._models["drive_strength"].add_value_changed_fn(
                            lambda m, config=self._config: config.set_default_drive_strength(m.get_value_as_float())
                        )
                        self._models["position_drive_damping"] = float_builder(
                            "Joint Position Drive Damping",
                            default_val=1e5,
                            tooltip="If the drive type is set to position, this will be used as a default damping for the drive, set to -1 to prevent this from getting used",
                        )
                        self._models["position_drive_damping"].add_value_changed_fn(
                            lambda m, config=self._config: config.set_default_position_drive_damping(
                                m.get_value_as_float()
                            )
                        )

                    with ui.VStack(spacing=2, height=0):
                        self._models["clean_stage"] = cb_builder(
                            label="Clean Stage", tooltip="Check this box to load URDF on a clean stage"
                        )
                        cb_builder(
                            "Convex Decomposition",
                            tooltip="If true, non-convex meshes will be decomposed into convex collision shapes, if false a convex hull will be used.",
                            on_clicked_fn=lambda m, config=self._config: config.set_convex_decomp(m),
                        )

                        cb_builder(
                            "Self Collision",
                            tooltip="If true, allows self intersection between links in the robot, can cause instability if collision meshes between links are self intersecting",
                            on_clicked_fn=lambda m, config=self._config: config.set_self_collision(m),
                        )
                        cb_builder(
                            "Create Physics Scene",
                            tooltip="If true, creates a default physics scene if one does not already exist in the stage",
                            default_val=True,
                            on_clicked_fn=lambda m, config=self._config: config.set_create_physics_scene(m),
                        )
                        ui.Spacer(height=ui.Pixel(70))
                        # cb_builder(
                        #     "Make Default Prim",
                        #     tooltip="If true, makes imported robot the default prim for the stage",
                        #     default_val=True,
                        #     on_clicked_fn=lambda m, config=self._config: config.set_make_default_prim(m),
                        # )

                with ui.VStack(height=0):
                    with ui.HStack(spacing=20):
                        btn_builder("Import URDF", text="Select and Import", on_clicked_fn=self._parse_urdf)
                        kwargs = {
                            "label": "Output Directory",
                            "type": "stringfield",
                            "default_val": self.get_dest_folder(),
                            "tooltip": "Click the Folder Icon to Set Filepath",
                            "use_folder_picker": True,
                        }
                        self.dest_model = str_builder(**kwargs)

        stage = self._usd_context.get_stage()
        if stage:
            if UsdGeom.GetStageUpAxis(stage) == UsdGeom.Tokens.y:
                self._config.set_up_vector(0, 1, 0)
            if UsdGeom.GetStageUpAxis(stage) == UsdGeom.Tokens.z:
                self._config.set_up_vector(0, 0, 1)
            units_per_meter = 1.0 / UsdGeom.GetStageMetersPerUnit(stage)
            self._models["scale"].set_value(units_per_meter)

    def get_dest_folder(self):
        stage = omni.usd.get_context().get_stage()
        if stage:
            path = stage.GetRootLayer().identifier
            if not path.startswith("anon"):
                basepath = path[: path.rfind("/")]
                if path.rfind("/") < 0:
                    basepath = path[: path.rfind("\\")]
                return basepath
        return "(same as source)"

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
        if event.type == int(omni.usd.StageEventType.OPENED) and stage:
            if UsdGeom.GetStageUpAxis(stage) == UsdGeom.Tokens.y:
                self._config.set_up_vector(0, 1, 0)
            if UsdGeom.GetStageUpAxis(stage) == UsdGeom.Tokens.z:
                self._config.set_up_vector(0, 0, 1)
            units_per_meter = 1.0 / UsdGeom.GetStageMetersPerUnit(stage)
            self._models["scale"].set_value(units_per_meter)
            self.dest_model.set_value(self.get_dest_folder())

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
        if self._last_folder:
            self._filepicker.set_current_directory(self._last_folder)
            self._filepicker.navigate_to(self._last_folder)
            self._filepicker.refresh_current_directory()
        self._filepicker.toggle_bookmark_from_path("Built In URDF Files", (self._extension_path + "/data/urdf"), True)
        self._filepicker.show()

    def _load_robot(self, path=None):
        if path:

            dest_path = self.dest_model.get_value_as_string()
            base_path = path[: path.rfind("/")]
            basename = path[path.rfind("/") + 1 :]
            basename = basename[: basename.rfind(".")]
            if path.rfind("/") < 0:
                base_path = path[: path.rfind("\\")]
                basename = path[path.rfind("\\") + 1]

            if dest_path != "(same as source)":
                base_path = dest_path  # + "/" + basename

            dest_path = "{}/{}/{}.usd".format(base_path, basename, basename)
            # counter = 1
            # while result[0] == Result.OK:
            #     dest_path = "{}/{}_{:02}.usd".format(base_path, basename, counter)
            #     result = omni.client.read_file(dest_path)
            #     counter +=1
            # result = omni.client.read_file(dest_path)
            # if
            #     stage = Usd.Stage.Open(dest_path)
            # else:
            # stage = Usd.Stage.CreateNew(dest_path)
            # UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
            omni.kit.commands.execute(
                "URDFParseAndImportFile", urdf_path=path, import_config=self._config, dest_path=dest_path
            )
            # print("Created file, instancing it now")
            stage = Usd.Stage.Open(dest_path)
            prim_name = str(stage.GetDefaultPrim().GetName())
            # print(prim_name)
            # stage.Save()
            def add_reference_to_stage():
                current_stage = omni.usd.get_context().get_stage()
                if current_stage:
                    prim_path = omni.usd.get_stage_next_free_path(
                        current_stage, str(current_stage.GetDefaultPrim().GetPath()) + "/" + prim_name, False
                    )
                    robot_prim = current_stage.OverridePrim(prim_path)
                    if "anon:" in current_stage.GetRootLayer().identifier:
                        robot_prim.GetReferences().AddReference(dest_path)
                    else:
                        robot_prim.GetReferences().AddReference(
                            omni.client.make_relative_url(current_stage.GetRootLayer().identifier, dest_path)
                        )
                    if self._config.create_physics_scene:
                        UsdPhysics.Scene.Define(current_stage, Sdf.Path("/physicsScene"))

            async def import_with_clean_stage():
                await omni.usd.get_context().new_stage_async()
                await omni.kit.app.get_app().next_update_async()
                add_reference_to_stage()
                await omni.kit.app.get_app().next_update_async()

            if self._models["clean_stage"].get_value_as_bool():
                asyncio.ensure_future(import_with_clean_stage())
            else:
                add_reference_to_stage()

    def _select_picked_file_callback(self, dialog: FilePickerDialog, filename=None, path=None):
        if not path.startswith("omniverse://"):
            if path and filename:
                self._last_folder = path
                self._load_robot(path + "/" + filename)
            else:
                carb.log_error("path and filename not specified")
        else:
            carb.log_error("Only Local Paths supported")
        dialog.hide()

    def on_shutdown(self):
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
