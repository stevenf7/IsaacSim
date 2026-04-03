"""Create a scene with ground, Franka robot, and blue cube."""

from isaacsim import SimulationApp

simulation_app = SimulationApp({"headless": False})

import isaacsim.core.experimental.utils.app as app_utils
from isaacsim.core.experimental.objects import Cube, DomeLight, GroundPlane
from isaacsim.core.experimental.prims import GeomPrim, RigidPrim
from isaacsim.core.simulation_manager import SimulationManager
from isaacsim.robot.manipulators.examples.franka import FrankaExperimental

DEVICE = "cpu"

GroundPlane("/World/ground_plane")
dome_light = DomeLight("/World/DomeLight")
dome_light.set_intensities(1000)

# Create the Franka robot
robot = FrankaExperimental(robot_path="/World/robot", create_robot=True)

# Create a blue cube for the robot to pick up
cube_shape = Cube(
    paths="/World/Cube",
    positions=[0.5, 0.0, 0.0258],
    sizes=1.0,
    scales=[0.0515, 0.0515, 0.0515],
    colors="blue",
)
GeomPrim(paths=cube_shape.paths, apply_collision_apis=True)
RigidPrim(paths=cube_shape.paths)

SimulationManager.setup_simulation(dt=1.0 / 60.0, device=DEVICE)
physics_scene = SimulationManager.get_physics_scenes()[0]
physics_scene.set_enabled_gpu_dynamics(False)
app_utils.play()
app_utils.update_app(steps=20)

while simulation_app.is_running():
    simulation_app.update()

app_utils.stop()
simulation_app.close()
