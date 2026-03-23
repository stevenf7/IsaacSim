# -- Test setup --
import isaacsim.core.experimental.utils.stage as stage_utils
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
# Get articulation information
print("DOF count:", articulation.num_dofs)
print("DOF names:", articulation.dof_names)
print("DOF paths:", articulation.dof_paths)
print("DOF types:", articulation.dof_types)
print("Link count:", articulation.num_links)
print("Link names:", articulation.link_names)
print("Link paths:", articulation.link_paths)

# -- Test cleanup --
omni.timeline.get_timeline_interface().stop()
