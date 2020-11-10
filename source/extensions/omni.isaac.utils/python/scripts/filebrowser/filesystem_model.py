# Copyright (c) 2018-2020, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
import os, sys, stat
import time
from datetime import datetime
import carb

from omni import ui
from .model import FileBrowserItem, FileBrowserItemFields, FileBrowserModel


class FileSystemItem(FileBrowserItem):
    def __init__(self, path: str, fields: FileBrowserItemFields, is_folder: bool = False):
        super().__init__(path, fields, is_folder=is_folder)
        self._populate_func = lambda item: self._populate(item)

    def _populate(self, item: FileBrowserItem):
        if not (item and item.is_folder):
            return []

        def keep_entry(entry: os.DirEntry) -> bool:
            if os.name == "nt":
                # On Windows, test for hidden directories & files
                try:
                    file_attrs = entry.stat().st_file_attributes
                except:
                    return False
                if file_attrs & stat.FILE_ATTRIBUTE_HIDDEN:
                    return False
                elif file_attrs & stat.FILE_ATTRIBUTE_SYSTEM:
                    return False
            return True

        item.children.clear()
        try:
            with os.scandir(item.path) as it:
                entries = {entry.name: entry for entry in it}
                for name in sorted(entries):
                    entry = entries[name]
                    if not keep_entry(entry):
                        continue
                    child_item = FileSystemItemFactory.create_entry_item(entry)
                    if child_item:
                        item.children[child_item.name] = child_item
        except PermissionError:
            carb.log_error("Permission Denied: {}".format(item.path))


class FileSystemItemFactory:
    @staticmethod
    def create_group_item(name: str, path: str) -> FileSystemItem:
        if not name:
            return None
        fields = FileBrowserItemFields(name, datetime.now(), 0)
        item = FileSystemItem(path, fields, is_folder=True)
        item._models = (ui.SimpleStringModel(item.name), ui.SimpleStringModel(""), ui.SimpleStringModel(""))
        return item

    @staticmethod
    def create_entry_item(entry: os.DirEntry) -> FileSystemItem:
        if not entry:
            return None

        epoch_to_datetime = lambda t: datetime.fromtimestamp(time.mktime(t))
        modified_time = epoch_to_datetime(time.gmtime(entry.stat().st_mtime))
        fields = FileBrowserItemFields(entry.name, modified_time, entry.stat().st_size)
        item = FileSystemItem(entry.path, fields, is_folder=entry.is_dir())

        date_model = ui.SimpleStringModel(modified_time.strftime("%x %I:%M%p"))
        size_model = ui.SimpleStringModel(f"{int(entry.stat().st_size/1000)} Mb")
        item._models = (ui.SimpleStringModel(item.name), date_model, size_model)
        return item


class FileSystemModel(FileBrowserModel):
    """
    A Filebrowser model class for navigating a the local filesystem in a tree view. Sub-classed from
    :obj:`FileBrowserModel`.

    Args:
        name (str): Name of root item..
        root_path (str): Root path. If None, then create empty model. Default "C:".

    Keyword Args:
        drop_fn (func): Function called to handle drag-n-drops. Function signature:
            void drop_fn(dst_item: :obj:`FileBrowserItem`, src_item: :obj:`FileBrowserItem`)
        filter_fn (func): This handler should return True if the given tree view item is visible,
            False otherwise. Function signature: bool filter_fn(item: :obj:`FileBrowserItem`)
        sort_by_field (str): Name of column by which to sort items in the same folder. Default "name".
        sort_ascending (bool): Sort in ascending order. Default True.
    """

    def __init__(self, name: str, root_path="C:", **kwargs):
        super().__init__(**kwargs)
        if not root_path:
            return
        if not root_path.endswith("/"):
            root_path += "/"
        self._root = FileSystemItemFactory.create_group_item(name, root_path)
        self._root.icon = "resources/glyphs/desktop.svg"
