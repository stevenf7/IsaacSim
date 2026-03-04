# Ackermann steering example using the experimental API (no core World).
# Uses Articulation from core.experimental.prims and AckermannController from
# isaacsim.robot.experimental.wheeled_robots.

from isaacsim import SimulationApp

simulation_app = SimulationApp({"headless": False})

import isaacsim.core.experimental.utils.app as app_utils
import isaacsim.core.experimental.utils.stage as stage_utils
from isaacsim.core.experimental.objects import DomeLight
from isaacsim.core.experimental.prims import Articulation
from isaacsim.core.simulation_manager import SimulationManager
from isaacsim.robot.experimental.wheeled_robots.controllers import AckermannController
from isaacsim.storage.native import get_assets_root_path

DEVICE = "cpu"

assets_root_path = get_assets_root_path()
if assets_root_path is None:
    raise RuntimeError("Could not find Isaac Sim assets folder")
leatherback_asset_path = assets_root_path + "/Isaac/Robots/NVIDIA/Leatherback/leatherback.usd"
leatherback_prim_path = "/World/Leatherback"

stage_utils.set_stage_up_axis("Z")
stage_utils.set_stage_units(meters_per_unit=1.0)
stage_utils.add_reference_to_stage(
    usd_path=assets_root_path + "/Isaac/Environments/Grid/default_environment.usd",
    path="/World/ground",
)
dome_light = DomeLight("/World/DomeLight")
dome_light.set_intensities(500)
stage_utils.add_reference_to_stage(usd_path=leatherback_asset_path, path=leatherback_prim_path)

my_leatherback = Articulation(leatherback_prim_path)

# Steering joints (position control) and wheel joints (velocity control)
steering_joint_names = [
    "Knuckle__Upright__Front_Left",
    "Knuckle__Upright__Front_Right",
]
wheel_joint_names = [
    "Wheel__Knuckle__Front_Left",
    "Wheel__Knuckle__Front_Right",
    "Wheel__Upright__Rear_Left",
    "Wheel__Upright__Rear_Right",
]

steering_dof_indices = my_leatherback.get_dof_indices(steering_joint_names)
wheel_dof_indices = my_leatherback.get_dof_indices(wheel_joint_names)

wheel_base = 1.65
track_width = 1.25
wheel_radius = 0.25
desired_forward_vel = 1.1  # m/s
desired_steering_angle = 0.1  # rad
acceleration = 0.0
steering_velocity = 0.0
dt = 0.0

controller = AckermannController(
    wheel_base=wheel_base,
    track_width=track_width,
    front_wheel_radius=wheel_radius,
    back_wheel_radius=wheel_radius,
)
# Command: [steering_angle, steering_angle_velocity, speed, acceleration, dt]
joint_positions, joint_velocities = controller.forward(
    [desired_steering_angle, steering_velocity, desired_forward_vel, acceleration, dt]
)

# Setup simulation and disable GPU dynamics for this example.
SimulationManager.setup_simulation(dt=1.0 / 60.0, device=DEVICE)
physics_scene = SimulationManager.get_physics_scenes()[0]
physics_scene.set_enabled_gpu_dynamics(False)
app_utils.play()
app_utils.update_app(steps=10)

# Simulation loop: apply steering positions and wheel velocities.
while simulation_app.is_running():
    simulation_app.update()
    if app_utils.is_playing() and joint_positions is not None and joint_velocities is not None:
        my_leatherback.set_dof_position_targets(
            joint_positions,
            dof_indices=steering_dof_indices,
        )
        my_leatherback.set_dof_velocity_targets(
            joint_velocities,
            dof_indices=wheel_dof_indices,
        )

app_utils.stop()
simulation_app.close()
