# Copyright (c) 2023, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
from typing import List

import carb
import omni.ui as ui
from omni.kit.property.usd.usd_attribute_model import UsdAttributeModel
from omni.kit.property.usd.usd_property_widget import UsdPropertiesWidget, UsdPropertyUiEntry
from omni.kit.property.usd.usd_property_widget_builder import UsdPropertiesWidgetBuilder
from omni.kit.property.usd.widgets import ICON_PATH
from omni.kit.window.property.templates import HORIZONTAL_SPACING, LABEL_HEIGHT, LABEL_WIDTH
from pxr import Gf, Sdf, Tf, Usd


class OnshapePropertiesWidget(UsdPropertiesWidget):
    def on_new_payload(self, payload):
        """
        See PropertyWidget.on_new_payload
        """

        if not super().on_new_payload(payload):
            return False

        if len(self._payload) == 0:
            return False

        for prim_path in self._payload:
            prim = self._get_prim(prim_path)
            if not prim:
                return False
            return prim.HasAttribute("omni:onshape:source")

        return False

    def _filter_props_to_build(self, props):
        # simple widget that handles array based properties
        return [
            prop for prop in props if isinstance(prop, Usd.Attribute) and any(prop.GetName() == "omni:onshape:source")
        ]

    def build_items(self):
        ui.Label("Success")

    def build_property_item(self, stage, ui_prop: UsdPropertyUiEntry, prim_paths: List[Sdf.Path]):
        if ui_prop.prim_paths:
            prim_paths = ui_prop.prim_paths
