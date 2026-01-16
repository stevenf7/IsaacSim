import isaacsim.core.experimental.utils.stage as stage_utils
import numpy as np
from isaacsim.core.experimental.materials import PreviewSurfaceMaterial
from isaacsim.core.experimental.objects import Cube
from isaacsim.core.experimental.prims import Articulation, GeomPrim, RigidPrim, XformPrim
from isaacsim.core.simulation_manager import SimulationManager
from isaacsim.examples.base.base_sample_experimental import BaseSample
from isaacsim.robot.manipulators.examples.franka import FrankaExperimental
from isaacsim.storage.native import get_assets_root_path

# RobotScenario class definition (same as above)
# ... (include the full RobotScenario class from the previous example)


class HelloWorld(BaseSample):
    def __init__(self) -> None:
        super().__init__()
        self._physics_callback_id = None
        self._scenarios = []
        self._num_scenarios = 2  # Number of parallel scenarios

    def setup_scene(self):
        # Add ground plane
        stage_utils.add_reference_to_stage(
            usd_path=get_assets_root_path() + "/Isaac/Environments/Grid/default_environment.usd",
            path="/World/ground",
        )

        # Create multiple scenarios with Y-axis offsets
        for i in range(self._num_scenarios):
            offset = np.array([0.0, (i - 1) * 2.0, 0.0])  # Spread along Y-axis
            scenario = RobotScenario(name=f"scenario_{i}", offset=offset)
            scenario.setup_scene()
            self._scenarios.append(scenario)

    async def setup_post_load(self):
        # Initialize all scenarios
        for scenario in self._scenarios:
            scenario.initialize()

        from isaacsim.core.simulation_manager.impl.isaac_events import IsaacEvents

        self._physics_callback_id = SimulationManager.register_callback(
            self.physics_step, IsaacEvents.POST_PHYSICS_STEP
        )

    def physics_step(self, dt, context):
        # Step all scenarios
        for scenario in self._scenarios:
            scenario.step()

    async def setup_post_reset(self):
        # Reset all scenarios
        for scenario in self._scenarios:
            scenario.reset()

    def physics_cleanup(self):
        if self._physics_callback_id is not None:
            SimulationManager.deregister_callback(self._physics_callback_id)
            self._physics_callback_id = None
        self._scenarios = []
