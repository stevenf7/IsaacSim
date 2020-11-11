import torch
import numpy as np
import os
import carb
import signal
import argparse

from omni.isaac.synthetic_utils import OmniKitHelper

from jetbot_env import JetbotEnv
from jetbot_model import CustomCNN

from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import BaseCallback, CheckpointCallback

# use this to switch from training to evaluation
TRAINING_MODE = True


def train(args):
    print("TEST 1")
    CUSTOM_CONFIG = {
        "width": 224,
        "height": 224,
        "renderer": "RayTracedLighting",
        "headless": args.headless,
        "experience": f'{os.environ["EXP_PATH"]}/isaac-sim-python.json',
    }
    omniverse_kit = OmniKitHelper(CUSTOM_CONFIG)

    # we disable all anti aliasing in the render because we want to train on the raw camera image.
    omniverse_kit.set_setting("/rtx/post/aa/op", 0)
    print("TEST 2")
    env = JetbotEnv(omniverse_kit, max_resets=args.rand_freq, updates_per_step=3)
    print("TEST 3")
    checkpoint_callback = CheckpointCallback(save_freq=args.save_freq, save_path="./params/", name_prefix=args.name)
    print("TEST 4")
    net_arch = [512, 256, dict(pi=[128, 64, 32], vf=[128, 64, 32])]
    policy_kwargs = {"net_arch": net_arch, "features_extractor_class": CustomCNN, "activation_fn": torch.nn.ReLU}
    print("TEST 5")
    if args.loadedCheckpoint=="":
        print("TEST 5.1")
        model = PPO("CnnPolicy", env, verbose=1, tensorboard_log=args.tensorboardDir, policy_kwargs=policy_kwargs, device="cuda", n_steps=args.step_freq)
    else:
        print("TEST 5.2")
        model = PPO.load(args.loadedCheckpoint,env)
    print("TEST 6")
    model.learn(
        total_timesteps=args.total_steps,
        callback=checkpoint_callback,
        eval_env=env,
        eval_freq=args.eval_freq,
        eval_log_path=args.evaluationDir,
        reset_num_timesteps=args.resetNumTimesteps,
    )
    model.save(args.name+".zip")


def runEval(args):
    CUSTOM_CONFIG = {
        "width": 224,
        "height": 224,
        "renderer": "RayTracedLighting",
        "headless": args.headless,
        "experience": f'{os.environ["EXP_PATH"]}/isaac-sim-python.json',
    }
    # load a zip file to evaluate here
    agent = PPO.load(args.evaluationDir+"/best_model.zip", device="cuda")

    omniverse_kit = OmniKitHelper(CUSTOM_CONFIG)

    # we disable all anti aliasing in the render because we want to train on the raw camera image.
    omniverse_kit.set_setting("/rtx/post/aa/op", 0)

    env = JetbotEnv(omniverse_kit)
    obs = env.reset()

    while True:
        action = agent.predict(obs)
        print(action)
        obs, rew, done, infos = env.step(action[0])
        if done:
            obs = env.reset()


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("loadedCheckpoint", 
                        help="path to checkpoint to be loaded", 
                        default="",
                        nargs='?', 
                        type=str)
    
    parser.add_argument("-e", "--eval", 
                        help="evaluate checkpoint", 
                        action="store_true")

    parser.add_argument("-r", "--resetNumTimesteps", 
                        help="reset the current timestep number (used in logging)", 
                        action="store_true")

    parser.add_argument("-d", "--headless", 
                        help="run in headless mode (no GUI)", 
                        action="store_true")

    parser.add_argument("--name", 
                        help="name of checkpoint file (no suffix)", 
                        default="checkpoint_25k", 
                        type=str)

    parser.add_argument("--tensorboardDir", 
                        help="path to tensorboard log directory", 
                        default="tensorboard", 
                        type=str)

    parser.add_argument("--evaluationDir", 
                        help="path to evaluation log directory", 
                        default="eval_log", 
                        type=str)

    parser.add_argument("--save_freq", 
                        help="number of steps before saving a checkpoint", 
                        default=1000, 
                        type=int)

    parser.add_argument("--eval_freq", 
                        help="number of steps before running an evaluation", 
                        default=1000, 
                        type=int)

    parser.add_argument("--step_freq", 
                        help="number of steps before executing a PPO update", 
                        default=1000, 
                        type=int)

    parser.add_argument("--rand_freq", 
                        help="number of environment resets before domain randomization", 
                        default=10, 
                        type=int)

    parser.add_argument("--total_steps", 
                        help="the total number of steps before exiting and saving a final checkpoint", 
                        default=25000, 
                        type=int)
    
    args = parser.parse_args()
    print(args)
    def handle_exit(*args, **kwargs):
        print("Exiting training...")
        quit()

    signal.signal(signal.SIGINT, handle_exit)

    if args.eval:
        runEval(args)
    else:
        train(args)
