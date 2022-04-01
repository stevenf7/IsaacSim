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
    """[summary]

        Args:
            name (str): [description]
        """

    def __init__(self, name, env, offset=None) -> None:

        super().__init__(name=name, offset=offset)

        # optimization flags for pytorch JIT
        torch._C._jit_set_profiling_mode(False)
        torch._C._jit_set_profiling_executor(False)

        self.test = self._cfg["test"]
        self._device = self._cfg["sim_device"] if self._sim_config.sim_params["use_gpu_pipeline"] else "cpu"
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

        self.stop = False
        self.cleanup()

    def cleanup(self):
        self.stop = False

        # prepare tensors
        self.obs_buf = torch.zeros((self._num_envs, self.num_observations), device=self._device, dtype=torch.float)
        self.states_buf = torch.zeros((self._num_envs, self.num_states), device=self._device, dtype=torch.float)
        self.rew_buf = torch.zeros(self._num_envs, device=self._device, dtype=torch.float)
        self.reset_buf = torch.ones(self._num_envs, device=self._device, dtype=torch.long)
        self.progress_buf = torch.zeros(self._num_envs, device=self._device, dtype=torch.long)
        self.extras = {}

    def set_up_scene(self, scene):
        super().set_up_scene(scene)

        if self._sim_config.task_config["sim"]["add_ground_plane"]:
            scene.add_default_ground_plane()
        prim_paths = self._cloner.generate_paths("/World/envs/env", self._num_envs)
        self._env_pos = self._cloner.clone(source_prim_path="/World/envs/env_0", prim_paths=prim_paths)
        self._env_pos = torch.tensor(self._env_pos, device=self._device, dtype=torch.float)
        self._cloner.filter_collisions("/World/collisions", prim_paths)

    @property
    def default_base_env_path(self):
        return "/World/envs"

    @property
    def default_zero_env_path(self):
        return f"{self.default_base_env_path}/env_0"

    @property
    def num_envs(self):
        return self._num_envs

    @property
    def data(self):
        return self._data

    def get_states(self):
        pass

    def get_extras(self):
        pass

    def reset(self):
        self.reset_buf = torch.ones_like(self.reset_buf)

    def pre_physics_step(self, actions):
        pass

    def post_physics_step(self):

        self.progress_buf[:] += 1

        self.get_observations()
        self.get_states()
        self.calculate_metrics()
        self.is_done()
        self.get_extras()

        # write states to queue
        data = dict()
        data["obs"] = self.obs_buf.clone()
        data["rew"] = self.rew_buf.clone()
        data["reset"] = self.reset_buf.clone()
        data["extras"] = self.extras.copy()
        data["states"] = self.states_buf.clone()
        self._data = data
