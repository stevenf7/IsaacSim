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
from omni.isaac.core.tasks.task import BaseTask
from omni.isaac.dynamic_control import _dynamic_control
import builtins
from pxr import Usd


class World(SimulationContext):
    _world_initialized = False

    def __init__(self, physics_dt: float = 1.0 / 60.0, stage_units_in_meters: float = 1.0) -> None:
        """[summary]

        Args:
            physics_dt (float, optional): [description]. Defaults to 1.0/60.0.
        """
        SimulationContext.__init__(self, physics_dt=physics_dt)
        if World._world_initialized:
            return
        World._world_initialized = True
        self._scene_finalized = False
        self._current_task = None
        self._stage_units_in_meters = stage_units_in_meters
        self._scene = None
        if not builtins.ISAAC_LAUNCHED_FROM_TERMINAL:
            self.create_new_stage()
        self._dc_interface = _dynamic_control.acquire_dynamic_control_interface()
        # TODO: double check the stage units are actually set properly
        # TODO: account for stage units properly across all new extensions
        return

    async def init_world_async(self):
        await self.create_new_stage_async()
        return

    async def create_new_stage_async(self):
        await SimulationContext.create_new_stage_async(self, stage_units_in_meters=self._stage_units_in_meters)
        del self._scene
        self._scene = Scene(self.stage, stage_units_in_meters=self._stage_units_in_meters)
        return

    def create_new_stage(self) -> Usd.Stage:
        stage = SimulationContext.create_new_stage(self, stage_units_in_meters=self._stage_units_in_meters)
        del self._scene
        self._scene = Scene(self.stage, stage_units_in_meters=self._stage_units_in_meters)
        self.start_simulation()
        return stage

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
        if not builtins.ISAAC_LAUNCHED_FROM_TERMINAL:
            self.play()
        self._scene._finalize()
        return

    def reset(self) -> None:
        """[summary]
        """
        # This will do one step internally regardless
        if not self._scene_finalized:
            if self._current_task is not None:
                self._current_task.set_up_scene(self.scene)
            self.finalize_scene()
            self._scene_finalized = True
        if self._current_task is not None:
            self._current_task.cleanup()
        self.stop()
        self.play()
        self.scene.reset()
        if self._current_task is not None:
            self._current_task.reset()
        return

    async def reset_async(self):
        if not self._scene_finalized:
            if self._current_task is not None:
                self._current_task.set_up_scene(self.scene)
                await self.play_async()
                self.finalize_scene()
                self._scene_finalized = True
        if self._current_task is not None:
            self._current_task.cleanup()
        await self.stop_async()
        await self.play_async()
        self._scene.reset()
        if self._current_task is not None:
            self._current_task.reset()
        await self.pause_async()
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

    def step(self, render: bool = True) -> None:
        """[summary]

        Args:
            number_of_steps (int, optional): [description]. Defaults to 1.
            render (bool, optional): [description]. Defaults to True.
        """
        if self._scene_finalized and self._current_task is not None:
            self._current_task.step(self.time_step_index, self.time)
        if self.scene._enable_bounding_box_computations:
            self.scene._bbox_cache.SetTime(Usd.TimeCode(self._current_time))
        SimulationContext.step(self, render=render)
        return
