# Copyright (c) 2022-2024, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

import os
from typing import Optional

import carb.settings
import omni.ui as ui
from omni.kit.browser.core import TreeCategoryDelegate
from omni.kit.browser.folder.core import TreeFolderBrowserWidgetEx

from .delegate import AssetDetailDelegate
from .empty_property_delegate import EmptyPropertyDelegate
from .model import AssetBrowserModel
from .multi_property_delegate import MultiPropertyDelegate
from .options_menu import FolderOptionsMenu
from .prop_property_delegate import PropAssetPropertyDelegate
from .style import PROPERTY_STYLE


class AssetBrowserWindow(ui.Window):
    """
    Represent a window to show Assets
    """

    WINDOW_TITLE = "Isaac Sim Assets"

    def __init__(self, visible=True):
        super().__init__(self.WINDOW_TITLE, visible=visible)

        self.__empty_delegate: Optional[EmptyPropertyDelegate] = None
        self.__prop_delegate: Optional[PropAssetPropertyDelegate] = None
        self.__multi_delegate: Optional[MultiPropertyDelegate] = None
        self._options_menu: Optional[FolderOptionsMenu] = None

        self.frame.set_build_fn(self._build_ui)

        self._browser_model = None
        self._delegate = None
        self._widget = None

        # Dock it to the same space where Stage is docked.
        self.deferred_dock_in("Content")

    def destroy(self):
        if self.__empty_delegate:
            self.__empty_delegate.destroy()
            self.__empty_delegate = None
        if self.__prop_delegate:
            self.__prop_delegate.destroy()
            self.__prop_delegate = None
        if self.__multi_delegate:
            self.__multi_delegate.destroy()
            self.__multi_delegate = None
        if self._browser_model:
            self._browser_model.destroy()
            self._browser_model = None
        if self._delegate:
            self._delegate.destroy()
            self._delegate = None
        if self._widget:
            self._widget.destroy()
            self._widget = None
        if self._options_menu:
            self._options_menu.destroy()
            self._options_menu = None

        super().destroy()

    def _build_ui(self):
        self.__empty_delegate = EmptyPropertyDelegate()
        self.__prop_delegate = PropAssetPropertyDelegate()
        self.__multi_delegate = MultiPropertyDelegate()
        preload_folder = os.path.abspath(carb.tokens.get_tokens_interface().resolve("${app}/../predownload"))
        self._browser_model = AssetBrowserModel()
        self._delegate = AssetDetailDelegate(self._browser_model)
        self._options_menu = FolderOptionsMenu()

        with self.frame:
            with ui.VStack(spacing=15):
                self._widget = TreeFolderBrowserWidgetEx(
                    self._browser_model,
                    detail_delegate=self._delegate,
                    options_menu=self._options_menu,
                    predownload_folder=preload_folder,
                    style=PROPERTY_STYLE,
                )
