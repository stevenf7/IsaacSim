# Copyright (c) 2018-2020, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
import os, sys
import asyncio
import omni.client

from datetime import datetime
from collections import OrderedDict
from omni import ui
from typing import Tuple


from collections import namedtuple

FileBrowserItemFields = namedtuple("FileBrowserItemFields", "name date size")


class FileBrowserItem(ui.AbstractItem):
    """
    Base class for the Filebrowser tree view Item. Should be sub-classed to implement specific filesystem
    behavior. The Constructor should not be called directly.  Instead there are factory methods available 
    for creating instances when needed.

    """

    def __init__(self, path: str, fields: FileBrowserItemFields, is_folder: bool = False):
        super().__init__()
        self._path = path.replace("\\", "/")
        self._fields = fields  # Raw field values
        self._models = ()  # Formatted values for display
        self._parent = None
        self._children = OrderedDict()
        self._is_folder = is_folder
        self._populated = False
        self._populate_func = None
        self._enable_sorting = True  # Enables children to be sorted
        self._icon = None
        self._expanded = False

    @property
    def expanded(self) -> bool:
        """bool: Item expanded status"""
        return self._expanded

    @expanded.setter
    def expanded(self, value: bool):
        self._expanded = value

    @property
    def name(self) -> str:
        """str: Item name."""
        return getattr(self._fields, "name", "")

    @property
    def path(self) -> str:
        """str: Full path name."""
        return self._path

    @property
    def fields(self) -> FileBrowserItemFields:
        """:obj:`FileBrowserItemFields`: A subset of the item's stats stored as a string tuple."""
        return self._fields

    @property
    def models(self) -> Tuple:
        """Tuple[:obj:`ui.AbstractValueModel`]: The columns of this item."""
        return self._models

    @property
    def parent(self) -> object:
        """:obj:`FileBrowserItem`: Parent of this item."""
        return self._parent

    @property
    def children(self) -> OrderedDict:
        """dict[:obj:`FileBrowserItem`]: Children of this item.  Does not populate the item if not already populated."""
        return self._children

    @property
    def is_folder(self) -> bool:
        """bool: True if this item is a folder."""
        return self._is_folder

    @property
    def populated(self) -> bool:
        """bool: Gets/Sets item populated state."""
        return self._populated

    @populated.setter
    def populated(self, value: bool):
        self._populated = value

    @property
    def populate_func(self) -> ():
        """func: The function called to populate an item.
        Function signature: list[obj] populate_func(item: :obj:`FileBrowserItem`).
        """
        return self._populate_func

    @property
    def enable_sorting(self) -> bool:
        """bool: True if item's children are sortable."""
        return self._enable_sorting

    @property
    def icon(self) -> str:
        """str: Gets/sets path to icon file."""
        return self._icon

    @icon.setter
    def icon(self, icon: str):
        self._icon = icon

    def get_subitem_model(self, index: int) -> object:
        """
        Returns ith column of this item.

        Returns:
            :obj:`AbstractValueModel`

        """
        if self._models and index < len(self._models):
            return self._models[index]
        return None

    def populate(self) -> [object]:
        """
        If not already populated, populates this item using its populate_func.

        Returns:
            list[:obj:`FileBrowserItem`]: List of children items.

        """
        if not self._populated:
            if self._populate_func:
                self._populate_func(self)
            for _, child in self._children.items():
                child._parent = self
            self._populated = True
        return list(self._children.values())

    def add_child(self, item: object):
        """
        Adds item as child.

        Args:
            item (:obj:`FileBrowserItem`): Child item.

        """
        if item:
            self._children[item.name] = item
            item._parent = self

    def del_child(self, item_name: str):
        """
        Deletes child item by name.

        Args:
            item_name (str): Name of child item.

        """
        if item_name in self._children:
            del self._children[item_name]


class FileBrowserItemFactory:
    @staticmethod
    def create_group_item(name: str, path: str) -> FileBrowserItem:
        if not name:
            return None
        fields = FileBrowserItemFields(name, datetime.now(), 0)
        item = FileBrowserItem(path, fields, is_folder=True)
        item._models = (ui.SimpleStringModel(item.name), ui.SimpleStringModel(""), ui.SimpleStringModel(""))
        item._enable_sorting = False
        return item


class FileBrowserModel(ui.AbstractItemModel):
    """
    Base class for the Filebrowser tree view Model. Should be sub-classed to implement specific filesystem
    behavior.

    Args:
        name (str): Name of root item. If None given, then create an initally empty model.

    Keyword Args:
        drop_fn (func): Function called to handle drag-n-drops. Function signature: 
            void drop_fn(dst_item: :obj:`FileBrowserItem`, src_item: :obj:`FileBrowserItem`)
        filter_fn (func): This handler should return True if the given tree view item is visible, 
            False otherwise. Function signature: bool filter_fn(item: :obj:`FileBrowserItem`)
        sort_by_field (str): Name of column by which to sort items in the same folder. Default "name".
        sort_ascending (bool): Sort in ascending order. Default True.
    """

    def __init__(self, name: str = None, **kwargs):
        super().__init__()
        if name:
            self._root = FileBrowserItemFactory.create_group_item(name, "")
        else:
            self._root = None
        # By default, display these number of columns
        self._visible_columns = 3
        self._drop_fn = kwargs.get("drop_fn", None)
        self._filter_fn = kwargs.get("filter_fn", None)
        self._sort_by_field = kwargs.get("sort_by_field", "name")
        self._sort_ascending = kwargs.get("sort_ascending", True)

    @property
    def root(self) -> FileBrowserItem:
        """:obj:`FileBrowserItem`: Gets/sets the root item of this model."""
        return self._root

    @root.setter
    def root(self, item: FileBrowserItem):
        self._root = item

    @property
    def sort_by_field(self) -> str:
        """:obj:`FileBrowserItem`: Gets/sets the sort-by field name."""
        return self._sort_by_field

    @sort_by_field.setter
    def sort_by_field(self, field: str):
        self._sort_by_field = field

    @property
    def sort_ascending(self) -> bool:
        """:obj:`FileBrowserItem`: Gets/sets the sort ascending state."""
        return self._sort_ascending

    @sort_ascending.setter
    def sort_ascending(self, value: bool):
        self._sort_ascending = value

    def get_item_children(self, item: FileBrowserItem) -> [FileBrowserItem]:
        """
        Returns the list of items that are nested to the given parent item.

        Args:
            item (:obj:`FileBrowserItem`): Parent item.

        Returns:
            list[:obj:`FileBrowserItem`]

        """
        item = item or self._root

        if item and item.is_folder:
            children = item.populate()
            if item.enable_sorting and self._sort_by_field in FileBrowserItemFields._fields:
                # Skip root level but otherwise, sort by specified field
                def get_value(item: FileBrowserItem):
                    value = getattr(item.fields, self._sort_by_field)
                    return value.lower() if isinstance(value, str) else value

                children = sorted(children, key=lambda item: get_value(item), reverse=not self._sort_ascending)
            if self._filter_fn:
                children = list(filter(self._filter_fn, children))
            return children
        return []

    def get_item_value_model_count(self, item: FileBrowserItem) -> int:
        """
        Returns the number of columns this model item contains.

        Args:
            item (:obj:`FileBrowserItem`): The item in question.

        Returns:
            int

        """
        if not item:
            return self._visible_columns
        return min(self._visible_columns, len(item.models))

    def get_item_value_model(self, item: FileBrowserItem, index: int) -> object:
        """
        Get the value model associated with this item.

        Args:
            item (:obj:`FileBrowserItem`): The item in question.

        Returns:
            :obj:`AbstractValueModel`

        """
        if not item:
            item = self._root
        if item:
            return item.get_subitem_model(index)
        else:
            return None

    def set_visible_columns(self, ncols: int):
        """
        Sets the number of columns to make visible.

        Args:
            ncols (int): Number of columns.

        """
        self._visible_columns = ncols

    def get_drag_mime_data(self, item: FileBrowserItem):
        """Returns Multipurpose Internet Mail Extensions (MIME) data for be able to drop this item somewhere"""
        return (item or self._root).path

    def drop_accepted(self, dst_item: FileBrowserItem, src_item: FileBrowserItem) -> bool:
        """
        Reimplemented from AbstractItemModel. Called to highlight target when drag and drop.
        Returns True if destination item is able to accept a drop. This function can be
        overriden to implement a different behavior.

        Args:
            dst_item (:obj:`FileBrowserItem`): Target item.
            src_item (:obj:`FileBrowserItem`): Source item.

        Returns:
            bool

        """
        if dst_item and dst_item.is_folder:
            # Returns True if item is a folder.
            return True
        return False

    def drop(self, dst_item: FileBrowserItem, src_item: FileBrowserItem):
        """
        Invokes user-supplied function to handle dropping source onto destination item.

        Args:
            dst_item (:obj:`FileBrowserItem`): Target item.
            src_item (:obj:`FileBrowserItem`): Source item.

        """
        if self._drop_fn:
            self._drop_fn(dst_item, src_item)

    @staticmethod
    async def stat_path_async(path: str, timeout: float = 10.0) -> omni.client.ListEntry:
        """
        Async function. Uses omni.client to stat the given path.  Raises errors if path is unreachable or
        invalid.

        Args:
            path (str): The full path name of a file or folder, e.g. "omniverse://ov-content/Users/me".
            timeout (float): Number of seconds to try before erroring out.  Default 10.

        Returns:
            :obj:`omni.client.ListEntry`

        Raises:
            :obj:`RuntimeWarning`: If path is unreachable or invalid.

        """
        try:
            path = path.replace("\\", "/")
            result, stats = await asyncio.wait_for(omni.client.stat_async(path), timeout=timeout)
        except asyncio.TimeoutError:
            raise RuntimeWarning(f"Error unable to stat '{path}': Timed out after {timeout} secs.")
        except Exception as e:
            raise RuntimeWarning(f"Error unable to stat '{path}': {e}")

        if result != omni.client.Result.OK:
            raise RuntimeWarning(f"Error unable to stat '{path}': {result}")

        return stats

    @staticmethod
    async def create_folder_async(path: str, timeout: float = 10.0) -> str:
        """
        Async function.  Creates a new folder at the given path name.

        Args:
            path (str): The full path name of a file or folder, e.g. "omniverse://ov-content/Users/me".
            timeout (float): Number of seconds to try before erroring out.  Default 10.

        Returns:
            str: Folder path name

        Raises:
            :obj:`RuntimeWarning`: If error or timeout.

        """
        try:
            path = path.replace("\\", "/")
            result = await asyncio.wait_for(omni.client.create_folder_async(path), timeout=timeout)
        except asyncio.TimeoutError:
            raise RuntimeWarning(f"Error unable to create folder '{path}': Timed out after {timeout} secs.")
        except Exception as e:
            raise RuntimeWarning(f"Error creating folder '{path}': {e}")

        if result != omni.client.Result.OK:
            raise RuntimeWarning(f"Error creating folder '{path}': {result}")

        return path

    @staticmethod
    async def copy_item_async(rel_path: str, src_root: str, dst_root: str, timeout: float = 30.0) -> str:
        """
        Async function.  Copies item (recursively) from one path to another. Note: this function simply
        uses the copy function from omni.client and makes no attempt to optimize for copying from one
        Omniverse server to another.  For that, use the Copy Service.  Example usage:
        await copy_item_async("my_file.usd", "C:/tmp", "omniverse://ov-content/Users/me")

        Args:
            rel_path (str): Name of file or folder relative to the source and destination paths.
            src_root (str): Source path to item being copied.
            dst_root (str): Destination path to copy the item.
            timeout (float): Number of seconds to try before erroring out.  Default 10.

        Returns:
            str: Destination path name

        Raises:
            :obj:`RuntimeWarning`: If error or timeout.

        """
        try:
            src_path = f"{src_root}/{rel_path}"
            dst_path = f"{dst_root}/{rel_path}"
            result = await asyncio.wait_for(omni.client.copy_async(src_path, dst_path), timeout=timeout)
        except asyncio.TimeoutError:
            raise RuntimeWarning(f"Error unable to copy '{src_path}' to '{dst_path}': Timed out after {timeout} secs.")
        except Exception as e:
            raise RuntimeWarning(f"Error copying '{src_path}' to '{dst_path}': {e}")

        if result != omni.client.Result.OK:
            raise RuntimeWarning(f"Error copying '{src_path}' to '{dst_path}': {result}")

        return dst_path

    @staticmethod
    async def get_auth_token_async(path: str, timeout: float = 10.0) -> Tuple[str, str, str]:
        """
        Async function.  Retrieves the authentication token for the given server/path.

        Args:
            path (str): The full path name to the server, e.g. "omniverse://ov-content".
            timeout (float): Number of seconds to try before erroring out.  Default 10.

        Returns:
            tupe[str, str, str]: host, username, auth_token.

        Raises:
            :obj:`RuntimeWarning`: If error or timeout.

        """
        try:
            result, username, auth_token = await asyncio.wait_for(
                omni.client.get_auth_token_async(path), timeout=timeout
            )
        except asyncio.TimeoutError:
            raise RuntimeWarning(f"Error unable to get auth token: Timed out after {timeout} secs.")
        except Exception as e:
            raise RuntimeWarning(str(e))

        if result != omni.client.Result.OK:
            raise RuntimeWarning(str(result))

        host = path.replace("omniverse://", "").split("/")[0]

        return (host, username, auth_token)

    @staticmethod
    async def delete_item_async(path: str, timeout: float = 10.0) -> str:
        """
        Async function.  Deletes the item at the given path name.

        Args:
            path (str): The full path name of a file or folder, e.g. "omniverse://ov-content/Users/me".
            timeout (float): Number of seconds to try before erroring out.  Default 10.

        Returns:
            str: Deleted path name

        Raises:
            :obj:`RuntimeWarning`: If error or timeout.

        """
        try:
            path = path.replace("\\", "/")
            result = await asyncio.wait_for(omni.client.delete_async(path), timeout=timeout)
        except asyncio.TimeoutError:
            raise RuntimeWarning(f"Error deleting item '{path}': Timed out after {timeout} secs.")
        except Exception as e:
            raise RuntimeWarning(f"Error deleting item '{path}': {e}")

        if result != omni.client.Result.OK:
            raise RuntimeWarning(f"Error deleting item '{path}': {result}")

        return path
