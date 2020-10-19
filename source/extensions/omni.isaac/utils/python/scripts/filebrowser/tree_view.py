# Copyright (c) 2018-2020, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
"""
A generic Tree View Widget for File Systems
"""
from omni import ui
from typing import Tuple
from .view import FileBrowserView
from .model import FileBrowserItem, FileBrowserItemFields, FileBrowserModel
from .style import UI_STYLES


class FileBrowserTreeView(FileBrowserView):
    def __init__(self, model: FileBrowserModel, **kwargs):
        super().__init__(model)
        self._widget = None
        self._tree_view = None
        self._headers = FileBrowserItemFields._fields

        try:
            import omni.kit.editor

            theme = omni.kit.editor.get_editor_interface().get_ui_style()
        except:
            theme = None
        finally:
            theme = theme or "NvidiaDark"

        self._style = UI_STYLES[theme]
        self._root_visible = kwargs.get("root_visible", True)
        self._header_visible = kwargs.get("header_visible", True)
        self._allow_multi_selection = kwargs.get("allow_multi_selection", True)
        self._selection_changed_fn = kwargs.get("selection_changed_fn", None)
        self._mouse_double_clicked_fn = kwargs.get("mouse_double_clicked_fn", None)

        kwargs["column_clicked_fn"] = lambda column_id: self._on_column_clicked(column_id)
        kwargs["sort_by_column"] = self._headers.index(self._model.sort_by_field)
        kwargs["sort_ascending"] = self._model.sort_ascending
        self._delegate = FileBrowserTreeViewDelegate(self._headers, theme, **kwargs)
        self._build_ui()

    def _build_ui(self):
        self._widget = ui.ZStack(style=self._style)
        column_widths = [ui.Fraction(1), 150, 100]

        with self._widget:
            ui.Rectangle(style_type_name_override="TreeView")
            with ui.HStack():
                # Tree View
                with ui.ScrollingFrame(
                    horizontal_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_ALWAYS_OFF,
                    vertical_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_AS_NEEDED,
                    style_type_name_override="TreeView.ScrollingFrame",
                ):
                    selection_changed_fn = lambda selections: self._on_selection_changed(selections)

                    self._tree_view = ui.TreeView(
                        self._model,
                        delegate=self._delegate,
                        column_widths=column_widths,
                        root_visible=self._root_visible,
                        header_visible=self._header_visible,
                        selection_changed_fn=selection_changed_fn,
                    )

    @property
    def tree_view(self):
        return self._tree_view

    def refresh_ui(self, item: FileBrowserItem = None):
        self.set_expanded(self._model._root, False, True)
        if not self._visible:
            return
        if self._model:
            # NOTE: The following action is not publicized but is required for a proper redraw
            self._model._item_changed(item)
        if self._tree_view:
            self._tree_view.dirty_widgets()

    def is_expanded(self, item: FileBrowserItem) -> bool:
        if self._tree_view and item:
            return self._tree_view.is_expanded(item)
        return False

    def set_expanded(self, item: FileBrowserItem, expanded: bool, recursive: bool = False):
        """
        Sets the expansion state of the given item.

        Args:
            item (:obj:`FileBrowserItem`): The item to effect.
            expanded (bool): True to expand, False to collapse.
            recursive (bool): Apply state recursively to descendent nodes. Default False.

        """
        if self._tree_view and item:
            self._tree_view.set_expanded(item, expanded, recursive)

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
            self.set_expanded(item, True)

        set_expanded_recursive(item)
        self._tree_view.selection = [item]

    def _on_selection_changed(self, selections: [FileBrowserItem]):
        if not self._allow_multi_selection:
            if selections:
                selections = selections[-1:]
                self._tree_view.selection = selections
        if self._selection_changed_fn:
            self._selection_changed_fn(selections)

    def _on_column_clicked(self, column_id: int):
        column_id = min(column_id, len(FileBrowserItemFields._fields) - 1)
        if column_id == self._delegate.sort_by_column:
            self._delegate.sort_ascending = not self._delegate.sort_ascending
        else:
            self._delegate.sort_by_column = column_id
        if self._model:
            self._model.sort_by_field = self._headers[column_id]
            self._model.sort_ascending = self._delegate.sort_ascending
        self.refresh_ui()

    def destroy(self):
        self._model = None
        self._tree_view = None
        self._widget = None


class FileBrowserTreeViewDelegate(ui.AbstractItemDelegate):
    def __init__(self, headers: Tuple, theme: str, **kwargs):
        super().__init__()
        self._headers = headers
        self._style = UI_STYLES[theme]
        self._hide_files = not kwargs.get("files_visible", True)
        self._tooltip = kwargs.get("tooltip", False)
        self._mouse_pressed_fn = kwargs.get("mouse_pressed_fn", None)
        self._mouse_double_clicked_fn = kwargs.get("mouse_double_clicked_fn", None)
        self._column_clicked_fn = kwargs.get("column_clicked_fn", None)
        self._sort_by_column = kwargs.get("sort_by_column", 0)
        self._sort_ascending = kwargs.get("sort_ascending", True)

    @property
    def sort_by_column(self) -> int:
        return self._sort_by_column

    @sort_by_column.setter
    def sort_by_column(self, column_id: int):
        self._sort_by_column = column_id

    @property
    def sort_ascending(self) -> bool:
        return self._sort_ascending

    @sort_ascending.setter
    def sort_ascending(self, value: bool):
        self._sort_ascending = value

    def build_header(self, column_id: int):
        def on_column_clicked(column_id):
            if self._column_clicked_fn:
                self._column_clicked_fn(column_id)

        icon = None
        if column_id == self._sort_by_column:
            if self._sort_ascending:
                icon = "resources/glyphs/arrow_up.svg"
            else:
                icon = "resources/glyphs/arrow_down.svg"

        with ui.ZStack(style=self._style):
            with ui.HStack():
                ui.Spacer(width=4)
                ui.Label(self._headers[column_id].capitalize(), height=20, style_type_name_override="TreeView.Header")
            # Invisible click area fills entire header frame
            button = ui.Button(" ", height=20, style_type_name_override="TreeView.Column")
            if icon:
                with ui.HStack():
                    ui.Spacer()
                    ui.Image(icon, width=30, style_type_name_override="TreeView.Column")

            button.set_clicked_fn(lambda: on_column_clicked(column_id))

    def refresh_item(self, item, model):
        item.populated = False
        try:
            item.populate()
        except:
            item.populated = True
        item.expanded = True
        model._item_changed(item)

    def build_branch(self, model: FileBrowserModel, item: FileBrowserItem, column_id: int, level: int, expanded: bool):
        """Create a branch widget that opens or closes subtree"""
        if column_id == 0:
            with ui.HStack(width=16 * (level + 1), height=0):
                ui.Spacer()
                if item is None or item.is_folder:
                    # Draw the +/- icon
                    if expanded:
                        icon = "resources/glyphs/menu_minus.svg"
                    else:
                        icon = "resources/glyphs/menu_plus.svg"
                    ui.Image(icon, name="expand", width=9, height=9, style_type_name_override="TreeView.Icon")
                    ui.Spacer(width=4)

    def build_widget(self, model: FileBrowserModel, item: FileBrowserItem, column_id: int, level: int, expanded: bool):
        """Create a widget per item"""
        item_or_root = item or model.root
        if not item_or_root:
            return

        if self._hide_files and not item_or_root.is_folder:
            # Don't show file items
            return

        def get_item_icon(item: FileBrowserItem, expanded: bool) -> str:
            icon = item.icon
            if not icon:
                if item and not item.is_folder:
                    icon = "resources/glyphs/file.svg"
                else:
                    if expanded:
                        if not item.expanded:
                            self.refresh_item(item, model)
                        icon = "resources/glyphs/folder_open.svg"
                    else:
                        item.expanded = False
                        icon = "resources/glyphs/folder.svg"
            return icon

        value_model = model.get_item_value_model(item_or_root, column_id)
        if not value_model:
            return

        # File Name Column
        if column_id == 0:
            with ui.HStack(spacing=4, height=20):
                ui.Spacer(width=4)
                # create the icon
                ui.Image(
                    get_item_icon(item_or_root, expanded), width=18, height=18, style_type_name_override="TreeView.Icon"
                )
                ui.Spacer(width=1)

                mouse_pressed_fn = None
                if self._mouse_pressed_fn:
                    mouse_pressed_fn = lambda x, y, b, _: self._mouse_pressed_fn(b, item_or_root)

                mouse_double_clicked_fn = None
                if self._mouse_double_clicked_fn:
                    mouse_double_clicked_fn = lambda x, y, b, _: self._mouse_double_clicked_fn(b, item_or_root)

                ui.Label(
                    value_model.get_value_as_string(),
                    tooltip=item_or_root.path if self._tooltip else "",
                    tooltip_offset=22,
                    style_type_name_override="TreeView.Item",
                    mouse_pressed_fn=mouse_pressed_fn,
                    mouse_double_clicked_fn=mouse_double_clicked_fn,
                )

        # Date Column
        elif column_id == 1:
            with ui.HStack():
                ui.Spacer(width=4)
                ui.Label(value_model.get_value_as_string(), style_type_name_override="TreeView.Item")

        # Size Column
        elif column_id == 2:
            if not item_or_root.is_folder:
                with ui.HStack():
                    ui.Spacer(width=4)
                    ui.Label(value_model.get_value_as_string(), style_type_name_override="TreeView.Item")
                    ui.Spacer()
