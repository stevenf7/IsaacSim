from omni.isaac.kit import SimulationApp

simulation_app = SimulationApp({"headless": True})

from omni.isaac.kit.simulation import SimulationContext
from omni.isaac.utils.scripts.nucleus_utils import find_nucleus_server
from omni.isaac.dynamic_control import _dynamic_control

_, nucleus_server = find_nucleus_server()
asset_path = nucleus_server + "/Isaac/Robots/Franka/franka_alt_fingers.usd"

simulation_context = SimulationContext()
simulation_context.create_new_stage()
simulation_context.open_usd(asset_path, "/Franka")

# need to start simulation before getting any articulation..etc
simulation_context.set_physics_dt(dt=1.0 / 100.0)
simulation_context.start_simulation()
dc = _dynamic_control.acquire_dynamic_control_interface()
art = dc.get_articulation("/Franka")
dof_ptr = dc.find_articulation_dof(art, "panda_joint2")


def step_callback_1():
    dc.wake_up_articulation(art)
    dc.set_dof_position_target(dof_ptr, -1.5)
    return


def step_callback_2():
    dof_state = dc.get_dof_state(dof_ptr)
    print("Current joint 2 position @ step " + str(simulation_context.time_step_index) + " : " + str(dof_state.pos))
    return


# Note: running using physics callbacks are not guaranteed to run with the specified dt, it might run
# faster or slower depends on the gpu specs
simulation_context.add_physics_callback(step_callback_1)
simulation_context.add_physics_callback(step_callback_2)
simulation_context.play()
for i in range(20):
    simulation_context.step(render=False)

simulation_context.stop()
simulation_app.close()
