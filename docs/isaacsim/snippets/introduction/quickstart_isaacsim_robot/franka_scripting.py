# isort: skip_file
# -- Test setup --
import omni.kit.app
import omni.timeline
from isaacsim.core.simulation_manager import IsaacEvents, SimulationManager

# -- End test setup --

# [add-franka-to-stage]
import isaacsim.core.experimental.utils.stage as stage_utils
from isaacsim.core.experimental.prims import Articulation, XformPrim
from isaacsim.storage.native import get_assets_root_path


assets_root_path = get_assets_root_path()
asset_path = assets_root_path + "/Isaac/Robots/FrankaRobotics/FrankaPanda/franka.usd"
stage_utils.add_reference_to_stage(usd_path=asset_path, path="/World/Arm")

arm_transform = XformPrim("/World/Arm")
arm_transform.set_world_poses(positions=[0.0, 1.0, 0.0])

arm_handle = Articulation("/World/Arm")
# [/add-franka-to-stage]

# -- Test setup --
omni.timeline.get_timeline_interface().play()
for _ in range(3):
    omni.kit.app.get_app().update()
# -- End test setup --

# [examine-robot-joints]
# Requires physics running (Press Play first). arm_handle from add_franka_to_stage snippet.
print("Number of joints:", arm_handle.num_dofs)
print("Joint names:", arm_handle.dof_names)
positions = arm_handle.get_dof_positions()
print("Joint positions:", positions)
# [/examine-robot-joints]

# [physics-callback]
from isaacsim.core.simulation_manager import IsaacEvents, SimulationManager


def print_joint_positions_callback(dt, context):
    positions = arm_handle.get_dof_positions()
    print("Joint positions:", positions)


# Store callback_id to remove later if needed
callback_id = SimulationManager.register_callback(print_joint_positions_callback, IsaacEvents.POST_PHYSICS_STEP)
# [/physics-callback]

# [remove-callback]
from isaacsim.core.simulation_manager import SimulationManager

# callback_id was returned when registering the callback
SimulationManager.deregister_callback(callback_id)
# [/remove-callback]

# [control-robot]
# Move arm to a target pose. arm_handle from add_franka_to_stage snippet.
# Franka has 9 DOFs: 7 arm joints + 2 finger joints
arm_handle.set_dof_positions([-1.5, 0.0, 0.0, -1.5, 0.0, 1.5, 0.5, 0.04, 0.04])

# To reset to default pose:
# arm_handle.set_dof_positions([0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.04, 0.04])
# [/control-robot]

# -- Test cleanup --
omni.timeline.get_timeline_interface().stop()
