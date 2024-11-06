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
from .model import ExampleBrowserModel
from .property_delegate import EmptyPropertyDelegate, MultiPropertyDelegate, PropAssetPropertyDelegate


class ExampleBrowserWindow(ui.Window):
    """
    Represent a window to show Assets
    """

    WINDOW_TITLE = "Isaac Examples"

    def __init__(self, model: ExampleBrowserModel, visible=True):
        super().__init__(self.WINDOW_TITLE, visible=visible)

        self.__empty_delegate: Optional[EmptyPropertyDelegate] = None
        self.__prop_delegate: Optional[PropAssetPropertyDelegate] = None
        self.__multi_delegate: Optional[MultiPropertyDelegate] = None

        self.frame.set_build_fn(self._build_ui)

        self._browser_model = model
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

    def _build_ui(self):
        self.__empty_delegate = EmptyPropertyDelegate()
        self.__prop_delegate = PropAssetPropertyDelegate()
        self.__multi_delegate = MultiPropertyDelegate()
        preload_folder = os.path.abspath(carb.tokens.get_tokens_interface().resolve("${app}/../predownload"))
        self._delegate = AssetDetailDelegate(self._browser_model)

        with self.frame:
            with ui.VStack(spacing=15):
                self._widget = TreeFolderBrowserWidgetEx(
                    self._browser_model,
                    detail_delegate=self._delegate,
                    predownload_folder=preload_folder,
                    min_thumbnail_size=32,
                    max_thumbnail_size=128,
                    detail_thumbnail_size=64,
                )
