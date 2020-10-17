import torch
import numpy as np
import os
import carb
from omni.isaac.synthetic_utils import OmniKitHelper

from jetbot_env import JetbotEnv
from jetbot_model import CustomCNN

from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import BaseCallback, CheckpointCallback


CUSTOM_CONFIG = {
    "width": 224,
    "height": 224,
    "renderer": "RayTracedLighting",
    "headless": False,
    "experience": f'{os.environ["EXP_PATH"]}/isaac-sim-python.json',
}

if __name__ == "__main__":
    omniverse_kit = OmniKitHelper(CUSTOM_CONFIG)

    # we disable all anti aliasing in the render because we want to train on the raw camera image.
    omniverse_kit.set_setting("/rtx/post/aa/op", 0)

    env = JetbotEnv(omniverse_kit, max_resets=10, updates_per_step=3)

    checkpoint_callback = CheckpointCallback(save_freq=1000, save_path="./params/", name_prefix="rl_model")

    net_arch = [512, 256, dict(pi=[128, 64, 32], vf=[128, 64, 32])]
    policy_kwargs = {"net_arch": net_arch, "features_extractor_class": CustomCNN, "activation_fn": torch.nn.ReLU}

    model = PPO("CnnPolicy", env, verbose=1, tensorboard_log="tensorboard", policy_kwargs=policy_kwargs, device="cuda")
    # model = PPO.load("checkpoint_25k.zip",env)
    model.learn(
        total_timesteps=25000,
        callback=checkpoint_callback,
        eval_env=env,
        eval_freq=1000,
        eval_log_path="./eval_log/",
        reset_num_timesteps=False,
    )
    model.save("checkpoint_25k")
