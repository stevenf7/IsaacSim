import omni.ext
import omni.kit.commands
import omni.ui as ui
from omni.kit.menu.utils import add_menu_items, remove_menu_items, MenuItemDescription

import os
import gc
import carb
import asyncio
import weakref

import platform

from functools import wraps, partial
from pathlib import Path

from . import usd_exporter
from .assembly_widget import *
from .tesselation_props_list import *
from .mesh_list_widget import *
from .style import *

# from .. import _step_importer
from omni.isaac.step_importer import _step_importer

from omni.kit.widget.filebrowser import FileBrowserItemFactory, FileSystemItem
from omni.kit.window.filepicker import FilePickerDialog
from omni.kit.window.content_browser import get_content_window


EXTENSION_NAME = "Step Importer"
SETTING_SAVED_CONNECTIONS = "/persistent/app/omniverse/savedServers"


def is_step_file(path: str):
    _, ext = os.path.splitext(path.lower())
    return ext in [".stp", ".step"]


def on_filter_item(item) -> bool:
    if not item or item.is_folder:
        # Bookmarks are listed as NucleusItem
        return not (
            item.name == "Omniverse"
        )  # or isinstance(item, omni.kit.widget.filebrowser.nucleus_model.NucleusItem))
    return is_step_file(item.path)


def on_filter_folder(item) -> bool:
    if item and item.is_folder:
        return True
    else:
        return False


class StepImporter(omni.ext.IExt):
    def on_startup(self, ext_id):
        self.ext_id = ext_id
        carb.log_info("Loading Step Importer Extension")
        self._si = _step_importer.acquire_interface()
        self.part = _step_importer.Part()
        self.exporter = None
        self.path = ""
        self._window = None
        self._assembly_model = None
        self._mesh_model = None

        self.build_steps = []
        self.build_steps_fns = [self.build_step_0, self.build_step_1, self.build_step_1]
        self.current_step = -1

        self.asset_importer = None

        self._content_browser = get_content_window()
        self._init_context_menu()

        self._folder_picker = FilePickerDialog(
            "Select output",
            allow_multi_selection=False,
            apply_button_label="Select folder",
            click_apply_handler=lambda a, b, c=weakref.proxy(self): c._on_open_folder_selected(a, b),
            click_cancel_handler=lambda a, b, c=weakref.proxy(self): c._on_picker_cancel(a, b),
            item_filter_fn=on_filter_folder,
        )
        self._filepicker = FilePickerDialog(
            "Import STEP",
            allow_multi_selection=False,
            apply_button_label="Import",
            click_apply_handler=lambda a, b, c=weakref.proxy(self): c._select_picked_file_callback(a, b),
            click_cancel_handler=lambda a, b, c=weakref.proxy(self): c._on_picker_cancel(a, b),
            item_filter_fn=on_filter_item,
        )
        self.extension_path = omni.kit.app.get_app().get_extension_manager().get_extension_path(self.ext_id)

        # self._filepicker.add_connections({"Built In STEP Files":(extension_path + "/data/step")})
        self._filepicker.toggle_bookmark_from_path("Built In STEP Files", (self.extension_path + "/data/step"), True)
        self._filepicker.hide()
        self._folder_picker.hide()

        self._tesselation_properties_list = None
        self._treeView = None
        self._mesh_list = None
        self.step_file = None

        self._usd_context = omni.usd.get_context()
        self._tesselation_properties_list = None
        self.stage = self._usd_context.get_stage()
        self._selection = self._usd_context.get_selection()
        self._events = self._usd_context.get_stage_event_stream()
        self._stage_event_subscription = self._events.create_subscription_to_pop(
            self._on_stage_event, name="UsdShadeGraphModel Selection Watch"
        )

        self._style = "NvidiaDark"

        self._menu_items = [
            MenuItemDescription(name="Step Importer", onclick_fn=lambda a=weakref.proxy(self): a.build_ui())
        ]
        add_menu_items(self._menu_items, "Isaac Utils")

        if self._style == "NvidiaLight":
            self.tree_style = tree_style_light
            self.menu_button_style = menu_button_light

        else:
            self.tree_style = tree_style_dark
            self.menu_button_style = menu_button_dark

        self._delegate = AssemblyDelegate()

        # self.show_window(None, True)
        self._build_ui()

    def _init_context_menu(self):
        self._context_menu = self._content_browser.add_context_menu(
            "Convert STEP to USD",
            "upload.svg",
            lambda menu, path: weakref.proxy(self)._select_picked_file_callback(path=path),
            is_step_file,
        )

    def _unregister_menus(self):
        self._content_browser.delete_context_menu("Convert STEP to USD")

    def _on_stage_event(self, event):
        """Called with omni.usd.context when stage event"""

        if event.type == int(omni.usd.StageEventType.SELECTION_CHANGED):
            self._on_kit_selection_changed()
        if event.type == int(omni.usd.StageEventType.OPENED):
            if self.exporter:
                try:
                    self.exporter.set_materials_to_color_layer()
                except:
                    pass

            if self._mesh_model:
                self._mesh_model.update_prim_paths()

            if self._assembly_model:
                self._assembly_model.update()

    def _select_meshes_with_same_volume(self):
        selection = []
        volumes = [item for item in self._mesh_list.selection]
        selection += volumes
        to_select = []
        for v in volumes:
            to_select = list(set(to_select + [i for i in self._mesh_list.model._children if v.is_similar(i)]))
        selection = selection + [i for i in list(set(to_select)) if i not in selection]
        self._mesh_list.selection = selection

    def get_selected_prim_paths(self, source):
        selection = []
        for item in self._mesh_list.selection:
            selection = selection + [i for i in item.prims if i not in selection]
        return [str(i.GetPath()) for i in selection]

    def toggle_selected_visibility(self):
        omni.kit.commands.execute(
            "ToggleVisibilitySelectedPrimsCommand", selected_paths=self.get_selected_prim_paths(self._mesh_list)
        )

    def ReplaceDuplicatesSelected(self):
        if len(self._mesh_list.selection):
            mesh_id = self._mesh_list.selection[0].id
            for i in range(1, len(self._mesh_list.selection)):
                self._mesh_list.selection[i].set_replacement_id(mesh_id)
            self._mesh_model.export_model()

    def _on_kit_selection_changed(self):
        """The selection in kit is changed"""
        if self.exporter:
            selection = []
            for sel in self._selection.get_selected_prim_paths():
                if sel.startswith("/Looks"):
                    self.exporter.set_material_authoring_layer()
                    return
                usd_path = ""
                current_sel = sel
                prim = self._usd_context.get_stage().GetPrimAtPath(sel)
                identifier = (prim.GetPrimStack()[-1]).layer.identifier
                if "meshes" in identifier:
                    if self.exporter.path.lower() in identifier.lower():
                        usd_path = os.path.relpath(identifier, self.exporter.path).replace("\\", "/")
                        if self._mesh_model._childrenMap[usd_path] not in selection:
                            selection.append(self._mesh_model._childrenMap[usd_path])

            self.exporter.set_root_authoring_layer()
            self._mesh_list.selection = [i for i in self._mesh_list.selection if i in selection] + [
                i for i in list(set(selection)) if i not in self._mesh_list.selection
            ]

    def _on_mesh_list_selection_changed(self, source):
        selection = self.get_selected_prim_paths(source)
        self._selection.set_selected_prim_paths(selection, False)

    def select_step(self, step):
        if step != self.current_step:
            if self.current_step >= 0:
                self.build_steps[self.current_step].visible = False
                self.step_btns[self.current_step].selected = False
            self.current_step = step
            self.build_steps[self.current_step].visible = True
            self.step_btns[self.current_step].selected = True

    def select_step_0(self):
        self.select_step(0)

    def select_step_1(self):
        self.select_step(1)

    def build_step_0(self, container):
        with container:
            self._step_picker_button = ui.Button("load Preview", clicked_fn=self._select_file)

    def show_full_part(self):
        self._delegate.on_mouse_double_clicked(self._assembly_model._root.children[0])

    def on_edit_names(self):
        self._mesh_model.toggle_edit_mode()
        if self._mesh_model.edit_mode:
            self.edit_meshes_btn.text = "Done Editing Names"
        else:
            self.edit_meshes_btn.text = "Edit Mesh Names"

    def on_edit_assembly_names(self):
        self._assembly_model.toggle_edit_mode()
        if self._assembly_model.edit_mode:
            self.edit_assembly_name_btn.text = "Done Editing Names"
        else:
            self.edit_assembly_name_btn.text = "Edit Assembly Names"

    def build_step_1(self, container):
        self._tp_delegate = TesselationPropsDelegate()
        props = _step_importer.Tesselation_Properties()
        props.max_linear_offset = 0.1
        props.max_angular_offset = 1.0
        props.min_surface = 0.2
        props.use_relative_offset = False
        props.use_internal_vertices = True
        props.volumetric_center_meshes = True
        self._tp_model = TesselationPropertiesListModel([props])

        self._mesh_delegate = MeshListDelegate()
        self._mesh_model = MeshListModel()

        with container:
            with ui.VStack(aligmnent=ui.Alignment.LEFT_TOP):
                with ui.CollapsableFrame("LOD properties", height=ui.Pixel(0)):
                    with ui.HStack(height=ui.Percent(100)):
                        with ui.VStack(width=ui.Pixel(20)):
                            ui.Spacer(height=ui.Pixel(13))
                            self._add_lod = ui.Button(
                                "+", clicked_fn=self._tp_model.add_prop, height=ui.Pixel(20), width=ui.Pixel(20)
                            )
                            self._remove_lod = ui.Button(
                                "-",
                                clicked_fn=self.remove_selected_lod,
                                height=ui.Pixel(20),
                                width=ui.Pixel(20),
                                tooltip="Removes selected element from the list. if None is selected, removes last.",
                            )
                        with ui.ScrollingFrame(
                            horizontal_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_ALWAYS_OFF,
                            # vertical_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_ALWAYS_ON,
                            # style_type_name_override="TreeView.ScrollingFrame",
                            style=self.tree_style,
                            height=ui.Pixel(90),
                        ):
                            self._tesselation_properties_list = ui.TreeView(
                                self._tp_model,
                                style=self.tree_style,
                                delegate=self._tp_delegate,
                                header_visible=True,
                                height=ui.Pixel(88),
                                alignment=ui.Alignment.CENTER_TOP,
                            )
                ui.Spacer(height=10)
                with ui.CollapsableFrame("Edit / Reimport Meshes", height=ui.Pixel(0)):
                    with ui.VStack(height=ui.Pixel(200)):
                        with ui.HStack():
                            with ui.ScrollingFrame(
                                horizontal_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_ALWAYS_OFF,
                                # vertical_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_ALWAYS_ON,
                                style_type_name_override="TreeView.ScrollingFrame",
                                style=self.tree_style,
                                height=ui.Pixel(198),
                            ):
                                self._mesh_list = ui.TreeView(
                                    self._mesh_model,
                                    style=self.tree_style,
                                    delegate=self._mesh_delegate,
                                    header_visible=True,
                                    height=ui.Percent(100),
                                    tooltip="Double click on item open isolated mesh",
                                    column_widths=[ui.Fraction(1), 60, 40, 150, 40],
                                )
                                self._mesh_list.set_selection_changed_fn(self._on_mesh_list_selection_changed)
                            with ui.VStack(width=80):
                                ui.Button("Show Full Part", clicked_fn=self.show_full_part, height=ui.Pixel(25))
                                ui.Button(
                                    "Find Similar Meshes",
                                    clicked_fn=self._select_meshes_with_same_volume,
                                    height=ui.Pixel(25),
                                    tooltip="Selects Potential duplicate meshes based on metadata",
                                )
                                ui.Button(
                                    "Toggle Visibility",
                                    clicked_fn=self.toggle_selected_visibility,
                                    height=ui.Pixel(25),
                                    tooltip="Show/Hide selected meshes",
                                )
                                self.edit_meshes_btn = ui.Button(
                                    "Edit Mesh Names",
                                    height=ui.Pixel(25),
                                    tooltip="Allow editing mesh names and updates assemblies.",
                                )
                                self.edit_meshes_btn.set_clicked_fn(self.on_edit_names)
                                ui.Button(
                                    "Remove selected duplicates",
                                    clicked_fn=self.ReplaceDuplicatesSelected,
                                    height=ui.Pixel(25),
                                    tooltip="Replaces all selected meshes with a single instance (First selected)",
                                )
                                with ui.HStack(tooltip="Import the meshes with given LOD properties"):
                                    ui.Spacer(width=ui.Pixel(5))
                                    ui.Label("Re-Mesh", height=ui.Pixel(25), width=ui.Pixel(30))
                                    ui.Spacer()
                                    ui.Button("All", clicked_fn=self.reimport_all_meshes, height=ui.Pixel(25))
                                    ui.Button("Selected", clicked_fn=self.reimport_selected_meshes, height=ui.Pixel(25))
                                    ui.Spacer()
                ui.Spacer(height=10)
                with ui.CollapsableFrame("Assembly Description", height=ui.Pixel(0)):
                    with ui.VStack(height=ui.Pixel(200)):
                        with ui.HStack():
                            self._sf = ui.ScrollingFrame(
                                horizontal_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_ALWAYS_OFF,
                                vertical_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_ALWAYS_ON,
                                style_type_name_override="TreeView.ScrollingFrame",
                                style=self.tree_style,
                                height=ui.Percent(98),
                            )

                            with self._sf:
                                self._treeView = ui.TreeView(
                                    self._assembly_model,
                                    column_widths=[ui.Fraction(1), 80],
                                    root_visible=False,
                                    header_visible=True,
                                    delegate=self._delegate,
                                    style=self.tree_style,
                                    height=ui.Percent(98),
                                )
                            with ui.VStack(width=80):

                                self.edit_assembly_name_btn = ui.Button(
                                    "Edit Assembly Names",
                                    height=ui.Pixel(25),
                                    tooltip="Allow editing assembly names and updates assemblies.",
                                )
                                self.edit_assembly_name_btn.set_clicked_fn(self.on_edit_assembly_names)
                with ui.HStack(height=ui.Pixel(0)):
                    with ui.VStack(width=ui.Pixel(0)):
                        ui.Spacer(height=ui.Pixel(5))
                        self._flatten_cb = ui.CheckBox(width=0)
                        ui.Spacer(height=ui.Pixel(5))
                    ui.Spacer(width=ui.Pixel(5))
                    ui.Label("Save Flattened", width=0, height=ui.Pixel(25))
                    ui.Spacer(width=ui.Pixel(8))
                    self._finish_import_btn = ui.Button(
                        "Finish Import", clicked_fn=lambda: self._select_folder(self), height=ui.Pixel(25)
                    )

    def reimport_meshes(self, import_all=False):
        props = self._tp_model.get_props()
        if import_all:
            items = self._mesh_model._children
        else:
            items = self._mesh_list.selection

        def export():
            for item in items:
                mesh_idx = item.id
                self.exporter.export_mesh(mesh_idx, props, len(items) == 1)

            if len(items) > 1 or import_all:
                self.exporter.export(True)

        omni.usd.get_context().new_stage_with_callback(on_finish_fn=lambda a, b: export())

    def reimport_all_meshes(self):
        self.reimport_meshes(True)

    def reimport_selected_meshes(self):
        if len(self._mesh_list.selection):
            self.reimport_meshes(False)

    def remove_selected_lod(self):
        self._tp_model.remove_item(self._tesselation_properties_list.selection)
        self._tesselation_properties_list.clear_selection()

    def close_window(self, a=None, b=None):
        self._window = None
        self.build_steps.clear()
        self.current_step = -1
        if self._assembly_model:
            self._assembly_model.reset()
            self._assembly_model = None
        if self._mesh_model:
            self._mesh_model.reset()
            self._mesh_model = None
        self.exporter = None

    def on_visibility_change(self, a):
        self.show_window(a)

    def _build_ui(self):
        if self._window is None:
            self._window = ui.Window(
                title=EXTENSION_NAME, width=800, height=400, visible=True, dockPreference=ui.DockPreference.LEFT_BOTTOM
            )
            self._window.deferred_dock_in("Console", omni.ui.DockPolicy.DO_NOTHING)
            self._window.set_visibility_changed_fn(self.on_visibility_change)
            self._assembly_model = AssemblyTreeModel()
            self.props = {}
            with self._window.frame:
                with ui.ScrollingFrame(
                    horizontal_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_ALWAYS_OFF,
                    # vertical_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_ALWAYS_ON,
                    style=self.tree_style,
                    height=ui.Percent(100),
                ):
                    with ui.HStack():
                        with ui.VStack(alignment=ui.Alignment.TOP):
                            with ui.HStack(
                                spacing=0,
                                height=ui.Pixel(20),
                                style={**self.menu_button_style},
                                alignment=ui.Alignment.BOTTOM,
                            ):
                                self._select_step_btn = ui.Button(
                                    "Select Step File", clicked_fn=self.select_step_0, height=ui.Pixel(20)
                                )
                                self._review_meshes_btn = ui.Button(
                                    "Review Meshes", clicked_fn=self.select_step_1, height=ui.Pixel(20)
                                )
                                self._review_meshes_btn.enabled = False
                                self.step_btns = [self._select_step_btn, self._review_meshes_btn]
                            for i in range(len(self.build_steps_fns) - 1):
                                vstack = ui.VStack(spacing=10, alignment=ui.Alignment.TOP)
                                self.build_steps_fns[i](vstack)
                                vstack.visible = False
                                self.build_steps.append(vstack)
                                self.step_btns[i].selected = False
                            self.select_step(0)
                        ui.Spacer(width=ui.Pixel(20))
        self._window.visible = True

    def build_ui(self):
        self.show_window()
        self._select_file()

    def show_window(self, value=True):
        if not value:
            self.select_step(0)
            self._on_picker_cancel(None, None)
            if self._assembly_model:
                self._assembly_model.reset()
            self.part = _step_importer.Part()
        else:
            self._build_ui()

    def _on_picker_cancel(self, a, b):
        if self._filepicker:
            self._filepicker.hide()
        if self._folder_picker:
            self._folder_picker.hide()

    def on_shutdown(self):
        self._unregister_menus()
        remove_menu_items(self._menu_items, "Isaac Utils")
        if self.asset_importer:
            self.asset_importer.on_shutdown()
        if self.step_file:
            self._si.release_step_file(self.step_file)
        if self.exporter:
            self.exporter = None
        if self.part:
            del self.part
            self.part = None
        if self._filepicker:
            self._filepicker._widget._file_bar._click_apply_handler = None
            self._filepicker._widget._click_apply_handler = None
            self._filepicker._widget._file_bar._click_cancel_handler = None
            self._filepicker._widget._click_cancel_handler = None
            self._filepicker.toggle_bookmark_from_path(
                "Built In STEP Files", (self.extension_path + "/data/step"), False
            )
            self._filepicker = None

        if self._folder_picker:
            self._folder_picker._widget._file_bar._click_apply_handler = None
            self._folder_picker._widget._click_apply_handler = None
            self._folder_picker._widget._file_bar._click_cancel_handler = None
            self._folder_picker._widget._click_cancel_handler = None
            self._folder_picker = None
        self._si = None

    def _select_file(self):
        if self._filepicker:
            self._filepicker.show()
            # self._filepicker._widget._model._item_changed(None)

    def _select_folder(self, btn_widget):
        self._folder_picker.show()

    def _import_file(self, step_path):
        self.show_window(True)
        self.step_file = self._si.load_step_file(step_path)
        if self._si.get_assembly_structure(self.step_file, self.part):
            carb.log_info(self.path)
            path, basename = os.path.split(self.path)
            carb.log_info(path + ", " + basename)
            basename = os.path.splitext(basename)[0]
            carb.log_info(basename)
            clean_path = None
            carb.log_info("Creating USD Exporter")
            self.exporter = usd_exporter.PartExporter(
                weakref.proxy(self._si), self.step_file, weakref.proxy(self.part), path, basename
            )
            self.exporter.set_on_exported_fn(self._on_exported_done)

            carb.log_info("Resetting models")
            self._mesh_model.reset()
            self._assembly_model.reset()

            self.exporter.export()

            self.step_btns[1].enabled = True
            self.select_step(1)

    def _on_exported_done(self):
        self._assembly_model.add_part(weakref.proxy(self.exporter))
        self._mesh_model.add_mesh_list(weakref.proxy(self.exporter))

    def _on_open_folder_selected(self, menu, path):
        self._folder_picker.hide()
        if self._flatten_cb.model.get_value_as_bool():
            self.exporter.save_flattened(path, self.close_window)
        else:
            self._finish_import(path)

    def _select_picked_file_callback(self, filename=None, path=None):
        if not path.startswith("omniverse://"):
            if filename:
                self.path = f"{path}/{filename}"
            else:
                self.path = path
            if self.path and self.exporter and self.exporter.is_temp_stage_open():

                def import_file():
                    del self.exporter
                    self.exporter = None
                    gc.collect()
                    self._import_file(self.path)

                omni.usd.get_context().close_stage_with_callback(on_finish_fn=lambda a, b: import_file())
            else:
                self._import_file(self.path)
        else:
            self._assembly_model.reset()
            self._mesh_model.reset()
            self.path = ""
            carb.log_error("Only Local Paths supported")
        if self._filepicker:
            self._filepicker.hide()

    def _finish_import(self, output_dir):
        # setting asset importer parameters to upload
        if self.asset_importer is None:
            from omni.kit.tool.asset_importer import importer

            self.asset_importer = importer.Importer()
            self.asset_importer.on_startup()

        upload_absolute_paths, upload_relative_paths = self.exporter.get_abs_and_rel_paths()

        async def upload():
            await self.asset_importer.create_import_task(
                False, upload_absolute_paths, upload_relative_paths, output_dir, None
            )
            omni.usd.get_context().open_stage(
                output_dir + "/" + self.exporter.part_name + "/" + os.path.basename(self.exporter.assemblies_path[1]),
                weakref.proxy(self).close_window,
            )

        asyncio.ensure_future(upload())
