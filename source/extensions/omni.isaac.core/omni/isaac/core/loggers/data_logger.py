# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
from typing import Callable, List
from omni.isaac.core.scenes.scene import Scene
from omni.isaac.core.tasks.base_task import BaseTask
from omni.isaac.core.utils.types import DataFrame
import json


class DataLogger:
    """[summary]
    """

    def __init__(self) -> None:
        self._pause = True
        self._data_frames = []
        self._data_frame_logging_func = None

    def add_data(self, data: dict, current_time_step: float, current_time: float) -> None:
        """[summary]

        Args:
            data (dict): [description]
            current_time_step (float): [description]
            current_time (float): [description]
        """
        self._data_frames.append(DataFrame(current_time_step=current_time_step, current_time=current_time, data=data))
        return

    def clear(self) -> None:
        """[summary]
        """
        self._pause = True
        self._data_frames = []
        return

    def pause(self) -> None:
        """[summary]
        """
        self._pause = True
        return

    def start(self) -> None:
        """[summary]
        """
        self._pause = False
        return

    def is_started(self) -> bool:
        """[summary]

        Returns:
            bool: [description]
        """
        return not self._pause

    def reset(self) -> None:
        """[summary]
        """
        self._pause = True
        self._data_frames = []
        return

    def get_data_frame(self, data_frame_index: int) -> DataFrame:
        """[summary]

        Args:
            data_frame_index (int): [description]

        Returns:
            DataFrame: [description]
        """
        return self._data_frames[data_frame_index]

    def add_data_frame_logging_func(self, func: Callable[[List[BaseTask], Scene], None]) -> None:
        """[summary]

        Args:
            func (Callable[[list[BaseTask], Scene], None]): [description]
        """
        self._data_frame_logging_func = func
        return

    def save(self, log_path: str) -> None:
        """[summary]

        Args:
            log_path (str): [description]
        """
        data = {}
        self._data_frames = [data_frame.get_dict() for data_frame in self._data_frames]
        data["Isaac Sim Data"] = self._data_frames
        with open(log_path, "w") as outfile:
            json.dump(data, outfile)
        return

    def load(self, log_path: str) -> None:
        """[summary]

        Args:
            log_path (str): [description]
        """
        self._pause = True
        self._data_frames = []
        self._data_frame_logging_func = None
        with open(log_path) as json_file:
            json_data = json.load(json_file)
            data_frames = json_data["Isaac Sim Data"]
            data_frames = [DataFrame.init_from_dict(dict_representation=data_frame) for data_frame in data_frames]
            self._data_frames = data_frames
        return
