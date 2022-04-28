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
    """ This class provides a base interface for connecting RL policies with task implementations.
        APIs provided in this interface follow the interface in gym.Env.
        This class also provides utilities for initializing simulation apps, creating the World,
        and initializing task and RL metadata.
    """

    def __init__(self, config: dict, headless: bool, start_sim: bool = True) -> None:
        """ Initializes RL and task parameters.

        Args:
            config (dict): Dictionary of config values for setting up task and RL parameters.
                           The dictionary can contain clip ranges for observations and actions buffers,
                           device for RL policy, and control frequency for applying actions.
            headless (bool): Whether to run training headless.
            start_sim (Opational[bool]): Whether to start sim immediately after initializing task. Defaults to True.
        """

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

    def _start_sim(self) -> None:
        """ Starts sim by resetting world.
        """

        if self._init_sim:
            self._world.reset()

    def set_task(
        self, task, task_data, backend="numpy", sim_params=None, obs_space=None, state_space=None, act_space=None
    ) -> None:
        """ Creates a World object and adds Task to World. 
            Initializes and sets task parameters required by RL.

        Args:
            task (RLTask): The task to run.
            task_data (dict): RL-specific task data initialized by task.
            backend (str): Backend to use for task. Can be "numpy" or "torch". Defaults to "numpy".
            sim_params (dict): Simulation parameters for physics settings. Defaults to None.
            obs_space (gym.spaces): Observation space for the task. Defaults to None.
            state_space (gym.spaces): State space for the task. Defaults to None.
            act_space (gym.spaces): Action space for the task. Defaults to None.
        """

        from omni.isaac.core.world import World

        self._world = World(stage_units_in_meters=1.0, rendering_dt=1.0 / 60.0, backend=backend, sim_params=sim_params)
        self._world.add_task(task)
        self._task = task
        self._set_metadata(task_data, obs_space, state_space, act_space)

        if self._world.get_physics_context().use_gpu_pipeline:
            self._world.get_physics_context().enable_flatcache(True)

        self._start_sim()

    def _set_metadata(self, data, obs_space=None, state_space=None, act_space=None) -> None:
        """ Sets metadata for task and RL.

        Args:
            data (dict): RL-specific task data initialized by the task.
            obs_space (gym.spaces): Observation space for the task. Defaults to None.
            state_space (gym.spaces): State space for the task. Defaults to None.
            act_space (gym.spaces): Action space for the task. Defaults to None.
        """

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

    def render(self, mode="human") -> None:
        """ Step the renderer.

        Args:
            mode (str): Select mode of rendering based on OpenAI environments.
        """

        if mode == "human":
            self._world.render()
        else:
            gym.Env.render(self, mode=mode)
        return

    def close(self) -> None:
        """ Closes simulation.
        """

        self._simulation_app.close()
        return

    def seed(self, seed=-1):
        """ Sets a seed. Pass in -1 for a random seed.

        Args:
            seed (int): Seed to set. Defaults to -1.
        Returns:
            seed (int): Seed that was set.
        """

        from omni.isaac.core.utils.torch.maths import set_seed

        return set_seed(seed)

    def step(self, actions):
        """ Basic implementation for stepping simulation. Can be overriden by inherited Env classes
            to satisfy requirements of specific RL libraries. This method passes actions to task
            for processing, steps simulation, and computes observations, rewards, and resets.

        Args:
            actions (Union[numpy.ndarray, torch.Tensor]): Actions buffer from policy.
        Returns:
            observations(Union[numpy.ndarray, torch.Tensor]): Buffer of observation data.
            rewards(Union[numpy.ndarray, torch.Tensor]): Buffer of rewards data.
            dones(Union[numpy.ndarray, torch.Tensor]): Buffer of resets/dones data.
            info(dict): Dictionary of extras data.
        """
        self._task.pre_physics_step(actions)
        self._world.step(render=self._render)

        self.sim_frame_count += 1

        observations = self._task.get_observations()
        rewards = self._task.calculate_metrics()
        dones = self._task.is_done()
        info = {}

        return observations, rewards, dones, info

    def reset(self):
        """ Resets the task. """
        self._task.reset()

    @property
    def observation_space(self):
        """ Retrieves observation space for task.

        Returns:
            observation_space(gym.Spaces): Observation space.
        """
        return self._obs_space

    @property
    def action_space(self):
        """ Retrieves action space for task.

        Returns:
            action_space(gym.Spaces): Action space.
        """
        return self._act_space

    @property
    def num_envs(self):
        """ Retrieves number of environments.

        Returns:
            num_envs(int): Number of environments.
        """
        return self._num_environments

    @property
    def num_acts(self):
        """ Retrieves dimension of actions.

        Returns:
            num_acts(int): Dimension of actions.
        """
        return self._num_actions

    @property
    def num_obs(self):
        """ Retrieves dimension of observations.

        Returns:
            num_obs(int): Dimension of observations.
        """
        return self._num_observations

    @property
    def num_states(self):
        """ Retrieves dimesion of states.

        Returns:
            num_states(int): Dimension of states.
        """
        return self._num_states
