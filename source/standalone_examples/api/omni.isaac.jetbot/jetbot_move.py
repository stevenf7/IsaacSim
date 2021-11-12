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

from omni.isaac.jetbot import Jetbot
from omni.isaac.core import World
from omni.isaac.jetbot.controllers import DifferentialController
import numpy as np

my_world = World(stage_units_in_meters=0.01)
my_jetbot = my_world.scene.add(Jetbot(prim_path="/World/Jetbot", name="my_jetbot", position=np.array([0, 0.0, 2.0])))
my_world.scene.add_default_ground_plane()
my_controller = DifferentialController(name="simple_control")
my_world.reset()

i = 0
while simulation_app.is_running():
    my_world.step(render=True)
    if my_world.is_playing():
        if my_world.current_time_step_index == 0:
            my_world.reset()
            my_controller.reset()
        if i >= 0 and i < 1000:
            # forward
            my_jetbot.apply_wheel_actions(my_controller.forward(command=[5, 0]))
            print(my_jetbot.get_linear_velocity())
        elif i >= 1000 and i < 1300:
            # rotate
            my_jetbot.apply_wheel_actions(my_controller.forward(command=[0.0, np.pi / 12]))
            print(my_jetbot.get_angular_velocity())
        elif i >= 1300 and i < 2000:
            # forward
            my_jetbot.apply_wheel_actions(my_controller.forward(command=[5, 0]))
        elif i == 2000:
            i = 0
        i += 1


simulation_app.close()
