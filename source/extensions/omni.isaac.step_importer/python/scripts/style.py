# Copyright (c) 2018-2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

tree_style_light = {
    "Field": {"background_color": 0xFF535354, "color": 0xFFCCCCCC},
    "ScrollingFrame": {"background_color": 0xFFE0E0E0, "secondary_color": 0xFF444444},
    "TreeView": {
        "background_color": 0xFFE0E0E0,
        "background_selected_color": 0x109D905C,
        "secondary_color": 0xFFACACAC,
    },
    "TreeView.ScrollingFrame": {"background_color": 0xFFE0E0E0},
    "TreeView.Header": {"color": 0xFFCCCCCC},
    "TreeView.Header::background": {"background_color": 0xFF535354, "border_color": 0xFF707070, "border_width": 0.5},
    "TreeView.Header::columnname": {"margin": 3},
    "TreeView.Image::object_icon_grey": {"color": 0x80FFFFFF},
    "TreeView.Item": {"color": 0xFF535354, "font_size": 16},
    "TreeView.Item::object_name": {"margin": 3},
    "TreeView.Item::object_name_grey": {"color": 0xFFACACAC},
    "TreeView.Item:selected": {"color": 0xFF2A2825},
    "TreeView:selected": {"background_color": 0x409D905C},
}
menu_button_light = {"Button.disabled": {"background_color": 0xFF535354, "color": 0xFFCCCCCC}}


tree_style_dark = {
    "TreeView": {
        "background_color": 0xFF23211F,
        "background_selected_color": 0x664F4D43,
        "secondary_color": 0xFF403B3B,
    },
    "TreeView.ScrollingFrame": {"background_color": 0xFF23211F},
    "TreeView.Header": {"background_color": 0xFF343432, "color": 0xFFCCCCCC, "font_size": 13.0},
    "TreeView.Image::object_icon_grey": {"color": 0x80FFFFFF},
    "TreeView.Item": {"color": 0xFF8A8777},
    "TreeView.Item::object_name_grey": {"color": 0xFF4D4B42},
    "TreeView.Item:selected": {"color": 0xFF23211F},
    "TreeView.Edit": {"background_color": 0xFF343432, "color": 0xFFBBBBBB, "border_radius": 5},
    "TreeView:selected": {"background_color": 0xFF8A8777},
}
menu_button_dark = {
    "Button": {"border_radius": 0, "margin": 0},
    "Button:selected": {"background_color": 0xFF454545, "padding": 5},
    ":disabled": {"color": 0xFF333333},
}
