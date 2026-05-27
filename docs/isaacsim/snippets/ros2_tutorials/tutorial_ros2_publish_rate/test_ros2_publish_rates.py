from isaacsim import SimulationApp

app = SimulationApp({"headless": False})

import carb
import isaacsim.core.experimental.utils.app as app_utils
import isaacsim.core.experimental.utils.stage as stage_utils
from isaacsim.core.rendering_manager import RenderingManager
from isaacsim.core.simulation_manager import SimulationManager
from isaacsim.storage.native import get_assets_root_path

app_utils.enable_extension("isaacsim.ros2.bridge")
app.update()

assets_root_path = get_assets_root_path()
stage_utils.open_stage(
    assets_root_path + "/Isaac/Samples/ROS2/Scenario/turtlebot_tutorial_multi_sensor_publish_rates.usd"
)

# Set physics, timeline, and run-loop rates coherently before pressing Play.
# Assumes `/app/runLoops/main/rateLimitEnabled` is true (default in the full
# Isaac Sim GUI app; false in `isaacsim.exp.base.kit` / standalone Python). If
# it is false, set it to True first or the loop will tick unthrottled. See the
# `RenderingManager.set_dt` docstring for the full effect list.
target_hz = 60
SimulationManager.setup_simulation(dt=1.0 / target_hz)
RenderingManager.set_dt(1.0 / target_hz)

app_utils.play()

while app.is_running():
    app.update()

app_utils.stop()
app.close()
