from functools import partial
from omni.kit.property.usd.custom_layout_helper import CustomLayoutFrame, CustomLayoutGroup, CustomLayoutProperty
from omni.graph.ui import OmniGraphAttributeModel
from omni.kit.property.usd.usd_property_widget import UsdPropertiesWidgetBuilder
import omni.graph.core as og

import omni.ui as ui
from omni.kit.widget.text_editor import TextEditor


class ScriptTextbox(TextEditor):
    def __init__(self, script_model: OmniGraphAttributeModel):
        super().__init__(
            syntax=TextEditor.Syntax.NONE,
            # style={"font": str(FONTS_PATH.joinpath("DejaVuSansMono.ttf"))},
            text=script_model.get_value_as_string(),
        )
        self.script_model = script_model
        self.script_model_callback_id = self.script_model.add_value_changed_fn(self._on_script_model_changed)

        self.set_edited_fn(self._on_script_edited)

    def _on_script_edited(self, text_changed: bool):
        if text_changed:
            # Don't trigger the model changed callback when script is edited
            self.script_model.remove_value_changed_fn(self.script_model_callback_id)
            # Remove the newline that TextEditor adds or else it will accumulate
            self.script_model.set_value(self.text[:-1])
            self.script_model_callback_id = self.script_model.add_value_changed_fn(self._on_script_model_changed)

    def _on_script_model_changed(self, script_model):
        self.text = script_model.get_value_as_string()  # noqa: PLW0201


class CustomLayout:
    def __init__(self, compute_node_widget):
        self.enable = True
        self.compute_node_widget = compute_node_widget
        self.compute_node_widget.get_bundles()
        self.node_prim_path = self.compute_node_widget._payload[-1]
        self.node = og.Controller.node(self.node_prim_path)
        self.DEFAULT_SCRIPT = ""

        bundle_items_iter = iter(self.compute_node_widget.bundles.items())
        _ = next(bundle_items_iter)[1][0].get_attribute_names_and_types()

    def apply(self, props):
        frame = CustomLayoutFrame(hide_extra=True)

        def find_prop(name):
            try:
                return next((p for p in props if p.prop_name == name))
            except StopIteration:
                return None

        with frame:
            with CustomLayoutGroup("Inputs"):
                prop = find_prop("inputs:yaml")
                if prop is not None:
                    CustomLayoutProperty(prop.prop_name, "Script", partial(self._script_textbox_build_fn, prop))

        return frame.apply(props)

    def _script_textbox_build_fn(self, *args):
        """Build the textbox used to input custom scripts"""
        self.script_textbox_model = OmniGraphAttributeModel(
            self.compute_node_widget.stage, [self.node_prim_path.AppendProperty("inputs:yaml")], False, {}
        )
        if self.script_textbox_model.get_value_as_string() == "":
            self.script_textbox_model.set_value(self.DEFAULT_SCRIPT)

        with ui.VStack():
            with ui.HStack():
                UsdPropertiesWidgetBuilder._create_label(  # noqa: PLW0212
                    "YAML", {}, {"style": {"alignment": ui.Alignment.RIGHT_TOP}}
                )
                ui.Spacer(width=7)
                with ui.ZStack():
                    with ui.VStack():
                        self.script_textbox_widget = ScriptTextbox(self.script_textbox_model)
                        # Disable editing if the script value comes from an upstream connection
                        if og.Controller.attribute("inputs:yaml", self.node).get_upstream_connection_count() > 0:
                            self.script_textbox_widget.read_only = True  # noqa: PLW0201
                        ui.Spacer(height=12)
                    # Add a draggable bar below the script textbox to resize it
                    self.script_textbox_resizer = ui.Placer(offset_y=200, draggable=True, drag_axis=ui.Axis.Y)
                    self.script_textbox_resizer.set_offset_y_changed_fn(self._on_script_textbox_resizer_dragged)
                    with self.script_textbox_resizer:
                        script_textbox_resizer_style = {
                            ":hovered": {"background_color": 0xFFB0703B},
                            ":pressed": {"background_color": 0xFFB0703B},
                        }
                        with ui.ZStack(height=12):
                            ui.Rectangle(style=script_textbox_resizer_style)
                            with ui.HStack():
                                ui.Spacer()
                                ui.Label("V", width=0)
                                ui.Spacer()
            ui.Spacer(height=5)
            # with ui.HStack():
            #     ui.Spacer()
            #     self._code_snippets_button_build_fn()

    def _on_script_textbox_resizer_dragged(self, offset_y: ui.Length):
        self.script_textbox_resizer.offset_y = max(offset_y.value, 50)
