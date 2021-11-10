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

from omni.isaac.kaya import Kaya
from omni.isaac.core import World
from omni.isaac.kaya.controllers import HolonomicController
import numpy as np

# TODO: changed this when asset gets converted
my_world = World(stage_units_in_meters=0.01)
my_kaya = my_world.scene.add(Kaya(prim_path="/World/Kaya", name="my_kaya", position=np.array([0, 0.0, 2.0])))
my_world.scene.add_default_ground_plane()
my_controller = HolonomicController(name="holonomic_controller")
my_world.reset()

i = 0
while simulation_app.is_running():
    my_world.step(render=True)
    if my_world.is_simulating():
        if i >= 0 and i < 1000:
            # TODO: change with new USD
            my_kaya.apply_wheel_actions(my_controller.forward(x_velocity=4.0, y_velocity=0.0, theta_velocity=0.0))
        elif i >= 1000 and i < 2000:
            # TODO: change with new USD
            my_kaya.apply_wheel_actions(my_controller.forward(x_velocity=0, y_velocity=4.0, theta_velocity=0.0))
        elif i >= 2000 and i < 3000:
            # TODO: change with new USD
            my_kaya.apply_wheel_actions(my_controller.forward(x_velocity=0.0, y_velocity=0.0, theta_velocity=0.5))
        elif i == 3000:
            i = 0
        i += 1


simulation_app.close()
