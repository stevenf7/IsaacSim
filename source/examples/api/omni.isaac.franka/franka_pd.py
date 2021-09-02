# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
from omni.isaac.kit import SimulationApp
import numpy as np

simulation_app = SimulationApp({"headless": False})

from omni.isaac.core.tasks.task import BaseTask
from omni.isaac.franka import Franka
from omni.isaac.core import World
from omni.isaac.core.controllers import BaseController
from omni.isaac.core.utils.types import ArticulationAction

my_world = World()


class FrankaTask(BaseTask):
    def __init__(self):
        pass

    def set_up_scene(self, scene):
        super().set_up_scene(scene)
        scene.add(Franka(stage=my_world.stage, prim_path="/World/Franka", name="my_franka"))
        return

    def get_observations(self):
        joints_state = self.scene.get_object("my_franka").get_joints_state()
        return {
            "franka": {
                "joint_positions": np.array(joints_state.positions),
                "joint_velcoities": np.array(joints_state.velocities),
            }
        }

    def reset(self):
        self.scene.get_object("my_franka").get_articulation_controller().switch_control_mode("accelaration")
        return


class PDController(BaseController):
    def __init__(self, name):
        super().__init__(name)
        self._kp = np.array([100000.0] * 9)
        self._kd = np.array([10.0] * 9)
        return

    def forward(self, observations):
        position_error = observations["franka"]["target_joint_positions"] - observations["franka"]["joint_positions"]
        velocity_error = -observations["franka"]["joint_velcoities"]
        torque_action = self._kp * position_error + self._kd * velocity_error
        # return torque_action
        # TODO: there is a bug here somewhere!
        return ArticulationAction(joint_torques=torque_action / 100.0)


my_task = FrankaTask()
my_world.load_task(my_task)
my_world.reset()
my_franka = my_world.scene.get_object("my_franka")
my_controller = PDController(name="generic_pd_controller")
articulation_controller = my_franka.get_articulation_controller()

while True:
    observations = my_world.get_observations()
    target_joint_positions = np.array([1.5, 1.5, 1.5, 0.087, 1.5, 1.5, 1.5, 0.04, 0.04])
    observations["franka"]["target_joint_positions"] = target_joint_positions
    actions = my_controller.forward(observations)
    articulation_controller.apply_action(actions)
    my_world.step(render=True)

simulation_app.close()
