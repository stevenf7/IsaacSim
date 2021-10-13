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
from omni.isaac.jetbot.controllers import SimpleController, SimpleContollerCommand
from omni.isaac.core.utils.stage import add_usd_reference
from omni.isaac.core.utils.nucleus_utils import find_nucleus_server
from omni.isaac.core.prims import XFormPrim
import numpy as np
import carb

# TODO: changed this when asset gets converted
my_world = World(stage_units_in_meters=0.01)
my_jetbot = my_world.scene.add(Jetbot(stage=my_world.stage, prim_path="/World/Jetbot", name="my_jetbot"))
result, nucleus_server = find_nucleus_server()
if result is False:
    carb.log_error("Could not find nucleus server with /Isaac folder")
prim = add_usd_reference(
    usd_path=nucleus_server + "/Isaac/Environments/Grid/gridroom_curved.usd", prim_path="/World/background"
)
# TODO: change with new USD
XFormPrim(prim, "background", position=np.array([0, 0, -9]))
my_controller = SimpleController(name="simple_control")
my_world.reset()

i = 0
while True:
    if i >= 0 and i < 1000:
        my_jetbot.apply_wheel_actions(my_controller.forward(SimpleContollerCommand.FORWARD))
    elif i >= 1000 and i < 1300:
        my_jetbot.apply_wheel_actions(my_controller.forward(SimpleContollerCommand.LEFT))
    elif i >= 1300 and i < 2000:
        my_jetbot.apply_wheel_actions(my_controller.forward(SimpleContollerCommand.FORWARD))
    elif i == 2000:
        i = 0
    my_world.step(render=True)
    i += 1


simulation_app.close()
