# -- Test setup --
import isaacsim.core.experimental.utils.stage as stage_utils
import omni.kit.app
import omni.timeline
from isaacsim.core.experimental.prims import Articulation
from isaacsim.storage.native import get_assets_root_path

assets_root_path = get_assets_root_path()
asset_path = assets_root_path + "/Isaac/Robots/FrankaRobotics/FrankaPanda/franka.usd"
stage_utils.add_reference_to_stage(usd_path=asset_path, path="/World/Arm")
arm_handle = Articulation("/World/Arm")

# Start physics so joint data is available
omni.timeline.get_timeline_interface().play()
for _ in range(3):
    omni.kit.app.get_app().update()
# -- End test setup --

# Requires physics running (Press Play first). arm_handle from add_franka_to_stage snippet.
print("Number of joints:", arm_handle.num_dofs)
print("Joint names:", arm_handle.dof_names)
positions = arm_handle.get_dof_positions()
print("Joint positions:", positions)

# -- Test cleanup --
omni.timeline.get_timeline_interface().stop()
