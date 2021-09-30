# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

from omni.isaac.kit import SimulationApp

simulation_app = SimulationApp({"headless": True})

from omni.isaac.kit.simulation_context import SimulationContext
from omni.isaac.core.utils.nucleus_utils import find_nucleus_server
from omni.isaac.dynamic_control import _dynamic_control

_, nucleus_server = find_nucleus_server()
asset_path = nucleus_server + "/Isaac/Robots/Franka/franka_alt_fingers.usd"

simulation_context = SimulationContext(physics_dt=1.0 / 60.0)
simulation_context.create_new_stage(stage_units_in_meters=1.0)
simulation_context.add_usd_reference(asset_path, "/Franka")
# need to start simulation before getting any articulation..etc
simulation_context.start_simulation()
dc = _dynamic_control.acquire_dynamic_control_interface()
art = dc.get_articulation("/Franka")
dof_ptr = dc.find_articulation_dof(art, "panda_joint2")


def step_callback_1(step_size):
    dc.wake_up_articulation(art)
    dc.set_dof_position_target(dof_ptr, -1.5)
    return


def step_callback_2(step_size):
    dof_state = dc.get_dof_state(dof_ptr, _dynamic_control.STATE_POS)
    print("Current joint 2 position @ step " + str(simulation_context.time_step_index) + " : " + str(dof_state.pos))
    print("TIME: ", simulation_context.time)
    return


def editor_callback(event):
    print("Render Frame")


simulation_context.add_physics_callback("physics_callback_1", step_callback_1)
simulation_context.add_physics_callback("physics_callback_2", step_callback_2)
simulation_context.add_editor_callback("editor_callback", editor_callback)
simulation_context.stop()
simulation_context.play()
# Simulate 60 timesteps
for i in range(60):
    simulation_context.step(render=False)
# Render one frame
simulation_context.render()

simulation_context.stop()
simulation_app.close()
