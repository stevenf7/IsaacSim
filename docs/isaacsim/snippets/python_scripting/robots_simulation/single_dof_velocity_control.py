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

articulation = Articulation("/Franka")
# Switch to velocity control mode
articulation.switch_dof_control_mode("velocity")
# Set the 'panda_joint4' DOF velocity to 0.25
articulation.set_dof_velocity_targets(0.25, dof_indices=articulation.get_dof_indices("panda_joint4"))

# -- Test cleanup --
omni.timeline.get_timeline_interface().stop()
