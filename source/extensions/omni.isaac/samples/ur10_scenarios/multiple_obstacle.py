#!/usr/bin/env python
# Copyright (c) 2020, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

import random
import time, sys, os, math
import numpy as np
from pxr import Sdf, Gf, PhysicsSchema
import concurrent.futures

from ..utils.world import World
from ..utils.state_machine import *
from ..utils.ur10 import UR10, default_config
from ..utils.math_utils import *
from .scenario import *


class MultipleObstacle(Scenario):
    """ Defines an obstacle avoidance scenario

    Scenarios define the life cycle within kit and handle init, startup, shutdown etc. 
    """

    def __init__(self, editor, dc, mp):
        super().__init__(editor, dc, mp)
        self.editor_step_count = [0, 0]
        self.incrementor = [1, 1]
        self.mid = [200, 1000]

    def step(self, step):
        if self._editor.is_playing():
            # Logic for generating motion of both rubiks cubes
            new_loc_y = (self.editor_step_count[0] - self.mid[0]) / self.mid[0] * math.pi * 0.5
            new_loc_z = (self.editor_step_count[1] - self.mid[1]) / self.mid[1] * math.pi * 0.5
            for prim in self._stage.GetPrimAtPath("/environments").GetChildren():
                obstacle_path = str(prim.GetPath()) + "/Rubiks_cube"
                obstacle_prim = self._stage.GetPrimAtPath(obstacle_path)
                if obstacle_prim:
                    translate_attr = obstacle_prim.GetAttribute("xformOp:translate")
                    translate_attr.Set(Gf.Vec3d(38, -20 * math.sin(new_loc_y), 50))
                # obstacle_path = str(prim.GetPath()) + "/Rubiks_cube1"
                # obstacle_prim = self._stage.GetPrimAtPath(obstacle_path)
                # if obstacle_prim:
                #     translate_attr = obstacle_prim.GetAttribute("xformOp:translate")
                #     translate_attr.Set(Gf.Vec3d(38, 0, -30 * math.sin(new_loc_z) + 60))

            for i in range(len(self.editor_step_count)):
                self.editor_step_count[i] = self.editor_step_count[i] + self.incrementor[i]
                if self.editor_step_count[i] > 2 * self.mid[i]:
                    self.incrementor[i] = -1
                if self.editor_step_count[i] < 0:
                    self.incrementor[i] = 1

            cube = self._stage.GetPrimAtPath("/environments/env/target")

            xform_attr = cube.GetAttribute("xformOp:transform")
            translate_attr = xform_attr.Get().GetRow3(3)
            # print(translate_attr.Get())
            rotate_z = xform_attr.Get().GetRow3(2)
            rotate_y = xform_attr.Get().GetRow3(1)

            orig = np.array(translate_attr) / 100.0
            axis_z = np.array(rotate_z)
            axis_y = np.array(rotate_y)
            self.ur10_solid.end_effector.go_local(
                orig=orig,
                axis_x=[],
                axis_y=axis_y,
                axis_z=axis_z,
                use_default_config=True,
                wait_for_target=False,
                wait_time=5.0,
            )
            self.world.update()
            self.ur10_solid.update()

    def create_UR10(self, *args):
        super().create_UR10()

        # Load robot environment and set its transform
        solid_robot = "/physics/scene/solid"
        env_path = "/environments/env"
        CreateSolidUR10(self._stage, env_path, self.ur10_table_usd, solid_robot, Gf.Vec3d(0, 0, 0))
        # Load first rubiks cube and set its transform
        CreateRubiksCube(self._stage, self.rubiks_cube_usd, env_path + "/Rubiks_cube", Gf.Vec3d(-10, -30, 12))
        # Load second rubiks cube and set its transform
        CreateRubiksCube(self._stage, self.rubiks_cube_usd, env_path + "/Rubiks_cube1", Gf.Vec3d(-10, 30, 12))

        GoalPrim = self._stage.DefinePrim(env_path + "/target", "Xform")
        setTranslate(GoalPrim, Gf.Vec3d(60, 30, 45))
        # Load background
        CreateBackground(self._stage, self.background_usd)
        # Setup physics simulation
        SetupPhysics(self._stage)

    def register_assets(self, *args):
        # Retrieve two rubiks cubes path in the scene
        prim = self._stage.GetPrimAtPath("/environments/env")
        obstacle_path = str(prim.GetPath()) + "/Rubiks_cube"
        obstacle_path_1 = str(prim.GetPath()) + "/Rubiks_cube1"

        # Create world and robot object
        self.world = World(self._dc, self._mp)
        self.ur10_solid = UR10(
            self._stage,
            self._stage.GetPrimAtPath(str(prim.GetPath()) + "/ur10"),
            self._dc,
            self._mp,
            self.world,
            "/physics/scene/solid",
            default_config,
        )

        # Set robot end effector
        orig = np.array([0.7, 0.0, 0.5])
        axis_x = np.array([0.0, 0.0, -1.0])
        self.ur10_solid.end_effector.go_local(
            orig=orig,
            axis_x=axis_x,
            axis_y=[],
            axis_z=[],
            use_default_config=True,
            wait_for_target=False,
            wait_time=5.0,
        )

        # Register both rubiks cubes and set them as obstacles
        i = 0
        for p in self._stage.GetPrimAtPath(str(prim.GetPath()) + "/sortbot_housing/Collision").GetChildren():
            self.world.register_object(0, p.GetPath().pathString, "housing_" + str(i))
            self.world.make_obstacle("housing_" + str(i), 3, (0.072, 0.072, 0.072))
            i += 1
        i = 0
        for p in self._stage.GetPrimAtPath(str(prim.GetPath()) + "/pallet_holder/Collision").GetChildren():
            self.world.register_object(0, p.GetPath().pathString, "holder_" + str(i))
            self.world.make_obstacle("holder_" + str(i), 3, (0.072, 0.072, 0.072))
            i += 1
        self.world.register_object(0, obstacle_path, "rubiks_cube")
        self.world.register_object(0, obstacle_path_1, "rubiks_cube1")
        self.world.make_obstacle("rubiks_cube", 3, (0.072, 0.072, 0.072))
        self.world.make_obstacle("rubiks_cube1", 3, (0.072, 0.072, 0.072))

        # Track the handles of the two rubiks cubes as obstacles
        self._obstacles.append(self.world.get_object_from_name("rubiks_cube"))
        self._obstacles.append(self.world.get_object_from_name("rubiks_cube1"))

        # # Create domain
        # blocks_world_suppressors = BlocksWorldSuppressors(ur10_solid, world, block_colors)
        # lookatcommander = LookAtCommander(ur10_solid)
        # lookatcommanders = {"short": lookatcommander, "medium": lookatcommander}
        # config_modulator = ConfigModulator(self._mp, ur10_solid.rmp_handle, False)
        # domain = Domain(
        #     ur10_solid, None, lookatcommanders, config_modulator, blocks_world_suppressors, block_colors, world, 30
        # )
        # self._domains.append(domain)

        # self._executor = concurrent.futures.ThreadPoolExecutor(max_workers=len(self._domains))
