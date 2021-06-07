import os
import carb
import omni.ui as ui

settings = carb.settings.get_settings()

UI_STYLES = {}

UI_STYLES["NvidiaLight"] = {
    "Button.Image::filter": {
        "image_url": os.path.join(settings.get_as_string("/persistent/app/window/uiStyle"), "filter.svg"),
        "color": 0xFF535354,
    },
    "Button.Image::options": {
        "image_url": os.path.join(settings.get_as_string("/persistent/app/window/uiStyle"), "options.svg"),
        "color": 0xFF535354,
    },
    "Button.Image::arrow_up": {"image_url": os.path.join("{}", "icons/arrow_up.svg"), "color": 0xFF535354, "margin": 0},
    "Button.Image::arrow_down": {
        "image_url": os.path.join("{}", "icons/arrow_down.svg"),
        "color": 0xFF535354,
        "margin": 0,
    },
    "Button.Image::accept": {"image_url": os.path.join("${glyphs}", "check_square.svg"), "color": 0xFF535354},
    "Button.Image::cancel": {"image_url": os.path.join("${glyphs}", "times_circle.svg"), "color": 0xFF535354},
    "Image::assembly": {"image_url": os.path.join("{}", "icons/assembly.svg"), "color": 0xFF535354, "margin": 0},
    "Image::part_studio": {"image_url": os.path.join("{}", "icons/part_studio.svg"), "color": 0xFF535354, "margin": 0},
    "Image::part": {"image_url": os.path.join("{}", "icons/part_studio.svg"), "color": 0xFF535354, "margin": 0},
    "Button::filter": {"background_color": 0x0, "margin": 0},
    "Button::options": {"background_color": 0x0, "margin": 0},
    "Button::arrow_up": {"background_color": 0x0, "margin": 0},
    "Button::arrow_down": {"background_color": 0x0, "margin": 0},
    "Rectangle::Splitter": {"background_color": 0xFFE0E0E0, "margin_width": 2},
    "Rectangle::Splitter:hovered": {"background_color": 0xFFB0703B},
    "Rectangle::Splitter:pressed": {"background_color": 0xFFB0703B},
    "Splitter": {"background_color": 0xFFE0E0E0, "margin_width": 2},
    "TreeView": {
        "background_color": 0xFF535354,
        "background_selected_color": 0xFF6E6E6E,
        "secondary_color": 0xFFACACAC,
    },
    "TreeView:hovered": {"background_color": 0xFF6E6E6E},
    "TreeView:selected": {"background_color": 0xFFBEBBAE},
    "TreeView.Column": {"background_color": 0x0, "color": 0xFFD6D6D6, "margin": 0},
    "TreeView.Header": {
        "background_color": 0xFF535354,
        "color": 0xFFD6D6D6,
        "border_color": 0xFF707070,
        "border_width": 0.5,
    },
    "TreeView.Header::name": {"margin": 3, "alignment": ui.Alignment.LEFT},
    "TreeView.Header::date": {"margin": 3, "alignment": ui.Alignment.CENTER},
    "TreeView.Header::size": {"margin": 3, "alignment": ui.Alignment.RIGHT},
    "TreeView.Icon:selected": {"color": 0xFF535354},
    "TreeView.Header.Icon": {"color": 0xFF8A8777},
    "TreeView.Icon::default": {"color": 0xFF8A8777},
    "TreeView.Icon::file": {"color": 0xFF8A8777},
    "TreeView.Item": {"color": 0xFFD6D6D6},
    "TreeView.Item:selected": {"color": 0xFF2A2825},
    "TreeView.ScrollingFrame": {"background_color": 0xFF535354, "secondary_color": 0xFFE0E0E0},
    "GridView.ScrollingFrame": {"background_color": 0xFF535354, "secondary_color": 0xFFE0E0E0},
    "GridView.Grid": {"background_color": 0x0, "margin_width": 10},
    "ZoomBar": {"background_color": 0x0, "border_radius": 2},
    "ZoomBar.Slider": {
        "draw_mode": ui.SliderDrawMode.HANDLE,
        "background_color": 0xFF23211F,
        "secondary_color": 0xFF9D9D9D,
        "color": 0x0,
        "alignment": ui.Alignment.CENTER,
        "padding": 0,
        "margin": 5,
        "font_size": 8,
    },
    "ZoomBar.Button": {"background_color": 0x0, "margin": 0, "padding": 0},
    "ZoomBar.Button.Image": {"color": 0xFFFFFFFF, "alignment": ui.Alignment.CENTER},
    "Card": {"background_color": 0x0, "margin": 8},
    "Card:hovered": {"background_color": 0xFF6E6E6E, "border_color": 0xFF3A3A3A, "border_width": 0},
    "Card:selected": {"background_color": 0xFFBEBBAE, "border_color": 0xFF8A8777, "border_width": 0},
    "Card.Image": {
        "background_color": 0xFFC9C9C9,
        "color": 0xFFFFFFFF,
        "corner_flag": ui.CornerFlag.TOP,
        "alignment": ui.Alignment.CENTER,
        "margin": 8,
    },
    "Card.Badge": {"background_color": 0xFFC9C9C9, "color": 0xFFFFFFFF},
    "Card.Badge::shadow": {"background_color": 0xFFC9C9C9, "color": 0xDD444444},
    "Card.Label": {
        "background_color": 0xFFC9C9C9,
        "color": 0xFFD6D6D6,
        "font_size": 12,
        "alignment": ui.Alignment.CENTER_TOP,
        "margin_width": 8,
        "margin_height": 2,
    },
    "Card.Label:checked": {"color": 0xFF23211F},
}

UI_STYLES["NvidiaDark"] = {
    "Button.Image::filter": {"image_url": os.path.join("${glyphs}", "filter.svg"), "color": 0x88FFFFDD},
    "Button.Image::accept": {
        "image_url": os.path.join("${glyphs}", "check_square.svg"),
        "color": 0x88FFFFDD,
        "margin": 0,
        "padding": 0,
    },
    "Button.Image::cancel": {
        "image_url": os.path.join("${glyphs}", "times_circle.svg"),
        "color": 0x88FFFFDD,
        "margin": 0,
        "padding": 0,
    },
    "Button.Image::options": {
        "image_url": os.path.join(settings.get_as_string("/persistent/app/window/uiStyle"), "options.svg"),
        "color": 0x88FFFFDD,
    },
    # "Button.Image::options": {"image_url": os.path.join("{}", "options.svg"), "color": 0x88FFFFDD},
    "Image::processing": {"image_url": os.path.join("${glyphs}", "spinner.svg"), "color": 0x88FFFFDD, "margin": 0},
    "Image::error": {"image_url": os.path.join("${glyphs}", "times_circle.svg"), "color": 0x88AAAAFF, "margin": 0},
    "Image::changed": {"image_url": os.path.join("${glyphs}", "info.svg"), "color": 0x88FFDDDD, "margin": 0},
    "Image::arrow_up": {"image_url": os.path.join("{}", "icons/arrow_up.svg"), "color": 0x88FFFFDD, "margin": 0},
    "Image::arrow_down": {"image_url": os.path.join("{}", "icons/arrow_down.svg"), "color": 0x88FFFFDD, "margin": 0},
    "Button.Image::arrow_up": {"image_url": os.path.join("{}", "icons/arrow_up.svg"), "color": 0x88FFFFDD, "margin": 0},
    "Button.Image::arrow_down": {
        "image_url": os.path.join("{}", "icons/arrow_down.svg"),
        "color": 0x88FFFFDD,
        "margin": 0,
    },
    "Image::assembly": {"image_url": os.path.join("{}", "icons/assembly.svg"), "color": 0x88FFFFDD, "margin": 0},
    "Image::part_studio": {"image_url": os.path.join("{}", "icons/part_studio.svg"), "color": 0x88FFFFDD, "margin": 0},
    "Image::part": {"image_url": os.path.join("{}", "icons/part_studio.svg"), "color": 0x88FFFFDD, "margin": 0},
    "Button::arrow_up": {"margin": 0, "background_color": 0x0},
    # "Button.Text::arrow_up": {"margin": 0, "background_color": 0x0},
    "Button::arrow_down": {"margin": 0, "background_color": 0x0},
    "Button::filter": {"background_color": 0x0, "margin": 0},
    "Button::options": {"background_color": 0x0, "margin": 0},
    "Button::accept": {"padding": 3, "margin": 1},
    "Button::cancel": {"padding": 3, "margin": 1},
    "Label::search": {"color": 0xFF808080, "margin_width": 4},
    "Label::error": {"color": 0xFF1E1EFF},
    "Label::changed": {"color": 0xFFEE3E3E},
    "Splitter": {"background_color": 0x0, "margin_width": 0},
    "Splitter:hovered": {"background_color": 0xFFB0703B},
    "Splitter:pressed": {"background_color": 0xFFB0703B},
    "TreeView.ScrollingFrame": {"background_color": 0xFF23211F},
    "TreeView.Frame": {"background_color": 0xFF23211F},
    "TreeView": {
        "background_color": 0xFF23211F,
        "background_selected_color": 0x223A3A3A,
        "color": 0xFF9E9E9E,
        "selected_color": 0xFF3E3E3E,
    },
    "TreeView:selected": {"background_color": 0xFF8A8777, "color": 0xFF2A2825},
    "TreeView.Column": {"background_color": 0x0, "color": 0xFFADAC9F, "margin": 0},
    "TreeView.Header": {"background_color": 0xFF343432, "color": 0xFF9E9E9E},
    "TreeView.Icon": {"color": 0xFFFFFFFF, "padding": 0},
    "TreeView.Icon::expand": {"color": 0xFFFFFFFF},
    "TreeView.Icon:selected": {"color": 0xFFFFFFFF},
    "TreeView.Checked": {"color": 0xFF444444},
    "Rectangle::Splitter": {"background_color": 0x0, "margin": 3, "border_radius": 2},
    "Rectangle::Splitter:hovered": {"background_color": 0xFFB0703B},
    "Rectangle::Splitter:pressed": {"background_color": 0xFFB0703B},
    "ZoomBar.Button": {"background_color": 0x0, "margin": 0, "padding": 0},
    "ZoomBar.Button.Image": {"color": 0xFFFFFFFF, "alignment": ui.Alignment.CENTER},
    "GridView": {"background_color": 0xFF13110F},
    "GridView.Grid": {"background_color": 0xFF13110F, "margin": 2},
    "Card": {"background_color": 0x33FFFFFF, "margin_width": 8, "border_radius": 10},
    "Card:hovered": {"background_color": 0xFF8A8777, "border_color": 0xFF8A8777, "border_width": 2},
    # "Card:selected": {"background_color": 0x0023212F, "border_color": 0x0023212F, "border_width": 0,"debug_color": 0x44FFFFFF},
    "Card:checked": {
        "background_color": 0xFF232120,
        "color": 0xFF232120,
        "border_color": 0xFFFFFFFF,
        "border_width": 2,
    },
    "Card.Image": {
        "background_color": 0x0,
        "color": 0xFFFFFFFF,
        "corner_flag": ui.CornerFlag.TOP,
        "alignment": ui.Alignment.CENTER,
        "margin": 8,
    },
    "Card.Badge": {"background_color": 0x0, "color": 0xFFFFFFFF},
    "Card.Badge::shadow": {"background_color": 0x0, "color": 0xDD444444},
    "Card.Label": {
        "background_color": 0x0,
        "color": 0xFF9E9E9E,
        "font_size": 13,
        "alignment": ui.Alignment.CENTER_TOP,
        "margin_width": 8,
        "margin_height": 2,
    },
    "Card.Label:checked": {"color": 0xFF1E1E1E},
}


# # try:
# #     import omni.kit.editor

# #     _style = omni.kit.editor.get_editor_interface().get_ui_style()
# # except:
# #     _style = None
# # finally:
# #     if not _style:
# #         _style = "NvidiaDark"
# _style = "NvidiaDark"

# if _style == "NvidiaLight":
#     style = {
#         "Button.Image::filter": {
#             "image_url": os.path.join(settings.get_as_string("/persistent/app/window/uiStyle"), "filter.svg"),
#             "color": 0xFF535354,
#         },
#         "Button.Image::options": {
#             "image_url": os.path.join(settings.get_as_string("/persistent/app/window/uiStyle"), "options.svg"),
#             "color": 0xFF535354,
#         },
#         "Button.Image::arrow_up": {
#             "image_url": os.path.join(settings.get_as_string("/persistent/app/window/uiStyle"), "arrow_up.svg"),
#             "color": 0xFF535354,
#         },
#         "Button.Image::arrow_down": {
#             "image_url": os.path.join(settings.get_as_string("/persistent/app/window/uiStyle"), "arrow_down.svg"),
#             "color": 0xFF535354,
#         },
#         "Button::filter": {"background_color": 0x0, "margin": 0},
#         "Button::options": {"background_color": 0x0, "margin": 0},
#         "Button::arrow_up": {"background_color": 0x0, "margin": 0},
#         "Button::arrow_down": {"background_color": 0x0, "margin": 0},
#         "Field": {"background_color": 0xFF535354, "color": 0xFFCCCCCC},
#         "Label::search": {"color": 0xFFACACAC},
#         "Menu.CheckBox": {"background_color": 0x0, "margin": 0},
#         "Menu.CheckBox::drag": {
#             "image_url": os.path.join(settings.get_as_string("/persistent/app/window/uiStyle"), "drag.svg"),
#             "color": 0xFF505050,
#             "alignment": ui.Alignment.CENTER,
#         },
#         "Menu.CheckBox.Image": {
#             "image_url": os.path.join(settings.get_as_string("/persistent/app/window/uiStyle"), "check_off.svg"),
#             "color": 0xFF8A8777,
#         },
#         "Menu.CheckBox.Image:checked": {
#             "image_url": os.path.join(settings.get_as_string("/persistent/app/window/uiStyle"), "check_on.svg")
#         },
#         "ScrollingFrame": {"secondary_color": 0xFF444444},
#         "TreeView": {
#             "background_color": 0xFFE0E0E0,
#             "background_selected_color": 0x109D905C,
#             "secondary_color": 0xFFACACAC,
#         },
#         "TreeView.ScrollingFrame": {"background_color": 0xFFE0E0E0},
#         "TreeView.Header": {"color": 0xFFCCCCCC},
#         "TreeView.Header::background": {
#             "background_color": 0xFF535354,
#             "border_color": 0xFF707070,
#             "border_width": 0.5,
#         },
#         "TreeView.Header::columnname": {"margin": 3},
#         "TreeView.Image::object_icon_grey": {"color": 0x80FFFFFF},
#         "TreeView.Item": {"color": 0xFF535354, "font_size": 16},
#         "TreeView.Item::object_name": {"margin": 3},
#         "TreeView.Item::object_name_grey": {"color": 0xFFACACAC},
#         "TreeView.Item::object_name_missing": {"color": 0xFF6F72FF},
#         "TreeView.Item:selected": {"color": 0xFF2A2825},
#         "TreeView:selected": {"background_color": 0x409D905C},
#     }
# else:
#     style = {
#         "Button.Image::filter": {
#             "image_url": os.path.join(settings.get_as_string("/persistent/app/window/uiStyle"), "filter.svg"),
#             "color": 0xFF8A8777,
#         },
#         "Button.Image::options": {
#             "image_url": os.path.join(settings.get_as_string("/persistent/app/window/uiStyle"), "options.svg"),
#             "color": 0xFF8A8777,
#         },
#         "Button.Image::arrow_up": {"margin": 0, "color": 0xFF8A8777},
#         "Button.Image::arrow_down": {"margin": 0, "color": 0xFF8A8777},
#         "Button::filter": {"background_color": 0x0, "margin": 0},
#         "Button::options": {"background_color": 0x0, "margin": 0},
#         "Label::search": {"color": 0xFF808080, "margin_width": 4},
#         "Menu.CheckBox": {"background_color": 0x0, "margin": 0},
#         "Menu.CheckBox::drag": {
#             "image_url": os.path.join(settings.get_as_string("/persistent/app/window/uiStyle"), "drag.svg"),
#             "color": 0xFF505050,
#             "alignment": ui.Alignment.CENTER,
#         },
#         "Menu.CheckBox.Image": {
#             "image_url": os.path.join(settings.get_as_string("/persistent/app/window/uiStyle"), "ckeck_off.svg"),
#             "color": 0xFF8A8777,
#         },
#         "Menu.CheckBox.Image:checked": {
#             "image_url": os.path.join(settings.get_as_string("/persistent/app/window/uiStyle"), "ckeck_on.svg")
#         },
#         "TreeView": {
#             "background_color": 0xFF23211F,
#             "background_selected_color": 0x664F4D43,
#             "secondary_color": 0xFF403B3B,
#         },
#         "TreeView.ScrollingFrame": {"background_color": 0xFF23211F},
#         "TreeView.Header": {"background_color": 0xFF343432, "color": 0xFFCCCCCC, "font_size": 13.0},
#         "TreeView.Image::object_icon_grey": {"color": 0x80FFFFFF},
#         "TreeView.Image:disabled": {"color": 0x60FFFFFF},
#         "TreeView.Item": {"color": 0xFF8A8777},
#         "TreeView.Item:disabled": {"color": 0x608A8777},
#         "TreeView.Item::object_name_grey": {"color": 0xFF4D4B42},
#         "TreeView.Item::object_name_missing": {"color": 0xFF6F72FF},
#         "TreeView.Item:selected": {"color": 0xFF23211F},
#         "TreeView:selected": {"background_color": 0xFF8A8777},
#     }
