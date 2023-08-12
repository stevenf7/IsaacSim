import omni.ui as ui
from omni.isaac.ui.style import COLOR_W, COLOR_X, COLOR_Y, COLOR_Z
from omni.isaac.ui.ui_utils import add_line_rect_flourish
from omni.kit.window.property.templates import LABEL_WIDTH

RECT_WIDTH = 13  # This is the width of the label on the left side of the field.
SPACING = 8  # This is the spacing between each field + label combination.
FIELD_WIDTH = 50  # This is the width of the actual number field associated with each label.
LABEL_PADDING = 100


def customized_dropdown_builder(
    label="",
    default_val=0,
    items=[],
    tooltip="",
    on_clicked_fn=None,
    add_line=False,
    width=ui.Fraction(100),
    label_width=LABEL_WIDTH,
):
    """Creates a Stylized Dropdown Combobox

    Args:
        label (str, optional): Label to the left of the UI element. Defaults to "".
        type (str, optional): Type of UI element. Defaults to "dropdown".
        default_val (int, optional): Default index of dropdown items. Defaults to 0.
        items (list, optional): List of items for dropdown box. Defaults to ["Option 1", "Option 2", "Option 3"].
        tooltip (str, optional): Tooltip to display over the Label. Defaults to "".
        on_clicked_fn (Callable, optional): Call-back function when clicked. Defaults to None.

    Returns:
        AbstractItemModel: model
    """
    with ui.HStack():
        ui.Label(label, width=label_width, alignment=ui.Alignment.LEFT_CENTER, tooltip=tooltip)
        combo_box = ui.ComboBox(
            default_val, *items, name="ComboBox", width=width, alignment=ui.Alignment.LEFT_CENTER
        ).model
        add_line_rect_flourish(add_line)

        def on_clicked_wrapper(model, val):
            on_clicked_fn(model.get_item_value_model().as_int)

        if on_clicked_fn is not None:
            combo_box.add_item_changed_fn(on_clicked_wrapper)

    return combo_box


def custom_pos_quat_builder(label_width=LABEL_WIDTH, enable_scroll=False, label="World"):
    models = []
    colors = {"X": COLOR_X, "Y": COLOR_Y, "Z": COLOR_Z, "W": COLOR_W}

    def _build_model(label, all_axis):
        with ui.HStack():
            with ui.HStack(width=label_width + 40):
                ui.Label(label, name="transform", width=50)
                ui.Spacer()

            for axis in all_axis:
                with ui.HStack():
                    with ui.ZStack(width=15):
                        ui.Rectangle(
                            width=15,
                            height=20,
                            style={
                                "background_color": colors[axis],
                                "border_radius": 3,
                                "corner_flag": ui.CornerFlag.LEFT,
                            },
                        )
                        ui.Label(
                            axis, name="transform_label", alignment=ui.Alignment.CENTER, style={"color": 0xFFFFFFFF}
                        )
                    model = ui.FloatDrag(name="transform", enabled=enable_scroll).model

                    models.append(model)
                    ui.Spacer(width=4)

    _build_model(f"{label} Position", all_axis=["X", "Y", "Z"])
    _build_model(f"{label} Orientation", all_axis=["W", "X", "Y", "Z"])

    return models
