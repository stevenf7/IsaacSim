import sys
import os
import subprocess
import carb.settings
import omni.ui as ui
import omni.ext
import omni.appwindow
import asyncio

from omni.kit.window.property.templates import LABEL_WIDTH, LABEL_HEIGHT
from omni.kit.window.extensions import SimpleCheckBox
from omni.kit.window.filepicker import FilePickerDialog

from .style import get_style, BUTTON_WIDTH, COLOR_X, COLOR_Y, COLOR_Z, COLOR_W


def btn_builder(label="", type="button", text="button", tooltip="", on_clicked_fn=None):
    """Creates a Stylized Button"""
    with ui.HStack():
        ui.Label(label, width=LABEL_WIDTH, alignment=ui.Alignment.LEFT_CENTER, tooltip=format_tt(tooltip))
        btn = ui.Button(
            text.upper(),
            name="Button",
            width=BUTTON_WIDTH,
            clicked_fn=on_clicked_fn,
            style=get_style(),
            alignment=ui.Alignment.LEFT_CENTER,
        )
        ui.Spacer(width=5)
        add_line_rect_flourish(True)
        # ui.Spacer(width=ui.Fraction(1))
        # ui.Spacer(width=10)
        # with ui.Frame(width=0):
        #     with ui.VStack():
        #         with ui.Placer(offset_x=0, offset_y=7):
        #             ui.Rectangle(height=5, width=5, alignment=ui.Alignment.CENTER)
        # ui.Spacer(width=5)
    return btn


def state_btn_builder(
    label="", type="state_button", a_text="STATE A", b_text="STATE B", tooltip="", on_clicked_fn=None
):
    """Creates a State Change Button"""

    def toggle():
        if btn.text == a_text.upper():
            btn.text = b_text.upper()
            on_clicked_fn(True)
        else:
            btn.text = a_text.upper()
            on_clicked_fn(False)

    with ui.HStack():
        ui.Label(label, width=LABEL_WIDTH, alignment=ui.Alignment.LEFT_CENTER, tooltip=format_tt(tooltip))
        btn = ui.Button(
            a_text.upper(),
            name="Button",
            width=BUTTON_WIDTH,
            clicked_fn=toggle,
            style=get_style(),
            alignment=ui.Alignment.LEFT_CENTER,
        )
        ui.Spacer(width=5)
        # add_line_rect_flourish(False)
        ui.Spacer(width=ui.Fraction(1))
        ui.Spacer(width=10)
        with ui.Frame(width=0):
            with ui.VStack():
                with ui.Placer(offset_x=0, offset_y=7):
                    ui.Rectangle(height=5, width=5, alignment=ui.Alignment.CENTER)
        ui.Spacer(width=5)
    return btn


def cb_builder(label="", type="checkbox", default_val=False, tooltip="", on_clicked_fn=None):
    """Creates a Stylized Checkbox"""

    with ui.HStack():
        ui.Label(label, width=LABEL_WIDTH - 12, alignment=ui.Alignment.LEFT_CENTER, tooltip=format_tt(tooltip))
        model = ui.SimpleBoolModel()
        callable = on_clicked_fn
        if callable is None:
            callable = lambda x: None
        SimpleCheckBox(default_val, callable, model=model)

        add_line_rect_flourish()
        return model


def multi_btn_builder(
    label="", type="multi_button", count=2, text=["button", "button"], tooltip=["", "", ""], on_clicked_fn=[None, None]
):
    """Creates a Row of Stylized Buttons"""
    btns = []
    with ui.HStack():
        ui.Label(label, width=LABEL_WIDTH, alignment=ui.Alignment.LEFT_CENTER, tooltip=format_tt(tooltip[0]))
        for i in range(count):
            btn = ui.Button(
                text[i].upper(),
                name="Button",
                width=BUTTON_WIDTH,
                clicked_fn=on_clicked_fn[i],
                tooltip=format_tt(tooltip[i + 1]),
                style=get_style(),
                alignment=ui.Alignment.LEFT_CENTER,
            )
            btns.append(btn)
            if i < count:
                ui.Spacer(width=5)
        add_line_rect_flourish()
    return btns


def multi_cb_builder(
    label="",
    type="multi_checkbox",
    count=2,
    text=[" ", " "],
    default_val=[False, False],
    tooltip=["", "", ""],
    on_clicked_fn=[None, None],
):
    """Creates a Row of Stylized Checkboxes"""
    cbs = []
    with ui.HStack():
        ui.Label(label, width=LABEL_WIDTH - 12, alignment=ui.Alignment.LEFT_CENTER, tooltip=format_tt(tooltip[0]))
        for i in range(count):
            cb = SimpleCheckBox(default_val[i], on_clicked_fn[i])
            ui.Label(
                text[i], width=BUTTON_WIDTH / 2, alignment=ui.Alignment.LEFT_CENTER, tooltip=format_tt(tooltip[i + 1])
            )
            if i < count - 1:
                ui.Spacer(width=5)
            cbs.append(cb)
        add_line_rect_flourish()
    return cbs


def str_builder(
    label="",
    type="stringfield",
    default_val=" ",
    tooltip="",
    on_clicked_fn=None,
    use_folder_picker=False,
    read_only=False,
):
    """Creates a Stylized Stringfield Widget"""
    with ui.HStack():
        ui.Label(label, width=LABEL_WIDTH, alignment=ui.Alignment.LEFT_CENTER, tooltip=format_tt(tooltip))
        str_field = ui.StringField(
            name="StringField", width=ui.Fraction(1), height=0, alignment=ui.Alignment.LEFT_CENTER, read_only=read_only
        ).model
        str_field.set_value(default_val)

        if use_folder_picker:

            def update_field(val):
                str_field.set_value(val)

            add_folder_picker_icon(update_field)
        else:
            add_line_rect_flourish(False)
        return str_field


def float_builder(label="", type="floatfield", default_val=0, tooltip=""):
    """Creates a Stylized Floatfield Widget"""
    with ui.HStack():
        ui.Label(label, width=LABEL_WIDTH, alignment=ui.Alignment.LEFT_CENTER, tooltip=format_tt(tooltip))
        float_field = ui.FloatField(
            name="FloatField", width=ui.Fraction(1), height=0, alignment=ui.Alignment.LEFT_CENTER
        ).model
        float_field.set_value(default_val)
        add_line_rect_flourish(False)
        return float_field


def combo_cb_str_builder(
    label="",
    type="checkbox_stringfield",
    default_val=[False, " "],
    tooltip="",
    on_clicked_fn=None,
    use_folder_picker=False,
):
    """Creates a Stylized Checkbox + Stringfield Widget"""
    with ui.HStack():
        ui.Label(label, width=LABEL_WIDTH - 12, alignment=ui.Alignment.LEFT_CENTER, tooltip=format_tt(tooltip))
        cb = SimpleCheckBox(default_val[0], on_clicked_fn)
        str_field = ui.StringField(
            name="StringField", width=ui.Fraction(1), height=0, alignment=ui.Alignment.LEFT_CENTER
        ).model
        str_field.set_value(default_val[1])

        if use_folder_picker:

            def update_field(val):
                str_field.set_value(val)

            add_folder_picker_icon(update_field)
        else:
            add_line_rect_flourish(False)
        return cb, str_field


def dropdown_builder(
    label="", type="dropdown", default_val=0, items=["Option 1", "Option 2", "Option 3"], tooltip="", on_clicked_fn=None
):
    """Creates a Stylized Dropdown Combobox"""
    with ui.HStack():
        ui.Label(label, width=LABEL_WIDTH, alignment=ui.Alignment.LEFT_CENTER, tooltip=format_tt(tooltip))
        combo_box = ui.ComboBox(
            default_val, *items, name="ComboBox", width=ui.Fraction(1), alignment=ui.Alignment.LEFT_CENTER
        ).model
        add_line_rect_flourish(False)

        def on_clicked_wrapper(model, val):
            on_clicked_fn(items[model.get_item_value_model().as_int])

        if on_clicked_fn is not None:
            combo_box.add_item_changed_fn(on_clicked_wrapper)

    return combo_box


def combo_floatfield_slider_builder(
    label="", type="floatfield_stringfield", default_val=0.5, min=0, max=1, step=0.01, tooltip=["", ""]
):
    """Creates a Stylized FloatField + Stringfield Widget"""
    with ui.HStack():
        ui.Label(label, width=LABEL_WIDTH, alignment=ui.Alignment.LEFT_CENTER, tooltip=format_tt(tooltip[0]))
        ff = ui.FloatField(
            name="Field", width=BUTTON_WIDTH / 2, alignment=ui.Alignment.LEFT_CENTER, tooltip=format_tt(tooltip[1])
        ).model
        ff.set_value(default_val)
        ui.Spacer(width=5)
        fs = ui.FloatSlider(
            width=ui.Fraction(1), alignment=ui.Alignment.LEFT_CENTER, min=min, max=max, step=step, model=ff
        )

        add_line_rect_flourish(False)
        return ff, fs


def multi_dropdown_builder(
    label="",
    type="dropdown",
    count=2,
    default_val=[0, 0],
    items=[["Option 1", "Option 2", "Option 3"], ["Option A", "Option B", "Option C"]],
    tooltip="",
    on_clicked_fn=[None, None],
):
    """Creates a Stylized Dropdown Combobox"""
    elems = []
    with ui.HStack():
        ui.Label(label, width=LABEL_WIDTH, alignment=ui.Alignment.LEFT_CENTER, tooltip=format_tt(tooltip))
        for i in range(count):
            elem = ui.ComboBox(
                default_val[i], *items[i], name="ComboBox", width=ui.Fraction(1), alignment=ui.Alignment.LEFT_CENTER
            )

            def on_clicked_wrapper(model, val, index):
                on_clicked_fn[index](items[index][model.get_item_value_model().as_int])

            elem.model.add_item_changed_fn(lambda m, v, index=i: on_clicked_wrapper(m, v, index))
            elems.append(elem)
            if i < count - 1:
                ui.Spacer(width=5)
        add_line_rect_flourish(False)
        return elems


def combo_cb_dropdown_builder(
    label="",
    type="checkbox_dropdown",
    default_val=[False, 0],
    items=["Option 1", "Option 2", "Option 3"],
    tooltip="",
    on_clicked_fn=[None, None],
):
    """Creates a Stylized Dropdown Combobox with an Enable Checkbox"""
    with ui.HStack():
        ui.Label(label, width=LABEL_WIDTH - 12, alignment=ui.Alignment.LEFT_CENTER, tooltip=format_tt(tooltip))
        cb = SimpleCheckBox(default_val[0], on_clicked_fn[0])
        combo_box = ui.ComboBox(
            default_val[1], *items, name="ComboBox", width=ui.Fraction(1), alignment=ui.Alignment.LEFT_CENTER
        )

        def on_clicked_wrapper(model, val):

            on_clicked_fn[1](items[model.get_item_value_model().as_int])

        combo_box.model.add_item_changed_fn(on_clicked_wrapper)

        add_line_rect_flourish(False)

        return cb, combo_box


def scrolling_frame_builder(label="", type="scrolling_frame", default_val="No Data", tooltip=""):
    """Creates a Labeled Scrolling Frame with CopyToClipboard button"""

    def copy_to_clipboard():
        try:
            import pyperclip

            pyperclip.copy(text.text)
        except ImportError:
            carb.log_warn("Could not import pyperclip.")

    with ui.VStack(style=get_style(), spacing=5):
        with ui.HStack():
            ui.Label(label, width=LABEL_WIDTH, alignment=ui.Alignment.LEFT_TOP, tooltip=format_tt(tooltip))
            with ui.ScrollingFrame(
                height=LABEL_HEIGHT * 5,
                style_type_name_override="ScrollingFrame",
                alignment=ui.Alignment.LEFT_TOP,
                horizontal_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_AS_NEEDED,
                vertical_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_ALWAYS_ON,
            ):
                text = ui.Label(
                    default_val,
                    style_type_name_override="Label::label",
                    word_wrap=True,
                    alignment=ui.Alignment.LEFT_TOP,
                )

            ui.Button(
                name="IconButton",
                width=20,
                height=20,
                clicked_fn=copy_to_clipboard,
                style=get_style()["IconButton.Image::CopyToClipboard"],
                alignment=ui.Alignment.RIGHT_TOP,
                tooltip="Copy To Clipboard",
            )
    return text


def combo_cb_scrolling_frame_builder(
    label="", type="scrolling_frame", default_val=[False, "No Data"], tooltip="", on_clicked_fn=None
):
    """Creates a Labeled, Checkbox-enabled Scrolling Frame with CopyToClipboard button"""

    def copy_to_clipboard():
        try:
            import pyperclip

            pyperclip.copy(text.text)
        except ImportError:
            carb.log_warn("Could not import pyperclip.")

    with ui.VStack(style=get_style(), spacing=5):
        with ui.HStack():
            ui.Label(label, width=LABEL_WIDTH - 12, alignment=ui.Alignment.LEFT_TOP, tooltip=format_tt(tooltip))
            with ui.VStack(width=0):
                cb = SimpleCheckBox(default_val[0], on_clicked_fn)
                ui.Spacer(height=18 * 4)
            with ui.ScrollingFrame(
                height=18 * 5,
                style_type_name_override="ScrollingFrame",
                alignment=ui.Alignment.LEFT_TOP,
                horizontal_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_AS_NEEDED,
                vertical_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_ALWAYS_ON,
            ):
                text = ui.Label(
                    default_val[1],
                    style_type_name_override="Label::label",
                    word_wrap=True,
                    alignment=ui.Alignment.LEFT_TOP,
                )

            ui.Button(
                name="IconButton",
                width=20,
                height=20,
                clicked_fn=copy_to_clipboard,
                style=get_style()["IconButton.Image::CopyToClipboard"],
                alignment=ui.Alignment.RIGHT_TOP,
                tooltip="Copy To Clipboard",
            )
    return cb, text


def xyz_builder(
    label="",
    tooltip="",
    axis_count=3,
    default_val=[0.0, 0.0, 0.0, 0.0],
    min=float("-inf"),
    max=float("inf"),
    step=0.001,
    on_value_changed_fn=[None, None, None, None],
):

    # These styles & colors are taken from omni.kit.property.transform_builder.py _create_multi_float_drag_matrix_with_labels
    if axis_count <= 0 or axis_count > 4:
        import builtins

        carb.log_warn("Invalid axis_count: must be in range 1 to 4. Clamping to default range.")
        axis_count = builtins.max(builtins.min(axis_count, 4), 1)

    field_labels = [("X", COLOR_X), ("Y", COLOR_Y), ("Z", COLOR_Z), ("W", COLOR_W)]
    field_tooltips = ["X Value", "Y Value", "Z Value", "W Value"]
    RECT_WIDTH = 13
    # SPACING = 4
    val_models = [None] * axis_count
    with ui.HStack():
        ui.Label(label, width=LABEL_WIDTH, alignment=ui.Alignment.LEFT_CENTER, tooltip=format_tt(tooltip))
        with ui.ZStack():
            with ui.HStack():
                ui.Spacer(width=RECT_WIDTH)
                for i in range(axis_count):
                    val_models[i] = ui.FloatDrag(
                        name="Field",
                        height=LABEL_HEIGHT,
                        min=min,
                        max=max,
                        step=step,
                        alignment=ui.Alignment.LEFT_CENTER,
                        tooltip=field_tooltips[i],
                    ).model
                    val_models[i].set_value(default_val[i])
                    if on_value_changed_fn[i] is not None:
                        val_models[i].add_value_changed_fn(on_value_changed_fn[i])
                    if i != axis_count - 1:
                        ui.Spacer(width=19)
            with ui.HStack():
                for i in range(axis_count):
                    if i != 0:
                        ui.Spacer()  # width=BUTTON_WIDTH - 1)
                    field_label = field_labels[i]
                    with ui.ZStack(width=RECT_WIDTH + 2 * i):
                        ui.Rectangle(name="vector_label", style={"background_color": field_label[1]})
                        ui.Label(field_label[0], name="vector_label", alignment=ui.Alignment.CENTER)
                ui.Spacer()
        add_line_rect_flourish(False)
        return val_models


def color_picker_builder(label="", type="color_picker", default_val=[1.0, 1.0, 1.0, 1.0], tooltip="Color Picker"):
    """Creates a Color Picker Widget"""
    with ui.HStack():
        ui.Label(label, width=LABEL_WIDTH, alignment=ui.Alignment.LEFT_CENTER, tooltip=format_tt(tooltip))
        model = ui.ColorWidget(*default_val, width=BUTTON_WIDTH).model
        ui.Spacer(width=5)
        add_line_rect_flourish()
    return model


def progress_bar_builder(label="", type="progress_bar", default_val=0, tooltip="Progress"):
    "Creates a Progress Bar Widget"
    with ui.HStack():
        ui.Label("Progress Bar", width=LABEL_WIDTH, alignment=ui.Alignment.LEFT_CENTER)
        model = ui.ProgressBar().model
        model.set_value(default_val)
        add_line_rect_flourish(False)
    return model


def plot_builder(label="", data=None, min=-1, max=1, type=ui.Type.LINE, value_stride=1, color=None, tooltip=""):
    with ui.VStack(spacing=5):
        with ui.HStack():
            ui.Label(label, width=LABEL_WIDTH, alignment=ui.Alignment.LEFT_TOP, tooltip=format_tt(tooltip))

            plot_height = LABEL_HEIGHT * 2 + 13
            plot_width = ui.Fraction(1)
            with ui.ZStack():
                ui.Rectangle(width=plot_width, height=plot_height)
                if not color:
                    color = 0xFFDDDDDD
                plot = ui.Plot(
                    type,
                    min,
                    max,
                    *data,
                    value_stride=value_stride,
                    width=plot_width,
                    height=plot_height,
                    style={"color": color, "background_color": 0x0},
                )

            def update_min(model):
                plot.scale_min = model.as_float

            def update_max(model):
                plot.scale_max = model.as_float

            ui.Spacer(width=5)
            with ui.Frame(width=0):
                with ui.VStack(spacing=5):
                    max_model = ui.FloatDrag(
                        name="Field", width=40, alignment=ui.Alignment.LEFT_BOTTOM, tooltip="Max"
                    ).model
                    max_model.set_value(max)
                    min_model = ui.FloatDrag(
                        name="Field", width=40, alignment=ui.Alignment.LEFT_TOP, tooltip="Min"
                    ).model
                    min_model.set_value(min)

                    min_model.add_value_changed_fn(update_min)
                    max_model.add_value_changed_fn(update_max)

            ui.Spacer(width=20)
        add_separator()

    return plot


def xyz_plot_builder(label="", data=[], min=-1, max=1, tooltip=""):
    with ui.VStack(spacing=5):
        with ui.HStack():
            ui.Label(label, width=LABEL_WIDTH, alignment=ui.Alignment.LEFT_TOP, tooltip=format_tt(tooltip))

            plot_height = LABEL_HEIGHT * 2 + 13
            plot_width = ui.Fraction(1)
            with ui.ZStack():
                ui.Rectangle(width=plot_width, height=plot_height)

                plot_0 = ui.Plot(
                    ui.Type.LINE,
                    min,
                    max,
                    *data[0],
                    width=plot_width,
                    height=plot_height,
                    style=get_style()["PlotLabel::X"],
                )
                plot_1 = ui.Plot(
                    ui.Type.LINE,
                    min,
                    max,
                    *data[1],
                    width=plot_width,
                    height=plot_height,
                    style=get_style()["PlotLabel::Y"],
                )
                plot_2 = ui.Plot(
                    ui.Type.LINE,
                    min,
                    max,
                    *data[2],
                    width=plot_width,
                    height=plot_height,
                    style=get_style()["PlotLabel::Z"],
                )

            def update_min(model):
                plot_0.scale_min = model.as_float
                plot_1.scale_min = model.as_float
                plot_2.scale_min = model.as_float

            def update_max(model):
                plot_0.scale_max = model.as_float
                plot_1.scale_max = model.as_float
                plot_2.scale_max = model.as_float

            ui.Spacer(width=5)
            with ui.Frame(width=0):
                with ui.VStack(spacing=5):
                    max_model = ui.FloatDrag(
                        name="Field", width=40, alignment=ui.Alignment.LEFT_BOTTOM, tooltip="Max"
                    ).model
                    max_model.set_value(max)
                    min_model = ui.FloatDrag(
                        name="Field", width=40, alignment=ui.Alignment.LEFT_TOP, tooltip="Min"
                    ).model
                    min_model.set_value(min)

                    min_model.add_value_changed_fn(update_min)
                    max_model.add_value_changed_fn(update_max)
            ui.Spacer(width=20)

        add_separator()
        return [plot_0, plot_1, plot_2]


def combo_cb_plot_builder(
    label="",
    default_val=False,
    on_clicked_fn=None,
    data=None,
    min=-1,
    max=1,
    type=ui.Type.LINE,
    value_stride=1,
    color=None,
    tooltip="",
):
    with ui.VStack(spacing=5):
        with ui.HStack():
            # Label
            ui.Label(label, width=LABEL_WIDTH, alignment=ui.Alignment.LEFT_TOP, tooltip=format_tt(tooltip))
            # Checkbox
            with ui.Frame(width=0):
                with ui.Placer(offset_x=-10, offset_y=0):
                    with ui.VStack():
                        SimpleCheckBox(default_val, on_clicked_fn)
                        ui.Spacer(height=ui.Fraction(1))
                        ui.Spacer()
            # Plot
            plot_height = LABEL_HEIGHT * 2 + 13
            plot_width = ui.Fraction(1)
            with ui.ZStack():
                ui.Rectangle(width=plot_width, height=plot_height)
                if not color:
                    color = 0xFFDDDDDD
                plot = ui.Plot(
                    type,
                    min,
                    max,
                    *data,
                    value_stride=value_stride,
                    width=plot_width,
                    height=plot_height,
                    style={"color": color, "background_color": 0x0},
                )

            # Min/Max Helpers
            def update_min(model):
                plot.scale_min = model.as_float

            def update_max(model):
                plot.scale_max = model.as_float

            ui.Spacer(width=5)
            with ui.Frame(width=0):
                with ui.VStack(spacing=5):
                    # Min/Max Fields
                    max_model = ui.FloatDrag(
                        name="Field", width=40, alignment=ui.Alignment.LEFT_BOTTOM, tooltip="Max"
                    ).model
                    max_model.set_value(max)
                    min_model = ui.FloatDrag(
                        name="Field", width=40, alignment=ui.Alignment.LEFT_TOP, tooltip="Min"
                    ).model
                    min_model.set_value(min)

                    min_model.add_value_changed_fn(update_min)
                    max_model.add_value_changed_fn(update_max)
            ui.Spacer(width=20)
        with ui.HStack():
            ui.Spacer(width=LABEL_WIDTH + 29)
            # Current Value Field (disabled by default)
            val_model = ui.FloatDrag(
                name="Field",
                width=BUTTON_WIDTH,
                height=LABEL_HEIGHT,
                enabled=False,
                alignment=ui.Alignment.LEFT_CENTER,
                tooltip="Value",
            ).model
        add_separator()
    return plot, val_model


def combo_cb_xyz_plot_builder(
    label="",
    default_val=False,
    on_clicked_fn=None,
    data=[],
    min=-1,
    max=1,
    type=ui.Type.LINE,
    value_stride=1,
    args=[0.0, 0.0, 0.0],
    tooltip="",
):
    with ui.VStack(spacing=5):
        with ui.HStack():
            ui.Label(label, width=LABEL_WIDTH, alignment=ui.Alignment.LEFT_TOP, tooltip=format_tt(tooltip))
            # Checkbox
            with ui.Frame(width=0):
                with ui.Placer(offset_x=-10, offset_y=0):
                    with ui.VStack():
                        SimpleCheckBox(default_val, on_clicked_fn)
                        ui.Spacer(height=ui.Fraction(1))
                        ui.Spacer()
            # Plots
            plot_height = LABEL_HEIGHT * 2 + 13
            plot_width = ui.Fraction(1)
            with ui.ZStack():
                ui.Rectangle(width=plot_width, height=plot_height)

                plot_0 = ui.Plot(
                    type,
                    min,
                    max,
                    *data[0],
                    value_stride=value_stride,
                    width=plot_width,
                    height=plot_height,
                    style=get_style()["PlotLabel::X"],
                )
                plot_1 = ui.Plot(
                    type,
                    min,
                    max,
                    *data[1],
                    value_stride=value_stride,
                    width=plot_width,
                    height=plot_height,
                    style=get_style()["PlotLabel::Y"],
                )
                plot_2 = ui.Plot(
                    type,
                    min,
                    max,
                    *data[2],
                    value_stride=value_stride,
                    width=plot_width,
                    height=plot_height,
                    style=get_style()["PlotLabel::Z"],
                )

            def update_min(model):
                plot_0.scale_min = model.as_float
                plot_1.scale_min = model.as_float
                plot_2.scale_min = model.as_float

            def update_max(model):
                plot_0.scale_max = model.as_float
                plot_1.scale_max = model.as_float
                plot_2.scale_max = model.as_float

            ui.Spacer(width=5)
            with ui.Frame(width=0):
                with ui.VStack(spacing=5):
                    max_model = ui.FloatDrag(
                        name="Field", width=40, alignment=ui.Alignment.LEFT_BOTTOM, tooltip="Max"
                    ).model
                    max_model.set_value(max)
                    min_model = ui.FloatDrag(
                        name="Field", width=40, alignment=ui.Alignment.LEFT_TOP, tooltip="Min"
                    ).model
                    min_model.set_value(min)

                    min_model.add_value_changed_fn(update_min)
                    max_model.add_value_changed_fn(update_max)
            ui.Spacer(width=20)

        # with ui.HStack():
        #     ui.Spacer(width=40)
        #     val_models = xyz_builder()#**{"args":args})

        field_labels = [("X", COLOR_X), ("Y", COLOR_Y), ("Z", COLOR_Z), ("W", COLOR_W)]
        RECT_WIDTH = 13
        # SPACING = 4
        with ui.HStack():
            ui.Spacer(width=LABEL_WIDTH + 29)

            with ui.ZStack():
                with ui.HStack():
                    ui.Spacer(width=RECT_WIDTH)
                    # value_widget = ui.MultiFloatDragField(
                    #     *args, name="multivalue", min=min, max=max, step=step, h_spacing=RECT_WIDTH + SPACING, v_spacing=2
                    # ).model
                    val_model_x = ui.FloatDrag(
                        name="Field",
                        width=BUTTON_WIDTH - 5,
                        height=LABEL_HEIGHT,
                        enabled=False,
                        alignment=ui.Alignment.LEFT_CENTER,
                        tooltip="X Value",
                    ).model
                    ui.Spacer(width=19)
                    val_model_y = ui.FloatDrag(
                        name="Field",
                        width=BUTTON_WIDTH - 5,
                        height=LABEL_HEIGHT,
                        enabled=False,
                        alignment=ui.Alignment.LEFT_CENTER,
                        tooltip="Y Value",
                    ).model
                    ui.Spacer(width=19)
                    val_model_z = ui.FloatDrag(
                        name="Field",
                        width=BUTTON_WIDTH - 5,
                        height=LABEL_HEIGHT,
                        enabled=False,
                        alignment=ui.Alignment.LEFT_CENTER,
                        tooltip="Z Value",
                    ).model
                with ui.HStack():
                    for i in range(3):
                        if i != 0:
                            ui.Spacer(width=BUTTON_WIDTH - 1)
                        field_label = field_labels[i]
                        with ui.ZStack(width=RECT_WIDTH + 1):
                            ui.Rectangle(name="vector_label", style={"background_color": field_label[1]})
                            ui.Label(field_label[0], name="vector_label", alignment=ui.Alignment.CENTER)

        add_separator()
        return [plot_0, plot_1, plot_2], [val_model_x, val_model_y, val_model_z]


def add_line_rect_flourish(draw_line=True):
    """Adds a Line + Rectangle after all UI elements in the row."""
    if draw_line:
        ui.Line(style={"color": 0x338A8777}, width=ui.Fraction(1), alignment=ui.Alignment.CENTER)
    ui.Spacer(width=10)
    with ui.Frame(width=0):
        with ui.VStack():
            with ui.Placer(offset_x=0, offset_y=7):
                ui.Rectangle(height=5, width=5, alignment=ui.Alignment.CENTER)
    ui.Spacer(width=5)


def add_separator():
    """Adds a Line Separator."""
    with ui.VStack(spacing=5):
        ui.Spacer()
        with ui.HStack():
            ui.Spacer(width=LABEL_WIDTH)
            ui.Line(style={"color": 0x338A8777}, width=ui.Fraction(1))
            ui.Spacer(width=20)
        ui.Spacer()


def add_folder_picker_icon(on_click_fn):
    def open_folder_picker():
        def on_selected(a, b):
            on_click_fn(b)
            folder_picker.hide()

        def on_canceled(a, b):
            folder_picker.hide()

        folder_picker = FilePickerDialog(
            "Select Output Folder",
            allow_multi_selection=False,
            apply_button_label="Select Folder",
            click_apply_handler=lambda a, b: on_selected(a, b),
            click_cancel_handler=lambda a, b: on_canceled(a, b),
        )

    with ui.Frame(width=0):
        ui.Button(
            name="IconButton",
            width=20,
            height=20,
            clicked_fn=open_folder_picker,
            style=get_style()["IconButton.Image::FolderPicker"],
            alignment=ui.Alignment.RIGHT_TOP,
            tooltip="Select Folder",
        )


def add_folder_picker_btn(on_click_fn):
    def open_folder_picker():
        def on_selected(a, b):
            on_click_fn(b)
            folder_picker.hide()

        def on_canceled(a, b):
            folder_picker.hide()

        folder_picker = FilePickerDialog(
            "Select Output Folder",
            allow_multi_selection=False,
            apply_button_label="Select Folder",
            click_apply_handler=lambda a, b: on_selected(a, b),
            click_cancel_handler=lambda a, b: on_canceled(a, b),
        )

    with ui.Frame(width=0):
        ui.Button("SELECT", width=BUTTON_WIDTH, clicked_fn=open_folder_picker, tooltip="Select Folder")


def format_tt(tt):
    import string

    formated = ""
    i = 0
    for w in tt.split():
        if w.isupper():
            formated += w + " "
        elif len(w) > 3 or i == 0:
            formated += string.capwords(w) + " "
        else:
            formated += w.lower() + " "
        i += 1
    return formated


def setup_ui_headers(
    ext_path,
    file_path,
    title="My Custom Extension",
    doc_link="https://docs.omniverse.nvidia.com/app_isaacsim/app_isaacsim/overview.html",
    overview="",
    author="",
    date="",
    log_filename="extension.log",
):
    """Creates the Standard UI Elements at the top of each Isaac Extension."""
    build_header(ext_path, file_path, title, doc_link)
    build_info_frame(overview, author, date)
    build_settings_frame(log_filename)


def build_header(
    ext_path,
    file_path,
    title="My Custom Extension",
    doc_link="https://docs.omniverse.nvidia.com/app_isaacsim/app_isaacsim/overview.html",
):
    """Title Header with Quick Access Utility Buttons."""

    def on_open_IDE_clicked():
        """Opens the current directory and file in VSCode"""
        if sys.platform == "win32":
            carb.log_warn("windows not supported")
        else:
            try:
                os.system("code " + ext_path + " " + file_path)
            except OSError:
                carb.log_warn(
                    "Could not open in VSCode. See Troubleshooting help here: https://code.visualstudio.com/docs/editor/command-line#_common-questions"
                )

    def on_open_folder_clicked():
        """Opens the current directory in a File Browser"""
        if sys.platform == "win32":
            # subprocess.Popen(['start', os.path.abspath(app_folder)], shell= True)
            carb.log_warn("windows not supported")
        else:
            try:
                subprocess.Popen(["xdg-open", os.path.abspath(file_path.rpartition("/")[0])])
            except OSError:
                carb.log_warn("could not open file browser")

    def on_docs_link_clicked():
        """Opens an extension's documentation in a Web Browser"""
        import webbrowser

        webbrowser.open(doc_link, new=2)

    def build_icon_bar():
        """Adds the Utility Buttons to the Title Header"""
        with ui.Frame(style=get_style(), width=0):
            with ui.VStack():
                with ui.HStack():
                    icon_size = 24
                    ui.Button(
                        name="IconButton",
                        width=icon_size,
                        height=icon_size,
                        clicked_fn=on_open_IDE_clicked,
                        style=get_style()["IconButton.Image::OpenConfig"],
                        # style_type_name_override="IconButton.Image::OpenConfig",
                        alignment=ui.Alignment.LEFT_CENTER,
                        tooltip="Open in IDE",
                    )
                    ui.Button(
                        name="IconButton",
                        width=icon_size,
                        height=icon_size,
                        clicked_fn=on_open_folder_clicked,
                        style=get_style()["IconButton.Image::OpenFolder"],
                        alignment=ui.Alignment.LEFT_CENTER,
                        tooltip="Open Containing Folder",
                    )
                    with ui.Placer(offset_x=0, offset_y=3):
                        ui.Button(
                            name="IconButton",
                            width=icon_size - icon_size * 0.25,
                            height=icon_size - icon_size * 0.25,
                            clicked_fn=on_docs_link_clicked,
                            # style_type_name_override="IconButton.Image::OpenLink",
                            style=get_style()["IconButton.Image::OpenLink"],
                            # image_url="/resources/glyphs/link.svg",
                            # style={"image_url": "resources/glyphs/link.svg"},
                            alignment=ui.Alignment.LEFT_TOP,
                            tooltip="Link to Docs",
                        )

    with ui.ZStack():
        ui.Rectangle(style={"border_radius": 5})
        with ui.HStack():
            ui.Spacer(width=5)
            ui.Label(title, width=0, name="title", style={"font_size": 16})
            ui.Spacer(width=ui.Fraction(1))
            build_icon_bar()
            ui.Spacer(width=5)


def build_info_frame(overview="", author="", date=""):
    """Info Frame with Overview, Instructions, and Metadata for an Extension"""
    frame = ui.CollapsableFrame(
        title="Information",
        height=0,
        collapsed=False,
        horizontal_clipping=False,
        style=get_style(),
        style_type_name_override="CollapsableFrame",
        horizontal_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_AS_NEEDED,
        vertical_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_ALWAYS_ON,
    )
    with frame:
        with ui.VStack(style=get_style(), spacing=5):
            scrolling_frame_builder("Overview", "scrolling_frame", overview)
            # with ui.HStack():
            #     ui.Label("Author", width=LABEL_WIDTH, alignment=ui.Alignment.LEFT_TOP)
            #     ui.Label(
            #         author,
            #         style_type_name_override="Label::label",
            #         alignment=ui.Alignment.LEFT_TOP,
            #         width=ui.Percent(75),
            #     )
            # with ui.HStack():
            #     ui.Label("Last Updated", width=LABEL_WIDTH, alignment=ui.Alignment.LEFT_TOP)
            #     ui.Label(
            #         date, style_type_name_override="Label::label", alignment=ui.Alignment.LEFT_TOP, width=ui.Percent(75)
            #     )


def build_settings_frame(log_filename="extension.log", log_to_file=False, save_settings=False):
    """Settings Frame for Common Utilities Functions"""
    frame = ui.CollapsableFrame(
        title="Settings",
        height=0,
        collapsed=True,
        horizontal_clipping=False,
        style=get_style(),
        style_type_name_override="CollapsableFrame",
    )

    def on_log_to_file_enabled(val):
        # TO DO
        carb.log_info(f"Logging to {model.get_value_as_string()}:", val)

    def on_save_out_settings(val):
        # TO DO
        carb.log_info("Save Out Settings?", val)

    def on_reload_environment():
        # TO DO
        carb.log_info("Reloading the Envirionment")

        """Resets the Stage and Reloads the Project """
        # Wait to create a new scenario until the Stage is done loading
        task = asyncio.ensure_future(omni.usd.get_context().new_stage_async())
        asyncio.ensure_future(setup_project(task))

    async def setup_project(task):
        """Sets up Project-Specific Variables and Parameters"""
        done, pending = await asyncio.wait({task})
        if task in done:
            carb.log_info("Setting Up Project")
            ext_manager = omni.kit.app.get_app().get_extension_manager()
            viewport_ext_enabled = ext_manager.is_extension_enabled("omni.kit.window.viewport")
            if viewport_ext_enabled:
                viewport = omni.kit.viewport.get_default_viewport_window()

                # Setup the Viewport at a CAMERA_PRESET (NEAR, MID, FAR)
                viewport.set_camera_position("/OmniverseKit_Persp", 150, 150, 50, True)
                viewport.set_camera_target("/OmniverseKit_Persp", 0, 0, 0, True)
            else:
                carb.log_warn("skipping viewport camera reset because omni.kit.window.viewport isn't enabled")

    with frame:
        with ui.VStack(style=get_style(), spacing=5):

            # # Log to File Settings
            # default_output_path = os.path.realpath(os.getcwd())
            # kwargs = {
            #     "label": "Log to File",
            #     "type": "checkbox_stringfield",
            #     "default_val": [log_to_file, default_output_path + "/" + log_filename],
            #     "on_clicked_fn": on_log_to_file_enabled,
            #     "tooltip": "Log Out to File",
            #     "use_folder_picker": True,
            # }
            # model = combo_cb_str_builder(**kwargs)[1]

            # Save Settings on Exit
            # kwargs = {
            #     "label": "Save Settings",
            #     "type": "checkbox",
            #     "default_val": save_settings,
            #     "on_clicked_fn": on_save_out_settings,
            #     "tooltip": "Save out GUI Settings on Exit.",
            # }
            # cb_builder(**kwargs)

            # Reload Environment
            kwargs = {
                "label": "Clear Scene",
                "type": "button",
                "text": "CLEAR",
                "on_clicked_fn": on_reload_environment,
                "tooltip": "Clear the Scene",
            }
            btn_builder(**kwargs)


class ListItem(ui.AbstractItem):
    def __init__(self, text):
        super().__init__()
        self.name_model = ui.SimpleStringModel(text)

    def __repr__(self):
        return f'"{self.name_model.as_string}"'

    def name(self):
        return self.name_model.as_string


class ListItemModel(ui.AbstractItemModel):
    """
    Represents the model for lists. It's very easy to initialize it
    with any string list:
        string_list = ["Hello", "World"]
        model = ListModel(*string_list)
        ui.TreeView(model)
    """

    def __init__(self, *args):
        super().__init__()
        self._children = [ListItem(t) for t in args]
        self._filtered = [ListItem(t) for t in args]

    def get_item_children(self, item):
        """Returns all the children when the widget asks it."""
        if item is not None:
            # Since we are doing a flat list, we return the children of root only.
            # If it's not root we return.
            return []

        return self._filtered

    def filter_text(self, text):
        import fnmatch

        self._filtered = []
        if len(text) == 0:
            for c in self._children:
                self._filtered.append(c)
        else:
            parts = text.split()
            for i in range(len(parts) - 1, -1, -1):
                w = parts[i]

            leftover = " ".join(parts)
            if len(leftover) > 0:
                filter_str = f"*{leftover.lower()}*"
                for c in self._children:
                    if fnmatch.fnmatch(c.name().lower(), filter_str):
                        self._filtered.append(c)

        # This tells the Delegate to update the TreeView
        self._item_changed(None)

    def get_item_value_model_count(self, item):
        """The number of columns"""
        return 1

    def get_item_value_model(self, item, column_id):
        """
        Return value model.
        It's the object that tracks the specific value.
        In our case we use ui.SimpleStringModel.
        """
        return item.name_model


class ListItemDelegate(ui.AbstractItemDelegate):
    """
    Delegate is the representation layer. TreeView calls the methods
    of the delegate to create custom widgets for each item.
    """

    def __init__(self, on_double_click_fn=None):
        super().__init__()
        self._on_double_click_fn = on_double_click_fn

    def build_branch(self, model, item, column_id, level, expanded):
        """Create a branch widget that opens or closes subtree"""
        pass

    def build_widget(self, model, item, column_id, level, expanded):
        """Create a widget per column per item"""
        stack = ui.ZStack(height=20, style=get_style())
        with stack:
            with ui.HStack():
                ui.Spacer(width=5)
                value_model = model.get_item_value_model(item, column_id)
                label = ui.Label(value_model.as_string, name="TreeView.Item")

        if not self._on_double_click_fn:
            self._on_double_click_fn = self.on_double_click

        # Set a double click function
        stack.set_mouse_double_clicked_fn(lambda x, y, b, m, l=label: self._on_double_click_fn(b, m, l))

    def on_double_click(self, button, model, label):
        """Called when the user double-clicked the item in TreeView"""
        if button != 0:
            return
        carb.log_info("List Item Double-Clicked: ", label.text)


def build_simple_search(label="", type="search", model=None, delegate=None, tooltip=""):
    """A Simple Search Bar + TreeView Widget.\n
    Pass a list of items through the model, and a custom on_click_fn through the delegate.\n
    Returns the SearchWidget so user can destroy it on_shutdown."""
    with ui.HStack():
        ui.Label(label, width=LABEL_WIDTH, alignment=ui.Alignment.LEFT_TOP, tooltip=format_tt(tooltip))

        with ui.VStack(spacing=5):

            def filter_text(item):
                model.filter_text(item)

            from omni.kit.window.extensions.ext_components import SearchWidget

            search_bar = SearchWidget(filter_text)

            with ui.ScrollingFrame(
                height=LABEL_HEIGHT * 5,
                horizontal_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_ALWAYS_OFF,
                vertical_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_ALWAYS_ON,
                style=get_style(),
                style_type_name_override="TreeView.ScrollingFrame",
            ):
                treeview = ui.TreeView(
                    model,
                    delegate=delegate,
                    root_visible=False,
                    header_visible=False,
                    style={
                        "TreeView.ScrollingFrame": {"background_color": 0xFFE0E0E0},
                        "TreeView.Item": {"color": 0xFF535354, "font_size": 16},
                        "TreeView.Item:selected": {"color": 0xFF23211F},
                        "TreeView:selected": {"background_color": 0x409D905C},
                    }
                    # name="TreeView",
                    # style_type_name_override="TreeView",
                )
        add_line_rect_flourish(False)
    return search_bar, treeview
