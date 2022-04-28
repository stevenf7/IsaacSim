# Copyright (c) 2022, NVIDIA  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.


import argparse
from collections import OrderedDict
import copy
import math
import numpy as np
import random
import sys

from omni.isaac.core.utils.stage import get_stage_units
from omni.isaac.core.utils.rotations import gf_quat_to_np_array

from df import *
from dfb import DfGoTarget, DfApproachGrasp, DfCloseGripper, DfOpenGripper
import math_util
from motion_commander import MotionCommand, PosePq, closest_R
from user.build_block_tower import build_context


class DoNothing(DfAction):
    pass


def build_tree(tools):
    context = build_context(tools)
    tree = DfTree(DoNothing(), monitors=context.monitors)
    # tree._tail_monitors.extend(context.tail_monitors)
    tree.bind_context(context)
    return tree
