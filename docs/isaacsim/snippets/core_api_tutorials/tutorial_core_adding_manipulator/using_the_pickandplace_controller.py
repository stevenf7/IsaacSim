"""Pick-and-place using FrankaPickPlace."""

from isaacsim import SimulationApp

simulation_app = SimulationApp({"headless": False})

import isaacsim.core.experimental.utils.app as app_utils
import isaacsim.core.experimental.utils.stage as stage_utils
from isaacsim.core.simulation_manager import SimulationManager
from isaacsim.robot.manipulators.examples.franka import FrankaPickPlace
from isaacsim.storage.native import get_assets_root_path

DEVICE = "cpu"

assets_root_path = get_assets_root_path()

stage_utils.set_stage_up_axis("Z")
stage_utils.set_stage_units(meters_per_unit=1.0)
stage_utils.add_reference_to_stage(
    usd_path=assets_root_path + "/Isaac/Environments/Grid/default_environment.usd",
    path="/World/ground",
)

# FrankaPickPlace spawns robot and cube, and provides the pick-place state machine
controller = FrankaPickPlace()
controller.setup_scene()

SimulationManager.setup_simulation(dt=1.0 / 60.0, device=DEVICE)
physics_scene = SimulationManager.get_physics_scenes()[0]
physics_scene.set_enabled_gpu_dynamics(False)
app_utils.play()
# Run a few steps so the articulation's physics tensor entity is valid before `controller.reset()`
app_utils.update_app(steps=20)
controller.reset()

# Main loop: run one pick-place step each physics frame until done
while simulation_app.is_running():
    simulation_app.update()
    if app_utils.is_playing():
        if not controller.is_done():
            controller.forward()
        else:
            print("Pick-and-place completed")
            app_utils.pause()

app_utils.stop()
simulation_app.close()
