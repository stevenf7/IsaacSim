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
        self.display_paths = []
        self.prims_to_update = {}
        self.lbl_no_selection = ui.Label("Select an object to display the semantic data")
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
        self.prims_to_update = {}
        if not len(self.display_paths) == 0:
            self._window.layout.add_child(ui.Label("Semantic data on selected objects"))
            for p in self.display_paths:
                self._add_prim_entry(p)
            btn_apply = ui.Button("Apply Changes")
            btn_apply.set_clicked_fn(self.apply_semantics)
            self._window.layout.add_child(btn_apply)
        else:
            self._window.layout.add_child(self.lbl_no_selection)

    def _add_prim_entry(self, prim_path):
        self.prims_to_update[prim_path] = {}
        self._window.layout.add_child(ui.Label(prim_path))
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
        self._window.layout.add_child(row_layout)

    def on_stage_event(self, event):
        if event.type == int(omni.usd.StageEventType.SELECTION_CHANGED):
            self.display_paths.clear()
            selected = self._selection.get_selected_prim_paths()
            for prim_path in selected:
                self.display_paths.append(prim_path)
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
        for p in self.prims_to_update:
            prim = self._stage.get_stage().GetObjectAtPath(p)

            if not prim.HasAPI(Semantics.SemanticsAPI):
                sem = Semantics.SemanticsAPI.Apply(prim, "Semantics")
                sem.CreateSemanticTypeAttr()
                sem.CreateSemanticDataAttr()
            else:
                sem = Semantics.SemanticsAPI.Get(prim, "Semantics")

            typeAttr = sem.GetSemanticTypeAttr()
            dataAttr = sem.GetSemanticDataAttr()

            if "updated_type" in self.prims_to_update[p].keys():
                typeAttr.Set(self.prims_to_update[p]["updated_type"])

            if "updated_data" in self.prims_to_update[p].keys():
                dataAttr.Set(self.prims_to_update[p]["updated_data"])

    def on_type_text_changed_fn(self, widget):
        prim = widget.user_data["prim_to_update"]
        self.prims_to_update[prim]["updated_type"] = widget.text
        pass

    def on_data_text_changed_fn(self, widget):
        prim = widget.user_data["prim_to_update"]
        self.prims_to_update[prim]["updated_data"] = widget.text
        pass
