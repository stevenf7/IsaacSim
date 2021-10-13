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

from omni.isaac.core import SimulationContext
from omni.isaac.core.utils.nucleus_utils import find_nucleus_server

_, nucleus_server = find_nucleus_server()
asset_path = nucleus_server + "/Isaac/Robots/Franka/franka_alt_fingers.usd"

simulation_context = SimulationContext(physics_dt=1.0 / 60.0)
simulation_context.create_new_stage(stage_units_in_meters=1.0)
simulation_context.add_usd_reference(asset_path, "/Franka")
# need to start simulation before getting any articulation..etc
simulation_context.start_simulation()


def step_callback(step_size):
    print("simulate with step: ", step_size)
    return


def editor_callback(event):
    print("update app with step: ", event.payload["dt"])


simulation_context.add_physics_callback("physics_callback", step_callback)
simulation_context.add_editor_callback("editor_callback", editor_callback)
simulation_context.stop()
simulation_context.play()
print("start")
print("step physics once with a step size of 1/60 second")
simulation_context.step(render=False)

print("step physics once with a step size of 1/30 second")
simulation_context.set_physics_dt(1.0 / 30.0)
simulation_context.step(render=False)

print("step physics once with a step size of 1 second")
simulation_context.set_physics_dt(1.0)
simulation_context.step(render=False)

print("step physics & rendering once with a step size of 1/60 second")
simulation_context.set_physics_dt(1.0)
simulation_context.step(render=True)

print("step rendering a frame without stepping physics")
simulation_context.render()
print("cleanup and exit")
simulation_context.stop()
simulation_app.close()
