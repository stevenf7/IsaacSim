# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
from abc import abstractmethod
import torch
from omni.isaac.core.tasks import BaseTask
from omni.isaac.core.utils.types import ArticulationAction
from omni.isaac.core.utils.prims import define_prim

from omni.isaac.cloner import GridCloner


class RLTask(BaseTask):

    """ This class provides a PyTorch RL-specific interface for setting up RL tasks. 
        It includes utilities for setting up RL task related parameters,
        cloning environments, and data collection for RL algorithms.
    """

    def __init__(self, name, env, offset=None) -> None:

        """ Initializes RL parameters, cloner object, and buffers.

        Args:
            name (str): Name of the task.
            offset (Optional[np.ndarray], optional): offset applied to all assets of the task. Defaults to None.
        """

        super().__init__(name=name, offset=offset)

        self.test = self._cfg["test"]
        self._device = self._cfg["sim_device"]
        print("Task Device:", self._device)

        self._env = env

        self.num_environments = self._cfg["task"]["env"]["numEnvs"]
        self.num_agents = self._cfg["task"]["env"].get("numAgents", 1)  # used for multi-agent environments
        self.num_observations = self._cfg["task"]["env"]["numObservations"]
        self.num_states = self._cfg["task"]["env"].get("numStates", 0)
        self.num_actions = self._cfg["task"]["env"]["numActions"]

        self._cloner = GridCloner(spacing=self._env_spacing)
        self._cloner.define_base_env(self.default_base_env_path)
        define_prim(self.default_zero_env_path)

        self.cleanup()

    def cleanup(self) -> None:
        """ Prepares torch buffers for RL data collection.

        Args:
            name (str): Name of the task.
            offset (Optional[np.ndarray], optional): offset applied to all assets of the task. Defaults to None.
        """

        # prepare tensors
        self.obs_buf = torch.zeros((self._num_envs, self.num_observations), device=self._device, dtype=torch.float)
        self.states_buf = torch.zeros((self._num_envs, self.num_states), device=self._device, dtype=torch.float)
        self.rew_buf = torch.zeros(self._num_envs, device=self._device, dtype=torch.float)
        self.reset_buf = torch.ones(self._num_envs, device=self._device, dtype=torch.long)
        self.progress_buf = torch.zeros(self._num_envs, device=self._device, dtype=torch.long)
        self.extras = {}

    def set_up_scene(self, scene) -> None:
        """ Clones environments based on value provided in task config and applies collision filters to mask 
            collisions across environments.

        Args:
            scene (Scene): Scene to add objects to.
        """

        super().set_up_scene(scene)

        if self._sim_config.task_config["sim"]["add_ground_plane"]:
            scene.add_default_ground_plane()
        prim_paths = self._cloner.generate_paths("/World/envs/env", self._num_envs)
        self._env_pos = self._cloner.clone(source_prim_path="/World/envs/env_0", prim_paths=prim_paths)
        self._env_pos = torch.tensor(self._env_pos, device=self._device, dtype=torch.float)
        self._cloner.filter_collisions("/World/collisions", prim_paths)

    @property
    def default_base_env_path(self):
        """ Retrieves default path to the parent of all env prims.

        Returns:
            default_base_env_path(str): Defaults to "/World/envs".
        """
        return "/World/envs"

    @property
    def default_zero_env_path(self):
        """ Retrieves default path to the first env prim (index 0).

        Returns:
            default_zero_env_path(str): Defaults to "/World/envs/env_0".
        """
        return f"{self.default_base_env_path}/env_0"

    @property
    def num_envs(self):
        """ Retrieves number of environments for task.

        Returns:
            num_envs(int): Number of environments.
        """
        return self._num_envs

    def get_states(self):
        """ API for retrieving states buffer, used for asymmetric AC training.

        Returns:
            states_buf(torch.Tensor): States buffer.
        """
        return self.states_buf

    def get_extras(self):
        """ API for retrieving extras data for RL.

        Returns:
            extras(dict): Dictionary containing extras data.
        """
        return self.extras

    def reset(self):
        """ Flags all environments for reset.
        """
        self.reset_buf = torch.ones_like(self.reset_buf)

    def pre_physics_step(self, actions):
        """ Optionally implemented by individual task classes to process actions.

        Args:
            actions (torch.Tensor): Actions generated by RL policy.
        """
        pass

    def post_physics_step(self):
        """ Processes RL required computations for observations, states, rewards, resets, and extras.
            Also maintains progress buffer for tracking step count per environment.

        Returns:
            obs_buf(torch.Tensor): Tensor of observation data.
            rew_buf(torch.Tensor): Tensor of rewards data.
            reset_buf(torch.Tensor): Tensor of resets/dones data.
            extras(dict): Dictionary of extras data.
        """

        self.progress_buf[:] += 1

        self.get_observations()
        self.get_states()
        self.calculate_metrics()
        self.is_done()
        self.get_extras()

        return self.obs_buf, self.rew_buf, self.reset_buf, self.extras
