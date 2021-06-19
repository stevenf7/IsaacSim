# Copyright (c) 2020-2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

import sys
import os
from pxr import Gf
import concurrent.futures
import numpy as np

from omni.isaac.samples.scripts.utils.franka import Franka, default_config
from omni.isaac.samples.scripts.utils.world import World
from omni.isaac.samples.scripts.utils.state_machine import *
from omni.isaac.samples.scripts.utils.behavior_states import *
from omni.isaac.samples.scripts.utils.behavior_helpers import *
from .scenario import create_solid_franka, create_background, setup_physics, create_blocks, Scenario


class PickAndPlaceSimple(HierarchicalState):
    """ Complete pick and place behavior sequencing a pick and a place.

    PickBlock --> PlaceBlock

    These sub state machines handle suppressing and unsuppressing environmental collisions at
    appropriate times. block_index is supplied on construction to enable the pick behavior to
    suppress just the block in question.
    """

    def __init__(
        self,
        domain,
        block_index,
        block_place_orig,
        target_axis_y=np.array([0.0, 1.0, 0.0]),
        use_full_orientation_constraint_on_pick=True,
    ):
        self.domain = domain
        self.block_index = block_index
        self.block_place_orig = block_place_orig
        self.target_axis_y = target_axis_y
        self.use_full_orientation_constraint_on_pick = use_full_orientation_constraint_on_pick

    def setup(self):
        pick_info = MakeNaturalPickInfo(self.domain, self.block_index)
        self.pick_block = PickBlock(
            self.domain, pick_info, self.block_index, self.use_full_orientation_constraint_on_pick
        )
        self.place_block = PlaceBlock(self.domain, self.block_place_orig, self.target_axis_y)
        self.pick_block.next_state = self.place_block

        super().__init__(init_state=self.pick_block)

    def enter(self):
        self.setup()
        super().enter()


class StackBlocksSimple(HierarchicalState):
    """ Full block stacking behavior stacking blocks in the order of the colors given in
    domain.block_colors.

    Runs pick-and-place behavior.
    """

    def __init__(self, domain):
        self.domain = domain
        init_state = latest_behavior = Behavior()
        for block_index, color in enumerate(domain.block_colors):
            block_tower_place_orig = np.array(
                [domain.goal_x, domain.goal_y, domain.block_height / 2 + block_index * domain.block_height]
            )
            tower_pick_and_place_behavior = Behavior(PickAndPlaceSimple(domain, block_index, block_tower_place_orig))
            latest_behavior.terminal_transition = NextStateTransition(tower_pick_and_place_behavior)
            latest_behavior = tower_pick_and_place_behavior

        super().__init__(init_state)


class SimpleStack(Scenario):
    """ Defines a block stacking scenario

    Scenarios define the life cycle within kit and handle init, startup, shutdown etc.
    """

    def __init__(self, dc, mp):
        super().__init__(dc, mp)

    def reset_blocks(self, *args):
        if self._timeline.is_playing():
            for domain in self._domains:
                domain.block_locations.reset([("00_block_blue", (60, 20, 12)), ("00_block_green", (60, -20, 12))])

    def stop_tasks(self, *args):
        super().stop_tasks()
        for domain in self._domains:
            domain.stop = True
        self.reset_blocks()

    def step(self, step):
        if self._timeline.is_playing():
            for domain in self._domains:
                domain.block_locations.update()
                domain.franka.update()
                domain.tick(step)

    def create_franka(self, *args):
        super().create_franka()

        # Load robot environment and set its transform
        env_path = "/environments/env"
        create_solid_franka(self._stage, "/environments/env", self.franka_table_usd, Gf.Vec3d(0, 0, 0))
        create_blocks(
            self._stage,
            [self.green_cube_usd, self.blue_cube_usd],
            [env_path + "/Blocks/block_01", env_path + "/Blocks/block_02"],
            [Gf.Vec3d(60, 15, 12), Gf.Vec3d(60, -15, 12)],
        )
        # Load background
        create_background(self._stage, self.background_usd)
        # Setup physics simulation
        setup_physics(self._stage)

    def register_assets(self, *args):
        self._domains = []

        # Blocks to pick and place
        block_colors = ["blue", "green"]

        # Prim path of two blocks and their handles
        prim = self._stage.GetPrimAtPath("/environments/env")
        green_path = str(prim.GetPath()) + "/Blocks/block_01/Cube"
        blue_path = str(prim.GetPath()) + "/Blocks/block_02/Cube"
        handle_3 = self._dc.get_rigid_body(green_path)
        handle_4 = self._dc.get_rigid_body(blue_path)

        # Create world and robot object
        world = World(self._dc, self._mp)
        franka_solid = Franka(
            self._stage,
            self._stage.GetPrimAtPath(str(prim.GetPath()) + "/Franka/panda"),
            self._dc,
            self._mp,
            world,
            default_config,
        )

        # Register two blocks and set them as obstacles
        world.register_object(handle_3, green_path, "00_block_green")
        world.register_object(handle_4, blue_path, "00_block_blue")
        world.register_object(0, str(prim.GetPath()) + "/DemoTable/simple_table/CollisionCube", "table")
        world.make_obstacle("00_block_green", 3, (0.05, 0.05, 0.05))
        world.make_obstacle("00_block_blue", 3, (0.05, 0.05, 0.05))

        # Create domain
        blocks_world_suppressors = BlocksWorldSuppressors(franka_solid, world, block_colors)
        domain = Domain(franka_solid, None, blocks_world_suppressors, block_colors, world, 30)
        self._domains.append(domain)

        self._executor = concurrent.futures.ThreadPoolExecutor(max_workers=len(self._domains))

    def task(self, domain):
        try:
            # Define the state machine
            start_state = latest_state = Behavior()
            stack_blocks = StackBlocksSimple(self._domains[0])
            latest_state.terminal_transition = NextStateTransition(stack_blocks)

            # Run the state machine.
            run_state_machine(start_state, self._domains[0].step_rate, [self._domains[0]])

        except Exception as exc:
            print("generated an exception: %s" % (exc))
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)

    def perform_tasks(self, *args):
        super().perform_tasks()
        self._domains[0].stop = False
        self._executor.submit(self.task, self._domains[0])
