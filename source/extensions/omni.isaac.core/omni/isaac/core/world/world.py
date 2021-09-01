# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
from omni.isaac.kit.simulation import SimulationContext
from omni.isaac.core.scenes.scene import Scene
from omni.isaac.core.tasks.task import BaseTask
from omni.isaac.dynamic_control import _dynamic_control


class World(SimulationContext):
    def __init__(self, add_ground_plane: bool = True, physics_dt: float = 1.0 / 60.0) -> None:
        """[summary]

        Args:
            add_ground_plane (bool, optional): [description]. Defaults to True.
            physics_dt (float, optional): [description]. Defaults to 1.0/60.0.
        """
        super().__init__()
        self._scene_finalized = False
        self._current_task = None
        self.create_new_stage()
        self.set_physics_dt(physics_dt)
        self._scene = Scene(self.stage)
        self._dc_interface = _dynamic_control.acquire_dynamic_control_interface()
        # TODO: double check the stage units are actually set properly
        if add_ground_plane:
            self._scene.add_ground_plane()
        self.start_simulation()
        return

    @property
    def dc_interface(self) -> _dynamic_control.DynamicControl:
        """[summary]

        Returns:
            _dynamic_control.DynamicControl: [description]
        """
        return self._dc_interface

    @property
    def scene(self) -> Scene:
        """[summary]

        Returns:
            Scene: [description]
        """
        return self._scene

    def finalize_scene(self) -> None:
        """[summary]
        """
        self.play()
        self.step(render=True)
        self._scene._finalize()
        return

    def reset(self) -> None:
        """[summary]
        """
        if not self._scene_finalized:
            if self._current_task is not None:
                self._current_task.set_up_scene(self.scene)
            self.finalize_scene()
            self._scene_finalized = True
        self.stop()
        self.play()
        self.scene.reset()
        if self._current_task is not None:
            self._current_task.reset()
        return

    def load_task(self, task: BaseTask) -> None:
        """[summary]

        Args:
            task (BaseTask): [description]
        """
        self._current_task = task
        return

    def get_observations(self) -> dict:
        """[summary]

        Returns:
            dict: [description]
        """
        return self._current_task.get_observations()

    def save(self):
        raise NotImplementedError

    def load(self):
        raise NotImplementedError

    def close(self):
        raise NotImplementedError

    def step(self, number_of_steps: int = 1, render: bool = True) -> None:
        """[summary]

        Args:
            number_of_steps (int, optional): [description]. Defaults to 1.
            render (bool, optional): [description]. Defaults to True.
        """
        if self._scene_finalized and self._current_task is not None:
            self._current_task.step(self.time_step_index, self.wallclock_time)
        super().step(number_of_steps=number_of_steps, render=render)
        return
