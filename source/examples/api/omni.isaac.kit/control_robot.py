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

from omni.isaac.kit.simulation import SimulationContext
from omni.isaac.utils.scripts.nucleus_utils import find_nucleus_server
from omni.isaac.dynamic_control import _dynamic_control

_, nucleus_server = find_nucleus_server()
asset_path = nucleus_server + "/Isaac/Robots/Franka/franka_alt_fingers.usd"

simulation_context = SimulationContext()
simulation_context.create_new_stage()
simulation_context.add_usd_reference(asset_path, "/Franka")

# need to start simulation before getting any articulation..etc
simulation_context.start_simulation()
dc = _dynamic_control.acquire_dynamic_control_interface()
art = dc.get_articulation("/Franka")
dof_ptr = dc.find_articulation_dof(art, "panda_joint2")

simulation_context.play()
# NOTE: after play, one step is needed for simulation to be running and to be able to wake up articulation..etc
simulation_context.step(render=True)
for i in range(1000):
    dc.wake_up_articulation(art)
    dc.set_dof_position_target(dof_ptr, -1.5)
    simulation_context.step(render=True)

simulation_context.stop()
simulation_app.close()
