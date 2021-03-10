# Copyright (c) 2020, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
import carb
import omni.usd
import omni.ui as ui
from omni.kit.property.usd.usd_property_widget import UsdPropertiesWidget, UsdPropertyUiEntry
from pxr import Usd, Sdf, Gf, Tf
from typing import List
from omni.kit.property.usd.usd_property_widget_builder import UsdPropertiesWidgetBuilder
from omni.kit.property.usd.usd_attribute_model import UsdAttributeModel

from .array_widget import ArrayPropertiesWidget
from .custom_data import CustomDataWidget


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
        w.register_widget("prim", "isaac_array", ArrayPropertiesWidget(title="Array Properties", collapsed=True), False)
        w.register_widget(
            "prim", "isaac_custom_data", CustomDataWidget(title="Prim Custom Data", collapsed=True), False
        )

    def _unregister_widget(self):
        import omni.kit.window.property as p

        w = p.get_window()
        if w:
            w.unregister_widget("prim", "isaac_array")
            w.unregister_widget("prim", "isaac_custom_data")
            self._registered = False
