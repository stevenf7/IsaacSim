from omni.isaac.kit import SimulationApp

simulation_app = SimulationApp({"headless": False})

from omni.isaac.kit.simulation import SimulationContext
from omni.isaac.utils.scripts.nucleus_utils import find_nucleus_server
from omni.isaac.dynamic_control import _dynamic_control

_, nucleus_server = find_nucleus_server()
asset_path = nucleus_server + "/Isaac/Robots/Franka/franka_alt_fingers.usd"

simulation_context = SimulationContext()
simulation_context.create_new_stage()
simulation_context.open_usd(asset_path, "/Franka")

# need to start simulation before getting any articulation..etc
simulation_context.start_simulation()
dc = _dynamic_control.acquire_dynamic_control_interface()
art = dc.get_articulation("/Franka")
dof_ptr = dc.find_articulation_dof(art, "panda_joint2")

simulation_context.play()
for i in range(1000):
    dc.wake_up_articulation(art)
    dc.set_dof_position_target(dof_ptr, -1.5)
    simulation_context.step(render=True)

simulation_context.stop()
simulation_app.close()
