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
from omni.isaac.core.materials import OmniPBR, OmniGlass
from omni.isaac.core.utils.nucleus import find_nucleus_server
import random
import carb


result, nucleus_server = find_nucleus_server()
if result is False:
    carb.log_error("Could not find nucleus server with /Isaac folder")
asset_path = nucleus_server + "/Isaac/Materials/Textures/TGen/bubbles_2.png"

my_world = World(stage_units_in_meters=0.01)

textured_material = OmniPBR(
    prim_path="/World/visual_cube_material",
    name="omni_pbr",
    color=np.array([1, 0, 0]),
    texture_path=asset_path,
    texture_scale=[1.0, 1.0],
)

glass = OmniGlass(
    prim_path=f"/World/visual_cube_material_2",
    ior=1.25,
    depth=0.001,
    thin_walled=False,
    color=np.array([random.random(), random.random(), random.random()]),
)

cube_1 = my_world.scene.add(
    VisualCuboid(
        prim_path="/new_cube_1",
        name="visual_cube",
        position=np.array([0, 0, 0.5]) * 100,
        size=np.array([1, 1, 1]) * 100,
        color=np.array([255, 255, 255]),
        visual_material=textured_material,
    )
)

cube_2 = my_world.scene.add(
    VisualCuboid(
        prim_path="/new_cube_2",
        name="visual_cube_2",
        position=np.array([2, 0.39, 0.5]) * 100,
        size=np.array([1, 1, 1]) * 100,
        color=np.array([255, 255, 255]),
        visual_material=glass,
    )
)

visual_material = cube_2.get_applied_visual_material()
visual_material.set_color(np.array([1.0, 0.5, 0.0]))

my_world.scene.add_ground_plane()

my_world.reset()
for i in range(10000):
    my_world.step(render=True)

simulation_app.close()
