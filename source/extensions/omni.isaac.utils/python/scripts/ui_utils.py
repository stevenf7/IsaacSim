from string import hexdigits
import carb.settings
import omni.ui as ui
import omni.ext
import omni.appwindow
import asyncio
from omni.kit.window.extensions.common import *
from omni.kit.window.property.templates import SimplePropertyWidget, LABEL_WIDTH, LABEL_HEIGHT

from .style import *

from omni.kit.window.extensions import SimpleCheckBox, styles


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
        add_line_rect_flourish()
    return btn


def cb_builder(label="", type="checkbox", default_val=False, tooltip="", on_clicked_fn=None):
    """Creates a Stylized Checkbox"""

    with ui.HStack():
        ui.Label(label, width=LABEL_WIDTH - 12, alignment=ui.Alignment.LEFT_CENTER, tooltip=format_tt(tooltip))
        cb = SimpleCheckBox(default_val, on_clicked_fn)

        add_line_rect_flourish()
        return cb


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


def combo_cb_str_builder(
    label="", type="checkbox_stringfield", default_val=[False, " "], tooltip="", on_clicked_fn=None
):
    """Creates a Stylized Checkbox + Stringfield Widget"""
    with ui.HStack():
        ui.Label(label, width=LABEL_WIDTH - 12, alignment=ui.Alignment.LEFT_CENTER, tooltip=format_tt(tooltip))
        cb = SimpleCheckBox(default_val[0], on_clicked_fn)
        str_field = ui.StringField(
            name="StringField", width=ui.Fraction(1), height=0, alignment=ui.Alignment.LEFT_CENTER
        ).model
        str_field.set_value(default_val[1])

        add_line_rect_flourish(False)
        return [cb, str_field]


def dropdown_builder(
    label="", type="dropdown", default_val=0, items=["Option 1", "Option 2", "Option 3"], tooltip="", on_clicked_fn=None
):
    """Creates a Stylized Dropdown Combobox"""
    with ui.HStack():
        ui.Label(label, width=LABEL_WIDTH, alignment=ui.Alignment.LEFT_CENTER, tooltip=format_tt(tooltip))
        combo_box = ui.ComboBox(
            default_val, *items, name="ComboBox", width=ui.Fraction(1), alignment=ui.Alignment.LEFT_CENTER
        )
        add_line_rect_flourish(False)

        def on_clicked_wrapper(model, val):
            on_clicked_fn(items[model.get_item_value_model().as_int])

        combo_box.model.add_item_changed_fn(on_clicked_wrapper)

    return combo_box


def combo_floatfield_slider_builder(
    label="", type="floatfield_stringfield", default_val=0.5, min=0, max=1, step=0.01, tooltip=["", ""]
):
    """Creates a Stylized FloatField + Stringfield Widget"""
    with ui.HStack():
        ui.Label(label, width=LABEL_WIDTH, alignment=ui.Alignment.LEFT_CENTER, tooltip=format_tt(tooltip[0]))
        ff = ui.FloatField(
            name="Field", width=BUTTON_WIDTH / 2, alignment=ui.Alignment.LEFT_CENTER, tooltip=format_tt(tooltip[1])
        )
        ff.model.set_value(default_val)
        ui.Spacer(width=5)
        fs = ui.FloatSlider(
            width=ui.Fraction(1), alignment=ui.Alignment.LEFT_CENTER, min=min, max=max, step=step, model=ff.model
        )

        add_line_rect_flourish(False)
        return [ff, fs]


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

        return [cb, combo_box]


def scrolling_frame_builder(label="", type="scrolling_frame", default_val="No Data", tooltip=""):
    """Creates a Labeled Scrolling Frame with CopyToClipboard button"""

    def copy_to_clipboard():
        try:
            import pyperclip

            pyperclip.copy(info_label.text)
        except ImportError:
            carb.log_warn("Could not import pyperclip.")

    with ui.VStack(style=get_style(), spacing=5):
        with ui.HStack():
            ui.Label(label, width=LABEL_WIDTH, alignment=ui.Alignment.LEFT_TOP, tooltip=format_tt(tooltip))
            with ui.ScrollingFrame(
                height=18 * 5,
                style_type_name_override="ScrollingFrame",
                alignment=ui.Alignment.LEFT_TOP,
                horizontal_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_AS_NEEDED,
                vertical_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_ALWAYS_ON,
            ):
                info_label = ui.Label(
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
    return info_label


def combo_cb_scrolling_frame_builder(
    label="", type="scrolling_frame", default_val=[False, "No Data"], tooltip="", on_clicked_fn=None
):
    """Creates a Labeled, Checkbox-enabled Scrolling Frame with CopyToClipboard button"""

    def copy_to_clipboard():
        try:
            import pyperclip

            pyperclip.copy(info_label.text)
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
                info_label = ui.Label(
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
    return [cb, info_label]


def add_line_rect_flourish(draw_line=True):
    """Adds a Line + Rectangle after all UI elements in the row."""
    if draw_line:
        ui.Line(style={"color": 0x338A8777}, width=ui.Fraction(1))
    ui.Spacer(width=10)
    with ui.Frame(width=0):
        with ui.VStack():
            with ui.Placer(offset_x=0, offset_y=7):
                ui.Rectangle(height=5, width=5, alignment=ui.Alignment.CENTER)
    ui.Spacer(width=5)


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


def build_header(
    title="My Custom Extension",
    doc_link="https://docs.omniverse.nvidia.com/app_isaacsim/app_isaacsim/overview.html",
    project_path="",
):
    def on_open_IDE_clicked():
        # TO DO
        print("Open IDE Clicked. Project Path: ", project_path)

    def on_open_folder_clicked():
        # TO DO
        print("Open Containing Folder Clicked. Project Path: ", project_path)

    def on_docs_link_clicked():
        import webbrowser

        webbrowser.open(doc_link, new=2)

    def build_icon_bar():
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
    def copy_to_clipboard():
        try:
            import pyperclip

            pyperclip.copy(overview)
        except ImportError:
            carb.log_warn("Could not import pyperclip.")

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
            # ui.Label("Overview", width=LABEL_WIDTH, useclipboard=True, alignment=ui.Alignment.LEFT_TOP)
            # with ui.ScrollingFrame(height=50, style_type_name_override="ScrollingFrame",
            #                     horizontal_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_AS_NEEDED,
            #                     vertical_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_ALWAYS_ON):
            #     ui.Label(overview, style_type_name_override="Label::label", word_wrap=True, alignment=ui.Alignment.LEFT_TOP)

            # ui.Button(name="IconButton",
            #         width=20,
            #         height=20,
            #         clicked_fn=copy_to_clipboard,
            #         style=get_style()["IconButton.Image::CopyToClipboard"],
            #         alignment=ui.Alignment.RIGHT_TOP,
            #         tooltip="Copy To Clipboard",
            #         )

            with ui.HStack():
                ui.Label("Author", width=LABEL_WIDTH, alignment=ui.Alignment.LEFT_TOP)
                ui.Label(
                    author,
                    style_type_name_override="Label::label",
                    alignment=ui.Alignment.LEFT_TOP,
                    width=ui.Percent(75),
                )
            with ui.HStack():
                ui.Label("Last Updated", width=LABEL_WIDTH, alignment=ui.Alignment.LEFT_TOP)
                ui.Label(
                    date, style_type_name_override="Label::label", alignment=ui.Alignment.LEFT_TOP, width=ui.Percent(75)
                )


def build_settings_frame(log_filename="extension.log", log_to_file=False, save_settings=False):
    frame = ui.CollapsableFrame(
        title="Settings",
        height=0,
        collapsed=False,
        horizontal_clipping=False,
        style=get_style(),
        style_type_name_override="CollapsableFrame",
    )

    def on_log_to_file_enabled(val):
        # TO DO
        print(f"Logging to {model.get_value_as_string()}:", val)

    def on_save_out_settings(val):
        # TO DO
        print("Save Out Settings?", val)

    def on_reload_environment():
        # TO DO
        print("Reloading the Envirionment")

        """Resets the Stage and Reloads the Project """
        # Wait to create a new scenario until the Stage is done loading
        task = asyncio.ensure_future(omni.usd.get_context().new_stage_async())
        asyncio.ensure_future(setup_project(task))

    async def setup_project(task):
        """Sets up Project-Specific Variables and Parameters"""
        done, pending = await asyncio.wait({task})
        if task in done:
            carb.log_info("Setting Up Project")
            viewport = omni.kit.viewport.get_default_viewport_window()

            # Setup the Viewport at a CAMERA_PRESET (NEAR, MID, FAR)
            viewport.set_camera_position("/OmniverseKit_Persp", 150, 150, 50, True)
            viewport.set_camera_target("/OmniverseKit_Persp", 0, 0, 0, True)

            # Set an Asset Path
            result, nucleus_server = find_nucleus_server()
            if result is False:
                carb.log_error("Could not find nucleus server with /Isaac folder")
                return

    with frame:
        with ui.VStack(style=get_style(), spacing=5):

            # Log to File Settings
            default_output_path = os.path.realpath(os.getcwd())
            dict = {
                "label": "Log to File",
                "type": "checkbox_stringfield",
                "default_val": [log_to_file, default_output_path + "/" + log_filename],
                "on_clicked_fn": on_log_to_file_enabled,
                "tooltip": "Log Out to File",
            }
            model = combo_cb_str_builder(**dict)[1]

            # Save Settings on Exit
            dict = {
                "label": "Save Settings",
                "type": "checkbox",
                "default_val": save_settings,
                "on_clicked_fn": on_save_out_settings,
                "tooltip": "Save out GUI Settings on Exit.",
            }
            cb_builder(**dict)

            # Reload Environment
            dict = {
                "label": "Reload Scene",
                "type": "button",
                "text": "LOAD",
                "on_clicked_fn": on_reload_environment,
                "tooltip": "Reload the Scene",
            }
            btn_builder(**dict)
