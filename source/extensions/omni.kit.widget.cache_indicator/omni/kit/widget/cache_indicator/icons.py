# Copyright (c) 2018-2020, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
from pathlib import Path


class Icons:
    """A singleton that scans the icon folder and returns the icon depending on the type"""

    _icons = {}

    @staticmethod
    def on_startup(extension_path):
        current_path = Path(extension_path)
        icon_path = current_path.joinpath("icons")
        # Read all the svg files in the directory
        Icons._icons = {icon.stem: icon for icon in icon_path.glob("*.svg")}

    @staticmethod
    def on_shutdown():
        Icons._icons = None

    @staticmethod
    def get(name, default=None):
        """Checks the icon cache and returns the icon if exists"""
        found = Icons._icons.get(name)
        if not found and default:
            found = Icons._icons.get(default)

        if found:
            return str(found)

        return None
