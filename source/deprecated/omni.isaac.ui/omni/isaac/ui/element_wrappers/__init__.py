# Copyright (c) 2023-2024, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

import carb

old_extension_name = "omni.isaac.ui"
new_extension_name = "isaacsim.gui.components"

# Provide deprecation warning to user
carb.log_warn(
    f"{old_extension_name} has been deprecated in favor of {new_extension_name}. Please update your code accordingly."
)


from .base_ui_element_wrappers import UIWidgetWrapper
from .ui_widget_wrappers import (
    Button,
    CheckBox,
    CollapsableFrame,
    ColorPicker,
    DropDown,
    FloatField,
    Frame,
    IntField,
    ScrollingFrame,
    ScrollingWindow,
    StateButton,
    StringField,
    TextBlock,
    XYPlot,
)
