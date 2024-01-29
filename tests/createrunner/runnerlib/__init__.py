# Copyright (c) 2020-2024, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
import logging
from typing import Union

from .create_runner import CreateRunner
from .kit_runner import KitRunner

_log = logging.getLogger("kit_runner")


def set_log_level(level: Union[int, str]):
    """
    Sets the module's logging level

    Args:
        level: the log level (can be an int like logging.DEBUG or a string like "DEBUG")
    """
    if isinstance(level, str):
        level = level.upper()

    _log.setLevel(level)
