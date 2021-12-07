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


class JetBotEnv(gym.Env):
    metadata = {"render.modes": ["human"]}

    def __init__(
        self,
        skip_frame=1,
        physics_dt=1.0 / 60.0,
        rendering_dt=1.0 / 60.0,
        max_episode_length=1000,
        seed=0,
        observation_mode="structured",
        headless=True,
    ) -> None:
        from omni.isaac.kit import SimulationApp

        self._simulation_app = SimulationApp({"headless": headless})
        self._skip_frame = skip_frame
        self._dt = physics_dt * self._skip_frame
        self._max_episode_length = max_episode_length
        self._steps_after_reset = int(rendering_dt / physics_dt)
        self.observation_mode = observation_mode
        from omni.isaac.core import World
        from omni.isaac.jetbot import Jetbot
        from omni.isaac.core.objects import VisualCuboid

        self._my_world = World(physics_dt=physics_dt, rendering_dt=rendering_dt, stage_units_in_meters=0.01)
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
        self.seed(seed)
        if self.observation_mode == "camera":
            self.sd_helper = None
            self.viewport_window = None
            self._set_camera()
        self.reward_range = (-float("inf"), float("inf"))
        gym.Env.__init__(self)
        self.action_space = spaces.Box(low=-10.0, high=10.0, shape=(2,), dtype=np.float32)
        if self.observation_mode == "structured":
            self.observation_space = spaces.Box(low=float("inf"), high=float("inf"), shape=(17,), dtype=np.float32)
        elif self.observation_mode == "camera":
            self.observation_space = spaces.Box(low=0, high=255, shape=(64, 64, 3), dtype=np.uint8)
        return

    def get_dt(self):
        return self._dt

    def step(self, action):
        previous_jetbot_position, _ = self.jetbot.get_world_pose()
        for i in range(self._skip_frame):
            from omni.isaac.core.utils.types import ArticulationAction

            self.jetbot.apply_wheel_actions(ArticulationAction(joint_velocities=action * 10.0))
            self._my_world.step(render=False)
        observations = self.get_observations()
        info = {}
        done = False
        if self._my_world.current_time_step_index - self._steps_after_reset >= self._max_episode_length:
            done = True
        reward = 0
        previous_dist_to_goal = np.linalg.norm(observations[10:13] - previous_jetbot_position)
        current_dist_to_goal = np.linalg.norm(observations[10:13] - observations[0:3])
        reward += previous_dist_to_goal - current_dist_to_goal
        # TODO: avoid obstacle reward
        return observations, reward, done, info

    def reset(self):
        self._my_world.reset()
        observations = self.get_observations()
        return observations

    def get_observations(self):
        if self.observation_mode == "structured":
            jetbot_world_position, jetbot_world_orientation = self.jetbot.get_world_pose()
            jetbot_linear_velocity = self.jetbot.get_linear_velocity()
            goal_world_position, goal_world_orientation = self.goal.get_world_pose()
            return np.concatenate(
                [
                    jetbot_world_position,
                    jetbot_world_orientation,
                    jetbot_linear_velocity,
                    goal_world_position,
                    goal_world_orientation,
                ]
            )
        elif self.observation_mode == "camera":
            self._my_world.render()
            gt = self.sd_helper.get_groundtruth(["rgb"], self.viewport_window, verify_sensor_init=False)
            return gt["rgb"][:, :, :3]

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
        viewport_window.set_texture_resolution(64, 64)
        viewport_window.set_window_pos(1000, 400)
        viewport_window.set_window_size(420, 420)
        self.sd_helper = SyntheticDataHelper()
        self.viewport_window = viewport_window
        self.sd_helper.initialize(sensor_names=["rgb"], viewport=self.viewport_window)
        self._my_world.render()
        self.sd_helper.get_groundtruth(["rgb"], self.viewport_window)
        return
