# Copyright (c) 2020-2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

import os
from omni.isaac.samples.scripts.base_sample import BaseSampleExtension
from omni.isaac.samples.scripts.follow_target import FollowTarget
import asyncio


class FollowTargetExtension(BaseSampleExtension):
    def on_startup(self, ext_id: str):
        super().on_startup(ext_id)
        super().start_extension(
            menu_name="Controlling",
            submenu_name="Manipulation",
            name="Follow Target",
            buttons_mapping={
                "Follow Target": self._on_follow_target_event,
                "Add Obstacle": self._on_add_obstacle_event,
                "Remove Obstacle": self._on_remove_obstacle_event,
            },
            title="Follow Target Controller",
            doc_link="https://docs.omniverse.nvidia.com/app_isaacsim/app_isaacsim/sample_urdf_import.html",
            overview="This Example shows how to follow a target using Franka robot in Isaac Sim.\n\nPress the 'Open in IDE' button to view the source code.",
            stage_units_in_meters=0.01,
            sample=FollowTarget(),
            file_path=os.path.abspath(__file__),
        )

    def _on_add_obstacle_event(self):
        world = self.get_world()
        current_task = list(world.get_current_tasks().values())[0]
        cube = current_task.add_obstacle()
        # TODO: verify that it actually works?
        self.sample._controller.add_cube_obstacle(cube.prim)
        self.get_buttons()["Remove Obstacle"].enabled = True
        return

    def _on_follow_target_event(self):
        async def _on_follow_target_event_async():
            world = self.get_world()
            world.add_physics_callback("sim_step", self.sample._on_follow_target_simulation_step)
            self.get_buttons()["Follow Target"].enabled = False
            await world.play_async()

        asyncio.ensure_future(_on_follow_target_event_async())
        return

    def _on_remove_obstacle_event(self):
        world = self.get_world()
        current_task = list(world.get_current_tasks().values())[0]
        obstacle_to_delete = current_task.get_obstacle_to_delete()
        self.sample._controller.remove_cube_obstacle(obstacle_to_delete.prim)
        current_task.remove_obstacle()
        if not current_task.obstacles_exist():
            self.get_buttons()["Remove Obstacle"].enabled = False
        return

    def on_reset(self):
        world = self.get_world()
        world.remove_physics_callback("sim_step")
        self.get_buttons()["Follow Target"].enabled = True
        return
