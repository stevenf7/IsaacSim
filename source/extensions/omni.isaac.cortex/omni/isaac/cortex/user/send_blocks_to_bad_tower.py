# Copyright (c) 2022, NVIDIA  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

import numpy as np
import time

from df import DfNetwork, DfAction
import user.build_block_tower as bbt

reload_list = [bbt]


class SendBlocksToBadTower(DfAction):
    def enter(self):
        try:
            print("sending blocks to (bad) tower")
            bad_order = ["yellow", "blue", "red", "green"]
            bad_stack = [("%s_block" % c) for c in bad_order]
            for i, name in enumerate(bad_stack):
                dz = (i + 0.5) * self.context.block_height
                print("%d) %s, dz: %f" % (i, name, dz))

                p = self.context.block_tower.tower_position + np.array([0.0, 0.0, dz])
                q = np.array([1.0, 0.0, 0.0, 0.0])
                self.context.blocks[name].obj.set_world_pose(p, q)
                self.context.blocks[name].obj.sync_sim()
        except Exception as e:
            print("\nProblem sending blocks to (bad) tower.")
            import traceback

            traceback.print_exc()


def build_behavior(tools):
    context = bbt.build_context(tools)
    behavior = DfNetwork(SendBlocksToBadTower(), monitors=context.monitors)
    behavior.bind_context(context)
    return behavior
