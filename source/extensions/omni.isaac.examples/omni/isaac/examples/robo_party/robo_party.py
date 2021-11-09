# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

from omni.isaac.examples.base_sample import BaseSample
from omni.isaac.universal_robots.tasks import Stacking as UR10Stacking
from omni.isaac.franka.tasks import Stacking as FrankaStacking
from omni.isaac.dofbot.tasks import PickPlace
from omni.isaac.kaya import Kaya
from omni.isaac.jetbot import Jetbot
from omni.isaac.franka.controllers import StackingController as FrankaStackingController
from omni.isaac.universal_robots.controllers import StackingController as UR10StackingController
from omni.isaac.kaya.controllers import HolonomicController
from omni.isaac.jetbot.controllers import DifferentialController
from omni.isaac.dofbot.controllers import PickPlaceController
import numpy as np


class RoboParty(BaseSample):
    def __init__(self) -> None:
        super().__init__()
        self._tasks = []
        self._controllers = []
        self._articulation_controllers = []
        self._pick_place_task_params = None
        self._robots = []
        return

    def setup_scene(self):
        world = self.get_world()
        self._tasks.append(FrankaStacking(name="task_0", offset=np.array([0, -200, 0])))
        world.add_task(self._tasks[-1])
        self._tasks.append(UR10Stacking(name="task_1", offset=np.array([50, 50, 0])))
        world.add_task(self._tasks[-1])
        self._tasks.append(PickPlace(name="task_2", offset=np.array([0, -100, 0])))
        world.add_task(self._tasks[-1])
        world.scene.add(Kaya(prim_path="/World/Kaya", name="my_kaya", position=np.array([-100, 0, 0])))
        world.scene.add(Jetbot(prim_path="/World/Jetbot", name="my_jetbot", position=np.array([-150, -150, 0])))
        return

    async def setup_post_load(self):
        self._tasks = [
            self._world.get_task(name="task_0"),
            self._world.get_task(name="task_1"),
            self._world.get_task(name="task_2"),
        ]
        for i in range(3):
            self._robots.append(self._world.scene.get_object(self._tasks[i].get_params()["robot_name"]["value"]))
        self._robots.append(self._world.scene.get_object("my_kaya"))
        self._robots.append(self._world.scene.get_object("my_jetbot"))
        self._pick_place_task_params = self._tasks[2].get_params()
        self._controllers.append(
            FrankaStackingController(
                name="stacking_controller",
                gripper_dof_indices=self._robots[0].gripper.dof_indices,
                robot_prim_path=self._robots[0].prim_path,
                picking_order_cube_names=self._tasks[0].get_cube_names(),
                robot_observation_name=self._robots[0].name,
            )
        )
        self._controllers.append(
            UR10StackingController(
                name="pick_place_controller",
                surface_gripper=self._robots[1].gripper,
                robot_prim_path=self._robots[1].prim_path,
                picking_order_cube_names=self._tasks[1].get_cube_names(),
                robot_observation_name=self._robots[1].name,
            )
        )
        self._controllers.append(
            PickPlaceController(
                name="pick_place_controller",
                gripper_dof_indices=self._robots[2].gripper.dof_indices,
                robot_prim_path=self._robots[2].prim_path,
            )
        )
        self._controllers.append(HolonomicController(name="holonomic_controller"))
        self._controllers.append(DifferentialController(name="simple_control"))
        for i in range(5):
            self._articulation_controllers.append(self._robots[i].get_articulation_controller())
        return

    def _on_start_party_physics_step(self, step_size):
        observations = self._world.get_observations()
        actions = self._controllers[0].forward(observations=observations, end_effector_offset=np.array([0, 0, -1.5]))
        self._articulation_controllers[0].apply_action(actions)
        actions = self._controllers[1].forward(observations=observations, end_effector_offset=np.array([0, 0, 2]))
        self._articulation_controllers[1].apply_action(actions)

        actions = self._controllers[2].forward(
            picking_position=observations[self._pick_place_task_params["cube_name"]["value"]]["position"],
            placing_position=observations[self._pick_place_task_params["cube_name"]["value"]]["target_position"],
            current_joint_positions=observations[self._pick_place_task_params["robot_name"]["value"]][
                "joint_positions"
            ],
            end_effector_offset=np.array([0, -6, 0]),
        )
        self._articulation_controllers[2].apply_action(actions)
        if self._world.current_time_step_index >= 0 and self._world.current_time_step_index < 500:
            self._robots[3].apply_wheel_actions(
                self._controllers[3].forward(x_velocity=20.0, y_velocity=0.0, theta_velocity=0.0)
            )
            self._robots[4].apply_wheel_actions(self._controllers[4].forward(command=[10, 0]))
        elif self._world.current_time_step_index >= 500 and self._world.current_time_step_index < 1000:
            self._robots[3].apply_wheel_actions(
                self._controllers[3].forward(x_velocity=0, y_velocity=20.0, theta_velocity=0.0)
            )
            self._robots[4].apply_wheel_actions(self._controllers[4].forward(command=[0.0, np.pi / 10]))
        elif self._world.current_time_step_index >= 1000 and self._world.current_time_step_index < 1500:
            self._robots[3].apply_wheel_actions(
                self._controllers[3].forward(x_velocity=0.0, y_velocity=0.0, theta_velocity=0.6)
            )
            self._robots[4].apply_wheel_actions(self._controllers[4].forward(command=[10, 0]))
        return

    async def _on_start_party_event_async(self):
        world = self.get_world()
        world.add_physics_callback("sim_step", self._on_start_party_physics_step)
        await world.play_async()
        return

    async def setup_post_reset(self):
        world = self.get_world()
        if world.physics_callback_exists("sim_step"):
            world.remove_physics_callback("sim_step")
        for i in range(len(self._controllers)):
            self._controllers[i].reset()
        return

    def world_cleanup(self):
        self._tasks = []
        self._controllers = []
        self._articulation_controllers = []
        self._pick_place_task_params = None
        self._robots = []
        return
