import carb
import isaacsim.core.experimental.utils.stage as stage_utils
import numpy as np
from isaacsim.core.experimental.prims import Articulation

# -- Begin importing SimulationManager -- #
from isaacsim.core.simulation_manager import SimulationManager

# -- End of importing SimulationManager -- #
from isaacsim.examples.base.base_sample_experimental import BaseSample
from isaacsim.storage.native import get_assets_root_path


class HelloWorld(BaseSample):
    def __init__(self) -> None:
        super().__init__()
        self._physics_callback_id = None

    def setup_scene(self):
        # Add ground plane
        ground_plane = stage_utils.add_reference_to_stage(
            usd_path=get_assets_root_path() + "/Isaac/Environments/Grid/default_environment.usd",
            path="/World/ground",
        )

        # Get the assets root path from the Nucleus server
        assets_root_path = get_assets_root_path()
        if assets_root_path is None:
            carb.log_error("Could not find nucleus server with /Isaac folder")
            return

        # Add the Jetbot robot to the stage
        asset_path = assets_root_path + "/Isaac/Robots/NVIDIA/Jetbot/jetbot.usd"
        stage_utils.add_reference_to_stage(usd_path=asset_path, path="/World/Fancy_Robot")

    async def setup_post_load(self):
        # Wrap the Jetbot with the Articulation class for control
        self._jetbot = Articulation("/World/Fancy_Robot")

        # -- Begin registering callback -- #
        # Register a physics callback to send actions every physics step
        from isaacsim.core.simulation_manager.impl.isaac_events import IsaacEvents

        self._physics_callback_id = SimulationManager.register_callback(
            self.send_robot_actions, IsaacEvents.POST_PHYSICS_STEP
        )
        # -- End of registering callback -- #

    # -- Begin sending actions -- #
    def send_robot_actions(self, dt, context):
        # Apply random velocity targets to the wheel joints
        # Jetbot has 2 DOFs: left_wheel_joint and right_wheel_joint
        random_velocities = 5 * np.random.rand(1, 2)  # Shape: (1, num_dofs)
        self._jetbot.set_dof_velocity_targets(random_velocities)

    # -- End of sending actions -- #

    def physics_cleanup(self):
        # Clean up callback when the extension is unloaded
        if self._physics_callback_id is not None:
            SimulationManager.deregister_callback(self._physics_callback_id)
            self._physics_callback_id = None
