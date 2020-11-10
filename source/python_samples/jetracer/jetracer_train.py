import torch
import os
import sys
import json
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

# Use this to switch from training to evaluation
TRAINING_MODE = True

# RL environment and agent JSON config files
ENV_CONFIG = None
AGENT_CONFIG = None

# All outputs for the experiment, go in the experiment dir
EXP_DIR = "."


def train():
    omniverse_kit = OmniKitHelper(CUSTOM_CONFIG)

    # we disable all anti aliasing in the render because we want to train on the raw camera image.
    omniverse_kit.set_setting("/rtx/post/aa/op", 0)

    env = JetracerEnv(omniverse_kit, ENV_CONFIG)

    checkpoint_callback = CheckpointCallback(save_freq=1000, save_path=EXP_DIR + "/params/", name_prefix="rl_model")

    net_arch = [512, 256, dict(pi=[128, 64, 32], vf=[128, 64, 32])]
    policy_kwargs = {"net_arch": net_arch, "features_extractor_class": CustomCNN, "activation_fn": torch.nn.ReLU}

    # create a new model
    model = PPO(
        "CnnPolicy",
        env,
        verbose=1,
        tensorboard_log=EXP_DIR + "/tensorboard",
        policy_kwargs=policy_kwargs,
        device="cuda",
    )

    # load an existing model and continue training
    # model = PPO.load("params/rl_model_125999_steps.zip", env)

    model.learn(
        total_timesteps=450000,
        callback=checkpoint_callback,
        eval_env=env,
        eval_freq=1000,
        eval_log_path=EXP_DIR + "/eval_log/",
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

    env = JetracerEnv(omniverse_kit, ENV_CONFIG)
    obs = env.reset()

    while True:
        action = agent.predict(obs)
        print(action)
        obs, rew, done, infos = env.step(action[0])
        if done:
            obs = env.reset()


if __name__ == "__main__":

    # Check the command line usage
    if len(sys.argv) > 2:
        print("Usage : python jetracer_train.py [EXP_DIR]")
        exit(1)

    # Grab EXP_DIR from the command line
    if len(sys.argv) == 2:
        EXP_DIR = sys.argv[1]

    # Parse the experimetn JSON
    exp_json_path = EXP_DIR + "/exp.json"
    if os.path.exists(exp_json_path):
        with open(exp_json_path) as f:
            exp_data = json.load(f)
            ENV_CONFIG = EXP_DIR + "/" + exp_data["env_config"]

    print("TRAINING_MODE = {}".format(TRAINING_MODE))
    print("ENV_CONFIG = {}".format(ENV_CONFIG))
    print("AGENT_CONFIG = {}".format(AGENT_CONFIG))

    def handle_exit(*args, **kwargs):
        print("Exiting training...")
        quit()

    signal.signal(signal.SIGINT, handle_exit)

    if TRAINING_MODE:
        train()
    else:
        runEval()
