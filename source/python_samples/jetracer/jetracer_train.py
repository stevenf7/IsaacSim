import torch
import os
import signal

from omni.isaac.synthetic_utils import OmniKitHelper

from jetracer_env import JetracerEnv
from jetracer_model import CustomCNN

from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import BaseCallback, CheckpointCallback


CUSTOM_CONFIG = {
    "width": 224,
    "height": 224,
    "renderer": "RayTracedLighting",
    "headless": False,
    "experience": f'{os.environ["EXP_PATH"]}/isaac-sim-python.json',
}

# use this to switch from training to evaluation
TRAINING_MODE = True


def train():
    omniverse_kit = OmniKitHelper(CUSTOM_CONFIG)

    # we disable all anti aliasing in the render because we want to train on the raw camera image.
    omniverse_kit.set_setting("/rtx/post/aa/op", 0)

    env = JetracerEnv(omniverse_kit)

    checkpoint_callback = CheckpointCallback(save_freq=1000, save_path="./params/", name_prefix="rl_model")

    net_arch = [512, 256, dict(pi=[128, 64, 32], vf=[128, 64, 32])]
    policy_kwargs = {"net_arch": net_arch, "features_extractor_class": CustomCNN, "activation_fn": torch.nn.ReLU}

    # create a new model
    model = PPO("CnnPolicy", env, verbose=1, tensorboard_log="tensorboard", policy_kwargs=policy_kwargs, device="cuda")

    # load an existing model and continue training
    # model = PPO.load("params/rl_model_125999_steps.zip", env)

    model.learn(
        total_timesteps=450000,
        callback=checkpoint_callback,
        eval_env=env,
        eval_freq=1000,
        eval_log_path="./eval_log/",
        reset_num_timesteps=False,
    )
    model.save("checkpoint_1900k")


def runEval():
    # load a zip file to evaluate here. PPO also saves the best model so far in the eval_log folder.
    # You can evaluate those zip files in the params folder as well (i.e params/rl_model_125999_steps.zip)
    agent = PPO.load("eval_log/best_model.zip", device="cuda")

    omniverse_kit = OmniKitHelper(CUSTOM_CONFIG)

    # we disable all anti aliasing in the render because we want to train on the raw camera image.
    omniverse_kit.set_setting("/rtx/post/aa/op", 0)

    env = JetracerEnv(omniverse_kit)
    obs = env.reset()

    while True:
        action = agent.predict(obs)
        print(action)
        obs, rew, done, infos = env.step(action[0])
        if done:
            obs = env.reset()


if __name__ == "__main__":

    def handle_exit(*args, **kwargs):
        print("Exiting training...")
        quit()

    signal.signal(signal.SIGINT, handle_exit)

    if TRAINING_MODE:
        train()
    else:
        runEval()
