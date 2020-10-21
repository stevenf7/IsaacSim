# Copyright (c) 2018-2020, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
import omni.ui as ui
from carb import log_error

from . import LAYOUT_SINGLE_PANE_SLIM, LAYOUT_SINGLE_PANE_WIDE, LAYOUT_SPLIT_PANES, LAYOUT_DEFAULT
from .model import FileBrowserModel, FileBrowserItem, FileBrowserItemFactory
from .tree_view import FileBrowserTreeView
from .grid_view import FileBrowserGridView
from .style import UI_STYLES


class FileBrowserWidget:
    """
    The basic UI widget for navigating a filesystem as a tree view. The filesystem can either be from
    your local machine or the Omniverse server.

    Args:
        title (str): Widget title. Default None.

    Keyword Args:
        layout (int): The overall layout of the window, one of: {LAYOUT_SPLIT_PANES, LAYOUT_SINGLE_PANE_SLIM,
            LAYOUT_SINGLE_PANE_WIDE, LAYOUT_DEFAULT}. Default LAYOUT_SPLIT_PANES.
        tooltip (bool): Display tooltips when hovering over items. Default False.
        allow_multi_selection (bool): Allow multiple items to be selected at once. Default True.
        mouse_pressed_fn (func): Function called on mouse press. Function signature:
            void mouse_pressed_fn(button: ui.Button, item: :obj:`FileBrowserItem`)
        mouse_double_clicked_fn (func): Function called on mouse double click. Function signature:
            void mouse_double_clicked_fn(button: ui.Button, item: :obj:`FileBrowserItem`)
        selection_changed_fn (func): Function called when selection changed. Function signature:
            void selection_changed_fn(selections: list[:obj:`FileBrowserItem`])
        drop_fn (func): Function called to handle drag-n-drops. Function signature:
            void drop_fn(dst_item: :obj:`FileBrowserItem`, src_item: :obj:`FileBrowserItem`)
        filter_fn (func): This user function should return True if the given tree view item is
            visible, False otherwise. Function signature: bool filter_fn(item: :obj:`FileBrowserItem`)
        show_grid_view (bool): If True, initializes the folder view to display icons. Default False. 

    """

    def __init__(self, title: str, **kwargs):
        self._widget = None
        self._tree_view = None
        self._grid_view = None
        self._table_view = None
        self._layout_button = None

        try:
            import omni.kit.editor

            theme = omni.kit.editor.get_editor_interface().get_ui_style()
        except:
            theme = None
        finally:
            theme = theme or "NvidiaDark"

        # Create model to group other models
        self._drop_fn = kwargs.get("drop_fn", None)
        self._filter_fn = kwargs.get("filter_fn", None)
        self._models = FileBrowserModel(name=title, drop_fn=self._drop_fn, filter_fn=self._filter_fn)
        self._models.root.icon = "resources/glyphs/cloud.svg"

        self._style = UI_STYLES[theme]
        self._layout = kwargs.get("layout", LAYOUT_DEFAULT)
        self._tooltip = kwargs.get("tooltip", False)
        self._tree_root_visible = kwargs.get("tree_root_visible", True)
        self._allow_multi_selection = kwargs.get("allow_multi_selection", True)
        self._mouse_pressed_fn = kwargs.get("mouse_pressed_fn", None)
        self._mouse_double_clicked_fn = kwargs.get("mouse_double_clicked_fn", None)
        self._selection_changed_fn = kwargs.get("selection_changed_fn", None)
        self._show_grid_view = kwargs.get("show_grid_view", False)
        self._build_ui()

    def _build_ui(self):
        if self._layout in [LAYOUT_SPLIT_PANES, LAYOUT_DEFAULT]:
            self._tree_view = self._build_split_panes_view()
        else:
            slim_view = self._layout == LAYOUT_SINGLE_PANE_SLIM
            self._tree_view = self._build_tree_view(
                self._models, slim_view=slim_view, selection_changed_fn=self._selection_changed_fn
            )

    def _build_split_panes_view(self) -> FileBrowserTreeView:
        with ui.HStack(style=self._style):
            with ui.ZStack(width=0):
                # Create navigation view as side pane
                self._models.set_visible_columns(1)

                with ui.HStack():
                    tree_view = self._build_tree_view(
                        self._models,
                        header_visible=False,
                        files_visible=False,
                        slim_view=True,
                        selection_changed_fn=lambda selected: self._on_tree_view_selection_changed(selected),
                    )
                    ui.Spacer(width=7)

                with ui.Placer(offset_x=400, draggable=True, drag_axis=ui.Axis.X):
                    ui.Rectangle(width=8, name="Splitter")

            details_model = FileBrowserModel(drop_fn=self._drop_fn, filter_fn=self._filter_fn)
            with ui.ZStack():
                self._grid_view = self._build_grid_view(details_model)
                self._table_view = self._build_table_view(details_model)
                with ui.VStack():
                    ui.Spacer()
                    with ui.ZStack(height=0, content_clipping=True):
                        self._build_zoom_bar(self._show_grid_view)
                    ui.Spacer(height=4)

            if self._show_grid_view:
                self._grid_view.visible = True
                self._table_view.visible = False
            else:
                self._grid_view.visible = False
                self._table_view.visible = True

        return tree_view

    def _build_tree_view(
        self,
        model: FileBrowserModel,
        header_visible: bool = True,
        files_visible: bool = True,
        slim_view: bool = True,
        selection_changed_fn: () = None,
    ) -> FileBrowserTreeView:

        if slim_view:
            model.set_visible_columns(1)

        with ui.ZStack(style=self._style):
            ui.Rectangle(style_type_name_override="TreeView")
            with ui.HStack():
                view = FileBrowserTreeView(
                    model,
                    header_visible=header_visible,
                    files_visible=files_visible,
                    tooltip=self._tooltip,
                    root_visible=self._tree_root_visible,
                    allow_multi_selection=self._allow_multi_selection,
                    mouse_pressed_fn=self._mouse_pressed_fn,
                    mouse_double_clicked_fn=lambda b, item: self._on_tree_view_double_clicked(b, item),
                    selection_changed_fn=selection_changed_fn,
                )
                view.build_ui()
        return view

    def _build_table_view(self, model: FileBrowserModel) -> FileBrowserTreeView:
        with ui.ZStack(style=self._style):
            ui.Rectangle(style_type_name_override="TreeView")
            with ui.HStack():
                # Create detail view as table view
                view = FileBrowserTreeView(
                    model,
                    root_visible=False,
                    tooltip=self._tooltip,
                    allow_multi_selection=self._allow_multi_selection,
                    mouse_pressed_fn=self._mouse_pressed_fn,
                    mouse_double_clicked_fn=lambda b, item: self._on_folder_view_double_clicked(b, item),
                    selection_changed_fn=self._selection_changed_fn,
                )
                view.build_ui()
        return view

    def _build_grid_view(self, model: FileBrowserModel) -> FileBrowserGridView:
        with ui.ZStack(style=self._style):
            ui.Rectangle(style_type_name_override="GridView")
            with ui.HStack():
                # Create detail view as table view
                view = FileBrowserGridView(
                    model,
                    root_visible=False,
                    tooltip=self._tooltip,
                    allow_multi_selection=self._allow_multi_selection,
                    mouse_pressed_fn=self._mouse_pressed_fn,
                    mouse_double_clicked_fn=lambda b, item: self._on_folder_view_double_clicked(b, item),
                    selection_changed_fn=self._selection_changed_fn,
                )
                view.build_ui()
        return view

    def _build_zoom_bar(self, grid_view: bool = False):
        def on_slider_value_changed(model: ui.AbstractValueModel):
            scale_map = {0: 0.25, 1: 0.5, 2: 0.75, 3: 1, 4: 1.5, 5: 2.0}
            self.scale_grid_view(scale_map.get(model.get_value_as_int(), 2))

        with ui.HStack(style=self._style):
            ui.Spacer()
            with ui.ZStack(width=0, style=self._style):
                ui.Rectangle(height=20, style_type_name_override="ZoomBar")
                with ui.HStack():
                    ui.Spacer(width=6)
                    slider = ui.IntSlider(min=0, max=5, width=150, style=self._style["ZoomBar.Slider"])
                    slider.model.set_value(2)
                    slider.model.add_value_changed_fn(lambda m: on_slider_value_changed(m))
                    self._layout_button = ui.Button(
                        image_url=self._get_layout_icon(self._show_grid_view),
                        width=16,
                        style_type_name_override="ZoomBar.Button",
                        clicked_fn=lambda: self.toggle_grid_view(not self._show_grid_view),
                    )
                    ui.Spacer(width=6)
            ui.Spacer(width=16)

    def _get_layout_icon(self, grid_view: bool) -> str:
        if grid_view:
            return "resources/glyphs/list.svg"
        else:
            return "resources/glyphs/thumbnail.svg"

    def _on_tree_view_selection_changed(self, selected: [FileBrowserItem]):
        if self._selection_changed_fn:
            self._selection_changed_fn(selected)
        if selected:
            if self._grid_view:
                self._grid_view.set_root(selected[-1])
            if self._table_view:
                self._table_view.set_root(selected[-1])
            self.refresh_ui()

    def _on_tree_view_double_clicked(self, button: ui.Button, item: FileBrowserItem):
        if self._mouse_double_clicked_fn:
            self._mouse_double_clicked_fn(button, item)
        if self._tree_view and item and item.is_folder:
            self._tree_view.set_expanded(item, not self._tree_view.is_expanded(item))
            if self._tree_view.is_expanded(item):
                if self._grid_view:
                    self._grid_view.set_root(item)
                if self._table_view:
                    self._table_view.set_root(item)

    def _on_folder_view_double_clicked(self, button: ui.Button, item: FileBrowserItem):
        if self._mouse_double_clicked_fn:
            self._mouse_double_clicked_fn(button, item)
        if item and item.is_folder:
            self._tree_view.select_and_center(item)
            if self._grid_view:
                self._grid_view.set_root(item)
            if self._table_view:
                self._table_view.set_root(item)

    def toggle_grid_view(self, show_grid_view: bool):
        if not (self._grid_view and self._table_view):
            return
        if show_grid_view:
            self._grid_view.visible = True
            self._table_view.visible = False
        else:
            self._grid_view.visible = False
            self._table_view.visible = True

        self._layout_button.image_url = self._get_layout_icon(show_grid_view)
        self._show_grid_view = show_grid_view
        self.refresh_ui()

    def scale_grid_view(self, scale: float = 1):
        if not self._grid_view:
            return
        if scale < 0.5:
            self.toggle_grid_view(False)
        else:
            self._grid_view.scale_view(scale)
            if not self._show_grid_view:
                self.toggle_grid_view(True)
            else:
                self.refresh_ui()

    def create_grouping_item(self, name: str, path: str, parent: FileBrowserItem = None) -> FileBrowserItem:
        item = FileBrowserItemFactory.create_group_item(name, path)
        if item:
            parent = parent or self._models.root
            parent.add_child(item)
            self.refresh_ui()
        return item

    def add_model_as_subtree(self, model: FileBrowserModel, parent: FileBrowserItem = None):
        if model:
            parent = parent or self._models.root
            parent.add_child(model.root)
            self.refresh_ui()

    def delete_child_by_name(self, item_name: str, parent: FileBrowserItem = None):
        if item_name:
            parent = parent or self._models.root
            parent.del_child(item_name)
            self.refresh_ui()

    def delete_child(self, item: FileBrowserItem, parent: FileBrowserItem = None):
        if item in self._models.get_item_children(parent):
            self.delete_child_by_name(item.name, parent)

    def link_views(self, src_widget: object):
        """
        Links this widget to the given widget, i.e. the 2 widgets will therafter display the same
        models but not necessarily share the same view.

        Args:
            src_widget (:obj:`FilePickerWidget`): The source widget.

        """
        if self._tree_view and src_widget._tree_view:
            src_model = src_widget._tree_view.model
            if src_model:
                self._tree_view.set_root(src_model.root)

    def refresh_item(self, item: FileBrowserItem = None, recursive=False):
        if self._tree_view:
            self._tree_view.refresh_item(item, recursive)

    def refresh_ui(self, item: FileBrowserItem = None):
        """
        Redraws the subtree rooted at the given item. If item is None, then redraws entire tree.

        Args:
            item (:obj:`FileBrowserItem`): Root of subtree to redraw. Default None, i.e. root.

        """
        if self._tree_view:
            self._tree_view.refresh_ui(item)
        if self._grid_view:
            self._grid_view.refresh_ui()
        if self._table_view:
            self._table_view.refresh_ui()

    def set_selections(self, selections: [FileBrowserItem]):
        if self._tree_view:
            self._tree_view.tree_view.selection = selections
        """
        TODO:
        if self._details_view:
            self._details_view.tree_view.selection = selections
        """

    def get_selections(self) -> [FileBrowserItem]:
        """
        Returns list of selected items from the tree view.

        Returns:
            list[:obj:`FileBrowserItem`]
        """
        selections = []
        """
        TODO:
        if self._details_view:
            selections = self._details_view.tree_view.selection
        """
        if self._tree_view and not selections:
            selections = self._tree_view.tree_view.selection
        return selections

    def select_and_center(self, selection: FileBrowserItem):
        """
        Selects and centers the view on the given item, expanding the tree if needed.

        Args:
            selection (:obj:`FileBrowserItem`): The selected item.

        """
        if self._tree_view:
            self._tree_view.select_and_center(selection)
        """
        TODO:
        if self._details_view:
            self._details_view.select_and_center(selection)
        """

    def set_expanded(self, item: FileBrowserItem, expanded: bool, recursive: bool = False):
        """
        Sets the expansion state of the given item.

        Args:
            item (:obj:`FileBrowserItem`): The item to effect.
            expanded (bool): True to expand, False to collapse.
            recursive (bool): Apply state recursively to descendent nodes. Default False.

        """
        if self._tree_view:
            self._tree_view.set_expanded(item, expanded, recursive)

    def destroy(self):
        """
        Destructor. Called by extension before destroying this object. It doesn't happen automatically.
        Without this hot reloading doesn't work.

        """
        self._layout_button = None
        self._tree_view = None
        self._grid_view = None
        self._table_view = None
        self._window = None
        self._models = None
