from omni.isaac.samples.scripts.base_sample import BaseSample
from omni.isaac.franka.tasks import FollowTarget as FollowTargetTask
from omni.isaac.franka.controllers import RMPFlowController


class FollowTarget(BaseSample):
    def __init__(self) -> None:
        super().__init__()
        self._controller = None
        self._articulation_controller = None

    def add_tasks(self):
        return [FollowTargetTask()]

    async def setup_load(self):
        self._franka_task = list(self._world.get_current_tasks().values())[0]
        self._task_params = self._franka_task.get_params()
        my_franka = self._world.scene.get_object(self._task_params["robot_name"]["value"])
        self._controller = RMPFlowController(name="target_follower_controller", robot_prim_path=my_franka.prim_path)
        self._articulation_controller = my_franka.get_articulation_controller()
        return

    def _on_follow_target_simulation_step(self, step_size):
        observations = self._world.get_observations()
        actions = self._controller.forward(
            target_end_effector_position=observations[self._task_params["target_name"]["value"]]["position"],
            target_end_effector_orientation=observations[self._task_params["target_name"]["value"]]["orientation"],
        )
        self._articulation_controller.apply_action(actions)
        return

    async def setup_reset(self):
        self._controller.reset()
        return

    def world_cleanup(self):
        super().world_cleanup()
        self._controller = None
        return

    async def setup_clear(self):
        return
