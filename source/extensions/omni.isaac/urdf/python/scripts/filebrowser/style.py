# Copyright (c) 2018-2020, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
import omni.ui as ui


UI_STYLES = {}

UI_STYLES["NvidiaLight"] = {
    "Label": {"font_size": 20},
    "Rectangle::Splitter": {"background_color": 0xFFE0E0E0, "margin": 3},
    "Rectangle::Splitter:hovered": {"background_color": 0xFFB0703B},
    "Rectangle::Splitter:pressed": {"background_color": 0xFFB0703B},
    "TreeView": {
        "background_color": 0xFFE0E0E0,
        "background_selected_color": 0x109D905C,
        "secondary_color": 0xFFACACAC,
    },
    "TreeView:selected": {"background_color": 0x409D905C},
    "TreeView.Header": {
        "background_color": 0xFFE0E0E0,
        "color": 0xFF535354,
        "border_color": 0xFF707070,
        "border_width": 0.5,
        "font_size": 16,
    },
    "TreeView.Header::name": {"margin": 3, "alignment": ui.Alignment.LEFT},
    "TreeView.Header::date": {"margin": 3, "alignment": ui.Alignment.CENTER},
    "TreeView.Header::size": {"margin": 3, "alignment": ui.Alignment.RIGHT},
    "TreeView.Icon:selected": {"color": 0xFF23211F},
    "TreeView.Header.Icon": {"color": 0xFF8A8777},
    "TreeView.Icon::default": {"color": 0xFF8A8777},
    "TreeView.Icon::file": {"color": 0xFF8A8777},
    "TreeView.Item": {"color": 0xFF535354, "font_size": 16},
    "TreeView.Item:selected": {"color": 0xFF2A2825},
    "TreeView.ScrollingFrame": {"background_color": 0xFFE0E0E0},
}

UI_STYLES["NvidiaDark"] = {
    "Label": {"font_size": 20},
    "Rectangle::Splitter": {"background_color": 0xFF23211F, "margin": 3},
    "Rectangle::Splitter:hovered": {"background_color": 0xFFB0703B},
    "Rectangle::Splitter:pressed": {"background_color": 0xFFB0703B},
    "TreeView": {
        "background_color": 0xFF23211F,
        "background_selected_color": 0x664F4D43,
        "secondary_color": 0xFF403B3B,
    },
    "TreeView:selected": {"background_color": 0xFF8A8777},
    "TreeView.Column": {"background_color": 0x0, "color": 0xFFADAC9F, "margin": 0},
    "TreeView.Header": {"background_color": 0xFF343432, "color": 0xFFADAC9F, "font_size": 16},
    "TreeView.Icon": {"color": 0xFFADAC9F, "padding": 0},
    "TreeView.Icon::expand": {"color": 0xFFFFFFFF, "padding": 0},
    "TreeView.Icon:selected": {"color": 0xFF23211F},
    "TreeView.Item": {"color": 0xFF8A8777, "font_size": 16, "alignment": ui.Alignment.LEFT},
    "TreeView.Item:selected": {"color": 0xFF23211F},
    "TreeView.ScrollingFrame": {"background_color": 0xFF23211F},
    "ZoomBar": {"background_color": 0xFF454545, "border_radius": 2},
    "ZoomBar.Slider": {
        "draw_mode": ui.SliderDrawMode.HANDLE,
        "background_color": 0xCC23211F,
        "color": 0x0,
        "alignment": ui.Alignment.CENTER,
        "padding": 0,
        "margin": 3,
    },
    "ZoomBar.Button": {"background_color": 0x0, "margin": 0, "padding": 0},
    "ZoomBar.Button.Image": {"color": 0xFFADAC9F, "alignment": ui.Alignment.CENTER},
    "GridView": {"background_color": 0xFF23211F},
    "GridView.ScrollingFrame": {"background_color": 0xFF23211F, "padding": 10},
    "Card": {"background_color": 0x0, "margin_width": 10, "margin_height": 0},
    "Card:hovered": {"background_color": 0xFF35352D, "border_radius": 4},
    "Card.Image": {
        "background_color": 0x0,
        "color": 0xFFFFFFFF,
        "border_radius": 2,
        "corner_flag": ui.CornerFlag.TOP,
        "alignment": ui.Alignment.CENTER,
        "margin_width": 10,
        "margin_height": 0,
    },
    "Card.Label": {
        "background_color": 0x0,
        "color": 0xFFADAC9F,
        "font_size": 12,
        "alignment": ui.Alignment.CENTER_TOP,
        "margin_width": 4,
        "margin_height": 2,
    },
}
