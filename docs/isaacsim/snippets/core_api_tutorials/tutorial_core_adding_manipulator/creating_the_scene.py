"""Create a scene with ground, Franka robot, and blue cube."""

from isaacsim import SimulationApp

simulation_app = SimulationApp({"headless": False})

import isaacsim.core.experimental.utils.app as app_utils
import isaacsim.core.experimental.utils.stage as stage_utils
from isaacsim.core.experimental.materials import PreviewSurfaceMaterial
from isaacsim.core.experimental.objects import Cube
from isaacsim.core.experimental.prims import GeomPrim, RigidPrim
from isaacsim.core.simulation_manager import SimulationManager
from isaacsim.robot.manipulators.examples.franka import FrankaExperimental
from isaacsim.storage.native import get_assets_root_path

DEVICE = "cpu"

assets_root_path = get_assets_root_path()

# Add ground plane
stage_utils.add_reference_to_stage(
    usd_path=assets_root_path + "/Isaac/Environments/Grid/default_environment.usd",
    path="/World/ground",
)

# Create the Franka robot
robot = FrankaExperimental(robot_path="/World/robot", create_robot=True)

# Create a blue cube for the robot to pick up
visual_material = PreviewSurfaceMaterial("/World/Materials/blue")
visual_material.set_input_values("diffuseColor", [0.0, 0.0, 1.0])
cube_shape = Cube(
    paths="/World/Cube",
    positions=[0.5, 0.0, 0.0258],
    sizes=1.0,
    scales=[0.0515, 0.0515, 0.0515],
)
GeomPrim(paths=cube_shape.paths, apply_collision_apis=True)
RigidPrim(paths=cube_shape.paths)
cube_shape.apply_visual_materials(visual_material)

SimulationManager.setup_simulation(dt=1.0 / 60.0, device=DEVICE)
physics_scene = SimulationManager.get_physics_scenes()[0]
physics_scene.set_enabled_gpu_dynamics(False)
app_utils.play()
app_utils.update_app(steps=20)

while simulation_app.is_running():
    simulation_app.update()

app_utils.stop()
simulation_app.close()
