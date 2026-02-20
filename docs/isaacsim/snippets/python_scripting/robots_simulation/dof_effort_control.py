import numpy as np
from isaacsim.core.experimental.prims import Articulation

articulation = Articulation("/Franka")
# Switch to effort control mode
articulation.switch_dof_control_mode("effort")
# Set all DOF efforts to random values between -100 and 100
articulation.set_dof_efforts(100 * (np.random.rand(9) * 2 - 1))
