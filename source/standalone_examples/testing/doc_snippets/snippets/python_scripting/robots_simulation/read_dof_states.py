from isaacsim.core.experimental.prims import Articulation

articulation = Articulation("/Franka")
# Get all DOF states
print("DOF positions:", articulation.get_dof_positions())
print("DOF velocities:", articulation.get_dof_velocities())
print("DOF efforts:", articulation.get_dof_efforts())
