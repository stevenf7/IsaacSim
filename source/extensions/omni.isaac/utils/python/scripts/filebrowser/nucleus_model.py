# Copyright (c) 2018-2020, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
import os, sys
import time
from datetime import datetime, timedelta

import omni.client
from omni import ui
from carb import log_error
from .model import FileBrowserItem, FileBrowserItemFields, FileBrowserModel


class NucleusItem(FileBrowserItem):
    def __init__(self, path: str, fields: FileBrowserItemFields, is_folder: bool = True):
        super().__init__(path, fields, is_folder=is_folder)
        self._populate_func = lambda item: self._populate(item)

    def _populate(self, item: FileBrowserItem):
        if not (item or not item.is_folder):
            return []

        def scandir(path: str):
            try:
                result, entries = omni.client.list(path)
            except:
                raise
            if not result == omni.client.Result.OK:
                raise ValueError(f"Error retrieving path: {path}")
            return entries

        entries = []
        try:
            entries = scandir(item.path)
        except Exception as e:
            log_error(f"Error scanning directory: {e}")

        item.children.clear()
        for entry in entries:
            full_path = f"{item.path}/{entry.relative_path}"
            child_item = NucleusItemFactory.create_entry_item(entry, full_path)
            if child_item:
                item.children[child_item.name] = child_item


class NucleusItemFactory:
    @staticmethod
    def create_group_item(name: str, path: str) -> NucleusItem:
        if not name:
            return None
        fields = FileBrowserItemFields(name, datetime.now(), 0)
        item = NucleusItem(path, fields)
        item._models = (ui.SimpleStringModel(item.name), ui.SimpleStringModel(""), ui.SimpleStringModel(""))
        return item

    @staticmethod
    def create_entry_item(entry: omni.client.ListEntry, path: str) -> NucleusItem:
        if not entry:
            return None
        name = entry.relative_path
        name = name[:-1] if name.endswith("/") else name

        epoch_time = lambda: datetime.fromtimestamp(time.mktime(time.gmtime(0)))
        modified_time = datetime.fromtimestamp(time.mktime(time.gmtime(0)) + entry.modified_time)
        fields = FileBrowserItemFields(name, modified_time, entry.size)
        is_folder = (entry.flags & 4) > 0
        item = NucleusItem(path, fields, is_folder=is_folder)

        # POSIX Epoch time (Jan 1, 1970)
        epoch_time = lambda: datetime.fromtimestamp(time.mktime(time.gmtime(0)))
        date_model = ui.SimpleStringModel(modified_time.strftime("%x %I:%M%p"))
        size_model = ui.SimpleStringModel(f"{int(entry.size/1000)} Mb")
        item._models = (ui.SimpleStringModel(item.name), date_model, size_model)
        return item


class NucleusModel(FileBrowserModel):
    """
    A Filebrowser model class for navigating a Nucleus server in a tree view. Sub-classed from
    :obj:`FileBrowserModel`.

    Args:
        name (str): Name of root item..
        root_path (str): Root path. If None, then create empty model. Example: "omniverse://ov-content".

    Keyword Args:
        drop_fn (func): Function called to handle drag-n-drops. Function signature:
            void drop_fn(dst_item: :obj:`FileBrowserItem`, src_item: :obj:`FileBrowserItem`)
        filter_fn (func): This handler should return True if the given tree view item is visible,
            False otherwise. Function signature: bool filter_fn(item: :obj:`FileBrowserItem`)
        sort_by_field (str): Name of column by which to sort items in the same folder. Default "name".
        sort_ascending (bool): Sort in ascending order. Default True.
    """

    def __init__(self, name: str, root_path: str, **kwargs):
        super().__init__(**kwargs)
        if not root_path:
            return
        self._root = NucleusItemFactory.create_group_item(name, root_path)
        self._root.icon = "resources/glyphs/hdd.svg"
