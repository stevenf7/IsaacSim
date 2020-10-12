# Copyright (c) 2018-2020, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
"""
The basic UI widget and set of supporting classes for navigating the filesystem through a tree view.
The filesystem can either be from your local machine or the Omniverse server.

Example:

    With just a few lines of code, you can create a powerful, flexible tree view widget that you 
    can embed into your view.

        filebrowser = FileBrowserWidget(
            "Omniverse",
            layout=SPLIT_PANES,
            mouse_pressed_fn=on_mouse_pressed,
            selection_changed_fn=on_selection_changed,
            drop_fn=drop_handler,
            filter_fn=item_filter_fn,
        )

Module Constants:

    layout: {LAYOUT_SINGLE_PANE_SLIM, LAYOUT_SINGLE_PANE_WIDE, LAYOUT_SPLIT_PANES, LAYOUT_DEFAULT}

.. _Google Python Style Guide:
   http://google.github.io/styleguide/pyguide.html

"""
LAYOUT_SINGLE_PANE_SLIM = 1
LAYOUT_SINGLE_PANE_WIDE = 2
LAYOUT_SPLIT_PANES = 3
LAYOUT_DEFAULT = 3

from .widget import FileBrowserWidget
from .card import FileBrowserItemCard
from .model import FileBrowserModel, FileBrowserItem
from .filesystem_model import FileSystemModel, FileSystemItem
from .nucleus_model import NucleusModel, NucleusItem
