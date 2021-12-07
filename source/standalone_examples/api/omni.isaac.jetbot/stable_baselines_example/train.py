# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

from env import JetBotEnv
from stable_baselines3 import PPO
from stable_baselines3.ppo import MlpPolicy
from stable_baselines3.ppo import CnnPolicy
import torch as th

# can be "camera" or "structured"
observation_mode = "camera"
log_dir = "./cnn_policy"
my_env = JetBotEnv(observation_mode=observation_mode)

if observation_mode == "structured":
    policy_kwargs = dict(activation_fn=th.nn.Tanh, net_arch=[256, 128])
    policy = MlpPolicy
elif observation_mode == "camera":
    policy_kwargs = dict(activation_fn=th.nn.Tanh, net_arch=[256, dict(pi=[128, 32], vf=[128, 32])])
    policy = CnnPolicy

model = PPO(
    policy,
    my_env,
    policy_kwargs=policy_kwargs,
    verbose=1,
    n_steps=10000,
    batch_size=1000,
    learning_rate=0.00025,
    gamma=0.9995,
    device="cuda",
    ent_coef=0,
    vf_coef=0.5,
    max_grad_norm=10,
    tensorboard_log=log_dir,
)
model.learn(total_timesteps=100000)

model.save(log_dir + "/jetbot_policy")

my_env.close()
