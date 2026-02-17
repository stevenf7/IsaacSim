from isaacsim.core.rendering_manager import RenderingManager
from isaacsim.core.simulation_manager import SimulationManager

# Move the arm
arm.set_dof_positions([-1.5, 0.0, 0.0, -1.5, 0.0, 1.5, 0.5, 0.04, 0.04])

for _ in range(100):
    SimulationManager.step()
    RenderingManager.render()
    simulation_app.update()
    # Print joint positions at every physics step
    joint_positions = arm.get_dof_positions()
    print("Joint positions:", joint_positions)
