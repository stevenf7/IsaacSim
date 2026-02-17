import numpy as np
from isaacsim.core.experimental.prims import Articulation

articulation = Articulation("/Franka")
# Set all DOF positions to random values between -1 and 1
articulation.set_dof_position_targets(np.random.rand(9) * 2 - 1)
