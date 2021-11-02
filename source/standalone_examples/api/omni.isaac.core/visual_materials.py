# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

from omni.isaac.kit import SimulationApp
import numpy as np

simulation_app = SimulationApp({"headless": False})

from omni.isaac.core import World
from omni.isaac.core.objects import VisualCuboid
from omni.isaac.core.materials import OmniGlass

my_world = World(stage_units_in_meters=0.01)

glass = OmniGlass(
    prim_path="/World/visual_cube_material",
    name="glass_name",
    ior=1.25,
    depth=1.0,
    thin_walled=True,
    color=np.array([1, 0, 0]),
)

cube_1 = my_world.scene.add(
    VisualCuboid(
        prim_path="/new_cube_1",
        name="visual_cube",
        position=np.array([0, 0, 0.5]) * 100,
        size=np.array([0.3, 0.3, 0.3]) * 100,
        color=np.array([255, 255, 255]),
        visual_material=glass,
    )
)

visual_material = cube_1.get_applied_visual_material()
visual_material.set_color(np.array([1.0, 0.5, 0.0]))

my_world.scene.add_ground_plane()

for i in range(5):
    my_world.reset()
    for i in range(1000):
        my_world.step(render=True)

simulation_app.close()
