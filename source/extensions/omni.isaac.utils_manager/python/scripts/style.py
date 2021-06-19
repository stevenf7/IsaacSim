# Copyright (c) 2018-2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

# style from /kit/source/extensions/omni.graph.ui/python/scripts/omnigraph_node_description_editor/style.py

"""Contains common information for styling of the OGN node editor and ancillary windows"""
from omni import ui

# from .ogn_icons import Icons

import os
from pathlib import Path
from typing import Dict

# These values are not affected by style parameters. Using **kwargs keeps them consistent.
VSTACK_ARGS = {"height": 0, "spacing": 8, "margin_height": 4}
HSTACK_PROPERTIES = {"spacing": 10}

# Style names that can be used for the overrides
STYLE_GHOST = "Ghost Prompt"

KIT_GREEN = 0xFF8A8777
LABEL_WIDTH = 120


# Styling information for tooltips
TOOLTIP_STYLE = (
    {
        "background_color": 0xFFFF0000,
        "color": 0xFFFFFFFF,
        "margin_width": 3,
        "margin_height": 2,
        "border_width": 3,
        "border_color": 0xFF000000,
    },
)
#             {
# "background_color": 0xFFD1F7FF,
# "color": 0xFF333333,
# "margin_width": 3,
# "margin_height": 2,
# "border_width": 3,
# "border_color": 0xFF000000,
# }
# Styling for integer input boxes
INT_STYLE = {"Tooltip": TOOLTIP_STYLE}
# Styling for the main menubar
MENU_STYLE = {
    "Tooltip": TOOLTIP_STYLE,
    "background_color": 0xFF555555,
    "background_selected_color": 0xFF999999,
    "color": 0xFFFFFFFF,
    "border_radius": 4,
    "padding": 8,
}
# Styling for the metadata subsection
METADATA_STYLE = {
    "Tooltip": TOOLTIP_STYLE,
    "border_color": 0xFF555555,
    "background_color": 0xFF000000,
    "border_width": 1,
    "margin": 0,
    "TreeView": {"font_size": 12, "color": 0xFFAAAAAA, "background_color": 0xFF23211F, "secondary_color": 0xFF23211F},
    "TreeView::header": {
        "font_size": 12,
        "color": 0xFFAAAAAA,
        "background_color": 0xFF00FFFF,
        "secondary_color": 0xFF23211F,
    },
}
# Styling for string input boxes
STRING_STYLE = {"Tooltip": TOOLTIP_STYLE}
# Styling information for vertical stacks.
VSTACK_STYLE = {"Tooltip": TOOLTIP_STYLE}

# ======================================================================
# General styling for the window as a whole (dark mode)
WINDOW_STYLE = {
    "Window": {"background_color": 0xFF444444},
    "Button": {"background_color": 0xFF292929, "margin": 3, "padding": 3, "border_radius": 2},
    "Button.Label": {"color": 0xFFCCCCCC},
    "Button:hovered": {"background_color": 0xFF9E9E9E},
    "Button:pressed": {"background_color": 0xC22A8778},
    "VStack::main_v_stack": {"secondary_color": 0x0, "margin_width": 10, "margin_height": 0},
    "VStack::frame_v_stack": {"margin_width": 15},
    "Rectangle::frame_background": {"background_color": 0xFF343432, "border_radius": 5},
    "Field::models": {"background_color": 0xFF23211F, "font_size": 14, "color": 0xFFAAAAAA, "border_radius": 4.0},
    "Frame": {"background_color": 0xFFAAAAAA},
    "Label::transform": {"font_size": 14, "color": 0xFF8A8777},
    "Circle::transform": {"background_color": 0x558A8777},
    "Field::transform": {
        "background_color": 0xFF23211F,
        "border_radius": 3,
        "corner_flag": ui.CornerFlag.RIGHT,
        "font_size": 14,
    },
    "Slider::transform": {
        "background_color": 0xFF23211F,
        "border_radius": 3,
        "draw_mode": ui.SliderDrawMode.DRAG,
        "corner_flag": ui.CornerFlag.RIGHT,
        "font_size": 14,
    },
    "Label::transform_label": {"font_size": 14, "color": 0xFFDDDDDD},
    "Label": {"font_size": 14, "color": 0xFF8A8777},
    "Label::label": {"font_size": 14, "color": 0xFF8A8777},
    "Label::title": {"font_size": 14, "color": 0xFFAAAAAA},
    "Triangle::title": {"background_color": 0xFFAAAAAA},
    "ComboBox::path": {"font_size": 12, "secondary_color": 0xFF23211F, "color": 0xFFAAAAAA},
    "ComboBox::choices": {
        "font_size": 12,
        "color": 0xFFAAAAAA,
        "background_color": 0xFF23211F,
        "secondary_color": 0xFF23211F,
    },
    "ComboBox:hovered:choices": {"background_color": 0xFF33312F, "secondary_color": 0xFF33312F},
    "Slider::value_less": {
        "font_size": 14,
        "color": 0x0,
        "border_radius": 5,
        "background_color": 0xFF23211F,
        "secondary_color": KIT_GREEN,
        "border_color": 0xFFAAFFFF,
        "border_width": 0,
    },
    "Slider::value": {
        "font_size": 14,
        "color": 0xFFAAAAAA,
        "border_radius": 5,
        "background_color": 0xFF23211F,
        "secondary_color": KIT_GREEN,
    },
    "Rectangle::add": {"background_color": 0xFF23211F},
    "Rectangle:hovered:add": {"background_color": 0xFF73414F},
    "CheckBox::greenCheck": {"font_size": 12, "background_color": KIT_GREEN, "color": 0xFF23211F},
    "CheckBox::whiteCheck": {"font_size": 12, "background_color": 0xFFDDDDDD, "color": 0xFF23211F},
    "Slider::colorField": {"background_color": 0xFF23211F, "font_size": 14, "color": 0xFF8A8777},
    # Frame
    "CollapsableFrame::standard_collapsable": {
        "background_color": 0xFF343432,
        "secondary_color": 0xFF343432,
        "font_size": 16,
        "border_radius": 2.0,
        "border_color": 0x0,
        "border_width": 0,
    },
    "CollapsableFrame:hovered:standard_collapsable": {"secondary_color": 0xFFFBF1E5},
    "CollapsableFrame:pressed:standard_collapsable": {"secondary_color": 0xFFF7E4CC},
    "Line::grab": {"color": 0xFF2E2E2E, "border_width": 2, "margin": 2},
    "Line::separator": {"color": 0xFF555555},
    "Tooltip": TOOLTIP_STYLE,
}

# ======================================================================
# Styling for tool bar from
# /kit/source/extensions/omni.kit.window.toolbar/omni/kit/window/toolbar/toolbar.py
TOOLBAR = {
    "Button": {"background_color": 0x0, "border_radius": 4, "margin": 2, "padding": 3},
    "Button:checked": {"background_color": 0xFF1F2123},
    "Button:pressed": {"background_color": 0xFF4B4B4B},
    "Button:hovered": {"background_color": 0xFF383838},
    "Button.Image::disabled": {"color": 0x608A8777},
    "Line::grab": {"color": 0xFF2E2E2E, "border_width": 2, "margin": 2},
    "Line::separator": {"color": 0xFF555555},
    "Separator": {"color": 0xFF2E2E2E, "border_width": 2, "margin": 2},
    "ToolButton::main": {
        "font_size": 48,
        "color": 0xFFAAAAAA,
        # "border_radius": 5,
        # "background_color": 0xFF23211F,
        # "secondary_color": KIT_GREEN,
    },
    "Tooltip": TOOLTIP_STYLE
    # "Tooltip": {
    #     "background_color": 0xFFC7F5FC,
    #     "color": 0xFF4B493B,
    #     "border_width": 1,
    #     "margin_width": 2,
    #     "margin_height": 1,
    #     "padding": 1,
    # },
}

# ======================================================================
# Styling for all of the collapsable frames
COLLAPSABLE_FRAME_STYLE = {
    "CollapsableFrame::standard_collapsable": {
        "background_color": 0xFF343432,
        "secondary_color": 0xFF343432,
        "color": 0xFFAAAAAA,
        "border_radius": 4.0,
        "border_color": 0x0,
        "border_width": 0,
        "font_size": 14,
        "padding": 0,
        "margin_height": 5,
        "margin_width": 5,
    },
    "HStack::header": {"margin": 5},
    "CollapsableFrame:hovered": {"secondary_color": 0xFF3A3A3A},
    "CollapsableFrame:pressed": {"secondary_color": 0xFF343432},
}


# ======================================================================
def get_window_style() -> Dict:
    """Returns a dictionary holding the style information for the OGN editor window"""
    import carb.settings

    style_name = carb.settings.get_settings().get_as_string("/persistent/app/window/uiStyle") or "NvidiaDark"
    icons = Icons()
    if style_name == "NvidiaLight":
        style = {
            "AddElement.Image": {"image_url": icons.get("Plus"), "color": 0xFF535354},
            "Button": {"background_color": 0xFF296929, "margin": 3, "padding": 3, "border_radius": 4},
            "Button.Label": {"color": 0xFFCCCCCC},
            "Button:hovered": {"background_color": 0xFF9E9E9E},
            "Button:pressed": {"background_color": 0xC22A8778},
            "DangerButton": {"background_color": 0xFF292989, "margin": 3, "padding": 3, "border_radius": 4},
            "Code": {"color": 0xFFACACAC, "margin_width": 4, "font_size": 14, "background_color": 0xFF535354},
            "FolderImage.Image": {"image_url": icons.get("folder"), "color": 0xFF535354},
            "LabelOverlay": {"background_color": 0xFF535354},
            "Rectangle::frame_background": {"background_color": 0xFFC4C4C2, "border_radius": 5},
            "RemoveElement.Image": {"image_url": icons.get("trash"), "color": 0xFF535354},
            "ScrollingFrame": {"secondary_color": 0xFF444444},
            STYLE_GHOST: {"color": 0xFF4C4C4C},
            "Tooltip": {
                "background_color": 0xFFD1F7FF,
                "color": 0xFF333333,
                "margin_width": 3,
                "margin_height": 2,
                "border_width": 3,
                "border_color": 0xFF000000,
            },
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
            "TreeView.Item": {"color": 0xFF535354, "font_size": 16},
            "TreeView.Item:selected": {"color": 0xFF2A2825},
            "TreeView:selected": {"background_color": 0x409D905C},
        }
    else:
        style = {
            "AddElement.Image": {"image_url": icons.get("Plus"), "color": 0xFF8A8777},
            "Button": {"background_color": 0xFF296929, "margin": 3, "padding": 3, "border_radius": 4},
            "Button.Label": {"color": 0xFFCCCCCC},
            "Button:hovered": {"background_color": 0xFF9E9E9E},
            "Button:pressed": {"background_color": 0xC22A8778},
            "DangerButton": {"background_color": 0xFF292989, "margin": 3, "padding": 3, "border_radius": 4},
            "Code": {"color": 0xFF808080, "margin_width": 4, "font_size": 14, "background_color": 0xFF8A8777},
            "FolderImage.Image": {"image_url": icons.get("folder"), "color": 0xFF8A8777},
            "RemoveElement.Image": {"image_url": icons.get("trash"), "color": 0xFF8A8777},
            STYLE_GHOST: {"color": 0xFF4C4C4C, "margin_width": 4},
            "Tooltip": {
                "background_color": 0xFFD1F7FF,
                "color": 0xFF333333,
                "margin_width": 3,
                "margin_height": 2,
                "border_width": 3,
                "border_color": 0xFF000000,
            },
            "TreeView": {
                "background_color": 0xFF23211F,
                "background_selected_color": 0x664F4D43,
                "secondary_color": 0xFF403B3B,
            },
            "TreeView.ScrollingFrame": {"background_color": 0xFF23211F},
            "TreeView.Header": {"background_color": 0xFF343432, "color": 0xFFCCCCCC, "font_size": 13.0},
            "TreeView.Image:disabled": {"color": 0x60FFFFFF},
            "TreeView.Item": {"color": 0xFF8A8777},
            "TreeView.Item:disabled": {"color": 0x608A8777},
            "TreeView.Item:selected": {"color": 0xFF23211F},
            "TreeView:selected": {"background_color": 0xFF8A8777},
        }

    # Add the style elements common to both light and dark
    shared_style = {
        "ScrollingFrame": {"margin_height": 10},
        "Frame::attribute_value_frame": {"margin_height": 5, "margin_width": 5},
        "Label::frame_label": {"margin_width": 5},
        "CheckBox": {"font_size": 12},
        "CollapsableFrame": {
            "background_color": 0xFF343432,
            "secondary_color": 0xFF343432,
            "color": 0xFFAAAAAA,
            "border_radius": 4.0,
            "border_color": 0x0,
            "border_width": 0,
            "font_size": 16,
            "padding": 0,
            "margin_width": 5,
        },
        "CollapsableFrame:hovered": {"secondary_color": 0xFF3A3A3A},
        "CollapsableFrame:pressed": {"secondary_color": 0xFF343432},
        # "HStack": {"height": 0, "spacing": 5, "margin_width": 10},
        # "HStack::header": {"margin": 5},
        # "Label": {"word_wrap": True},
        "VStack": {"margin_height": 5},
    }

    # Add some color to hovered widgets for debugging
    if os.getenv("OGN_DEBUG_EDITOR"):
        shared_style[":hovered"] = {"debug_color": 0x22FFDDDD}

    style.update(shared_style)
    return style


# ======================================================================
# Constants for the layout of the window
WIDGET_WIDTH = 200  # Standard widget width
LINE_HEIGHT = 16  # Height of a single input line
NAME_VALUE_WIDTH = 150  # Width of the node property name column


# ======================================================================
def name_value_label(property_name: str, tooltip: str = ""):
    """Emit a UI label for the node property names; allows a common fixed width for the column"""
    return ui.Label(property_name, width=NAME_VALUE_WIDTH, alignment=ui.Alignment.RIGHT_TOP, tooltip=tooltip)


# ======================================================================
def name_value_hstack():
    """Emit an HStack widget suitable for the property/value pairs for node properties"""
    return ui.HStack(**HSTACK_PROPERTIES)


# ======================================================================
def icon_directory() -> Path:
    """Returns a string containing the path to the icon directory for the current style"""
    import carb.settings

    style_name = carb.settings.get_settings().get_as_string("/persistent/app/window/uiStyle") or "NvidiaDark"
    return Path(__file__).joinpath("icons").joinpath(style_name)
