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
# Set the 'panda_finger_joint1' DOF position to 0.04.
# The 'panda_finger_joint2' will mimic the value, as they are linked
articulation.set_dof_position_targets(0.04, dof_indices=articulation.get_dof_indices("panda_finger_joint1"))

# -- Test cleanup --
omni.timeline.get_timeline_interface().stop()
