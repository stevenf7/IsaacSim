import isaacsim.core.utils.stage as stage_utils
from isaacsim.core.prims import SingleArticulation

usd_path = "/Path/To/Robots/FrankaRobotics/FrankaPanda/franka.usd"
prim_path = "/World/envs/env_0/panda"

# load the Franka Panda robot USD file
stage_utils.add_reference_to_stage(usd_path, prim_path)
# wrap the prim as an articulation
prim = SingleArticulation(prim_path=prim_path, name="franka_panda")
