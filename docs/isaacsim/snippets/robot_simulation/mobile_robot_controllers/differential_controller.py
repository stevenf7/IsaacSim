# Reference: source/standalone_examples/api/isaacsim.robot.wheeled_robots.examples/jetbot_differential_move.py
# Timeline: use app_utils (play/stop/is_playing) instead of omni.timeline. Use app_utils.update_app(steps=N) instead of for-loop simulation_app.update(); same for other mobile_robot_controllers examples.

from isaacsim import SimulationApp

simulation_app = SimulationApp({"headless": False})

import isaacsim.core.experimental.utils.app as app_utils
import isaacsim.core.experimental.utils.stage as stage_utils
from isaacsim.core.experimental.objects import DomeLight
from isaacsim.core.simulation_manager import SimulationManager
from isaacsim.robot.experimental.wheeled_robots.controllers import DifferentialController
from isaacsim.robot.experimental.wheeled_robots.robots import WheeledRobot
from isaacsim.storage.native import get_assets_root_path

DEVICE = "cpu"

assets_root_path = get_assets_root_path()
if assets_root_path is None:
    raise RuntimeError("Could not find Isaac Sim assets folder")
jetbot_asset_path = assets_root_path + "/Isaac/Robots/NVIDIA/Jetbot/jetbot.usd"

stage_utils.set_stage_up_axis("Z")
stage_utils.set_stage_units(meters_per_unit=1.0)
stage_utils.add_reference_to_stage(
    usd_path=assets_root_path + "/Isaac/Environments/Grid/default_environment.usd",
    path="/World/ground",
)
dome_light = DomeLight("/World/DomeLight")
dome_light.set_intensities(500)

my_jetbot = WheeledRobot(
    paths="/World/Jetbot",
    wheel_dof_names=["left_wheel_joint", "right_wheel_joint"],
    usd_path=jetbot_asset_path,
    positions=[0.0, 0.0, 0.05],
)
my_controller = DifferentialController(wheel_radius=0.03, wheel_base=0.1125)

# Setup simulation and disable GPU dynamics for this example.
SimulationManager.setup_simulation(dt=1.0 / 60.0, device=DEVICE)
physics_scene = SimulationManager.get_physics_scenes()[0]
physics_scene.set_enabled_gpu_dynamics(False)
app_utils.play()
app_utils.update_app(steps=10)

# Simulation loop: apply [linear_speed, angular_speed]; e.g. 0.3 m/s, 1.0 rad/s.
linear_speed = 0.3
angular_speed = 1.0
while simulation_app.is_running():
    simulation_app.update()
    if app_utils.is_playing():
        velocities = my_controller.forward([linear_speed, angular_speed])
        my_jetbot.apply_wheel_actions(velocities)

app_utils.stop()
simulation_app.close()
