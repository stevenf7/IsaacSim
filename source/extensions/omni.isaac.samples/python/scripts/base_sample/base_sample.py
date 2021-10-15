# Copyright (c) 2018-2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
from omni.isaac.core import World
from omni.isaac.core.utils.stage import create_new_stage_async
import omni.usd
import gc
from abc import abstractmethod


class BaseSample(object):
    def __init__(self) -> None:
        self._world = None
        self._task = None
        self._world_settings = None

    def set_world_settings(self, settings):
        self._world_settings = settings
        return

    async def load_world_async(self):
        # await create_new_stage_async()
        if World.instance() is None:
            self._world = World(**self._world_settings)
            await self._world.init_simulation_context_async()
            self._task = self._load_task()
            if self._task is not None:
                self._world.load_task(self._task)
        else:
            self._world = World.instance()
            self._task = self._world.get_current_task()
        await self._world.reset_async()
        if self._task is not None:
            self._world.add_physics_callback("task_step", self.task_simulation_step)
        await self.setup_load()
        await self.setup_reset()
        return

    async def reset_async(self):
        await self._world.reset_async()
        await omni.kit.app.get_app().next_update_async()
        await self.setup_reset()
        self._world.remove_physics_callback("task_step")
        if self._world._scene_finalized and self._task is not None:
            self._world.add_physics_callback("task_step", self.task_simulation_step)

    @abstractmethod
    def _load_task(self):
        return None

    @abstractmethod
    async def setup_load(self):
        return

    @abstractmethod
    async def setup_reset(self):
        return

    def task_simulation_step(self, step_size):
        self._task.step(self._world.current_time_step_index, self._world.current_time)
        return

    def world_cleanup(self):
        self._world.stop()
        self._world.clear_all_callbacks()
        self._task = None
        return

    async def clear_async(self):
        await create_new_stage_async()
        if self._world is not None:
            self._world.clear_all_callbacks()
            self._world.clear_instance()
            gc.collect()
            self._world = None
        return
