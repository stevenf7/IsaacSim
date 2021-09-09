# Copyright (c) 2018-2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

from omni.isaac.samples.scripts.base_sample import BaseSample
from omni.isaac.franka.tasks import TargetFollower
from omni.isaac.franka.controllers import RMPFlowIKSolver
import asyncio
import os


class Extension(BaseSample):
    def on_startup(self):
        super().on_startup()
        # TODO: change doc link when available
        super()._on_startup(
            menu_name="Controlling",
            submenu_name="Manipulation",
            name="Follow Target",
            buttons_mapping={
                "Follow Target": self._on_follow_target_event,
                "Add Obstacle": self._on_add_obstacle_event,
                "Remove Obstacle": self._on_remove_obstacle_event,
            },
            extension_path=os.path.abspath(__file__),
            title="Follow Target Controller",
            doc_link="https://docs.omniverse.nvidia.com/app_isaacsim/app_isaacsim/sample_urdf_import.html",
            date="09/14/2021",
            overview="This Example shows how to follow a target using Franka robot in Isaac Sim.\n\nPress the 'Open in IDE' button to view the source code.",
        )
        self._controller = None
        self._articulation_controller = None
        return

    def _load_task(self):
        return TargetFollower()

    def _setup_controllers(self):
        my_franka = self._world.scene.get_object("my_franka")
        extension_id = self._world.get_extension_id("omni.isaac.motion_generation")
        mg_extension_path = self._world.get_extension_path(ext_id=extension_id)
        self._controller = RMPFlowIKSolver(
            name="ik_controller",
            dc_interface=self._world.dc_interface,
            stage=self._world.stage,
            robot_prim=my_franka.prim,
            mg_extension_path=mg_extension_path,
        )
        self._articulation_controller = my_franka.get_articulation_controller()
        return

    def _on_add_obstacle_event(self):
        cube = self._task.add_obstacle()
        # TODO: verify that it actually works?
        self._controller.add_cube_obstacle(cube.prim)
        self._buttons["Remove Obstacle"].enabled = True
        return

    def _on_remove_obstacle_event(self):
        obstacle_to_delete = self._task.get_obstacle_to_delete()
        self._controller.remove_cube_obstacle(obstacle_to_delete.prim)
        self._task.remove_obstacle()
        if not self._task.obstacles_exist():
            self._buttons["Remove Obstacle"].enabled = False
        return

    def _on_follow_target_event(self):
        async def _on_follow_target_event_async():
            self._world.add_physics_callback(self._on_follow_target_simulation_step)
            self._buttons["Follow Target"].enabled = False
            await self._world.play_async()

        asyncio.ensure_future(_on_follow_target_event_async())
        return

    def _on_follow_target_simulation_step(self, step_size):
        observations = self._world.get_observations()
        actions = self._controller.forward(
            target_end_effector_position=observations["target_cube"]["position"],
            current_joint_positions=observations["my_franka"]["joint_positions"],
        )
        self._articulation_controller.apply_action(actions)
        return

    def _reset_call(self):
        # TODO: on reset the motion generation policy needs to clear the world function? missing
        self._controller.reset()
        self._buttons["Remove Obstacle"].enabled = False
        return
