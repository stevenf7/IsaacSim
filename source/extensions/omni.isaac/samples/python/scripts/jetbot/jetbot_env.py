import torch
import numpy as np

import carb

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

from jetbot import Jetbot
from road_environment import Environment

import gym
from gym import spaces


class JetbotEnv:
    metadata = {"render.modes": ["human"]}

    def __init__(self, omni_kit, z_height=0, max_resets=10, updates_per_step=3):
        self.action_space = spaces.Box(low=-2.0, high=2.0, shape=(2,), dtype=np.float32)
        # IMPORTANT NOTE!  SB3 wraps all image spaces in a transposer.
        # it assumes the image outputed is of standard form
        self.observation_space = spaces.Box(low=0, high=255, shape=(224, 224, 6), dtype=np.uint8)
        self.noise = 0.05

        # every time we update the stage, this is how much time will be simulated
        self.dt = 1 / 30.0
        self.omniverse_kit = omni_kit
        self.sd_helper = SyntheticDataHelper()
        self.roads = Environment(self.omniverse_kit)

        # we are going to train on a randomized loop that fits in a 6x6 tile area.
        self.shape = [6, 6]
        self.roads.generate_road(self.shape)
        self.roads.generate_lights()

        # spawn robot
        self.jetbot = Jetbot(self.omniverse_kit)
        self.initial_loc = self.roads.get_valid_location()
        self.jetbot.spawn(Gf.Vec3d(self.initial_loc[0], self.initial_loc[1], 5), 0)

        # switch kit camera to jetbot camera
        self.jetbot.activate_camera()

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
        self.maxresets = max_resets
        self.updates_per_step = updates_per_step

    def calculate_reward(self):
        # distance to nearest point on path in units of block.  [0,1]
        dist = self.roads.distance_to_path_in_tiles(self.current_pose)
        self.dist = dist

        reward = self.current_speed * np.exp(-dist ** 2 / 0.05 ** 2)
        return reward

    def is_dead(self):
        alive = self.roads.is_inside_path_boundary(self.current_pose)
        done = not alive

        if self.numsteps > 500:
            done = True

        if self.dist > 0.1:
            done = True

        if self.current_forward_velocity <= -1:
            done = True

        return done

    def to_numpy(self, data):
        """Helper to ensure data is on the CPU as a numpy array.
            """
        if isinstance(data, np.ndarray):
            return data
        elif type(data).__name__ == "Tensor":
            return data.cpu().numpy()
        else:
            raise ValueError(f"Unable to convert to numpy data of type {type(data)}.")

    def reset(self):
        # randomize the road configuration every self.maxresets resets.
        if self.numresets % self.maxresets == 0:
            self.roads.reset(self.shape)

        if not self.initialized:
            state, reward, done, info, = self.step([0, 0])
            self.initialized = True

        # every time we reset, we move the robot to a random location, with a random rotation in the horizontal plane
        loc = self.roads.get_valid_location()
        rot = random.uniform(-180, 180)
        self.jetbot.teleport(Gf.Vec3d(loc[0], loc[1], 5), rot, settle=True)

        obs = self.jetbot.observations()
        self.current_pose = obs["pose"]
        self.current_speed = np.linalg.norm(np.array(obs["linear_velocity"]))
        self.current_forward_velocity = obs["local_linear_velocity"][0]
        self.current_loc = self.roads.get_tile_from_pose(self.current_pose)
        self.previous_loc = self.roads.get_tile_from_pose(self.current_pose)
        self.dist = self.roads.distance_to_path_in_tiles(self.current_pose)

        # wait for loading
        if self.numresets % self.maxresets == 0:
            frame = 0
            while self.omniverse_kit.is_loading():
                self.omniverse_kit.update(self.dt)
                frame += 1

        gt = self.sd_helper.get_groundtruth(["rgb", "depth", "instanceSegmentation", "semanticSegmentation", "camera"])
        currentState = gt["rgb"][:, :, :3]

        img = np.concatenate((currentState, currentState), axis=2)
        img = np.clip((255 * self.noise * np.random.randn(224, 224, 6) + img.astype(np.float)), 0, 255).astype(np.uint8)

        self.numsteps = 0
        self.previousState = currentState
        self.numresets += 1

        return img

    def step(self, action):
        if self.initialized:
            self.previous_loc = self.current_loc

        self.jetbot.command(action)
        frame = 0
        total_reward = 0
        reward = 0

        while frame < self.updates_per_step:
            self.omniverse_kit.update(self.dt)
            obs = self.jetbot.observations()
            self.current_pose = obs["pose"]
            self.current_speed = np.linalg.norm(np.array(obs["linear_velocity"]))
            self.current_forward_velocity = obs["local_linear_velocity"][0]
            self.current_loc = self.roads.get_tile_from_pose(self.current_pose)
            if not self.initialized:
                self.previous_loc = self.roads.get_tile_from_pose(self.current_pose)

            reward = self.calculate_reward()

            total_reward += reward
            frame = frame + 1

        gt = self.sd_helper.get_groundtruth(["rgb", "depth", "instanceSegmentation", "semanticSegmentation", "camera"])
        depth = np.expand_dims(gt["depth"], -1)
        segmentation = vis.semantic_segmentation_to_rgb(self.to_numpy(gt["semanticSegmentation"][1]))
        segmentation = segmentation

        currentState = gt["rgb"][:, :, :3]

        if not self.initialized:
            self.previousState = currentState

        img = np.concatenate((currentState, self.previousState), axis=2)
        img = np.clip((255 * self.noise * np.random.randn(224, 224, 6) + img.astype(np.float)), 0, 255).astype(np.uint8)

        self.previousState = currentState

        self.numsteps += 1
        done = self.is_dead()

        return img, reward, done, {}
