# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
from abc import abstractmethod
from omni.isaac.core.scenes.scene import Scene


class BaseTask(object):
    def __init__(self, name: str, offset):
        """[summary]

        Args:
            name (str): [description]
        """
        self._scene = None
        self._name = name
        self._offset = offset
        self._task_objects = dict()

    @property
    def scene(self) -> Scene:
        """[summary]

        Returns:
            Scene: [description]
        """
        return self._scene

    @property
    def name(self) -> str:
        """[summary]

        Returns:
            str: [description]
        """
        return self._name

    def set_up_scene(self, scene: Scene) -> None:
        """[summary]

        Args:
            scene (Scene): [description]
        """
        self._scene = scene
        return

    def get_task_objects(self):
        return self._task_objects

    @abstractmethod
    def get_observations(self) -> dict:
        """[summary]

        Raises:
            NotImplementedError: [description]

        Returns:
            dict: [description]
        """
        raise NotImplementedError

    @abstractmethod
    def calculate_metrics(self) -> None:
        """[summary]
        """
        raise NotImplementedError

    @abstractmethod
    def is_done(self) -> None:
        """[summary]
        """
        raise NotImplementedError

    @abstractmethod
    def pre_step(self, control_index: int, simulation_time: float) -> None:
        """[summary]

        Args:
            control_index (int): [description]
            simulation_time (float): [description]
        """
        return

    def post_reset(self) -> None:
        """[summary]
        """
        return

    @abstractmethod
    def get_description(self) -> str:
        """[summary]

        Returns:
            str: [description]
        """
        return ""

    @abstractmethod
    def cleanup(self) -> None:
        """[summary]
        """
        return

    @abstractmethod
    def set_params(self, *args, **kwargs):
        raise NotImplementedError

    @abstractmethod
    def get_params(self):
        raise NotImplementedError
