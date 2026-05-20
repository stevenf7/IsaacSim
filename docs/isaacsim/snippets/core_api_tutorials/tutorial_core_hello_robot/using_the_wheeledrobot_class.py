import carb
import isaacsim.core.experimental.utils.stage as stage_utils
import numpy as np
from isaacsim.core.experimental.prims import Articulation
from isaacsim.core.simulation_manager import SimulationManager
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

        # Add the Jetbot robot to the stage
        assets_root_path = get_assets_root_path()
        asset_path = assets_root_path + "/Isaac/Robots/NVIDIA/Jetbot/jetbot.usd"
        stage_utils.add_reference_to_stage(usd_path=asset_path, path="/World/Fancy_Robot")

    async def setup_post_load(self):
        # Wrap the Jetbot with the Articulation class
        self._jetbot = Articulation("/World/Fancy_Robot")

        # -- Begin getting indices -- #
        # Print available DOF names
        print("Available DOFs:", self._jetbot.dof_names)

        # Get indices for specific wheel joints
        self._wheel_indices = self._jetbot.get_dof_indices(["left_wheel_joint", "right_wheel_joint"]).numpy()
        print("Wheel indices:", self._wheel_indices)
        # -- End of getting indices -- #

        # Register physics callback
        from isaacsim.core.simulation_manager.impl.isaac_events import IsaacEvents

        self._physics_callback_id = SimulationManager.register_callback(
            self.send_robot_actions, IsaacEvents.POST_PHYSICS_STEP
        )

    def send_robot_actions(self, dt, context):
        # -- Begin setting wheel velocity -- #
        # Apply velocity targets to specific DOF indices
        wheel_velocities = np.array([[10.0, 10.0]])  # Both wheels same speed = forward
        self._jetbot.set_dof_velocity_targets(wheel_velocities, dof_indices=self._wheel_indices)
        # -- End of setting wheel velocity -- #

    def physics_cleanup(self):
        if self._physics_callback_id is not None:
            SimulationManager.deregister_callback(self._physics_callback_id)
            self._physics_callback_id = None
