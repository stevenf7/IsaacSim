# Copyright (c) 2020, NVIDIA CORPORATION.  All rights reserved.
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.


from omni.isaac.gym.vec_env import VecEnvBase

import torch
import numpy as np


# VecEnv Wrapper for RL training
class VecEnv(VecEnvBase):
    def _parse_data(self, data):
        self.obs = torch.clamp(data["obs"], -self.clip_obs, self.clip_obs).to(self.rl_device).clone()
        self.rew = data["rew"].to(self.rl_device).clone()
        self.states = torch.clamp(data["states"], -self.clip_obs, self.clip_obs).to(self.rl_device).clone()
        self.resets = data["reset"].to(self.rl_device).clone()
        self.extras = data["extras"].copy()

    def get_state(self):
        return self.states

    def step(self, actions):
        actions = torch.clamp(actions, -self.clip_actions, self.clip_actions).clone()
        self._task.pre_physics_step(actions)

        self._world.step(render=self._render)
        self.sim_frame_count += 1
        self._task.post_physics_step()

        data = self._parse_data(self._task.data)
        obs_dict = {"obs": self.obs, "states": self.states}

        return obs_dict, self.rew, self.resets, self.extras

    def reset(self):
        self._task.reset()
        actions = torch.zeros((self.num_environments, self.num_actions), device=self._task.device)
        obs_dict, _, _, _ = self.step(actions)

        return obs_dict
