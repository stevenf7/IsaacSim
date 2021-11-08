# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
from omni.isaac.core.simulation_context import SimulationContext
from omni.isaac.core.scenes.scene import Scene
from omni.isaac.core.tasks import BaseTask
from omni.isaac.core.utils.prims import is_prim_ancestral, get_prim_type_name, is_prim_no_delete
from omni.isaac.core.utils.stage import clear_stage, update_stage_async
from omni.isaac.dynamic_control import _dynamic_control
import builtins
from pxr import Usd
from omni.isaac.core.utils.viewports import set_camera_view
from omni.isaac.core.loggers import DataLogger


class World(SimulationContext):
    _world_initialized = False

    def __init__(
        self, physics_dt: float = None, rendering_dt: float = None, stage_units_in_meters: float = 1.0
    ) -> None:
        """[summary]

        Args:
            physics_dt (float, optional): [description]. Defaults to 1.0/60.0.
        """
        # TODO: below values will be removed once default stage units in meters are set to 1
        SimulationContext.__init__(
            self, physics_dt=physics_dt, rendering_dt=rendering_dt, stage_units_in_meters=stage_units_in_meters
        )
        if World._world_initialized:
            return
        World._world_initialized = True
        self._scene_finalized = False
        self._current_tasks = dict()
        self._dc_interface = _dynamic_control.acquire_dynamic_control_interface()
        self._scene = Scene()
        # if not builtins.ISAAC_LAUNCHED_FROM_TERMINAL:
        #     self.start_simulation()
        set_camera_view()
        self._data_logger = DataLogger()
        return

    @classmethod
    def clear_instance(cls):
        SimulationContext.clear_instance()
        World._world_initialized = None
        return

    def __del__(self):
        SimulationContext.__del__(self)
        World._world_initialized = None
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

    def get_current_tasks(self):
        return self._current_tasks

    def get_task(self, name):
        if name not in self._current_tasks:
            raise Exception("task name {} doesn't exist in the current world tasks.".format(name))
        return self._current_tasks[name]

    def finalize_scene(self) -> None:
        """[summary]
        """
        if not builtins.ISAAC_LAUNCHED_FROM_TERMINAL:
            self.play()
        self._scene._finalize()
        return

    def reset(self) -> None:
        """[summary]
        """
        # This will do one step internally regardless
        # Note: you need to add all articulated systems and tasks before first reset
        if not self._scene_finalized:
            for task in self._current_tasks.values():
                task.set_up_scene(self.scene)
            self.finalize_scene()
            self._scene_finalized = True
        for task in self._current_tasks.values():
            task.cleanup()
        self.stop()
        self.play()
        self.scene.post_reset()
        for task in self._current_tasks.values():
            task.post_reset()
        return

    def clear(self):

        self.scene.clear()
        self._current_tasks = dict()
        self._scene_finalized = False
        self._data_logger = DataLogger()

        def check_deletable_prim(prim_path):
            if is_prim_no_delete(prim_path):
                return False
            if is_prim_ancestral(prim_path):
                return False
            if get_prim_type_name(prim_path=prim_path) == "PhysicsScene":
                return False
            if prim_path == "/World":
                return False
            if prim_path == "/":
                return False
            return True

        clear_stage(predicate=check_deletable_prim)
        return

    async def reset_async(self):
        if not self._scene_finalized:
            for task in self._current_tasks.values():
                task.set_up_scene(self.scene)
            await self.play_async()
            self.finalize_scene()
            self._scene_finalized = True
        for task in self._current_tasks.values():
            task.cleanup()
        await self.stop_async()
        await self.play_async()
        self._scene.post_reset()
        for task in self._current_tasks.values():
            task.post_reset()
        await update_stage_async()
        return

    def add_task(self, task: BaseTask) -> None:
        """[summary]

        Args:
            task (BaseTask): [description]
        """
        if task.name in self._current_tasks:
            raise Exception("Task name should be unique in the world")
        self._current_tasks[task.name] = task
        return

    def get_observations(self, task_name=None) -> dict:
        """[summary]

        Returns:
            dict: [description]
        """
        if task_name is not None:
            return self._current_tasks[task_name].get_observations()
        else:
            observations = dict()
            for task in self._current_tasks.values():
                observations.update(task.get_observations())
            return observations

    def calculate_metrics(self, task_name=None) -> None:
        """[summary]
        """
        if task_name is not None:
            return self._current_tasks[task_name].calculate_metrics()
        else:
            metrics = dict()
            for task in self._current_tasks.values():
                metrics.update(task.calculate_metrics())
            return metrics

    def is_done(self, task_name=None) -> None:
        """[summary]
        """
        if task_name is not None:
            return self._current_tasks[task_name].is_done()
        else:
            result = [task.is_done() for task in self._current_tasks.values()]
            return all(result)

    def step(self, render: bool = True) -> None:
        """[summary]

        Args:
            number_of_steps (int, optional): [description]. Defaults to 1.
            render (bool, optional): [description]. Defaults to True.
        """
        if self._scene_finalized:
            for task in self._current_tasks.values():
                task.pre_step(self.current_time_step_index, self.current_time)
        if self.scene._enable_bounding_box_computations:
            self.scene._bbox_cache.SetTime(Usd.TimeCode(self._current_time))
        SimulationContext.step(self, render=render)
        if self._data_logger.is_started():
            if self._data_logger._data_frame_logging_func is None:
                raise Exception("You need to add data logging function before starting the data logger")
            data = self._data_logger._data_frame_logging_func(tasks=self.get_current_tasks(), scene=self.scene)
            self._data_logger.add_data(
                data=data, current_time_step=self.current_time_step_index, current_time=self.current_time
            )
        return

    def step_async(self, step_size):
        if self._scene_finalized:
            for task in self._current_tasks.values():
                task.pre_step(self.current_time_step_index, self.current_time)
        if self.scene._enable_bounding_box_computations:
            self.scene._bbox_cache.SetTime(Usd.TimeCode(self._current_time))
        if self._data_logger.is_started():
            if self._data_logger._data_frame_logging_func is None:
                raise Exception("You need to add data logging function before starting the data logger")
            data = self._data_logger._data_frame_logging_func(tasks=self.get_current_tasks(), scene=self.scene)
            self._data_logger.add_data(
                data=data, current_time_step=self.current_time_step_index, current_time=self.current_time
            )
        return

    def get_data_logger(self):
        return self._data_logger
