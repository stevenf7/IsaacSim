# Copyright (c) 2022, NVIDIA  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

import numpy as np

from cortex_object import CortexObject
from df import DfNetwork, DfAction
from dfb import DfToolsContext
from math_util import to_stage_units


class SendBlocksToBadTower(DfAction):
    def __init__(self):
        self.tower_position = np.array([0.25, 0.4, 0.0])
        self.block_height = 0.0515

    def enter(self):
        try:
            print("sending blocks to (bad) tower")
            bad_order = ["yellow", "blue", "red", "green"]
            bad_stack = [("%s_block" % c) for c in bad_order]
            for i, name in enumerate(bad_stack):
                dz = (i + 0.5) * self.block_height
                print("%d) %s, dz: %f" % (i, name, dz))

                p = self.tower_position + np.array([0.0, 0.0, dz])
                q = np.array([1.0, 0.0, 0.0, 0.0])
                obj = self.context.tools.objects[name]
                obj.set_world_pose(to_stage_units(p), q)
                CortexObject(obj).sync_sim()
        except Exception as e:
            print("\nProblem sending blocks to (bad) tower.")
            import traceback

            traceback.print_exc()


def build_behavior(tools):
    return DfNetwork(SendBlocksToBadTower(), context=DfToolsContext(tools))
