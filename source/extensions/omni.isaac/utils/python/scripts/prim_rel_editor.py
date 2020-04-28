import os
import omni.ext
import omni.kit.commands
import omni.kit.editor
import omni.kit.ui
import carb.tokens
from pxr import Usd, UsdGeom, Sdf, Gf, Tf, PhysicsSchemaTools
import gc


class PrimRelModel(omni.kit.ui.Model):
    def __init__(self, prim=None):
        omni.kit.ui.Model.__init__(self)
        self._prim = prim
        self._labels = {}
        self._usd_context = omni.usd.get_context()

    def get_type(self, path, meta):
        return omni.kit.ui.ModelNodeType.STRING

    def get_value(self, path, meta, index, is_time_sampled, time):
        paths = path[1:].split("/")
        if len(paths) == 2:
            targets = self._prim.GetRelationship(paths[0]).GetTargets()
            if int(paths[1]) < len(targets):
                return str(targets[int(paths[1])])
            else:
                return "/Add/New/Relation/Path"
        return ""

    def set_value(self, path, meta, value, index, is_time_sampled, time, info):
        prim = self._usd_context.get_stage().GetPrimAtPath(value)
        if prim:
            self._labels[path].text = "  Valid"
            self._labels[path].set_text_color((0, 1, 0, 1))
        else:
            self._labels[path].text = "Invalid"
            self._labels[path].set_text_color((1, 0, 0, 1))

    def get_key_count(self, path, meta):
        if self._prim is None:
            return 0

        if len(path) > 0 and path[0] == "/":
            paths = path[1:].split("/")
            if len(paths) == 1:  # we are at the first level
                # return the number of targets
                count = len(self._prim.GetRelationship(paths[0]).GetTargets())
                # add an extra future target
                return count + 1
            else:
                return 0
        else:
            return len(self._prim.GetRelationships())

    def get_key(self, path, meta, index):
        if len(path) > 0 and path[0] == "/":
            paths = path[1:].split("/")
            if len(paths) == 1:  # at first level return the
                return str(index)
            if len(paths) == 2:
                targets = self._prim.GetRelationship(paths[0]).GetTargets()
                if int(paths[1]) < len(targets):
                    return str(self._prim.GetRelationship(paths[0]).GetTargets()[int(index)])
                else:
                    return ""
        else:
            return self._prim.GetRelationships()[index].GetBaseName()


class Extension(omni.ext.IExt):
    def on_startup(self):
        print("Starting Prim Relationship Editor")
        self._usd_context = omni.usd.get_context()
        if self._usd_context is not None:
            self._selection = self._usd_context.get_selection()
            self._events = self._usd_context.get_stage_event_stream()
            self._stage_event_sub = self._events.create_subscription_to_pop(
                self._on_stage_event, name="omni.example.ui abstract model stage update"
            )

        self._rel_editor_window = omni.kit.ui.Window(
            "Relationship Editor",
            100,
            200,
            menu_path=f"Utilities/Relationship Editor",
            dock=omni.kit.ui.DockPreference.RIGHT_BOTTOM,
            flags=omni.kit.ui.WINDOW_FLAGS_NO_FOCUS_ON_APPEARING,
            add_to_menu=True,
        )
        # self._rel_editor_window.hide()
        self._layout = self._rel_editor_window.layout
        self._model = PrimRelModel()

        self._view_treegrid = omni.kit.ui.ViewTreeGrid(True, True, 1)
        self._view_treegrid.set_build_cell_fn(self.build_cell_fn)
        self._view_treegrid.set_model(self._model)
        self._view_treegrid.draw_table_header = True
        self._view_treegrid.set_header_cell_text(0, "Relationships For Selected Prim")
        self._layout.add_child(self._view_treegrid)

    def build_cell_fn(self, model, model_path, column_idx, column_count):
        key_count = model.get_key_count(model_path, meta="")
        if key_count > 0:
            tree_node_widget = omni.kit.ui.ViewTreeGrid(True, True, column_count)
            tree_node_widget.set_build_cell_fn(self.build_cell_fn)
            tree_node_widget.set_model(model, model_path)
            tree_node_widget.is_root = False
            tree_node_widget.text = os.path.basename(model_path)
            return omni.kit.ui.DelegateResult(tree_node_widget)
        else:
            layout = omni.kit.ui.RowColumnLayout(5)
            layout.width = -1
            layout.set_column_width(0, 30)
            layout.set_column_width(1, omni.kit.ui.Percent(100))
            layout.set_column_width(2, 60)
            layout.set_column_width(3, 60)
            layout.set_column_width(4, 80)

            path = model_path[1:]
            paths = path.split("/")

            index = path.split("/")[-1]
            layout.add_child(omni.kit.ui.Label(index))
            name = model.get_key(model_path, "", index)
            tbox = layout.add_child(omni.kit.ui.TextBox(name))
            tbox.set_model(model, model_path)
            tbox.width = -1
            valid_label = layout.add_child(omni.kit.ui.Label("---"))
            model._labels.update({model_path: valid_label})
            btn_text = "Modify"
            if int(index) > len(model._prim.GetRelationship(paths[0]).GetTargets()) - 1:
                btn_text = "Add"
            btn = omni.kit.ui.Button(btn_text)

            def modify_add_fun(widget, model_path=model_path, model=model, tbox=tbox):
                path = model_path[1:]
                paths = path.split("/")
                if widget.text == "Add":
                    model._prim.GetRelationship(paths[0]).AddTarget(tbox.text)
                    self._selection.clear_selected_prim_paths()
                    self._selection.set_selected_prim_paths([str(model._prim.GetPrimPath())], True)
                    return
                if len(paths) == 2:
                    targets = model._prim.GetRelationship(paths[0]).GetTargets()
                    targets[int(paths[1])] = tbox.text
                    model._prim.GetRelationship(paths[0]).SetTargets(targets)
                self._selection.clear_selected_prim_paths()
                self._selection.set_selected_prim_paths([str(model._prim.GetPrimPath())], True)

            btn.set_clicked_fn(modify_add_fun)
            layout.add_child(btn)

            if int(index) < len(model._prim.GetRelationship(paths[0]).GetTargets()):
                remove_btn = omni.kit.ui.Button("Remove")

                def remove_fun(widget, model_path=model_path, model=model, tbox=tbox):
                    path = model_path[1:]
                    paths = path.split("/")
                    if len(paths) == 2:
                        targets = model._prim.GetRelationship(paths[0]).GetTargets()
                        del targets[int(paths[1])]
                        model._prim.GetRelationship(paths[0]).SetTargets(targets)
                        self._selection.clear_selected_prim_paths()
                        self._selection.set_selected_prim_paths([str(model._prim.GetPrimPath())], True)

                remove_btn.set_clicked_fn(remove_fun)
                layout.add_child(remove_btn)

            return omni.kit.ui.DelegateResult(layout)

    def _on_stage_event(self, event):
        if event.type == int(omni.usd.StageEventType.SELECTION_CHANGED):
            selection = self._selection.get_selected_prim_paths()
            stage = self._usd_context.get_stage()
            prim = None
            if len(selection) == 0:
                pass
            else:
                path = selection[0]
                prim = stage.GetPrimAtPath(path)

            self._model = PrimRelModel(prim)
            self._layout.remove_child(self._view_treegrid)
            self._view_treegrid = omni.kit.ui.ViewTreeGrid(True, True, 1)
            self._view_treegrid.set_build_cell_fn(self.build_cell_fn)
            self._view_treegrid.set_model(self._model)
            self._view_treegrid.draw_table_header = True
            self._view_treegrid.set_header_cell_text(0, "Relationships For Selected Prim")
            self._layout.add_child(self._view_treegrid)

    def on_shutdown(self):
        gc.collect()
        print("Stopping Prim Relationship Editor")
