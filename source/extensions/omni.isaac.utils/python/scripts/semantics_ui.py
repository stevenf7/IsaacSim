# Copyright (c) 2018-2020, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

import os
import gc
import omni.ext
import omni.usd
import omni.kit.ui as ui
import omni.kit.editor

from pxr import Usd, UsdGeom, Semantics

EXTENSION_NAME = "Semantics Schema Editor"


class Extension(omni.ext.IExt):
    def on_startup(self):
        """Caled to load the extension"""
        self._window = None
        self._editor = omni.kit.editor.get_editor_interface()
        self._stage = omni.usd.get_context()
        self._display_paths = []
        self._prims_to_update = {}
        self._lbl_no_selection = ui.Label("Select an object to display the semantic data")
        self._window = ui.Window(
            EXTENSION_NAME,
            600,
            400,
            menu_path=f"Window/Isaac/{EXTENSION_NAME}",
            dock=omni.kit.ui.DockPreference.RIGHT_BOTTOM,
            # flags=omni.kit.ui.WINDOW_FLAGS_NO_FOCUS_ON_APPEARING,
            add_to_menu=True,
            open=False,
        )
        self._build_window_ui()
        self._selection_sub = self._stage.get_stage_event_stream().create_subscription_to_pop(
            self.on_stage_event, name="semantics_ui stage update"
        )
        self._selection = self._stage.get_selection()

    def on_shutdown(self):
        """Called when the extesion us unloaded"""
        gc.collect()
        del self._window

    def _build_window_ui(self):
        self._window.layout.clear()
        self._layout_collapsing_automated = omni.kit.ui.CollapsingFrame("Apply semantic data on entire stage", True)
        self._window.layout.add_child(self._layout_collapsing_automated)
        self._build_semantic_automated_ui()

        self._prims_to_update = {}
        self._layout_collapsing_manual = omni.kit.ui.CollapsingFrame("Apply semantic data on selected objects", True)
        self._window.layout.add_child(self._layout_collapsing_manual)
        if not len(self._display_paths) == 0:
            for p in self._display_paths:
                self._add_prim_entry(p)
            btn_apply = ui.Button("Apply Changes")
            btn_apply.set_clicked_fn(self.apply_semantics)
            self._layout_collapsing_manual.add_child(btn_apply)
        else:
            self._layout_collapsing_manual.add_child(self._lbl_no_selection)

    def _build_semantic_automated_ui(self):
        ui_layout = omni.kit.ui.RowColumnLayout(2, True)
        ui_layout.set_column_width(0, 125)
        ui_layout.set_column_width(1, 350)
        self._layout_collapsing_automated.add_child(ui_layout)
        ui_layout.add_child(omni.kit.ui.Label("Prim types to label"))
        self._prim_list_txt = omni.kit.ui.TextBox("Mesh,Cube,Sphere,Cylinder,Capsule,Cone")
        self._prim_list_txt.width = -1
        ui_layout.add_child(self._prim_list_txt)
        ui_layout.add_child(omni.kit.ui.Label("Class list"))
        self._class_list_txt = omni.kit.ui.TextBox("cube,table,box")
        self._class_list_txt.width = -1
        ui_layout.add_child(self._class_list_txt)
        self._capture_btn = ui_layout.add_child(omni.kit.ui.Button("Generate Labels"))
        self._capture_btn.set_clicked_fn(self.generate_label_fn)

    def generate_label_fn(self, widget):
        print("Generating Labels!")
        self._allowed_prim_types = str(self._prim_list_txt.value).split(",")
        self._class_list = str(self._class_list_txt.value).split(",")
        current_stage = omni.usd.get_context().get_stage()
        for prim in current_stage.Traverse():
            # Filter prims based on types needed to label as mentioned in self.allowed_prim_types
            if prim.GetTypeName() in self._allowed_prim_types:
                prim_split = str(prim.GetPrimPath()).split("/")
                obj_name = prim_split[len(prim_split) - 1]
                # Assign class labels for those prims such that the string after last "/" in prim path
                # contains one of the labels mentioned in self.class_list
                for class_name in self._class_list:
                    if class_name in obj_name.lower():
                        # print(prim.GetPrimPath(), " : ", class_name)
                        self.apply_semantics_automated(prim, "class", class_name)

    def apply_semantics_automated(self, prim, semantic_type, semantic_data):
        if not prim.HasAPI(Semantics.SemanticsAPI):
            sem = Semantics.SemanticsAPI.Apply(prim, "Semantics")
            sem.CreateSemanticTypeAttr()
            sem.CreateSemanticDataAttr()
        else:
            sem = Semantics.SemanticsAPI.Get(prim, "Semantics")

        typeAttr = sem.GetSemanticTypeAttr()
        dataAttr = sem.GetSemanticDataAttr()
        if semantic_type is not None:
            typeAttr.Set(semantic_type)
        if semantic_data is not None:
            dataAttr.Set(semantic_data)

    def _add_prim_entry(self, prim_path):
        self._prims_to_update[prim_path] = {}
        self._layout_collapsing_manual.add_child(ui.Label(prim_path))
        row_layout = ui.RowLayout()
        row_layout.add_child(ui.Label("Type:"))
        txt_type = ui.TextBox()
        txt_type.user_data = {"prim_to_update": prim_path}
        txt_type.set_text_changed_fn(self.on_type_text_changed_fn)
        row_layout.add_child(txt_type)
        row_layout.add_child(ui.Label("Data:"))
        txt_data = ui.TextBox()
        txt_data.user_data = {"prim_to_update": prim_path}
        txt_data.set_text_changed_fn(self.on_data_text_changed_fn)
        row_layout.add_child(txt_data)
        # Get semantic data
        hasSem, semVal = self.get_semantics(prim_path)
        if hasSem and semVal["semantic"]["type"] is not None and semVal["semantic"]["data"] is not None:
            txt_type.text = semVal["semantic"]["type"]
            txt_data.text = semVal["semantic"]["data"]
        self._layout_collapsing_manual.add_child(row_layout)

    def on_stage_event(self, event):
        if event.type == int(omni.usd.StageEventType.SELECTION_CHANGED):
            self._display_paths.clear()
            selected = self._selection.get_selected_prim_paths()
            for prim_path in selected:
                self._display_paths.append(prim_path)
            self._build_window_ui()

    def get_semantics(self, prim_path):
        sem = Semantics.SemanticsAPI
        has_semantics = False
        semantics_val = {"prim_path": prim_path, "semantic": {"type": "", "data": ""}}
        prim = self._stage.get_stage().GetObjectAtPath(prim_path)
        if prim.HasAPI(sem):
            has_semantics = True
            p_sem = sem.Get(prim, "Semantics")
            semantics_val["semantic"]["type"] = p_sem.GetSemanticTypeAttr().Get()
            semantics_val["semantic"]["data"] = p_sem.GetSemanticDataAttr().Get()
        return has_semantics, semantics_val

    def apply_semantics(self, widget):
        for p in self._prims_to_update:
            prim = self._stage.get_stage().GetObjectAtPath(p)

            if not prim.HasAPI(Semantics.SemanticsAPI):
                sem = Semantics.SemanticsAPI.Apply(prim, "Semantics")
                sem.CreateSemanticTypeAttr()
                sem.CreateSemanticDataAttr()
            else:
                sem = Semantics.SemanticsAPI.Get(prim, "Semantics")

            typeAttr = sem.GetSemanticTypeAttr()
            dataAttr = sem.GetSemanticDataAttr()

            if "updated_type" in self._prims_to_update[p].keys():
                typeAttr.Set(self._prims_to_update[p]["updated_type"])

            if "updated_data" in self._prims_to_update[p].keys():
                dataAttr.Set(self._prims_to_update[p]["updated_data"])

    def on_type_text_changed_fn(self, widget):
        prim = widget.user_data["prim_to_update"]
        self._prims_to_update[prim]["updated_type"] = widget.text
        pass

    def on_data_text_changed_fn(self, widget):
        prim = widget.user_data["prim_to_update"]
        self._prims_to_update[prim]["updated_data"] = widget.text
        pass
