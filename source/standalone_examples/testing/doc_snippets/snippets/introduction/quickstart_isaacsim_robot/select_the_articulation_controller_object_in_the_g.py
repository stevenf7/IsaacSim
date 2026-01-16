import carb
import numpy as np
from isaacsim.core.prims import Articulation
from isaacsim.core.utils.stage import add_reference_to_stage
from isaacsim.storage.native import get_assets_root_path

assets_root_path = get_assets_root_path()
if assets_root_path is None:
    carb.log_error("Could not find Isaac Sim assets folder")
usd_path = assets_root_path + "/Isaac/Robots/FrankaRobotics/FrankaPanda/franka.usd"
prim_path = "/World/Arm"

add_reference_to_stage(usd_path=usd_path, prim_path=prim_path)
arm_handle = Articulation(prim_paths_expr=prim_path, name="Arm")
arm_handle.set_world_poses(positions=np.array([[0, -1, 0]]))
