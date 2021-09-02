# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
from omni.isaac.kit import SimulationApp

simulation_app = SimulationApp({"headless": False})

from omni.isaac.franka import Franka
from omni.isaac.core import World

my_world = World()
my_franka = my_world.scene.add(Franka(stage=my_world.stage, prim_path="/World/Franka", name="my_franka"))
my_world.reset()

i = 0
while True:
    i += 1
    if i < 500:
        my_franka.open_gripper()
    if i > 500:
        my_franka.close_gripper()
    if i == 1000:
        i = 0
    my_world.step(render=True)


simulation_app.close()
