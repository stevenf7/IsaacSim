# Copyright (c) 2020, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

import omni.usd
import omni.ui as ui
from omni.kit.property.usd.usd_property_widget import UsdPropertiesWidget, UsdPropertyUiEntry
from pxr import Usd, Sdf
from typing import List
from omni.kit.property.usd.usd_property_widget_builder import UsdPropertiesWidgetBuilder
from omni.kit.property.usd.usd_attribute_model import UsdAttributeModel

HORIZONTAL_SPACING = 4


class IsaacPropertyWidgets(omni.ext.IExt):
    def __init__(self):
        self._registered = False

    def on_startup(self, ext_id):
        self._register_widget()

    def on_shutdown(self):
        self._unregister_widget()

    def _register_widget(self):
        import omni.kit.window.property as p

        w = p.get_window()
        w.register_widget(
            "prim", "isaac_strings", StringPropertiesWidget(title="String Properties", collapsed=True), False
        )

    def _unregister_widget(self):
        import omni.kit.window.property as p

        w = p.get_window()
        if w:
            w.unregister_widget("prim", "isaac_strings")
            self._registered = False


class StringPropertiesWidget(UsdPropertiesWidget):
    def _filter_props_to_build(self, props):
        # simple widget that handles string based properties
        return [prop for prop in props if isinstance(prop, Usd.Attribute) and prop.GetTypeName() == "string"]

    def build_property_item(self, stage, ui_prop: UsdPropertyUiEntry, prim_paths: List[Sdf.Path]):
        if ui_prop.prim_paths:
            prim_paths = ui_prop.prim_paths

        if ui_prop.property_type == Usd.Attribute:
            type_name = UsdPropertiesWidgetBuilder._get_type_name(ui_prop.metadata)
            tf_type = type_name.type

            self._string_builder(stage, ui_prop.prop_name, tf_type, ui_prop.metadata, prim_paths)

    @classmethod
    def _string_builder(
        cls,
        stage,
        attr_name,
        type_name,
        metadata,
        prim_paths: List[Sdf.Path],
        additional_label_kwargs=None,
        additional_widget_kwargs=None,
    ):
        with ui.HStack(spacing=HORIZONTAL_SPACING):
            UsdPropertiesWidgetBuilder._create_label(attr_name, metadata, additional_label_kwargs)
            model = UsdAttributeModel(stage, [path.AppendProperty(attr_name) for path in prim_paths], False, metadata)
            widget_kwargs = {"name": "string"}
            if additional_widget_kwargs:
                widget_kwargs.update(additional_widget_kwargs)
            with ui.ZStack():
                value_widget = ui.StringField(model, **widget_kwargs)
                mixed_overlay = UsdPropertiesWidgetBuilder._create_mixed_text_overlay()
            UsdPropertiesWidgetBuilder._create_control_state(
                model=model, value_widget=value_widget, mixed_overlay=mixed_overlay, **widget_kwargs
            )
            return model
