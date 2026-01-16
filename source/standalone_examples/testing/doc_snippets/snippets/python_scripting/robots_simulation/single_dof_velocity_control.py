import numpy as np
from isaacsim.core.experimental.prims import Articulation

articulation = Articulation("/Franka")
# Switch to velocity control mode
articulation.switch_dof_control_mode("velocity")
# Set the 'panda_joint4' DOF velocity to 0.25
articulation.set_dof_velocity_targets(0.25, dof_indices=articulation.get_dof_indices("panda_joint4"))
