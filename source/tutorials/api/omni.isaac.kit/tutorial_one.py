from omni.isaac.kit import SimulationApp

simulation_app = SimulationApp({"headless": False})

from omni.isaac.kit.simulation import SimulationContext
from omni.isaac.utils.scripts.nucleus_utils import find_nucleus_server

_, nucleus_server = find_nucleus_server()
asset_path = nucleus_server + "/Isaac/Robots/Franka/franka_alt_fingers.usd"

simulation_context = SimulationContext()
simulation_context.create_new_stage()
simulation_context.open_usd(asset_path, "/Franka")
# need to start simulation before getting any articulation..etc
simulation_context.start_simulation()
simulation_context.play()

for i in range(100):
    simulation_context.step(render=True)

simulation_context.stop()
simulation_app.close()
