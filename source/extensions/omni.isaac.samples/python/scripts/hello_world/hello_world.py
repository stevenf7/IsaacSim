# Copyright (c) 2020-2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

from omni.isaac.samples.scripts.base_sample import BaseSample
import numpy as np
from omni.isaac.core.objects import DynamicCube, FixedCube


class HelloWorld(BaseSample):
    def __init__(self) -> None:
        super().__init__()
        return

    def setup_scene(self):
        world = self.get_world()
        world.scene.add_ground_plane()
        dynamic_cube = world.scene.add(
            DynamicCube(
                prim_path="/World/cube",
                name="my_first_cube",
                position=np.array([0, 0, 0.8]) * 100,
                size=0.2 * 100,
                color=np.array([1.0, 1.0, 1.0]),
            )
        )
        fixed_cube = world.scene.add(
            FixedCube(
                prim_path="/World/fixed_cube",
                name="my_first_fixed_cube",
                position=np.array([0, 0, 0.5]) * 100,
                size=0.2 * 100,
                color=np.array([0, 0.5, 0]),
            )
        )
        return

    async def setup_post_load(self):
        return

    async def setup_post_reset(self):
        return

    def world_cleanup(self):
        return
