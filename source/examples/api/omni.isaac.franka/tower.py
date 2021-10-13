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

from omni.isaac.franka.tasks import Tower
from omni.isaac.franka.controllers import RMPFlowTower
from omni.isaac.core import World
from omni.isaac.core.utils.extensions import get_extension_id, get_extension_path

my_world = World()
extension_id = get_extension_id("omni.isaac.motion_generation")
mg_extension_path = get_extension_path(ext_id=extension_id)
my_task = Tower()
my_world.load_task(my_task)
my_world.reset()
my_franka = my_world.scene.get_object("my_franka")
my_controller = RMPFlowTower(
    name="pick_place_controller",
    dc_interface=my_world.dc_interface,
    stage=my_world.stage,
    robot_prim=my_franka.prim,
    mg_extension_path=mg_extension_path,
)
my_controller.configure(cubes_order=["cube_1", "cube_2"], robot_observation_name="my_franka")
articulation_controller = my_franka.get_articulation_controller()

i = 0
while True:
    observations = my_world.get_observations()
    actions = my_controller.forward(observations=observations)
    articulation_controller.apply_action(actions)
    my_world.step(render=True)

simulation_app.close()
