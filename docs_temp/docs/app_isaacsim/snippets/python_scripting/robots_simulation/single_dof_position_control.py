import numpy as np
from isaacsim.core.experimental.prims import Articulation

articulation = Articulation("/Franka")
# Set the 'panda_finger_joint1' DOF position to 0.04.
# The 'panda_finger_joint2' will mimic the value, as they are linked
articulation.set_dof_position_targets(0.04, dof_indices=articulation.get_dof_indices("panda_finger_joint1"))
