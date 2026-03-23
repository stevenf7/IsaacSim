# -- Test setup --
import isaacsim.core.experimental.utils.stage as stage_utils
import omni.kit.app
import omni.timeline
from isaacsim.core.experimental.prims import Articulation
from isaacsim.storage.native import get_assets_root_path

assets_root_path = get_assets_root_path()
asset_path = assets_root_path + "/Isaac/Robots/FrankaRobotics/FrankaPanda/franka.usd"
stage_utils.add_reference_to_stage(usd_path=asset_path, path="/World/Robot")

omni.timeline.get_timeline_interface().play()
for _ in range(3):
    omni.kit.app.get_app().update()
# -- End test setup --

# Open your USD and PLAY the simulation before running this snippet
# Change the path to the robot you want to inspect
prim = Articulation(paths="/World/Robot")
print(str(prim.dof_names))

# -- Test cleanup --
omni.timeline.get_timeline_interface().stop()
