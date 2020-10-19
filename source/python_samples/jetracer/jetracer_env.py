import torch
from torchvision.transforms import ColorJitter
import PIL
import numpy as np

import carb
import omni.kit.app
import omni.kit.editor
import omni.kit.asyncapi
import omni.kit.commands
from omni.isaac.dynamic_control import _dynamic_control
import omni.syntheticdata._syntheticdata as _synthetic_data

from pxr import UsdGeom, Gf, Sdf, Usd, PhysxSchema, PhysicsSchema, PhysicsSchemaTools, Semantics

import os
import time
import atexit
import asyncio
import numpy as np
import random
import matplotlib.pyplot as plt
from omni.isaac.synthetic_utils import visualization as vis
from omni.isaac.synthetic_utils import OmniKitHelper
from omni.isaac.synthetic_utils import SyntheticDataHelper
from omni.isaac.synthetic_utils import utils as ut

from jetracer import Jetracer
from road_environment import Environment
from gtc2020_track_utils import *

import gym
from gym import spaces


class JetracerEnv:
    metadata = {"render.modes": ["human"]}

    def __init__(self, omni_kit, z_height=0):
        self.action_space = spaces.Box(low=-1.0, high=1.0, shape=(2,), dtype=np.float32)
        self.observation_space = spaces.Box(low=0, high=255, shape=(224, 224, 6), dtype=np.uint8)

        self.color_jitter = ColorJitter(0.1, 0.05, 0.05, 0.05)
        self.noise = 0.05

        self.dt = 1 / 30.0
        self.omniverse_kit = omni_kit
        self.sd_helper = SyntheticDataHelper()
        self.roads = Environment(self.omniverse_kit)

        self.shape = [6, 6]
        self.roads.generate_road(self.shape)
        self.roads.generate_lights()

        # spawn robot
        self.jetracer = Jetracer(self.omniverse_kit)
        self.initial_loc = self.roads.get_valid_location()
        self.jetracer.spawn(Gf.Vec3d(self.initial_loc[0], self.initial_loc[1], 5), 0)

        # switch kit camera to jetracer camera
        self.jetracer.activate_camera()

        # start simulation
        self.omniverse_kit.play()

        # Step simulation so that objects fall to rest
        # wait until all materials are loaded
        frame = 0
        print("simulating physics...")
        while frame < 60 or self.omniverse_kit.is_loading():
            self.omniverse_kit.update(self.dt)
            frame = frame + 1
        print("done after frame: ", frame)

        self.initialized = False
        self.numsteps = 0
        self.numresets = 0
        self.maxresets = 10

        # LOCMOD set this to 1 after around 200k steps to randomnize less
        # self.maxresets = 1

    def calculate_reward(self):
        # distance to nearest point on path in units of block.  [0,1]
        # dist = self.roads.distance_to_path_in_tiles(self.current_pose)
        dist = center_line_dist(np.array([self.current_pose[0], self.current_pose[1]]))
        # print("Distance ", dist)

        self.dist = dist

        reward = self.current_speed * np.exp(-dist ** 2 / 0.05 ** 2)
        return reward

    def is_dead(self):
        # alive = self.roads.is_inside_path_boundary(self.current_pose)
        dist = center_line_dist(np.array([self.current_pose[0], self.current_pose[1]]))
        alive = dist < 0.7  # the width of the track is w = 1.22 LOCMOD revisit hardcoded
        return not alive

    def translate_action(self, action):
        return action

    def reset(self):
        if self.numresets % self.maxresets == 0:
            self.roads.reset(self.shape)

        if not self.initialized:
            state, reward, done, info, = self.step([0, 0])
            self.initialized = True

        loc = self.roads.get_valid_location()
        rot = random.uniform(-180, 180)
        self.jetracer.teleport(Gf.Vec3d(loc[0], loc[1], 5), rot, settle=True)

        obs = self.jetracer.observations()
        self.current_pose = obs["pose"]
        self.current_speed = np.linalg.norm(np.array(obs["linear_velocity"]))
        self.current_forward_velocity = obs["local_linear_velocity"][0]

        if self.numresets % self.maxresets == 0:
            frame = 0
            while self.omniverse_kit.is_loading():  # or frame < 750:
                self.omniverse_kit.update(self.dt)
                frame += 1

        gt = self.sd_helper.get_groundtruth(["rgb", "depth", "instanceSegmentation", "semanticSegmentation", "camera"])
        currentState = gt["rgb"][:, :, :3]
        # print(currentState.shape)

        img = np.concatenate((currentState, currentState), axis=2)
        img = np.clip((255 * self.noise * np.random.randn(224, 224, 6) + img.astype(np.float)), 0, 255).astype(np.uint8)

        self.numsteps = 0
        self.previousState = currentState
        self.numresets += 1

        return img

    def step(self, action):
        print("Number of steps ", self.numsteps)

        # print("Action ", action)

        translated_action = self.translate_action(action)
        self.jetracer.command(translated_action)
        frame = 0
        total_reward = 0
        reward = 0
        while frame < 3:
            self.omniverse_kit.update(self.dt)
            obs = self.jetracer.observations()
            self.current_pose = obs["pose"]
            self.current_speed = np.linalg.norm(np.array(obs["linear_velocity"]))
            self.current_forward_velocity = obs["local_linear_velocity"][0]

            reward = self.calculate_reward()
            done = self.is_dead()

            total_reward += reward
            frame = frame + 1

        gt = self.sd_helper.get_groundtruth(["rgb", "depth", "instanceSegmentation", "semanticSegmentation", "camera"])
        depth = np.expand_dims(gt["depth"], -1)
        segmentation = vis.semantic_segmentation_to_rgb(ut.to_numpy(gt["semanticSegmentation"][1]))
        segmentation = segmentation

        currentState = gt["rgb"][:, :, :3]

        if not self.initialized:
            self.previousState = currentState

        img = np.concatenate((currentState, self.previousState), axis=2)
        img = np.clip((255 * self.noise * np.random.randn(224, 224, 6) + img.astype(np.float)), 0, 255).astype(np.uint8)

        self.previousState = currentState

        other = np.array(
            [*obs["pose"], *obs["linear_velocity"], *obs["local_linear_velocity"], *obs["angular_velocity"]]
        )
        other = np.expand_dims(other.astype(float), 0)

        self.numsteps += 1
        if done:
            print("robot is dead")

        if self.numsteps > 500:
            done = True
            print("robot stepped 500 times")

        if self.dist > 0.7:  # width of the track is w=1.22 LOCMOD revisit hardcoded
            print("robot out of bounds. dist = ", self.dist)
            done = True
        # LOCMOD revisit
        if self.current_forward_velocity <= -20:
            print("robot was going backwards forward velocity = ", self.current_forward_velocity)
            done = True

        return img, reward, done, {}
