# Copyright (c) 2022-2023, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

import omni.ui as ui
from omni.kit.window.property.templates import LABEL_HEIGHT, LABEL_WIDTH

label_kwargs = {
    "style_type_name_override": "Label::label",
    "word_wrap": True,
    "width": LABEL_WIDTH / 2,
    "height": LABEL_HEIGHT,
    "alignment": ui.Alignment.LEFT_TOP,
}
text_kwargs = {
    "style_type_name_override": "Label::label",
    "height": LABEL_HEIGHT,
    "alignment": ui.Alignment.LEFT_TOP,
    "style": {"font_size": 16, "color": 0xFFC7C7C7},
    "word_wrap": True,
}
scroll_kwargs = {
    "style_type_name_override": "ScrollingFrame",
    "alignment": ui.Alignment.LEFT_TOP,
    "horizontal_scrollbar_policy": ui.ScrollBarPolicy.SCROLLBAR_AS_NEEDED,
    "vertical_scrollbar_policy": ui.ScrollBarPolicy.SCROLLBAR_ALWAYS_ON,
}
