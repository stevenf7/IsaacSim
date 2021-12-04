# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
import gym
from gym import spaces
import numpy as np


class JetBotGymEnv(gym.Env):
    metadata = {"render.modes": ["human"]}

    def __init__(
        self, skip_frame=2, physics_dt=1.0 / 120.0, max_episode_length=10000, seed=0, observation_mode="structured"
    ) -> None:
        from omni.isaac.kit import SimulationApp

        self._simulation_app = SimulationApp({"headless": False})
        self._skip_frame = skip_frame
        self._dt = physics_dt * self._skip_frame
        self._max_episode_length = max_episode_length
        from omni.isaac.core import World
        from omni.isaac.jetbot import Jetbot
        from omni.isaac.core.objects import VisualCuboid, DynamicCuboid

        self._my_world = World(physics_dt=physics_dt, stage_units_in_meters=0.01)
        self._my_world.scene.add_default_ground_plane()
        self.jetbot = self._my_world.scene.add(
            Jetbot(
                prim_path="/jetbot",
                name="my_jetbot",
                position=np.array([0, 0.0, 2.0]),
                orientation=np.array([1.0, 0.0, 0.0, 0.0]),
            )
        )
        self.goal = self._my_world.scene.add(
            VisualCuboid(
                prim_path="/new_cube_1",
                name="visual_cube",
                position=np.array([60, 30, 2.5]),
                size=np.array([5, 5, 5]),
                color=np.array([1.0, 0, 0]),
            )
        )

        self.obstacle = self._my_world.scene.add(
            DynamicCuboid(
                prim_path="/new_cube_2",
                name="cube_1",
                position=np.array([30, 30, 5]),
                size=np.array([10, 100, 10]),
                color=np.array([0, 0, 1.0]),
            )
        )

        self.seed(seed)
        self.sd_helper = None
        self.viewport_window = None
        self._set_camera()
        # TODO: add reward range
        self.reward_range = (-float("inf"), float("inf"))
        gym.Env.__init__(self)
        self.action_space = spaces.Box(low=-10.0, high=10.0, shape=(2,), dtype=np.float32)
        self.observation_mode = observation_mode
        if self.observation_mode == "structured":
            self.observation_space = spaces.Box(low=0, high=2.0, shape=(2,), dtype=np.float32)
        elif self.observation_mode == "camera":
            self.observation_space = spaces.Box(low=0, high=255, shape=(128, 128, 3), dtype=np.uint8)
        return

    def get_dt(self):
        return self._dt

    def step(self, action):
        for i in range(self._skip_frame):
            from omni.isaac.core.utils.types import ArticulationAction

            self.jetbot.apply_wheel_actions(ArticulationAction(joint_velocities=action))
            self._my_world.step(render=False)
        observations = self.get_observations()
        info = {}
        # TODO: setup done flag
        done = False
        # TODO: setup reward calc
        reward = 0
        return observations, reward, done, info

    def reset(self):
        self._my_world.reset()
        observations = self.get_observations()
        return observations

    def get_observations(self):
        if self.observation_mode == "structured":
            # TODO: setup observations
            return np.zeros(2)
        elif self.observation_mode == "camera":
            self._my_world.render()
            gt = self.sd_helper.get_groundtruth(["rgb"], self.viewport_window)
            return gt["rgb"]

    def render(self, mode="human"):
        self._my_world.render()
        return

    def close(self):
        self._simulation_app.close()
        return

    def seed(self, seed=None):
        self.np_random, seed = gym.utils.seeding.np_random(seed)
        np.random.seed(seed)
        return [seed]

    def _set_camera(self):
        import omni.kit
        from omni.isaac.synthetic_utils import SyntheticDataHelper

        camera_path = "/jetbot/chassis/rgb_camera/jetbot_camera"
        viewport_handle = omni.kit.viewport.get_viewport_interface().create_instance()
        new_viewport_name = omni.kit.viewport.get_viewport_interface().get_viewport_window_name(viewport_handle)
        viewport_window = omni.kit.viewport.get_viewport_interface().get_viewport_window(viewport_handle)
        viewport_window.set_active_camera(camera_path)
        viewport_window.set_texture_resolution(128, 128)
        viewport_window.set_window_pos(1000, 400)
        viewport_window.set_window_size(420, 420)
        self.sd_helper = SyntheticDataHelper()
        self.viewport_window = viewport_window
        self.sd_helper.initialize(sensor_names=["rgb"], viewport=self.viewport_window)
        self._my_world.render()
        self.sd_helper.get_groundtruth(["rgb"], self.viewport_window)
        return
