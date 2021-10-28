from omni.isaac.samples.scripts.base_sample import BaseSample
from omni.isaac.franka.tasks import Stacking
from omni.isaac.franka.controllers import StackingController


class SimpleStack(BaseSample):
    def __init__(self) -> None:
        super().__init__()
        self._controller = None
        self._articulation_controller = None

    def setup_scene(self):
        world = self.get_world()
        world.add_task(Stacking(name="stacking_task"))
        return

    async def setup_load(self):
        self._franka_task = self._world.get_task(name="stacking_task")
        self._task_params = self._franka_task.get_params()
        my_franka = self._world.scene.get_object(self._task_params["robot_name"]["value"])
        self._controller = StackingController(
            name="stacking_controller",
            gripper_dof_indices=my_franka.gripper.dof_indices,
            robot_prim_path=my_franka.prim_path,
            picking_order_cube_names=self._franka_task.get_cube_names(),
            robot_observation_name=my_franka.name,
        )
        self._articulation_controller = my_franka.get_articulation_controller()
        return

    def _on_stacking_simulation_step(self, step_size):
        observations = self._world.get_observations()
        actions = self._controller.forward(observations=observations)
        self._articulation_controller.apply_action(actions)
        if self._controller.is_done():
            self._world.pause()
        return

    async def setup_post_reset(self):
        self._controller.reset()
        return

    def world_cleanup(self):
        self._controller = None
        return
