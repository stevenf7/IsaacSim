import isaacsim.core.experimental.utils.app as app_utils
import isaacsim.core.experimental.utils.stage as stage_utils
from isaacsim.core.experimental.prims import Articulation
from isaacsim.storage.native import get_assets_root_path

# Add Franka robots to the stage
usd_path = get_assets_root_path() + "/Isaac/Robots/FrankaRobotics/FrankaPanda/franka.usd"
variants = [("Gripper", "AlternateFinger"), ("Mesh", "Quality")]
stage_utils.add_reference_to_stage(usd_path, path="/World/Franka_1", variants=variants)
stage_utils.add_reference_to_stage(usd_path, path="/World/Franka_2", variants=variants)

# Wrap Franka robots via an Articulation object
articulations = Articulation(
    "/World/Franka_.*",
    positions=[[-1, -1, 0], [1, 1, 0]],
    reset_xform_op_properties=True,
)
# [snippet-control]
# -- Test setup --
import omni.kit.app
import omni.timeline

omni.timeline.get_timeline_interface().play()
for _ in range(3):
    omni.kit.app.get_app().update()
# -- End test setup --

# Set the joint positions for each articulation
articulations.set_dof_position_targets(
    [
        [1.5, 1.5, 1.5, 1.5, 1.5, 1.5, 1.5, 0.0, 0.0],
        [-1.5, -1.5, -1.5, -1.5, -1.5, -1.5, -1.5, 0.04, 0.04],
    ]
)

# -- Test cleanup --
omni.timeline.get_timeline_interface().stop()
