# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

from omni.isaac.kit import SimulationApp

from abc import abstractmethod
import gym
from gym import spaces
import numpy as np


class VecEnvBase(gym.Env):
    """[summary]

        Args:
            name (str): [description]
        """

    def __init__(self, config, headless, start_sim=True):
        self._simulation_app = SimulationApp({"headless": headless})

        self._render = not headless
        self._cfg = config
        self._init_sim = start_sim

        self.clip_obs = self._cfg["task"]["env"].get("clipObservations", np.Inf)
        self.clip_actions = self._cfg["task"]["env"].get("clipActions", np.Inf)
        self.rl_device = self._cfg.get("rl_device", "cuda:0")

        self._control_frequency_inv = self._cfg["task"]["env"].get("controlFrequencyInv", 1)

        print("RL device: ", self.rl_device)

        self.sim_frame_count = 0

    def _start_sim(self):
        if self._init_sim:
            self._world.reset()

    def set_task(
        self, task, task_data, backend="numpy", sim_params=None, obs_space=None, state_space=None, act_space=None
    ):
        from omni.isaac.core.world import World

        self._world = World(stage_units_in_meters=1.0, rendering_dt=1.0 / 60.0, backend=backend, sim_params=sim_params)
        self._world.add_task(task)
        self._task = task
        self._set_metadata(task_data, obs_space, state_space, act_space)

        self._start_sim()

    def _set_metadata(self, data, obs_space=None, state_space=None, act_space=None):
        self._num_environments = data["num_envs"]
        self._num_agents = data["num_agents"]
        self._num_observations = data["num_obs"]
        self._num_states = data["num_states"]
        self._num_actions = data["num_actions"]

        self._obs_space = obs_space
        self._state_space = state_space
        self._act_space = act_space

        if self._obs_space is None:
            self._obs_space = spaces.Box(np.ones(self.num_obs) * -np.Inf, np.ones(self.num_obs) * np.Inf)
        if self._state_space is None:
            self._state_space = spaces.Box(np.ones(self.num_states) * -np.Inf, np.ones(self.num_states) * np.Inf)
        if self._act_space is None:
            self._act_space = spaces.Box(np.ones(self.num_acts) * -1.0, np.ones(self.num_acts) * 1.0)

    def render(self, mode="human"):
        if mode == "human":
            self._world.render()
        else:
            gym.Env.render(self, mode=mode)
        return

    def close(self):
        self._simulation_app.close()
        return

    def seed(self, seed=-1):
        from omni.isaac.core.utils.torch.maths import set_seed

        return set_seed(seed)

    def step(self, actions):
        self._task.pre_physics_step(actions)
        self._world.step(render=self._render)

        self.sim_frame_count += 1

        observations = self._task.get_observations()
        rewards = self._task.calculate_metrics()
        dones = self._task.is_done()
        info = {}

        return observations, rewards, dones, info

    def reset(self):
        self._task.reset()

    @property
    def observation_space(self):
        return self._obs_space

    @property
    def action_space(self):
        return self._act_space

    @property
    def num_envs(self):
        return self._num_environments

    @property
    def num_acts(self):
        return self._num_actions

    @property
    def num_obs(self):
        return self._num_observations

    @property
    def num_states(self):
        return self._num_states
