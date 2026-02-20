import isaacsim.core.experimental.utils.stage as stage_utils
import numpy as np
from isaacsim.core.simulation_manager import SimulationManager
from isaacsim.examples.base.base_sample_experimental import BaseSample
from isaacsim.robot.manipulators.examples.franka import FrankaPickPlace


class HelloWorld(BaseSample):
    def __init__(self) -> None:
        super().__init__()
        self._physics_callback_id = None

    def setup_scene(self):
        # FrankaPickPlace.setup_scene() spawns the complete scene:
        # - Ground plane
        # - Franka robot (using FrankaExperimental)
        # - Blue cube for manipulation
        self._controller = FrankaPickPlace()
        self._controller.setup_scene()

    async def setup_post_load(self):
        # Reset the controller to initialize the robot position
        self._controller.reset()

        # Register physics callback to execute pick-place steps
        from isaacsim.core.simulation_manager.impl.isaac_events import IsaacEvents

        self._physics_callback_id = SimulationManager.register_callback(
            self.physics_step, IsaacEvents.POST_PHYSICS_STEP
        )

    def physics_step(self, dt, context):
        # Execute one step of the pick-and-place operation
        if not self._controller.is_done():
            self._controller.forward()
        else:
            print("Pick-and-place completed!")
            self._timeline.pause()

    # This function is called after Reset button is pressed
    # Resetting anything in the world should happen here
    async def setup_post_reset(self):
        self._controller.reset()
        self._franka.gripper.set_joint_positions(self._franka.gripper.joint_opened_positions)
        await self._world.play_async()
        return

    def physics_step(self, step_size):
        cube_position, _ = self._fancy_cube.get_world_pose()
        goal_position = np.array([-0.3, -0.3, 0.0515 / 2.0])
        current_joint_positions = self._franka.get_joint_positions()
        actions = self._controller.forward(
            picking_position=cube_position,
            placing_position=goal_position,
            current_joint_positions=current_joint_positions,
        )
        self._franka.apply_action(actions)
        # Only for the pick and place controller, indicating if the state
        # machine reached the final state.
        if self._controller.is_done():
            self._world.pause()
        return
