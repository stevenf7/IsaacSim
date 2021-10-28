from omni.isaac.samples.scripts.base_sample import BaseSample
from omni.isaac.franka.tasks import FollowTarget as FollowTargetTask
from omni.isaac.franka.controllers import RMPFlowController


class FollowTarget(BaseSample):
    def __init__(self) -> None:
        super().__init__()
        self._controller = None
        self._articulation_controller = None

    def setup_scene(self):
        world = self.get_world()
        world.add_task(FollowTargetTask())
        return

    async def setup_post_reset(self):
        world = self.get_world()
        if world.physics_callback_exists("sim_step"):
            world.remove_physics_callback("sim_step")
        self._controller.reset()
        return

    def world_cleanup(self):
        self._controller = None
        return

    async def setup_load(self):
        self._franka_task = list(self._world.get_current_tasks().values())[0]
        self._task_params = self._franka_task.get_params()
        my_franka = self._world.scene.get_object(self._task_params["robot_name"]["value"])
        self._controller = RMPFlowController(name="target_follower_controller", robot_prim_path=my_franka.prim_path)
        self._articulation_controller = my_franka.get_articulation_controller()
        return

    async def _on_follow_target_event_async(self):
        world = self.get_world()
        await world.play_async()
        world.add_physics_callback("sim_step", self._on_follow_target_simulation_step)
        return

    def _on_follow_target_simulation_step(self, step_size):
        observations = self._world.get_observations()
        actions = self._controller.forward(
            target_end_effector_position=observations[self._task_params["target_name"]["value"]]["position"],
            target_end_effector_orientation=observations[self._task_params["target_name"]["value"]]["orientation"],
        )
        self._articulation_controller.apply_action(actions)
        return

    def _on_add_obstacle_event(self):
        world = self.get_world()
        current_task = list(world.get_current_tasks().values())[0]
        cube = current_task.add_obstacle()
        self._controller.add_cube_obstacle(cube.prim)
        return

    def _on_remove_obstacle_event(self):
        world = self.get_world()
        current_task = list(world.get_current_tasks().values())[0]
        obstacle_to_delete = current_task.get_obstacle_to_delete()
        self._controller.remove_cube_obstacle(obstacle_to_delete.prim)
        current_task.remove_obstacle()
        return
