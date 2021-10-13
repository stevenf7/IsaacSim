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

from omni.isaac.core import SimulationContext
from omni.isaac.core.utils.nucleus_utils import find_nucleus_server

_, nucleus_server = find_nucleus_server()
asset_path = nucleus_server + "/Isaac/Robots/Franka/franka_alt_fingers.usd"
# TODO: change camera view if the assets will stay in cm
simulation_context = SimulationContext()
simulation_context.create_new_stage()
simulation_context.add_usd_reference(asset_path, "/Franka")
# need to start simulation before getting any articulation..etc
simulation_context.start_simulation()
simulation_context.play()

for i in range(10000):
    simulation_context.step(render=True)

simulation_context.stop()
simulation_app.close()
