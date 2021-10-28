# Copyright (c) 2020-2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

import os
from omni.isaac.samples.scripts.base_sample import BaseSampleExtension
from omni.isaac.samples.scripts.simple_stack import SimpleStack
import asyncio


class SimpleStackExtension(BaseSampleExtension):
    def on_startup(self, ext_id: str):
        super().on_startup(ext_id)
        super().start_extension(
            menu_name="Controlling",
            submenu_name="Manipulation",
            name="Simple Stack",
            buttons_mapping={"Start Stacking": self._on_stacking_event},
            title="Stack Two Cubes",
            doc_link="https://docs.omniverse.nvidia.com/app_isaacsim/app_isaacsim/sample_urdf_import.html",
            overview="This Example shows how to stack two cubes using Franka robot in Isaac Sim.\n\nPress the 'Open in IDE' button to view the source code.",
            stage_units_in_meters=0.01,
            sample=SimpleStack(),
            file_path=os.path.abspath(__file__),
        )

    def _on_stacking_event(self):
        async def _on_stacking_event_async():
            world = self.get_world()
            world.add_physics_callback("sim_step", self.sample._on_stacking_simulation_step)
            self.get_buttons()["Start Stacking"].enabled = False
            await world.play_async()

        asyncio.ensure_future(_on_stacking_event_async())
        return

    def on_reset(self):
        world = self.get_world()
        if world.physics_callback_exists("sim_step"):
            world.remove_physics_callback("sim_step")
        self.get_buttons()["Start Stacking"].enabled = True
        return
