# Copyright (c) 2020-2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

import math
import numpy as np
from pxr import Gf

from omni.isaac.samples.scripts.utils.franka import Franka, default_config
from omni.isaac.samples.scripts.utils.world import World
from omni.isaac.samples.scripts.utils.state_machine import *
from .scenario import Scenario, create_solid_franka, create_rubiks_cube, create_background, setup_physics


class MultipleObstacle(Scenario):
    """ Defines an obstacle avoidance scenario

    Scenarios define the life cycle within kit and handle init, startup, shutdown etc.
    """

    def __init__(self, dc, mp):
        super().__init__(dc, mp)
        self.editor_step_count = [0, 0]
        self.incrementor = [1, 1]
        self.mid = [200, 1000]

    def step(self, step):
        if self._timeline.is_playing() and self._running:
            # Logic for generating motion of both rubiks cubes
            new_loc_y = (self.editor_step_count[0] - self.mid[0]) / self.mid[0] * math.pi * 0.5
            new_loc_z = (self.editor_step_count[1] - self.mid[1]) / self.mid[1] * math.pi * 0.5
            for prim in self._stage.GetPrimAtPath("/environments").GetChildren():
                obstacle_path = str(prim.GetPath()) + "/Rubiks_cube"
                obstacle_prim = self._stage.GetPrimAtPath(obstacle_path)
                if obstacle_prim:
                    translate_attr = obstacle_prim.GetAttribute("xformOp:translate")
                    translate_attr.Set(Gf.Vec3d(38, -20 * math.sin(new_loc_y), 50))
                obstacle_path = str(prim.GetPath()) + "/Rubiks_cube1"
                obstacle_prim = self._stage.GetPrimAtPath(obstacle_path)
                if obstacle_prim:
                    translate_attr = obstacle_prim.GetAttribute("xformOp:translate")
                    translate_attr.Set(Gf.Vec3d(38, 0, -30 * math.sin(new_loc_z) + 60))
            for i in range(len(self.editor_step_count)):
                self.editor_step_count[i] = self.editor_step_count[i] + self.incrementor[i]
                if self.editor_step_count[i] > 2 * self.mid[i]:
                    self.incrementor[i] = -1
                if self.editor_step_count[i] < 0:
                    self.incrementor[i] = 1
            # Update franka
            self.franka.update()
            self.world.update()

    def create_franka(self, *args):
        super().create_franka()

        # Load robot environment and set its transform
        env_path = "/environments/env"
        create_solid_franka(self._stage, env_path, self.franka_table_usd, Gf.Vec3d(0, 0, 0))
        # Load first rubiks cube and set its transform
        create_rubiks_cube(self._stage, self.rubiks_cube_usd, env_path + "/Rubiks_cube", Gf.Vec3d(-10, -30, 12))
        # Load second rubiks cube and set its transform
        create_rubiks_cube(self._stage, self.rubiks_cube_usd, env_path + "/Rubiks_cube1", Gf.Vec3d(-10, 30, 12))
        # Load background
        create_background(self._stage, self.background_usd)
        # Setup physics simulation
        setup_physics(self._stage)

    def register_assets(self, *args):
        # Retrieve two rubiks cubes path in the scene
        prim = self._stage.GetPrimAtPath("/environments/env")
        obstacle_path = str(prim.GetPath()) + "/Rubiks_cube"
        obstacle_path_1 = str(prim.GetPath()) + "/Rubiks_cube1"

        # Create world and robot object
        self.world = World(self._dc, self._mp)
        self.franka = Franka(
            self._stage,
            self._stage.GetPrimAtPath(str(prim.GetPath()) + "/Franka/panda"),
            self._dc,
            self._mp,
            self.world,
            default_config,
        )

        # Set robot end effector
        orig = np.array([0.37431321144104004, 5.1372178859310225e-05, 0.4564971923828125])
        axis_z = np.array([0.4785744547843933, 0.00031368513009510934, -0.8780469298362732])
        self.franka.end_effector.go_local(
            orig=orig,
            axis_x=[],
            axis_y=[],
            axis_z=axis_z,
            use_default_config=True,
            wait_for_target=False,
            wait_time=5.0,
        )

        # Register both rubiks cubes and set them as obstacles
        self.world.register_object(0, str(prim.GetPath()) + "/DemoTable/simple_table/CollisionCube", "table")
        self.world.register_object(0, obstacle_path, "rubiks_cube")
        self.world.register_object(0, obstacle_path_1, "rubiks_cube1")
        self.world.make_obstacle("rubiks_cube", 3, (0.072, 0.072, 0.072))
        self.world.make_obstacle("rubiks_cube1", 3, (0.072, 0.072, 0.072))

        # Track the handles of the two rubiks cubes as obstacles
        self._obstacles.append(self.world.get_object_from_name("rubiks_cube"))
        self._obstacles.append(self.world.get_object_from_name("rubiks_cube1"))

    def perform_tasks(self, *args):
        super().perform_tasks()

    def stop_tasks(self, *args):
        super().stop_tasks()
