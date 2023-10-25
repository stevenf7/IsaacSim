import sys

import carb
import omni
from omni.isaac.kit import SimulationApp

# The most basic usage for creating a simulation app
kit = SimulationApp()

ADDITIONAL_EXTENSIONS_PEOPLE = [
    "omni.anim.people",
    "omni.anim.navigation.bundle",
    "omni.anim.timeline",
    "omni.anim.graph.bundle",
    "omni.anim.graph.core",
    "omni.anim.graph.ui",
    "omni.anim.retarget.bundle",
    "omni.anim.retarget.core",
    "omni.anim.retarget.ui",
    "omni.kit.scripting",
]


from omni.isaac.core.utils.extensions import enable_extension

for e in ADDITIONAL_EXTENSIONS_PEOPLE:
    enable_extension(e)

enable_extension("omni.isaac.ros2_bridge")

# Locate Isaac Sim assets folder to load sample
from omni.isaac.core.utils.nucleus import get_assets_root_path, is_file

assets_root_path = get_assets_root_path()
if assets_root_path is None:
    carb.log_error("Could not find Isaac Sim assets folder")
    kit.close()
    sys.exit()
usd_path = assets_root_path + "/Isaac/Samples/NvBlox/carter_warehouse_navigation_with_dynamics.usd"

omni.usd.get_context().open_stage(usd_path)

for i in range(100):
    kit.update()

omni.timeline.get_timeline_interface().play()

for i in range(100):
    kit.update()

kit.close()  # Cleanup application
