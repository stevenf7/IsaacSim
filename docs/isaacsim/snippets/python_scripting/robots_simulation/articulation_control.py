# -- Test setup --
import isaacsim.core.experimental.utils.stage as stage_utils
import numpy as np
import omni.kit.app
import omni.timeline
from isaacsim.core.experimental.prims import Articulation
from isaacsim.storage.native import get_assets_root_path

# Load Franka robot
assets_root_path = get_assets_root_path()
asset_path = assets_root_path + "/Isaac/Robots/FrankaRobotics/FrankaPanda/franka.usd"
stage_utils.add_reference_to_stage(usd_path=asset_path, path="/Franka")

omni.timeline.get_timeline_interface().play()
for _ in range(3):
    omni.kit.app.get_app().update()
# -- End test setup --

# [query-articulation]
from isaacsim.core.experimental.prims import Articulation

articulation = Articulation("/Franka")
# Get articulation information
print("DOF count:", articulation.num_dofs)
print("DOF names:", articulation.dof_names)
print("DOF paths:", articulation.dof_paths)
print("DOF types:", articulation.dof_types)
print("Link count:", articulation.num_links)
print("Link names:", articulation.link_names)
print("Link paths:", articulation.link_paths)
# [/query-articulation]

# [read-dof-states]
from isaacsim.core.experimental.prims import Articulation

articulation = Articulation("/Franka")
# Get all DOF states
print("DOF positions:", articulation.get_dof_positions())
print("DOF velocities:", articulation.get_dof_velocities())
print("DOF efforts:", articulation.get_dof_efforts())
# [/read-dof-states]

# [dof-position-control]
import numpy as np
from isaacsim.core.experimental.prims import Articulation

articulation = Articulation("/Franka")
# Set all DOF positions to random values between -1 and 1
articulation.set_dof_position_targets(np.random.rand(9) * 2 - 1)
# [/dof-position-control]

# [single-dof-position-control]
from isaacsim.core.experimental.prims import Articulation

articulation = Articulation("/Franka")
# Set the 'panda_finger_joint1' DOF position to 0.04.
# The 'panda_finger_joint2' will mimic the value, as they are linked
articulation.set_dof_position_targets(0.04, dof_indices=articulation.get_dof_indices("panda_finger_joint1"))
# [/single-dof-position-control]

# [velocity-control]
import numpy as np
from isaacsim.core.experimental.prims import Articulation

articulation = Articulation("/Franka")
# Switch to velocity control mode
articulation.switch_dof_control_mode("velocity")
# Set all DOF velocities to random values between -10 and 10
articulation.set_dof_velocity_targets(10 * (np.random.rand(9) * 2 - 1))
# [/velocity-control]

# [single-dof-velocity-control]
from isaacsim.core.experimental.prims import Articulation

articulation = Articulation("/Franka")
# Switch to velocity control mode
articulation.switch_dof_control_mode("velocity")
# Set the 'panda_joint4' DOF velocity to 0.25
articulation.set_dof_velocity_targets(0.25, dof_indices=articulation.get_dof_indices("panda_joint4"))
# [/single-dof-velocity-control]

# [effort-control]
import numpy as np
from isaacsim.core.experimental.prims import Articulation

articulation = Articulation("/Franka")
# Switch to effort control mode
articulation.switch_dof_control_mode("effort")
# Set all DOF efforts to random values between -100 and 100
articulation.set_dof_efforts(100 * (np.random.rand(9) * 2 - 1))
# [/effort-control]

# -- Test cleanup --
omni.timeline.get_timeline_interface().stop()
