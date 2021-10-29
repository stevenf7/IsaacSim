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
import gc
from abc import abstractmethod


class BaseSample(object):
    def __init__(self) -> None:
        self._world = None
        self._current_tasks = None
        self._world_settings = None

    def get_world(self):
        return self._world

    def set_world_settings(self, settings):
        self._world_settings = settings
        return

    async def load_world_async(self):
        # await create_new_stage_async()
        if World.instance() is None:
            self._world = World(**self._world_settings)
            await self._world.init_simulation_context_async()
            self.setup_scene()
        else:
            self._world = World.instance()
        self._current_tasks = self._world.get_current_tasks()
        await self._world.reset_async()
        if len(self._current_tasks) > 0:
            self._world.add_physics_callback("tasks_step", self._world.step_async)
        await self.setup_post_load()
        await self.setup_post_reset()
        return

    async def reset_async(self):
        await self._world.reset_async()
        if self._world._scene_finalized and len(self._current_tasks) > 0:
            self._world.remove_physics_callback("tasks_step")
            self._world.add_physics_callback("tasks_step", self._world.step_async)
        await self.setup_post_reset()
        return

    @abstractmethod
    def setup_scene(self, scene):
        # used to setup anything in the world, called before add tasks
        return

    @abstractmethod
    async def setup_post_load(self):
        # called after first reset of the world when pressing load
        return

    @abstractmethod
    async def setup_post_reset(self):
        # called 1) in load after normal reset of the world as well as 2) in reset button after resetting the world
        return

    @abstractmethod
    async def setup_post_clear(self):
        # called in clear button after creating a new stage and clearing the instance of the world with its callbacks
        return

    def _world_cleanup(self):
        self._world.stop()
        self._world.clear_all_callbacks()
        self._current_tasks = None
        self.world_cleanup()
        return

    def world_cleanup(self):
        return

    async def clear_async(self):
        await create_new_stage_async()
        if self._world is not None:
            self._world_cleanup()
            self._world.clear_instance()
            self._world = None
            gc.collect()
        await self.setup_post_clear()
        return
