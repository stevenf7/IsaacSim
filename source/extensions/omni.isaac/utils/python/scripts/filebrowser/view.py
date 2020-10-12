# Copyright (c) 2018-2020, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
"""
An abstract View class, subclassed by TreeView and GridView
"""
from omni import ui
from abc import abstractmethod
from .model import FileBrowserItem, FileBrowserModel


class FileBrowserView:
    def __init__(self, model: FileBrowserModel):
        self._model = model
        self._widget = None
        self._visible = True

    @abstractmethod
    def build_ui(self):
        pass

    @property
    def model(self):
        return self._model

    @property
    def visible(self):
        return self._visible

    @visible.setter
    def visible(self, visible: bool):
        if self._widget:
            self._widget.visible = visible
        self._visible = visible

    def set_root(self, item: FileBrowserItem):
        if self._model:
            self._model.root = item

    @abstractmethod
    def refresh_ui(self, item: FileBrowserItem = None):
        pass

    @abstractmethod
    def select_and_center(self, item: FileBrowserItem):
        pass

    @abstractmethod
    def _on_selection_changed(self, selections: [FileBrowserItem]):
        pass

    @abstractmethod
    def destroy(self):
        pass
