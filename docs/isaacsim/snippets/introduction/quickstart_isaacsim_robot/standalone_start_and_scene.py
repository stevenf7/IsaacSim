from isaacsim import SimulationApp

simulation_app = SimulationApp({"headless": False})

import isaacsim.core.experimental.utils.stage as stage_utils
from isaacsim.core.experimental.objects import GroundPlane
from isaacsim.core.experimental.prims import Articulation, XformPrim
from isaacsim.storage.native import get_assets_root_path

assets_root_path = get_assets_root_path()
stage_utils.create_new_stage()
GroundPlane("/World/GroundPlane", positions=[0, 0, 0])

asset_path = assets_root_path + "/Isaac/Robots/FrankaRobotics/FrankaPanda/franka.usd"
stage_utils.add_reference_to_stage(usd_path=asset_path, path="/World/Arm")
arm_transform = XformPrim("/World/Arm")
arm_transform.set_world_poses(positions=[0.0, 1.0, 0.0])
arm = Articulation("/World/Arm")
