# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
from omni.isaac.kit import SimulationApp

simulation_app = SimulationApp({"headless": False})


from omni.isaac.universal_robots.tasks import Stacking as UR10Stacking
from omni.isaac.universal_robots.controllers import StackingController as UR10StackingController
from omni.isaac.franka.tasks import Stacking as FrankaStacking
from omni.isaac.dofbot.tasks import PickPlace
from omni.isaac.franka.controllers import StackingController as FrankaStackingController
from omni.isaac.core import World
from omni.isaac.kaya import Kaya
from omni.isaac.jetbot import Jetbot
from omni.isaac.core.prims.xform_prim import XFormPrim
from omni.isaac.wheeled_robots.controllers.holonomic_controller import HolonomicController
from omni.isaac.jetbot.controllers import DifferentialController
from omni.isaac.dofbot.controllers import PickPlaceController
import numpy as np

my_world = World(stage_units_in_meters=0.01)
tasks = []
num_of_tasks = 3

tasks.append(FrankaStacking(name="task_0", offset=np.array([0, -200, 0])))
my_world.add_task(tasks[-1])
tasks.append(UR10Stacking(name="task_1", offset=np.array([50, 50, 0])))
my_world.add_task(tasks[-1])
tasks.append(PickPlace(offset=np.array([0, -100, 0])))
my_world.add_task(tasks[-1])
my_kaya = my_world.scene.add(Kaya(prim_path="/World/Kaya", name="my_kaya", position=np.array([-100, 0, 0])))
my_jetbot = my_world.scene.add(Jetbot(prim_path="/World/Jetbot", name="my_jetbot", position=np.array([-150, -150, 0])))
my_world.reset()
robots = []
for i in range(num_of_tasks):
    task_params = tasks[i].get_params()
    robots.append(my_world.scene.get_object(task_params["robot_name"]["value"]))

controllers = []
controllers.append(
    FrankaStackingController(
        name="pick_place_controller",
        gripper_dof_indices=robots[0].gripper.dof_indices,
        robot_prim_path=robots[0].prim_path,
        picking_order_cube_names=tasks[0].get_cube_names(),
        robot_observation_name=robots[0].name,
    )
)
controllers[-1].reset()
controllers.append(
    UR10StackingController(
        name="pick_place_controller",
        surface_gripper=robots[1].gripper,
        robot_prim_path=robots[1].prim_path,
        picking_order_cube_names=tasks[1].get_cube_names(),
        robot_observation_name=robots[1].name,
    )
)
controllers[-1].reset()
controllers.append(
    PickPlaceController(
        name="pick_place_controller",
        gripper_dof_indices=robots[2].gripper.dof_indices,
        robot_prim_path=robots[2].prim_path,
    )
)

kaya_controller = HolonomicController(
    name="holonomic_controller",
    robot=my_kaya,
    com_prim=XFormPrim("/World/kaya/base_link/control_offset"),
    angular_gain=1,
)
jetbot_controller = DifferentialController(name="simple_control")
pick_place_task_params = tasks[2].get_params()

articulation_controllers = []
for i in range(num_of_tasks):
    articulation_controllers.append(robots[i].get_articulation_controller())

i = 0
my_world.pause()
while simulation_app.is_running():
    my_world.step(render=True)
    if my_world.is_playing():
        if my_world.current_time_step_index == 0:
            my_world.reset()
            controllers[0].reset()
            controllers[1].reset()
            controllers[2].reset()
            kaya_controller.reset()
            jetbot_controller.reset()
        observations = my_world.get_observations()
        actions = controllers[0].forward(observations=observations, end_effector_offset=np.array([0, 0, -1.5]))
        articulation_controllers[0].apply_action(actions)
        actions = controllers[1].forward(observations=observations, end_effector_offset=np.array([0, 0, 2]))
        articulation_controllers[1].apply_action(actions)

        actions = controllers[2].forward(
            picking_position=observations[pick_place_task_params["cube_name"]["value"]]["position"],
            placing_position=observations[pick_place_task_params["cube_name"]["value"]]["target_position"],
            current_joint_positions=observations[pick_place_task_params["robot_name"]["value"]]["joint_positions"],
            end_effector_offset=np.array([0, -6, 0]),
        )
        articulation_controllers[2].apply_action(actions)
        if i >= 0 and i < 500:
            my_kaya.apply_wheel_actions(kaya_controller.forward(command=[2.0, 0.0, 0.0]))
            my_jetbot.apply_wheel_actions(jetbot_controller.forward(command=[10, 0]))
        elif i >= 500 and i < 1000:
            # TODO: change with new USD
            my_kaya.apply_wheel_actions(kaya_controller.forward(command=[0, 2.0, 0.0]))
            my_jetbot.apply_wheel_actions(jetbot_controller.forward(command=[0.0, np.pi / 10]))
        elif i >= 1000 and i < 1500:
            # TODO: change with new USD
            my_kaya.apply_wheel_actions(kaya_controller.forward(command=[0, 0.0, 0.6]))
            my_jetbot.apply_wheel_actions(jetbot_controller.forward(command=[10, 0]))
        i += 1


simulation_app.close()
