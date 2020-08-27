import omni.ext
import omni.kit.commands
import omni.kit.editor
import omni.ui as ui
import os
import gc
import carb
import asyncio
import weakref

from functools import wraps, partial
from pathlib import Path

from . import usd_exporter
from .assembly_widget import *
from .tesselation_props_list import *
from .mesh_list_widget import *


# from .. import _step_importer
from omni.isaac.step_importer import _step_importer

EXTENSION_NAME = "Step Importer"


class StepImporter(omni.ext.IExt):
    def on_startup(self):
        carb.log_info("Loading Step Importer Extension")
        self._si = _step_importer.acquire_interface()
        self._editor = omni.kit.editor.get_editor_interface()
        self.part = _step_importer.Part()
        # self._filepicker = None
        self.exporter = None
        self.path = ""
        self._window = None
        self._assembly_model = None
        self._mesh_model = None

        self.build_steps = []
        self.build_steps_fns = [self.build_step_0, self.build_step_1, self.build_step_1]
        self.current_step = -1

        self.asset_importer = None

        self._filepicker = None

        self.step_file = None

        self._usd_context = omni.usd.get_context()
        self.stage = self._usd_context.get_stage()
        self._selection = self._usd_context.get_selection()
        self._events = self._usd_context.get_stage_event_stream()
        self._stage_event_subscription = self._events.create_subscription_to_pop(
            self._on_stage_event, name="UsdShadeGraphModel Selection Watch"
        )

        try:
            self._style = self._editor.get_ui_style()
        except:
            self._style = None
        finally:
            if not self._style:
                self._style = "NvidiaDark"

        self._menu = omni.kit.ui.get_editor_menu().add_item(
            "Window/Isaac/" + EXTENSION_NAME, self.show_window, toggle=False, value=False
        )

        if self._style == "NvidiaLight":
            self.tree_style = {
                "Field": {"background_color": 0xFF535354, "color": 0xFFCCCCCC},
                "ScrollingFrame": {"background_color": 0xFFE0E0E0, "secondary_color": 0xFF444444},
                "TreeView": {
                    "background_color": 0xFFE0E0E0,
                    "background_selected_color": 0x109D905C,
                    "secondary_color": 0xFFACACAC,
                },
                "TreeView.ScrollingFrame": {"background_color": 0xFFE0E0E0},
                "TreeView.Header": {"color": 0xFFCCCCCC},
                "TreeView.Header::background": {
                    "background_color": 0xFF535354,
                    "border_color": 0xFF707070,
                    "border_width": 0.5,
                },
                "TreeView.Header::columnname": {"margin": 3},
                "TreeView.Image::object_icon_grey": {"color": 0x80FFFFFF},
                "TreeView.Item": {"color": 0xFF535354, "font_size": 16},
                "TreeView.Item::object_name": {"margin": 3},
                "TreeView.Item::object_name_grey": {"color": 0xFFACACAC},
                "TreeView.Item:selected": {"color": 0xFF2A2825},
                "TreeView:selected": {"background_color": 0x409D905C},
            }
            self.menu_button_style = {"Button.disabled": {"background_color": 0xFF535354, "color": 0xFFCCCCCC}}

        else:
            self.tree_style = {
                "TreeView": {
                    "background_color": 0xFF23211F,
                    "background_selected_color": 0x664F4D43,
                    "secondary_color": 0xFF403B3B,
                },
                "TreeView.ScrollingFrame": {"background_color": 0xFF23211F},
                "TreeView.Header": {"background_color": 0xFF343432, "color": 0xFFCCCCCC, "font_size": 13.0},
                "TreeView.Image::object_icon_grey": {"color": 0x80FFFFFF},
                "TreeView.Item": {"color": 0xFF8A8777},
                "TreeView.Item::object_name_grey": {"color": 0xFF4D4B42},
                "TreeView.Item:selected": {"color": 0xFF23211F},
                "TreeView:selected": {"background_color": 0xFF8A8777},
            }
            self.menu_button_style = {
                "Button": {"border_radius": 0, "margin": 0},
                "Button:selected": {"background_color": 0xFF454545, "padding": 5},
                ":disabled": {"color": 0xFF333333},
                # "Button:hovered":{"background_color":0xFF9A9A9A},
            }

        self._delegate = AssemblyDelegate()

        # self.show_window(None, True)

    def _on_stage_event(self, event):
        """Called with omni.usd.context when stage event"""

        if event.type == int(omni.usd.StageEventType.SELECTION_CHANGED):
            self._on_kit_selection_changed()
        if event.type == int(omni.usd.StageEventType.OPENED):
            if self.exporter:
                if self.exporter.is_temp_stage_open():
                    self.exporter.set_materials_to_color_layer()

            if self._mesh_model:
                self._mesh_model.update_prim_paths()

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

    def toggle_selected_visibility(self, source):
        omni.kit.commands.execute(
            "ToggleVisibilitySelectedPrimsCommand", selected_paths=self.get_selected_prim_paths(source)
        )

    def ReplaceDuplicatesSelected(self):
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
                        # print (identifier)
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

    def build_step_0(self, container):
        with container:
            self._step_picker_button = ui.Button("load Preview", clicked_fn=lambda a=self: self._select_file(a))

    def build_step_1(self, container):
        self._tp_delegate = TesselationPropsDelegate()
        self._tp_model = TesselationPropertiesListModel([_step_importer.Tesselation_Properties()])

        self._mesh_delegate = MeshListDelegate()
        self._mesh_model = MeshListModel()

        with container:
            with ui.VStack(aligmnent=ui.Alignment.LEFT_TOP):
                with ui.CollapsableFrame("LOD properties", height=ui.Pixel(0)):
                    with ui.HStack(height=ui.Percent(100)):
                        with ui.VStack(width=ui.Pixel(20)):
                            ui.Spacer(height=ui.Pixel(13))
                            self._add_lod = ui.Button(
                                "+",
                                clicked_fn=lambda: self._tp_model.add_prop(),
                                height=ui.Pixel(20),
                                width=ui.Pixel(20),
                            )
                            self._remove_lod = ui.Button(
                                "-",
                                clicked_fn=lambda: self.remove_selected_lod(),
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
                                ui.Button(
                                    "Show Full Part",
                                    clicked_fn=lambda: self._delegate.on_mouse_double_clicked(
                                        self._assembly_model._root.children[0]
                                    ),
                                    height=ui.Pixel(25),
                                )
                                ui.Button(
                                    "Find Similar Meshes",
                                    clicked_fn=lambda: self._select_meshes_with_same_volume(),
                                    height=ui.Pixel(25),
                                    tooltip="Selects Potential duplicate meshes based on metadata",
                                )
                                ui.Button(
                                    "Toggle Visibility",
                                    clicked_fn=lambda: self.toggle_selected_visibility(self._mesh_list),
                                    height=ui.Pixel(25),
                                    tooltip="Show/Hide selected meshes",
                                )

                                def on_edit_names(button):
                                    self._mesh_model.toggle_edit_mode()
                                    if self._mesh_model.edit_mode:
                                        button.text = "Done Editing Names"
                                    else:
                                        button.text = "Edit Mesh Names"

                                btn = ui.Button(
                                    "Edit Mesh Names",
                                    height=ui.Pixel(25),
                                    tooltip="Allow editing mesh names and updates assemblies.",
                                )
                                btn.set_clicked_fn(lambda a=btn: on_edit_names(a))
                                ui.Button(
                                    "Remove selected duplicates",
                                    clicked_fn=lambda: self.ReplaceDuplicatesSelected(),
                                    height=ui.Pixel(25),
                                    tooltip="Replaces all selected meshes with a single instance (First selected)",
                                )
                                with ui.HStack(tooltip="Import the meshes with given LOD properties"):
                                    ui.Spacer(width=ui.Pixel(5))
                                    ui.Label("Re-Mesh", height=ui.Pixel(25), width=ui.Pixel(30))
                                    ui.Spacer()
                                    ui.Button("All", clicked_fn=lambda: self.reimport_meshes(True), height=ui.Pixel(25))
                                    ui.Button(
                                        "Selected", clicked_fn=lambda: self.reimport_meshes(), height=ui.Pixel(25)
                                    )
                                    ui.Spacer()
                                # with ui.HStack():
                                #     ui.CheckBox(model=ui.SimpleBoolModel(self._mesh_model.hide_duplicates), width=10)
                                #     ui.Label("Hide Mesh Duplicates")
                ui.Spacer(height=10)
                with ui.CollapsableFrame("Assembly Description", height=ui.Pixel(0)):
                    self._sf = ui.ScrollingFrame(
                        horizontal_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_ALWAYS_OFF,
                        vertical_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_ALWAYS_ON,
                        style_type_name_override="TreeView.ScrollingFrame",
                        style=self.tree_style,
                        height=ui.Pixel(100)
                        # mouse_pressed_fn=lambda x, y, b, _: self._delegate.on_mouse_pressed(b, None, False),
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
                self._finish_import_btn = ui.Button(
                    "Finish Import", clicked_fn=lambda: self._select_folder(self), height=ui.Pixel(25)
                )

            # ui.Button("Review Assemblies", clicked_fn=lambda: self.select_step(2), height=ui.Pixel(25))

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
                # self.exporter.export() #regenerate USDs

            if len(items) > 1 or import_all:
                self.exporter.export()

        omni.usd.get_context().new_stage(on_finish_fn=lambda a, b: export())

    def remove_selected_lod(self):
        # print(self._tesselation_properties_list.selection)
        self._tp_model.remove_item(self._tesselation_properties_list.selection)
        self._tesselation_properties_list.clear_selection()

    def _finish_import(self, output_dir):
        # setting asset importer parameters to upload
        if not self.asset_importer:
            from omni.assetimport import get_extension as get_asset_importer

            self.asset_importer = get_asset_importer()
            self.asset_importer.__dict__["_waiting_popup_upload"] = None
            self.asset_importer.__dict__["_content_window"] = None
        self.asset_importer._menu_upload_clicked = True
        self.asset_importer._upload_absolute_paths, self.asset_importer._upload_relative_paths = (
            self.exporter.get_abs_and_rel_paths()
        )

        async def import_file():
            await self.asset_importer._start_upload_internal(output_dir, False, None)
            omni.usd.get_context().open_stage(
                output_dir + "/" + self.exporter.part_name + "/" + os.path.basename(self.exporter.assemblies_path[1]),
                lambda a, b: self.close_window(),
            )
            self.asset_importer.on_shutdown()
            self.asset_importer = None

            # omni.usd.get_context().close_stage(on_finish_fn= lambda a,b: omni.usd.get_context().open_stage(output_dir +"/"+self.exporter.part_name+ "/root.usd", None))

        self.asset_importer._upload_future = asyncio.ensure_future(
            import_file()
            # self.asset_importer._start_upload_internal(output_dir, False, None)
        )

    def close_window(self):
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
        self.part = None

    def show_window(self, menu, value):
        if self._window:
            self._window = None
            self.build_steps.clear()
            self.current_step = -1
            if self._assembly_model:
                self._assembly_model.reset()
                self._assembly_model = None
            self.part = _step_importer.Part()
        else:
            self._window = ui.Window(
                EXTENSION_NAME,
                width=800,
                height=400,
                menu_path="Isaac Robotics/Importers/" + EXTENSION_NAME,
                open=value,
                dock=ui.DockPreference.LEFT_BOTTOM,
            )
            self._window.set_visibility_changed_fn(lambda a: self.show_window(self._menu, False))
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
                                    "Select Step File", clicked_fn=lambda: self.select_step(0), height=ui.Pixel(20)
                                )
                                self._review_meshes_btn = ui.Button(
                                    "Review Meshes", clicked_fn=lambda: self.select_step(1), height=ui.Pixel(20)
                                )
                                self._review_meshes_btn.enabled = False
                                # self._review_assemblies_btn = ui.Button(
                                #     "Review Assemblies", clicked_fn=lambda: self.select_step(2), height=ui.Pixel(20)
                                # )
                                # self._review_assemblies_btn.enabled = False
                                self.step_btns = [
                                    self._select_step_btn,
                                    self._review_meshes_btn,
                                ]  # , self._review_assemblies_btn]
                            # with ui.ZStack():
                            for i in range(len(self.build_steps_fns) - 1):
                                vstack = ui.VStack(spacing=10, alignment=ui.Alignment.TOP)
                                self.build_steps_fns[i](vstack)
                                vstack.visible = False
                                self.build_steps.append(vstack)
                                self.step_btns[i].selected = False
                            self.select_step(0)
                        ui.Spacer(width=ui.Pixel(20))
            if menu:
                self._select_file(self)
                # self._select_picked_file_callback("/home/rgasoto/Downloads/as1-oc-214.stp")

    def on_shutdown(self):
        carb.log_info("Shutting down Step Importer")
        self._menu = None
        if self._assembly_model:
            self._assembly_model.reset()
            self._assembly_model = None
            self._treeView = None
        if self._mesh_model:
            self._mesh_model.reset()
            self._mesh_list = None
        if self.asset_importer:
            # del self.asset_importer
            self.asset_importer = None
        self._sf = None
        self._mesh_model = None
        self._assembly_model = None
        if self._filepicker:
            self._filepicker.set_file_selected_fn(None)
            # self._filepicker = None  # Why does that crash?
        if self.exporter:
            self.exporter = None
        if self.part:
            self.part = None
        gc.collect()
        print("releasing interface")
        if self.step_file:
            self._si.release_step_file(self.step_file)

        _step_importer.release_interface(self._si)
        self._si = None
        print("done")
        carb.log_info("done")

    def _select_file(self, btn_widget):

        self._filepicker = omni.kit.ui.FilePicker("Select STEP File", file_type=omni.kit.ui.FileDialogSelectType.FILE)
        self._filepicker.set_file_selected_fn(self._select_picked_file_callback)
        self._filepicker.add_filter("STEP Files (*.step | *.stp)", r".*.step$|.*.stp$")

        self._filepicker.show()

    def _select_folder(self, btn_widget):
        self._filepicker = omni.kit.ui.FilePicker(
            "Select Destination Folder", file_type=omni.kit.ui.FileDialogSelectType.DIRECTORY
        )
        self._filepicker.set_file_selected_fn(self._finish_import)
        self._filepicker.show()

    def _import_file(self, step_path):
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
            # self.step_btns[2].enabled = True
            self.select_step(1)

    def _on_exported_done(self):
        self._assembly_model.add_part(weakref.proxy(self.exporter))
        self._mesh_model.add_mesh_list(weakref.proxy(self.exporter))

    def _select_picked_file_callback(self, path):
        if not path.startswith("omniverse://"):
            self.path = path
            if self.exporter and self.exporter.is_temp_stage_open():

                def import_file():
                    del self.exporter
                    self.exporter = None
                    gc.collect()
                    self._import_file(self.path)

                omni.usd.get_context().close_stage(on_finish_fn=lambda a, b: import_file())
            else:
                self._import_file(self.path)
        else:
            self._assembly_model.reset()
            self._mesh_model.reset()
            self.path = ""
            self._exporter_button.enabled = False
            carb.log_error("Only Local Paths supported")
