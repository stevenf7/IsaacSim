# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
from omni.isaac.core.prims.xform_prim import XFormPrim
from omni.isaac.core.scenes.scene import Scene
import numpy as np
from omni.isaac.core.utils.prims import move_prim


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
        if self._offset is None:
            self._offset = np.array([0.0, 0.0, 0.0])

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

    def _move_task_objects_to_their_frame(self):

        # if self._task_path:
        # TODO: assumption all task objects are under the same parent
        # Specifying a task path has many limitations atm
        # XFormPrim(prim_path=self._task_path, position=self._offset)
        # for object_name, task_object in self._task_objects.items():
        #     new_prim_path = self._task_path + "/" + task_object.prim_path.split("/")[-1]
        #     task_object.change_prim_path(new_prim_path)
        #     current_position, current_orientation = task_object.get_world_pose()
        for object_name, task_object in self._task_objects.items():
            current_position, current_orientation = task_object.get_world_pose()
            task_object.set_world_pose(position=current_position + self._offset)
            task_object.set_default_state(position=current_position + self._offset)
        return

    def get_task_objects(self):
        return self._task_objects

    def get_observations(self) -> dict:
        """[summary]

        Raises:
            NotImplementedError: [description]

        Returns:
            dict: [description]
        """
        raise NotImplementedError

    def calculate_metrics(self) -> None:
        """[summary]
        """
        raise NotImplementedError

    def is_done(self) -> None:
        """[summary]
        """
        raise NotImplementedError

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

    def get_description(self) -> str:
        """[summary]

        Returns:
            str: [description]
        """
        return ""

    def cleanup(self) -> None:
        """[summary]
        """
        return

    def set_params(self, *args, **kwargs):
        raise NotImplementedError

    def get_params(self):
        raise NotImplementedError
