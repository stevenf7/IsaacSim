# Copyright (c) 2018-2020, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
"""
A generic GridView Widget for File Systems
"""
from omni import ui
from .view import FileBrowserView
from .model import FileBrowserItem, FileBrowserModel
from .style import UI_STYLES
from .card import FileBrowserItemCard


class FileBrowserGridView(FileBrowserView):
    def __init__(self, model: FileBrowserModel, **kwargs):
        super().__init__(model)
        self._grid_view = None

        try:
            import omni.kit.editor

            theme = omni.kit.editor.get_editor_interface().get_ui_style()
        except:
            theme = None
        finally:
            theme = theme or "NvidiaDark"

        get_attr = lambda key, default: kwargs.get(key) if key in kwargs else default
        self._style = UI_STYLES[theme]
        self._allow_multi_selection = get_attr("allow_multi_selection", True)
        self._selection_changed_fn = get_attr("selection_changed_fn", None)

        kwargs["sort_by_field"] = get_attr("sort_by_field", "name")
        kwargs["sort_ascending"] = self._model.sort_ascending
        self._delegate = FileBrowserGridViewDelegate(theme, **kwargs)

    def build_ui(self):
        self._widget = ui.ZStack(style=self._style)

        with self._widget:
            ui.Rectangle(style_type_name_override="GridView")
            with ui.VStack():
                self._grid_view = ui.ScrollingFrame(
                    horizontal_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_ALWAYS_OFF,
                    vertical_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_ALWAYS_ON,
                    style_type_name_override="GridView.ScrollingFrame",
                )

    @property
    def view(self):
        return self._grid_view

    def scale_view(self, scale: float):
        if self._delegate:
            self._delegate.scale = scale

    def refresh_ui(self, _=None):
        if not self._visible or not self._delegate:
            return
        with self._grid_view:
            self._delegate.build_grid(self._model)

    def select_and_center(self, item: FileBrowserItem):
        if not self._visible:
            return

        item = item or self._model.root
        if not item:
            return

        def set_expanded_recursive(item: FileBrowserItem):
            if not item:
                return
            set_expanded_recursive(item.parent)
            self._grid_view.set_expanded(item, True, False)

        set_expanded_recursive(item)
        self._grid_view.selection = [item]

    def _on_selection_changed(self, selections: [FileBrowserItem]):
        if not self._allow_multi_selection:
            if selections:
                selections = selections[-1:]
                self._grid_view.selection = selections
        if self._selection_changed_fn:
            self._selection_changed_fn(selections)


class FileBrowserGridViewDelegate:
    def __init__(self, theme: str, **kwargs):
        get_attr = lambda key, default: kwargs.get(key) if key in kwargs else default
        self._style = UI_STYLES[theme]
        self._num_columns = get_attr("num_collumns", 6)
        self._hide_files = not get_attr("files_visible", True)
        self._tooltip = get_attr("tooltip", False)
        self._mouse_pressed_fn = get_attr("mouse_pressed_fn", None)
        self._mouse_double_clicked_fn = get_attr("mouse_double_clicked_fn", None)
        self._column_clicked_fn = get_attr("column_clicked_fn", None)
        self._sort_by_field = get_attr("sort_by_field", "name")
        self._sort_ascending = get_attr("sort_ascending", True)
        self._card_width = 120
        self._card_height = 120
        self._scale = 1

    """
    @property
    def sort_by_field(self) -> int:
        return self._sort_by_column

    @sort_by_column.setter
    def sort_by_column(self, column_id: int):
        self._sort_by_column = column_id
    """

    @property
    def sort_ascending(self) -> bool:
        return self._sort_ascending

    @sort_ascending.setter
    def sort_ascending(self, value: bool):
        self._sort_ascending = value

    @property
    def scale(self):
        return self._scale

    @scale.setter
    def scale(self, scale: float):
        self._scale = scale

    def build_grid(self, model: FileBrowserModel):
        if model:
            children = model.get_item_children(None)
        else:
            return

        with ui.VGrid(column_width=self._scale * self._card_width, row_height=self._scale * self._card_height + 10):
            # Display folders before files
            for item, is_folder in [(c, f) for f in [True, False] for c in children]:
                if item.is_folder == is_folder:
                    ui.Frame(build_fn=lambda m=model, i=item: self.build_widget(m, i))

    def build_widget(self, model: FileBrowserModel, item: FileBrowserItem):
        """Create a widget per item"""
        if not item:
            return

        card = FileBrowserItemCard(
            item,
            width=self._scale * self._card_width,
            height=self._scale * self._card_height,
            mouse_pressed_fn=self._mouse_pressed_fn,
            mouse_double_clicked_fn=self._mouse_double_clicked_fn,
        )
