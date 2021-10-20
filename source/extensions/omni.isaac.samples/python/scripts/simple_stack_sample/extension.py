# Copyright (c) 2018-2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

from omni.isaac.samples.scripts.base_sample import BaseSample
from omni.isaac.franka.tasks import Stacking
from omni.isaac.franka.controllers import StackingController
import asyncio
import os


class Extension(BaseSample):
    def on_startup(self, ext_id):
        super().on_startup(ext_id)
        # TODO: change doc link when available
        # TODO: change physics properties of the cubes
        super()._on_startup(
            menu_name="Controlling",
            submenu_name="Manipulation",
            name="Simple Stack",
            buttons_mapping={"Start Stacking": self._on_stacking_event},
            title="Stack Two Cubes",
            doc_link="https://docs.omniverse.nvidia.com/app_isaacsim/app_isaacsim/sample_urdf_import.html",
            overview="This Example shows how to stack two cubes using Franka robot in Isaac Sim.\n\nPress the 'Open in IDE' button to view the source code.",
            file_path=os.path.abspath(__file__),
        )
        self._controller = None
        self._articulation_controller = None
        return

    def _load_task(self):
        return Stacking()

    def _setup_controllers(self):
        my_franka = self._world.scene.get_object("my_franka")
        my_franka = self._world.get_current_task()
        self._controller = StackingController(
            name="pick_place_controller",
            gripper_dof_indices=my_franka.gripper.dof_indices,
            robot_prim_path=my_franka.prim_path,
            picking_order_cube_names=my_franka.get_cube_names(),
            robot_observation_name="my_franka",
        )
        self._articulation_controller = my_franka.get_articulation_controller()
        return

    def _on_stacking_event(self):
        async def _on_stacking_event_async():
            self._world.add_physics_callback("sim_step", self._on_stacking_simulation_step)
            self._buttons["Start Stacking"].enabled = False
            await self._world.play_async()

        asyncio.ensure_future(_on_stacking_event_async())
        return

    def _on_stacking_simulation_step(self, step_size):
        observations = self._world.get_observations()
        actions = self._controller.forward(observations=observations)
        self._articulation_controller.apply_action(actions)
        if self._controller.is_done():
            self._world.pause()
        return

    def _reset_call(self):
        self._controller.reset()
        return
