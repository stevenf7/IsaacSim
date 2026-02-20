import numpy as np
from isaacsim.core.experimental.prims import Articulation

articulation = Articulation("/Franka")
# Switch to velocity control mode
articulation.switch_dof_control_mode("velocity")
# Set all DOF velocities to random values between -10 and 10
articulation.set_dof_velocity_targets(10 * (np.random.rand(9) * 2 - 1))
