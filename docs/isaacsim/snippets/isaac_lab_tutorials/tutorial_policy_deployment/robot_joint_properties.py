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
print("DOF names:", prim.dof_names)
print("DOF types:", prim.dof_types)
print("DOF limits:", prim.get_dof_limits())
print("DOF gains (stiffness, damping):", prim.get_dof_gains())
print("DOF max efforts:", prim.get_dof_max_efforts())
print("DOF max velocities:", prim.get_dof_max_velocities())
print("DOF drive types:", prim.get_dof_drive_types())
print("DOF friction:", prim.get_dof_friction_properties())
print("DOF armatures:", prim.get_dof_armatures())

# -- Test cleanup --
omni.timeline.get_timeline_interface().stop()
