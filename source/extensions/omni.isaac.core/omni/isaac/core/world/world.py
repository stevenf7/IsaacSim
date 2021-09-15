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
import omni.isaac.kit.global_vars as global_vars
from pxr import Usd


class World(SimulationContext):
    def __init__(
        self, add_ground_plane: bool = True, physics_dt: float = 1.0 / 60.0, stage_units_in_meters: float = 1.0
    ) -> None:
        """[summary]

        Args:
            add_ground_plane (bool, optional): [description]. Defaults to True.
            physics_dt (float, optional): [description]. Defaults to 1.0/60.0.
        """
        super().__init__(physics_dt=physics_dt)
        self._scene_finalized = False
        self._current_task = None
        self._ground_plane_exists = add_ground_plane
        self._stage_units_in_meters = stage_units_in_meters
        self._scene = None
        if not global_vars.LAUNCHED_FROM_TERMINAL:
            self.create_new_stage()
        self._dc_interface = _dynamic_control.acquire_dynamic_control_interface()
        # TODO: double check the stage units are actually set properly
        # TODO: account for stage units properly across all new extensions
        return

    async def init_world_async(self):
        await self.create_new_stage_async()
        return

    async def create_new_stage_async(self):
        await super().create_new_stage_async(stage_units_in_meters=self._stage_units_in_meters)
        del self._scene
        self._scene = Scene(self.stage)
        if self.ground_plane_exists:
            self._scene.add_ground_plane(
                size=50.0 / self._stage_units_in_meters, thickness=0.5 / self._stage_units_in_meters
            )
        return

    def create_new_stage(self) -> Usd.Stage:
        stage = super().create_new_stage(stage_units_in_meters=self._stage_units_in_meters)
        del self._scene
        self._scene = Scene(self.stage)
        if self.ground_plane_exists:
            self._scene.add_ground_plane(
                size=50.0 / self._stage_units_in_meters, thickness=0.5 / self._stage_units_in_meters
            )
            self.start_simulation()
        return stage

    @property
    def ground_plane_exists(self):
        return self._ground_plane_exists

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
        if not global_vars.LAUNCHED_FROM_TERMINAL:
            self.play()
            # TODO: is this needed
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
        if self._current_task is not None:
            self._current_task.task_cleanup()
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
            self._current_task.task_cleanup()
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
        super().step(render=render)
        return
