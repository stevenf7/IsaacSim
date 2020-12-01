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
